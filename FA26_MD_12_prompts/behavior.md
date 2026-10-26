# Behavior

| Rule | Implementation |
|---|---|
| Read records; prepare student inserts | `read_database`, `save_database` |
| Writes require human approval | Project 11 checkpoint and reviewer token |
| Missing information | `needs_input`; no invented values |
| Unsupported or unsafe requests | `refused`; no tool execution |
| Stable policy outranks input | Separate system message; runtime values encoded as JSON |
| Fixed response format | Request, action and response schemas checked in Python |
| Bounded ReAct | Select → act → observe → select; maximum three selections |
| Terminal conditions | Completion, pending approval, refusal, error or limit |
| Private content | No free-form reasoning in traces; credentials never enter the prompt |

The prompt defines behavior. Python also enforces the action list, schema, approval boundary and stopping limit. This keeps a model mistake from authorizing a database write.

Runtime variables are `request`, `context.course` and `context.term`. Extra fields, empty values and wrong types are rejected. Observations remain data and cannot authorize a save after a read.

Only action names, reason codes and result statuses enter traces. The final message comes from verified program state. The response can include requested demo records, but cannot echo arbitrary model text.

`validate.py` records live Gemini cases separately from deterministic tests. `tests.txt` covers malformed model output, action limits and tool errors using controlled inputs. `validation.json` and `matrix.md` record actual outcomes and failures. No successful live run is assumed before these files are produced.

Missing API keys, provider errors and database errors stop without a retry. The model name remains configurable. Demonstration data uses fictional `example.invalid` addresses.

## Failure handling

| Failure | Control |
|---|---|
| Malformed JSON file or model output | Structured error before action dispatch |
| Unexpected action or private reasoning field | Schema rejection |
| Observation attempts to authorize a write | Read scope cannot expand to save |
| Repeated actions | Stop at three selections |
| Provider or database failure | Safe error code; no raw exception or automatic retry |

Fixed clarification handling: known student fields now return needs_input without executing a tool. The rerun passed.
