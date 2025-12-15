# Titulo-Trabajo
Titulo-Trabajo
# Instrucciones de uso
- Front: 
    - `cd sala-debate\frontend\sala-de-conversacion2`
    - `npm i; npm run dev`
    - se debe crear un .env con la variable NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
      esto apunta a donde está corriendo el backend. 
- Backend: 
    - Crear .env en este directorio `cd sala-debate\nuevoBackend\app`
    el .env debe tener API_KEY='.....', como en este caso se usó chatgpt 4o-mini entonces se debe tener una apiket de openai 
    se pueden usar otros modelos si se cambia el parametro de la factory que se usa para crear los agentes. Esto está  en la carpeta agentComponents
    Tambien se debe tener la variable DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/NOMBREBD
    - crear entorno .venv con python3
        - `python3 -m venv .venv`
        - `.venv\Scripts\activate`
        - `pip install -r .\requirements.txt`

    para correr el backend se usa 'uvicorn app.main:app --reload --host 0.0.0.0 --port 8000'

- Base de datos. en la carpeta nuevoBackend/baseDatos se encuentra el archivo que se tiene que usar para crear y poblar las tablas que se necesitan para correr el sistema. Se usa una base de datos Postgres para el proeycto. 





las requirements son las siguientes:
fastapi 
uvicorn 
python-socketio[asgi] 
python-dotenv
sqlalchemy
agentscope
psycopg2-binary
