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
WHERE created_at >= '2025-11-17'::date
  AND created_at <  '2025-11-18'::date;

"""
query2 = """
SELECT *
FROM messages
WHERE room_session_id IN (
'fd701be3-5fe1-4a3a-a482-db52a09d3ca5', 
'92e5445e-7af0-4fbe-b53d-9e080f65d176',
'7b554461-322e-46d7-8fbe-76b0d54d9427',
'6839986a-b86d-4f57-bc9b-88af1caca663',
'24869212-0a3b-438a-9248-dc4c95767bae',
'c220708e-1bbb-4e28-a7fb-872af1de3379',
'3c334700-82d8-4b44-941e-10c028889239',
'5bce17ae-3d33-4713-b4f5-a63f888841d6'
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
cursor.execute(query3)

# Obtener nombres de columnas y filas
columnas = [desc[0] for desc in cursor.description]
filas = cursor.fetchall()

# --- Guardar como CSV ---
with open("prompts_sesion1.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(columnas)
    writer.writerows(filas)

cursor.close()
conn.close()
