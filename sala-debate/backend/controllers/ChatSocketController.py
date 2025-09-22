import asyncio
import threading
from flask_socketio import join_room, leave_room, emit
from flask_socketio import SocketIO, join_room, leave_room, emit
from models.models import *
from agentsComponents.clases.intermediador import Intermediario

def register_sockets(socketio,salas_activas):
# esta es la funcion para poder usar los socketsEvents  para el chat.
    usuarios_por_sala = {}  # {room_name: set(username1, username2, ...)}

    @socketio.on('join')
    def on_join(data):
        username = data['username']
        room = data['room']
        # Inicializar el set si no existe
        if room not in usuarios_por_sala:
            usuarios_por_sala[room] = set()
        join_room(room)
        if username not in usuarios_por_sala[room]:
            emit('status', {'msg': f'{username} ha entrado a la sala {room}.'}, room=room)
            #Avisamos al sistema multiagente que ha entrado un participante
            intermediario:Intermediario = salas_activas.get(room)
            asyncio.run(intermediario.anunciar_entrada_participante(username))
        # Agregamos al usuario al set, el set no permite duplicados
        usuarios_por_sala[room].add(username)

    @socketio.on('leave')
    def on_leave(data):
        username = data['username']
        room = data['room']
        leave_room(room)
        if room in usuarios_por_sala and username in usuarios_por_sala[room]:
            emit('status', {'msg': f'{username} ha salido de la sala {room}.'}, room=room)
            #Avisamos al sistema multiagente que ha salido un participante
            intermediario:Intermediario = salas_activas.get(room)
            asyncio.run(intermediario.anunciar_salida_participante(username))
            # Remover del set
            usuarios_por_sala[room].remove(username)
         # Limpiar set vacío(no hay usuarios) para no acumular memoria
        if room in usuarios_por_sala and len(usuarios_por_sala[room]) == 0:
            del usuarios_por_sala[room]

    @socketio.on('message')
    def handle_message(data):
        """
        Maneja un mensaje entrante de un usuario, lo envía al pipeline
        y emite la evaluación resultante.
        """
        room = data['room']
        username = data['username']
        content = data['content']
        #extraemos la id de la sala 
        id_room_session = get_active_room_session_id(room)
        if not id_room_session:
            emit('error', {'msg': f"No hay sesión activa para la sala {room}"}, room=room)
            return
        
        message_data = {'username': username, 'content': content}
        emit('message', message_data, room=room)
        #guardamos en la bd 
        insert_message(
            room_session_id=id_room_session,
            user_id=username,
            agent_name=None,
            sender_type=SenderType.user,
            content=content
        )
        
        intermediario:Intermediario = salas_activas.get(room)
        if not intermediario:
            emit('error', {'msg': 'La sala no está inicializada con agentes.'}, room=room)
            return
        def process_message():
            # Ejecutar async desde el loop de asyncio
            resultado = asyncio.run(intermediario.agregarMensage(username, content))
            # Emitir resultado de evaluación del agente si es que existe 
            if resultado: 
                # Guardar en la BD cada respuesta de agente
                for r in resultado:
                    insert_message(
                        room_session_id=id_room_session,
                        user_id=None,
                        agent_name=r["agente"],
                        sender_type=SenderType.agent,
                        content=r["respuesta"]
                    )
                socketio.emit('evaluacion', resultado, room=room)

        # Lanzar como tarea de fondo de SocketIO
        socketio.start_background_task(process_message)

    @socketio.on('typing')
    def handle_typing(data):
        username = data['username']
        room = data['room']
        # Enviamos a todos los demás de la sala que este usuario está escribiendo
        emit('typing', {'username': username}, room=room, include_self=False)

    # Nuevo: cuando alguien deja de escribir
    @socketio.on('stop_typing')
    def handle_stop_typing(data):
        username = data['username']
        room = data['room']
        # Avisamos a todos los demás que este usuario dejó de escribir
        emit('stop_typing', {'username': username}, room=room, include_self=False)