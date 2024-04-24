SELECT 'CREATE DATABASE inventory_database_internal_items' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'inventory_database_internal_items')\gexec

\c inventory_database_internal_items

CREATE TABLE IF NOT EXISTS Items (
  upc TEXT PRIMARY KEY,
  name TEXT,
  quantity TEXT,
  quantityunit TEXT
);