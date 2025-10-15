import asyncio
import threading
from flask_socketio import join_room, leave_room, emit
from flask_socketio import SocketIO, join_room, leave_room, emit
from models.models import *
from agentsComponents.clases.intermediador import Intermediario


# sockets_events.py (o donde tengas register_sockets)
def emitir_resultado_socket(socketio: SocketIO, evento:str,resultado, sala:str):
    """Emitir resultados de intermediario de forma segura usando el contexto del servidor."""
    def _emit():
        try:
            socketio.emit(evento, resultado, room=sala)
        except Exception as e:
            print("Error emitiendo resultado desde background task:", e)
    # start_background_task corre la función en el contexto del servidor (thread/greenlet según async_mode)
    socketio.start_background_task(_emit)

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
        emit('message', {'username': username, 'content': content}, room=room)
        id_room_session = get_active_room_session_id(room)
        if not id_room_session:
            emit('error', {'msg': f"No hay sesión activa para la sala {room}"}, room=room)
            return
        insert_message(
            room_session_id=id_room_session,
            user_id=username,
            agent_name=None,
            sender_type=SenderType.user,
            content=content
        )

        intermediario: Intermediario = salas_activas.get(room)
        if not intermediario:
            emit('error', {'msg': 'La sala no está inicializada con agentes.'}, room=room)
            return
        intermediario.enqueue_message(username,content)


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
    
    @socketio.on('subscribe_monitor')
    def handle_monitor_subscription(data):
        room = f"monitor_{data['room']}"
        print(f"🟢 Cliente  se está uniendo a {room}")
        join_room(room)
        emit('status',{'msg':f'Monitor susbrito a la sala {room}'})
    
    @socketio.on('unsubscribe_monitor')
    def handle_monitor_unsubscribe(data):
        room = f"monitor_{data['room']}"
        leave_room(f"monitor_{room}")