import asyncio
import threading
from flask_socketio import join_room, leave_room, emit
from flask_socketio import SocketIO, join_room, leave_room, emit
from models.models import *
from agentsComponents.clases.pipeLine_ejecucion import CascadaPipeline


def register_sockets(socketio,salas_activas):
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
            content=content
        )
        
        pipeLine:CascadaPipeline = salas_activas.get(room)
        if not pipeLine:
            emit('error', {'msg': 'La sala no está inicializada con agentes.'}, room=room)
            return
        
        # Función de tarea de fondo
        def process_message():
            # Ejecutar async desde el loop de asyncio
            resultado = asyncio.run(pipeLine.analizar_argumento_cascada(content, username))
            # Emitir resultado de evaluación del agente
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


'''
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
resultado = loop.run_until_complete(
    pipeLine.analizar_argumento_cascada(content, username)
)

# Emitimos el resultado de la evaluación
socketio.emit('evaluacion', {
    'evaluacion': resultado["evaluacion"],
    'respuesta': resultado["respuesta"],
    'intervencion': resultado["intervencion"],
    'agente': resultado["agente"],
    'evaluado': resultado["evaluado"]
}, room=room)

# Ejecutar async sin bloquear el servidor
threading.Thread(target=process_message).start()
'''



'''
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
'''
