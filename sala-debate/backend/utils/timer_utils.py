from datetime import datetime, timedelta
import threading
# Diccionario global
room_timers = {}  # { "nombre_sala": {"end_time": datetime, "duration": int } }

def start_room_timer(room_name: str, duration_minutes: int = 30):
    end_time = datetime.now() + timedelta(minutes=duration_minutes)
    room_timers[room_name] = {
        "end_time": end_time,
        "duration": duration_minutes
    }

def get_remaining_time(room_name: str) -> int:
    """Devuelve los segundos restantes para una sala."""
    if room_name not in room_timers:
        return 0
    remaining = (room_timers[room_name]["end_time"] - datetime.now()).total_seconds()
    return max(0, int(remaining))


def tarea_periodica():
    # Aquí va la función que quieres ejecutar cada 30 segundos
    print("Ejecutando tarea periódica")
    # Por ejemplo, revisar temporizadores y cerrar salas vencidas
    for room, timer in room_timers.items():
        remaining = get_remaining_time(room)
        print(f"Sala {room}: {remaining} segundos restantes")

    # Volver a llamar a la misma función en 30 segundos
    threading.Timer(30, tarea_periodica).start()

# Iniciar la tarea
tarea_periodica()
