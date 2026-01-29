#!/bin/bash

docker exec -i app-medical_assistant_db-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -F "" <<EOF | jq '.' > user_profile.json
COPY (
    SELECT json_agg(row_to_json(t))
    FROM (
        SELECT *
        FROM user_profile
        LIMIT 10
    ) t
) TO STDOUT;
EOF
