-- Tabla de salas
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- identificador único y global
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Tabla de mensajes relacionados a salas
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
