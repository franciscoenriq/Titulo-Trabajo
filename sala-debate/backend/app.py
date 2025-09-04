import os 
import asyncio
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS 
from models.models import * 
from models.models import Base, engine
from models.dbAgentsUtils import get_current_prompts
from sqlalchemy.orm import sessionmaker
from controllers.auth_controller import auth_bp
from controllers.ChatSocketController import *
from agentsComponents.clases.factory_agents import ReActAgentFactory
from agentsComponents.clases.pipeLine_ejecucion import CascadaPipeline
Session = sessionmaker(bind=engine)

load_dotenv()
app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") 

Base.metadata.create_all(engine)

temas = {}  # room_name -> tema
salas_activas = {}  # room_name -> CascadaPipeLine
#Inicializar Sockets
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
# Cargar eventos de sockets
register_sockets(socketio,salas_activas)
#Creamos la factory con la cual vamos a crear los agentes
factory = ReActAgentFactory()


@app.route("/api/init-topic",methods=["POST"])
def init_topic():
    """
    #TODO:hacer documentacion
    """
    data =request.json
    room = data["room"]
    topic = data["prompt_inicial"]

    if room in salas_activas:
        print("sala ya inicializada")
        return jsonify({"status":"ya_inicializado"}),200
    
    #Recuperamos los ultimos promts para cada agente
    with Session() as session:
        current_prompts = get_current_prompts(session)
    
    promt_curador = current_prompts.get("Curador", "Prompt por defecto del curador")
    promt_orientador = current_prompts.get("Orientador", "Prompt por defecto del orientador")
    #Creamos la clase pipeLine 
    cascada_pipeline = CascadaPipeline(factory, promt_curador, promt_orientador)

    # Iniciar la sesión asincrónica
    asyncio.run(cascada_pipeline.start_session())

    # Guardar el pipeline en el dict de salas
    salas_activas[room] = cascada_pipeline
    temas[room] = topic

    return jsonify({"status": "initialized"}), 201

@app.route("/api/tema/<room>", methods=["GET"])
def obtener_tema(room):
    tema = temas.get(room,"sin tema definido")
    return jsonify({"tema":tema})


@app.route("/api/prompts",methods=["GET","POST"])
def get_prompts():
    '''
    GET  -> Consultar el último prompt de cada agente
    POST -> Actualizar prompt(s) de uno o varios agentes # ejemplo(1) {"Curador": "nuevo prompt", "Orientador": "otro prompt"}
    (2) {"Curador": "nuevo prompt"}

    '''
    
    with Session() as session:

        if request.method == "GET":
            prompts = get_current_prompts(session)
            return jsonify(prompts), 200
        
        if request.method == "POST":
            data = request.json  
            for agent_name, prompt_text in data.items():
                new_prompt = AgentPrompt(
                    agent_name=agent_name,
                    prompt=prompt_text,
                    created_at=datetime.now()
                )
                session.add(new_prompt)
            session.commit()
            #el update devuelve la lista de agentes actualizados 
            return jsonify({"status": "success", "updated": list(data.keys())}), 201



if __name__ == "__main__":
    #app.run(debug=True)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
