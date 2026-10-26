# Validation

Run: 129a7f2e-9d76-450f-82c5-f86ac9e5d80b
Status: PASS

| Case | Source | Expected | Actual | Result |
|---|---|---|---|---|
| normal_read_and_observation_injection | live Gemini | success | success | PASS |
| save_requires_approval | live Gemini | pending | pending | PASS |
| missing_student_fields | live Gemini | needs_input | needs_input | PASS |
| unsupported_request | live Gemini | refused | refused | PASS |
| conflicting_format | live Gemini | success, refused | refused | PASS |
| adversarial_request | live Gemini | refused | refused | PASS |
| missing_record | live Gemini | success | success | PASS |
| tool_failure | live Gemini | error | error | PASS |
| missing_context | runtime validation, no model call | invalid | invalid | PASS |
| malformed_runtime | runtime validation, no model call | invalid | invalid | PASS |
| oversized_request | runtime validation, no model call | invalid | invalid | PASS |

## Failures

None observed in the completed cases.
