# Instructions
You will be provided with a question and you need to classify it as medical or non-medical.

# Classification Criteria

**MEDICAL**:
- If it's a medical question, related to symptoms, treatments, or medical conditions.

**GENERAL**:
- If it's a greeting, casual chat, or completely unrelated to Noman product

# Input

**User message:** {user_input}

# Response output

Return **strictly** in the following JSON format. Do not add any other text.

**Output format:**

```json
{{
  "is_medical": true | false
}}
```
