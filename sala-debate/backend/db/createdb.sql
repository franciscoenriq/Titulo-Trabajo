CREATE DATABASE chatdb;
CREATE USER chat_user WITH PASSWORD 'chat_user_password';
ALTER ROLE chat_user SET client_encoding TO 'utf8';
ALTER ROLE chat_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE chat_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE chatdb TO chat_user;
GRANT ALL ON SCHEMA public TO chat_user;

-- Dar permisos sobre todas las tablas existentes
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chat_user;

-- Dar permisos sobre todas las secuencias (necesario para seriales/id autoincrementales)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chat_user;