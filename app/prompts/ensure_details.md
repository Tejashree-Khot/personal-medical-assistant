# User Input

{user_input}

## User Profile Context

{user_profile}

set has_sufficient_details even if details are not provided

## Output Format(strict JSON)

```json
{{
  "has_sufficient_details": "bool true or false. Based on user profile and medical issue analyse the neccessity of the details",
  "response": "**well-structured markdown medical response** with headings, bullet points, and clear sections.",
  "requested_details": "Request missing details in anothe section for personlized solution."
}}
```
