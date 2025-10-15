import os 
import asyncio
import threading
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS 
from models.models import * 
from models.models import Base, engine
from controllers.auth_controller import auth_bp
from controllers.ChatSocketController import *
from agentsComponents.clases.intermediador import Intermediario


load_dotenv()
app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") 
Base.metadata.create_all(engine)

salas_activas = {}  # room_name -> Intermediario
#Inicializar Sockets
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
# Cargar eventos de sockets
register_sockets(socketio,salas_activas)

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
    print("se inicializa la sala")
    room_session = get_or_create_Active_room_session(room_name,topic)
    if(room_session["primera_inicializacion"] == True):
        print(f"id de la sala:{room_session["id"]}")
        #Recuperamos los ultimos promts para cada agente
        current_prompts = get_current_prompts()
        prompt_clasificador = current_prompts.get("Clasificador","Prompt por defecto del clasificador")
        prompt_puntuador = current_prompts.get("Puntuador","Prompt por defecto del puntuador")
        prompt_curador = current_prompts.get("Curador", "Prompt por defecto del curador")
        prompt_orientador = current_prompts.get("Orientador", "Prompt por defecto del orientador")
        #Recuperamos la configuracion del sistema multiagente 
        configuracion_multiagente = get_multiagent_config()
        tamaño_ventana_mensajes = configuracion_multiagente.ventana_mensajes
        tiempo_fase_1 = configuracion_multiagente.fase_1_segundos 
        tiempo_fase_2 = configuracion_multiagente.fase_2_segundos
        update_interval = configuracion_multiagente.update_interval

        intermediario = Intermediario(
            tamañoVentana=tamaño_ventana_mensajes,
            prompt_agenteClasificador=prompt_clasificador,
            prompt_agentePuntuador=prompt_puntuador,
            prompt_agenteCurador=prompt_curador,
            prompt_agenteOrientador=prompt_orientador,
            socketIo=socketio,
            sala=room_name,
            emit_callback=lambda evento, resultado, sala: emitir_resultado_socket(socketio,evento,resultado,sala)
            )
        
        asyncio.run(intermediario.start_session(topic))
        intermediario.start_processing()

        timer = threading.Thread(target=intermediario.start_timer, args=((tiempo_fase_1, tiempo_fase_2), update_interval))
        timer.start()
        # Guardar el intermediario en el dict de salas
        salas_activas[room_name] = intermediario

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
            intermediario = salas_activas.get(room_name)
            asyncio.run(intermediario.stop_session())
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
    
@app.route("/api/cuantosagentes", methods=["GET"])
def get_agents():
    """
    Endpoint: Retorna la lista de nombres únicos de agentes registrados.
    """
    agents = get_all_agents()
    return jsonify({"agents": agents}), 200

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



@app.route("/api/multiagent-config", methods=["GET", "POST"])
def multiagent_config():
    
    if request.method == "GET":
        config = get_multiagent_config()
        if not config:
            return jsonify({"error": "No configuration found"}), 404
        return jsonify({
            "ventana_mensajes": config.ventana_mensajes,
            "fase_1_segundos": config.fase_1_segundos,
            "fase_2_segundos": config.fase_2_segundos,
            "update_interval": config.update_interval,
            "created_at": config.created_at.isoformat()
        }), 200

    if request.method == "POST":
        # Validar campos obligatorios
        try:
            data = request.json 
            ventana_mensajes = data["ventana_mensajes"]
            fase_1_segundos = data["fase_1_segundos"]
            fase_2_segundos = data["fase_2_segundos"]
            update_interval = data["update_interval"]
            print(ventana_mensajes)
            print(fase_1_segundos)
            print(fase_2_segundos)
            print(update_interval)

        except (TypeError, KeyError):
            return jsonify({"error": "Missing required fields"}), 400

        config = get_multiagent_config()
        if config is None:
            # Crear configuración nueva
            result = create_multiagent_config(
                ventana_mensajes=ventana_mensajes,
                fase_1_segundos=fase_1_segundos,
                fase_2_segundos=fase_2_segundos,
                update_interval=update_interval
            )
            return jsonify({
                "ventana_mensajes": result.ventana_mensajes,
                "fase_1_segundos": result.fase_1_segundos,
                "fase_2_segundos": result.fase_2_segundos,
                "update_interval": result.update_interval,
                "created_at": result.created_at.isoformat()
            }), 201

        # Actualizar configuración existente
        result = update_multiagent_config(
            ventana_mensajes=ventana_mensajes,
            fase_1_segundos=fase_1_segundos,
            fase_2_segundos=fase_2_segundos,
            update_interval=update_interval
        )
        return jsonify({
            "ventana_mensajes": result.ventana_mensajes,
            "fase_1_segundos": result.fase_1_segundos,
            "fase_2_segundos": result.fase_2_segundos,
            "update_interval": result.update_interval,
            "created_at": result.created_at.isoformat()
        }), 200


if __name__ == "__main__":
    #app.run(debug=True)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
