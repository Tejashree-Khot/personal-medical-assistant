# Instructions
check if user has provided sufficient details.

# Input
**User input:** {user_input}

**User profile:** {user_profile}

# Guidelines for response
- If user has provided sufficient details, set has_sufficient_details to true and response to empty string.
- If user has not provided sufficient details, set has_sufficient_details to false and response to a message asking for more details.
- If user has provided sufficient details, set has_sufficient_details to true and response to empty string else set has_sufficient_details to false and response to a message asking for more details.

# Output
Return **strictly** in the following JSON format. Do not add any other text.

**Output format:**

```json
{{
  "has_sufficient_details": true | false,
  "response": ""
}}
```
