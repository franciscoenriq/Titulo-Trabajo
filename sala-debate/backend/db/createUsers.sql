CREATE TYPE userrole AS ENUM ('alumno', 'monitor');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role userrole NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
