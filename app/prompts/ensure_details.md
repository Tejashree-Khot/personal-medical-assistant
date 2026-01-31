# User Input

{user_input}

## User Profile Context

{user_profile}

## Output Format(strict JSON)

Return ONLY a JSON object. No prose, no explanations.

```json
{{
  "has_sufficient_details": [LITERAL_BOOLEAN],
  "response": "markdown_string",
  "requested_details": "markdown_string"
}}
```

Rules:
1. "has_sufficient_details" must be a JSON boolean literal (true or false).
2. DO NOT use quotes like "true" or "false".
3. If details are missing, set "has_sufficient_details" to false.

Example of valid boolean: "has_sufficient_details": true
Example of INVALID string: "has_sufficient_details": "true"