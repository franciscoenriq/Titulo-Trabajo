from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_cors import CORS 
import os 
from models.models import * 
from dotenv import load_dotenv
#from agentsComponents.evaluador import *
from agentsComponents.multiagent_evaluador import *
from controllers.auth_controller import auth_bp
from models.models import Base, engine

load_dotenv()
app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") 

# Crear tablas si no existen
Base.metadata.create_all(engine)

socketio = SocketIO(app, cors_allowed_origins="*")


temas = {}  # room_name -> tema
salas_activas = {}  # room_name -> session_id

@app.route("/api/messages", methods=["POST"])
def create_message():
    data = request.json
    message_id = insert_message(
        room_id=data["room_id"],
        user_id=data["user_id"],
        content=data["content"]
    )
    return jsonify({"message_id": message_id}), 201

@app.route("/api/log-conversation-agent", methods=["POST"])
def safeConversation():
    data = request.json
    nombre_agente=data["agent"]
    mensaje=data["message"]
    print(f"info:{nombre_agente,mensaje}")
    socketio.emit("message",{
        "username":nombre_agente,
        "content":mensaje
    }, room="chat")
    return jsonify({"status":"ok"}), 200
# Socket.IO events
@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'{username} ha entrado a la sala {room}.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'{username} ha salido de la sala {room}.'}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    username = data['username']
    content = data['content']
    #extraemos la id de la sala 
    id_room = salas_activas.get(room)
    message_data = {'username': username, 'content': content}
    emit('message', message_data, room=room)
    #guardamos en la bd 
    insert_message(
        room_session_id=id_room,
        user_id=username,
        content=content
    )

    # Analizar el mensaje usando IA
    #resultado = analizar_argumento(room, content,username)
    resultado = analizar_argumento_cascada(room,content,username)
    # Enviar la evaluación a la misma sala
    if(resultado["intervencion"] == True):
        emit('evaluacion', {
            'evaluacion': resultado["evaluacion"],
            'respuesta': resultado["respuesta"],
            'intervencion': resultado["intervencion"],
            'agente':resultado["agente"],
            'evaluado':resultado["evaluado"]
        }, room=room)

@app.route("/api/init-topic",methods=["POST"])
def init_topic():
    data =request.json
    room = data["room"]
    topic = data["prompt_inicial"]

    if room in conversaciones:
        print("sala ya inicializada")
        return jsonify({"status":"ya_inicializado"}),200
    session_id = create_room_session(room_name=room, topic=topic)
    salas_activas[room] = session_id
    temas[room] = topic
    inicializar_conversacion_cascada(room, topic)
    return jsonify({"status": "initialized"}), 201

@app.route('/api/tema/<room>', methods=["GET"])
def obtener_tema(room):
    tema = temas.get(room,"sin tema definido")
    return jsonify({"tema":tema})


if __name__ == "__main__":
    #app.run(debug=True)

    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
