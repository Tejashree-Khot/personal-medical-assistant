# Instructions
check if user has provided sufficient details.

# Input
**User input:** {user_input}

**User profile:** {user_profile}

# Evaluation Criteria
Consider if you need to ask for clarification:
- Age, gender, or other demographic information
- Current medications or supplements
- Existing medical conditions
- Allergies
- Duration or severity of symptoms
- Specific context about their situation
- Ask for clarification only once.
- if user explicitly states that they do not want to provide any additional information, do not ask for any additional information and set need_specialist to false.
- If need_specialist is false, return an empty string for response.
- Don't be too aggressive in asking for clarification. Only ask for clarification if you need it.

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
