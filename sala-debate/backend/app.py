import os 
import asyncio
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS 
from models.models import * 
from models.models import Base, engine
from controllers.auth_controller import auth_bp
from controllers.ChatSocketController import *
from agentsComponents.clases.factory_agents import ReActAgentFactory
from agentsComponents.clases.pipeLine_ejecucion import CascadaPipeline


load_dotenv()
app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") 

Base.metadata.create_all(engine)

salas_activas = {}  # room_name -> CascadaPipeLine
#Inicializar Sockets
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
# Cargar eventos de sockets
register_sockets(socketio,salas_activas)
#Creamos la factory con la cual vamos a crear los agentes
factory = ReActAgentFactory()


@app.route("/api/estado-salas",methods=["GET"])
def get_estado_salas():
    """
    Devuelve el estado más reciente de cada sala.
    Ejemplo de respuesta:
    [
      {"room_name": "Sala_1", "status": "active"},
      {"room_name": "Sala_2", "status": "closed"}
    ]
    """
    try:
        statuses = get_latest_room_statuses()
        return jsonify(statuses), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/init-topic",methods=["POST"])
def init_topic():
    """
    Se extrae el nombre de la sala y el prompt inicial que en verdad es el tema que se va a discutir en la sala 
    Luego se crea la room_session o si estaba ya activa se devuelve el id. 
    Si se tuvo que crear entonces se tiene que setear la clase del sistema multiagente.
    """
    data =request.json
    room_name = data["room"]
    topic = data["prompt_inicial"]

    if room_name in salas_activas:
        print("sala ya inicializada")
        return jsonify({"status":"ya_inicializado"}),200

    room_session = get_or_create_Active_room_session(room_name,topic)
    if(room_session["primera_inicializacion"] == True):
        print(f"id de la sala:{room_session["id"]}")
        #Recuperamos los ultimos promts para cada agente
        current_prompts = get_current_prompts()
        
        promt_curador = current_prompts.get("Curador", "Prompt por defecto del curador")
        promt_orientador = current_prompts.get("Orientador", "Prompt por defecto del orientador")
        #Creamos la clase pipeLine 
        cascada_pipeline = CascadaPipeline(factory, promt_curador, promt_orientador)

        # Iniciar la sesión asincrónica
        asyncio.run(cascada_pipeline.start_session(topic))

        # Guardar el pipeline en el dict de salas
        salas_activas[room_name] = cascada_pipeline

        return jsonify({"status": "initialized"}), 201
    if(room_session["primera_inicializacion"] == False):
        print(f"id de la sala ya inicializada:{room_session["id"]}")
        return jsonify({"status":"ya_inicializado"}),200

@app.route("/api/close-room", methods=["POST"])
def close_room():
    data = request.json
    room_name = data.get("room")

    if not room_name:
        return jsonify({"error": "Se requiere el nombre de la sala"}), 400

    try:
        result = close_active_room_session(room_name)
        if not result:
            return jsonify({"status": "no_active_session", "message": "No hay sesión activa para esta sala"}), 404

        # Limpiar la instancia en memoria
        if room_name in salas_activas:
            cascada_pipeline = salas_activas.get(room_name)
            asyncio.run(cascada_pipeline.stop_session())
            del salas_activas[room_name]


        return jsonify({"status": "closed", **result}), 200

    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tema/<room>", methods=["GET"])
def obtener_tema(room):
    topic = get_active_room_topic(room)
    if topic is None:
        return jsonify({"tema": "sin tema definido"}), 404
    return jsonify({"tema":topic}), 200


@app.route("/api/prompts",methods=["GET","POST"])
def get_prompts():
    '''
    GET  -> Consultar el último prompt de cada agente
    POST -> Actualizar prompt(s) de uno o varios agentes # ejemplo(1) {"Curador": "nuevo prompt", "Orientador": "otro prompt"}
    (2) {"Curador": "nuevo prompt"}

    '''
    if request.method == "GET":
        prompts = get_current_prompts()
        return jsonify(prompts), 200
    
    if request.method == "POST":
        data = request.json  
        created_ids = []
        for agent_name, prompt_text in data.items():
            prompt_id = create_promt(agent_name, prompt_text)
            created_ids.append({"agent": agent_name, "id": prompt_id})
        #el update devuelve la lista de agentes actualizados 
        return jsonify({
            "status": "success", 
            "updated": created_ids}), 201

@app.route("/api/rooms",methods=["GET","POST"])
def get_salas():
    '''
    GET  -> Devuelve las salas a las cuales los usuarios pueden conectarse a chatear
    POST -> Crea una nueva sala  
    '''
    if request.method == "GET":
        rooms = get_rooms()
        return jsonify(rooms), 200
    if request.method == "POST":
        data = request.json 
        room_id = create_room_name(data["nombre_sala"])
        return jsonify({"id":room_id,"nombre":data["nombre_sala"]}),201

@app.route("/api/room-messages/<room_name>",methods=["GET"])
def get_room_messages(room_name):
    #recuperamos el id de la sesion activa
    id_session = get_active_room_session_id(room_name)
    if not id_session:
        return jsonify({"error":"No hay sesion activa"}) , 404

    messages = get_messages_by_room(id_session)
    return jsonify(messages), 200 
if __name__ == "__main__":
    #app.run(debug=True)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
