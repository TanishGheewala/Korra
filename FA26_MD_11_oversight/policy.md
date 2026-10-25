# Oversight policy

- Protected action: `save_database`. Reads need no approval; every insert pauses first.
- Reviewer context: original request, action, arguments, risk, decision ID, version, status and deadline.
- Approve: insert the reviewed record and complete the checkpoint in one transaction.
- Reject or cancel: stop without inserting. Terminal requests cannot resume.
- Revise: validate changes, increment the version and remain pending. A new approval is required; the original deadline stays unchanged.
- Timeout: default 10 minutes. The restart demo allows 24 hours. Expiry wins over any late decision and never approves automatically.
- Invalid, unauthorized, stale or repeated decisions are refused without executing the action.
- Priority: expiry first; otherwise the first valid decision acquiring the database transaction wins. Pending requests display oldest first.
- Authorization: the local operator with OS/Docker access is the reviewer. The interactive review command passes a generated private token; model proposals never receive it. This is a local demonstration, not a multi-user authentication service.
- State: SQLite stores the full proposal and stable UUID. A Docker volume preserves pending requests and records across container recreation.
- Exactly once: the insert, completion state and audit events commit together under a write lock. Failure rolls back the transaction; retries cannot repeat a committed insert.
- Failure: duplicate email becomes `failed`; unavailable storage stops the command. No failure path assumes approval.
- Audit: only time, ID, version, event, actor, status and argument hash. No prompt, student fields, token or API key.
- Scope: this version uses the Project 10 student fields with SQLite. Gemini input is optional; the complete approval lifecycle also runs directly from the terminal.

## Evidence

| Section | Evidence |
|---|---|
| 1 | This policy, `state.svg`, `decision.schema.json` |
| 2 | `before.txt`, `run.json`, `01-paused.png` |
| 3 | `before.txt`, `summary.json`, `02-outcomes.png` |
| 4 | `after.txt`, `audit.json`, `containers-before.txt`, `containers-after.txt`, `03-restart.png`, `04-final.png` |
