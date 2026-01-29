#!/bin/bash

docker exec -i app-medical_assistant_db-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A <<EOF > session_state.jsonl
COPY (
    SELECT row_to_json(t)
    FROM (
        SELECT *
        FROM session_state
        LIMIT 10
    ) t
) TO STDOUT;
EOF
