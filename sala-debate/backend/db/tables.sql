-- Tabla base con nombre de sala 
CREATE TABLE room_names (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

-- Cada sesión concreta 
CREATE TABLE room_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_name TEXT NOT NULL,
    topic TEXT,              
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Mensajes por sesión
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    room_session_id UUID REFERENCES room_sessions(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

GRANT INSERT, SELECT, UPDATE, DELETE ON TABLE messages TO chat_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO chat_user;



CREATE TABLE temas (
    id SERIAL PRIMARY KEY,
    tema_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
