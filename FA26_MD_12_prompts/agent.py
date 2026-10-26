import hashlib
import json
import os
import re
import sqlite3
import urllib.error
import urllib.request
import uuid
from jsonschema import ValidationError

from oversight import Store, validate_student
from templates import render, schema, system_prompt, validate


MAX_STEPS = 3
REASONS = {
    "read_database": {"lookup"}, "save_database": {"new_student"},
    "finish": {"done"}, "clarify": {"missing_fields"},
    "refuse": {"out_of_scope", "unsafe_request"},
}
MESSAGES = {
    "success": "Records retrieved.", "pending": "Human approval required. No student was inserted.",
    "refused": "This request is outside the permitted actions.",
    "needs_input": "Provide name, email, major, GPA and enrollment date for a new student.",
    "invalid": "The request or model output has an invalid format.",
    "error": "The operation failed. No automatic retry was made.",
    "limit": "The action limit was reached.",
}


class ModelError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class Gemini:
    def __init__(self):
        self.key = os.getenv("GOOGLE_API_KEY", "")
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.calls = 0

    def select(self, policy, runtime):
        if not self.key:
            raise ModelError("missing_api_key")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", self.model):
            raise ModelError("invalid_model")
        body = {"systemInstruction": {"parts": [{"text": policy}]},
                "contents": [{"role": "user", "parts": [{"text": runtime}]}],
                "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": schema("action")}}
        request = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.key})
        self.calls += 1
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.load(response)
            parts = result["candidates"][0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts if not part.get("thought"))
            return json.loads(text)
        except urllib.error.HTTPError as error:
            raise ModelError("provider_" + str(error.code)) from None
        except (OSError, TimeoutError):
            raise ModelError("provider_unavailable") from None
        except (ValueError, KeyError, IndexError, TypeError):
            raise ModelError("malformed_model_output") from None


def read_database(store, arguments):
    if set(arguments) - {"email"}:
        raise ValueError("invalid_arguments")
    rows = store.students()
    email = arguments.get("email", "").strip().lower()
    if email:
        rows = [row for row in rows if row["email"] == email]
    return {"students": rows[:100]}


def safe_data(value, secrets):
    if isinstance(value, str):
        for secret in secrets:
            if secret and secret in value:
                value = value.replace(secret, "[redacted]")
        return re.sub(r"AIza[\w-]{35}|github_pat_[\w]{20,}|tvly-[\w-]{20,}|sk-(?:proj-)?[\w-]{30,}", "[redacted]", value)
    if isinstance(value, list):
        return [safe_data(item, secrets) for item in value]
    if isinstance(value, dict):
        return {key: safe_data(item, secrets) for key, item in value.items()}
    return value


def run(request, model=None, store=None):
    store = store or Store()
    model = model or Gemini()
    request_id = str(uuid.uuid4())
    trace = []
    secrets = [os.getenv("GOOGLE_API_KEY", "")]
    try:
        secrets.append(store.local_reviewer_token())
    except OSError:
        pass

    def event(step, stage, action, code):
        trace.append({"step": step, "stage": stage, "action": action, "code": code})

    def finish(status, code, data=None):
        event(trace[-1]["step"] if trace else 0, "stop", "none", code)
        return validate("response", {"request_id": request_id, "status": status,
                                    "message": MESSAGES[status], "data": safe_data(data or {}, secrets), "trace": trace})

    try:
        validate("request", request)
    except ValidationError:
        return finish("invalid", "invalid_request")
    policy = system_prompt()
    observations = []
    last_data = None
    for step in range(1, MAX_STEPS + 1):
        try:
            selection = model.select(policy, render(request, observations, step))
            validate("action", selection)
        except ModelError as error:
            return finish("error", error.code)
        except (ValidationError, ValueError, TypeError):
            return finish("invalid", "malformed_model_output")
        action, arguments, reason = selection["action"], selection["arguments"], selection["reason_code"]
        if reason not in REASONS[action]:
            return finish("invalid", "invalid_reason")
        event(step, "select", action, reason)
        if action in {"finish", "refuse", "clarify"}:
            if arguments and action != "clarify":
                return finish("invalid", "unexpected_arguments")
            if action == "refuse":
                return finish("refused", reason)
            if action == "clarify":
                return finish("needs_input", "missing_fields")
            if last_data is None:
                return finish("invalid", "no_observation")
            return finish("success", "completed", last_data)
        if action == "save_database" and observations:
            return finish("refused", "action_scope_changed")
        event(step, "act", action, "started")
        try:
            if action == "read_database":
                data = safe_data(read_database(store, arguments), secrets)
                event(step, "observe", action, "records_found" if data["students"] else "no_records")
                observations.append({"action": action, "status": "success", "data": data})
                last_data = data
            else:
                if not {"name", "email", "major", "gpa", "enrollment_date"}.issubset(arguments):
                    return finish("needs_input", "missing_fields")
                student = validate_student(arguments)
                pending = store.propose(student, request=request["request"])
                event(step, "observe", action, "approval_pending")
                return finish("pending", "approval_required", {"decision_id": pending["decision_id"], "version": pending["version"], "proposed_arguments": pending["proposed_arguments"]})
        except (ValueError, TypeError):
            return finish("invalid", "invalid_arguments")
        except (sqlite3.Error, OSError):
            event(step, "observe", action, "tool_error")
            return finish("error", "tool_error")
    return finish("limit", "max_steps")


def policy_hash():
    return hashlib.sha256(system_prompt().encode()).hexdigest()

