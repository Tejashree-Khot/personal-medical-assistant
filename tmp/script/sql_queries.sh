#!/bin/bash

# --- Configuration ---
# You'll need to replace these with your actual database details
DB_NAME="medical_db"
DB_USER="medical_admin"
# You might be prompted for the password unless you use a .pgpass file or environment variables

# --- SQL Command ---
SQL_COMMAND="CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestap TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"

# --- Execution ---

echo "Attempting to create the 'chat_history' table in database '$DB_NAME'..."

# Execute the SQL command using psql
# -c: Executes the command string (SQL_COMMAND)
# -d: Specifies the database name
# -U: Specifies the user name
if psql -c "$SQL_COMMAND" -d "$DB_NAME" -U "$DB_USER"; then
    echo "✅ Success: The 'chat_history' table has been created."
else
    echo "❌ Error: Failed to create the table. Check the error message above and ensure psql is installed, the user/database exist, and you have correct permissions."
    exit 1
fi

exit 0