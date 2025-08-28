from flask_socketio import join_room, leave_room, emit
from flask_socketio import SocketIO, join_room, leave_room, emit
from models.models import *
from agentsComponents.multiagent_evaluador import *

# Diccionario que mapea nombre de sala -> id en BD
salas_activas = {}

def register_sockets(socketio):
# esta es la funcion para poder usar los socketsEvents  para el chat.
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

            # ---- 2) Revisar si alguien llamó al relator ----
        resultado_relator = llamar_relator(room, content, username)

        if resultado_relator:  # solo si devolvió algo
            emit('evaluacion', {
                'evaluacion': resultado_relator["evaluacion"],
                'respuesta': resultado_relator["respuesta"],
                'intervencion': resultado_relator["intervencion"],
                'agente': resultado_relator["agente"],
                'evaluado': resultado_relator["evaluado"]
            }, room=room)
