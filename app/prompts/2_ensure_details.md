# Instructions
Check if user has provided sufficient details.

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
- If user explicitly states that they do not want to provide additional information, do not ask for more.
- Don't be too aggressive in asking for clarification. Only ask if necessary.

# Guidelines
- If user has provided sufficient details, set has_sufficient_details to true and response to empty string.
- If user has not provided sufficient details, set has_sufficient_details to false and response to a message asking for more details.
