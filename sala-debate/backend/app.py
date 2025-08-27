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
from controllers.ChatSocketController import *
import eventlet

load_dotenv()
app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") 

Base.metadata.create_all(engine)

#Inicializar Sockets
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
# Cargar eventos de sockets
register_sockets(socketio)

temas = {}  # room_name -> tema
salas_activas = {}  # room_name -> session_id

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
