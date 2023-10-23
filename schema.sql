SELECT 'CREATE DATABASE upc_database' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'upc_database')\gexec

\c upc_database

CREATE TABLE IF NOT EXISTS Items (
  upc TEXT PRIMARY KEY,
  name TEXT,
  quantity TEXT,
  quantityunit TEXT
);

CREATE TABLE IF NOT EXISTS Backups (
  pasteid TEXT,
  date BIGINT PRIMARY KEY
);