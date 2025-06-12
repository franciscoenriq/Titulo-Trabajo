from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_cors import CORS 
from task.analize import *
import os 
from flask_pymongo import PyMongo
from models import messages
from dotenv import load_dotenv
from agentsComponents.evaluador import *
load_dotenv()
app = Flask(__name__)
CORS(app)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") 
redis_url = os.getenv("REDIS_URL")

#conectamos a mongo
mongo = PyMongo(app)
app.mongo = mongo
#conectamos con redis 
#redis_conn = Redis.from_url(redis_url)
socketio = SocketIO(app, cors_allowed_origins="*")

#temas a discutir 
temas = {}
"""
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    user_message = data["message"]
    try:
        #response = get_chat_response(user_message)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
"""    
@app.route("/api/messages", methods=["POST"])
def create_message():
    data = request.json
    message_id = messages.insert_message(
        room_id=data["room_id"],
        user_id=data["user_id"],
        content=data["content"]
    )
    return jsonify({"message_id": message_id}), 201

@app.route("/api/check-mongo")
def check_mongo():
    uri = os.getenv("MONGO_URI")
    if not uri:
        return {"error": "MONGO_URI not loaded"}, 500
    try:
        collections = app.mongo.db.list_collection_names()
        return {"status": "ok", "collections": collections}
    except Exception as e:
        return {"error": str(e)}, 500
    
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
    message_data = {'username': username, 'content': content}
    emit('message', message_data, room=room)

    # Analizar el mensaje usando IA
    resultado = analizar_argumento(room, content,username)

    # Enviar la evaluación a la misma sala
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
    temas[room] = topic
    inicializar_conversacion(room, topic)
    return jsonify({"status": "initialized"}), 201

@app.route('/api/tema/<room>', methods=["GET"])
def obtener_tema(room):
    tema = temas.get(room,"sin tema definido")
    return jsonify({"tema":tema})


if __name__ == "__main__":
    #app.run(debug=True)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
