import psycopg2
import csv
from dotenv import load_dotenv
import os 
load_dotenv()
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
# --- Configurar conexión ---
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="chatdb",
    user="chat_user",
    password="chat_user_password"
)

cursor = conn.cursor()

# --- Consulta SQL ---
query1 = """
SELECT *
FROM room_sessions
WHERE created_at >= '2025-12-1'::date
  AND created_at <  '2025-12-2'::date;

"""
query2 = """
SELECT *
FROM messages
WHERE room_session_id IN (
'87c84f51-5a3e-4b53-b325-829b264add6f', 
'813f17ef-79c2-4178-afb1-18cea18bc564',
'85b25ef8-ea68-42ce-b18d-6560445b50a1',
'2c8913ce-2c25-4c7b-b6a5-8df1c755f160',
'7a2a93d8-c1ba-45e1-8cc7-8aa1ed9929b2',
'13f7713f-fc30-4842-85f6-001454194796',
'819240ea-2308-453c-bdc1-7588bd7878e0'
);

"""


query3 ="""
WITH ranked_prompts AS (
    SELECT
        id,
        agent_name,
        prompt,
        system_type,
        created_at,
        ROW_NUMBER() OVER (PARTITION BY agent_name ORDER BY created_at DESC) AS rn
    FROM agent_prompts
    WHERE system_type = 'default'
)
SELECT id, agent_name, prompt, system_type, created_at
FROM ranked_prompts
WHERE rn = 1;

"""

# 
cursor.execute(query2)

# Obtener nombres de columnas y filas
columnas = [desc[0] for desc in cursor.description]
filas = cursor.fetchall()

# --- Guardar como CSV ---
with open("mensajes_sesion2.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(columnas)
    writer.writerows(filas)

cursor.close()
conn.close()
