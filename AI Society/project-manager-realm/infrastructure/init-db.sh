#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER intelligence WITH PASSWORD 'dev_password';
    CREATE USER workspace_council WITH PASSWORD 'dev_password';
    
    CREATE DATABASE intelligence;
    CREATE DATABASE workspace_council;
    
    GRANT ALL PRIVILEGES ON DATABASE intelligence TO intelligence;
    GRANT ALL PRIVILEGES ON DATABASE workspace_council TO workspace_council;
    
    \c intelligence
    GRANT ALL ON SCHEMA public TO intelligence;
    \c workspace_council
    GRANT ALL ON SCHEMA public TO workspace_council;
EOSQL
