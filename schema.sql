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

-- This is for item misses, so a human can look through
-- and manually enter item details.
CREATE TABLE IF NOT EXISTS Misses (
  upc TEXT PRIMARY KEY,
  converted BOOLEAN, -- Whether or not the UPC was originally a UPC-E.
  date BIGINT
);