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

- User explicitly or implicitly declines to provide more info (e.g., "no", "skip", "I don't want to share", "I'd rather not say", "that's all I have", "just answer", "no more details", "prefer not to answer", or any refusal/reluctance to share further information).

3. Set to false if:
- Populate the "response" field with exactly one concise clarifying question.

- Forbidden: Do not include any other text, advice, or bullet points within the JSON fields.

- Leave "requested_details" as an empty string.

4. Strict Adherence: If the user declines, refuses, or shows any reluctance to share info, you MUST immediately set has_sufficient_details to true and leave "response" and "requested_details" as empty strings. Do not explain why the info is needed. Do not try to convince, persuade, or build trust. Do not give a general answer. Simply set has_sufficient_details to true.

5. No Templates: Do not use headers like "General Guidance," "Possible Causes," or "Requested Details."

Example of valid boolean: "has_sufficient_details": true
Example of INVALID string: "has_sufficient_details": "true"