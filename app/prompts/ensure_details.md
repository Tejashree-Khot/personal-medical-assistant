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
1. has_sufficient_details: JSON boolean (true/false), no quotes.

2. Set to true if:

- All critically essential details are provided.

- User explicitly declines to provide more info (e.g., "no", "skip").

3. Set to false if:

- Essential info is missing. Action: Ask a concise follow-up question

4. Strict Adherence: If the user declines to share info, you must stop requesting it immediately. Do not explain why the info is needed or try to build trust. Simply set has_sufficient_details to true

5. No Templates: Do not use headers like "General Guidance," "Possible Causes," or "Requested Details."

Example of valid boolean: "has_sufficient_details": true
Example of INVALID string: "has_sufficient_details": "true"