import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parent


def schema(name):
    return json.loads((ROOT / "schemas" / f"{name}.json").read_text())


def validate(name, value):
    Draft202012Validator(schema(name), format_checker=FormatChecker()).validate(value)
    return value


def system_prompt():
    return (ROOT / "prompts" / "system.txt").read_text()


def render(request, observations, step):
    validate("request", request)
    return json.dumps({"runtime": request, "observations": observations, "selection": step}, ensure_ascii=True)
