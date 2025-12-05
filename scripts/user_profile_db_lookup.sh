#!/bin/bash
docker exec -i app-medical_assistant_db-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
\dt
SELECT * FROM user_profile LIMIT 10;
EOF