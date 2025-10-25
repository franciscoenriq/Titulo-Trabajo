import asyncio
import time
from datetime import datetime, timedelta
import threading

class Timer:
    def __init__(self):
        self.start_at = None
        self.end_time = None
        self.total_duration_seconds = 0
        self.phases: list[int] = []
        self.callback = None  # async function

        # Estado actual accesible desde otros hilos
        self.fase_actual: int = 0
        self.remaining_phase: int = 0
        self.elapsed_phase: int = 0
        self.remaining_total: int = 0
        self.elapsed_total: int = 0

        # Lock para leer/escribir estado de forma segura
        self._lock = threading.Lock()

    def start(self, phases: list[int]):
        """
        Inicia el temporizador con múltiples fases.
        phases: lista de duraciones en segundos [fase1, fase2, ...]
        """
        self.phases = phases
        self.total_duration_seconds = sum(phases)
        self.start_at = datetime.now()
        self.end_time = self.start_at + timedelta(seconds=self.total_duration_seconds)

        # inicializar estado
        with self._lock:
            self.fase_actual = 1 if phases else 0
            self.elapsed_phase = 0
            self.remaining_phase = phases[0] if phases else 0
            self.elapsed_total = 0
            self.remaining_total = self.total_duration_seconds

    def get_times(self) -> tuple[int, int, int, int, int]:
        """
        Devuelve:
        fase_actual (1-indexed),
        segundos_restantes_en_fase,
        segundos_transcurridos_en_fase,
        segundos_restantes_total,
        segundos_transcurridos_total
        """
        if not self.start_at:
            return 0, 0, 0, 0, 0

        now = datetime.now()
        elapsed_total = (now - self.start_at).total_seconds()
        remaining_total = (self.end_time - now).total_seconds()

        elapsed_total = min(elapsed_total, self.total_duration_seconds)
        remaining_total = max(0, remaining_total)

        # Determinar fase actual
        elapsed = 0
        for i, phase_duration in enumerate(self.phases):
            if elapsed_total < elapsed + phase_duration:
                fase_actual = i + 1
                elapsed_in_phase = elapsed_total - elapsed
                remaining_in_phase = phase_duration - elapsed_in_phase
                return (
                    fase_actual,
                    int(remaining_in_phase),
                    int(elapsed_in_phase),
                    int(remaining_total),
                    int(elapsed_total),
                )
            elapsed += phase_duration

        # Si ya terminó todo
        return len(self.phases), 0, int(self.phases[-1]), 0, int(self.total_duration_seconds)

    def get_state(self) -> dict:
        """
        Devuelve snapshot thread-safe del estado actual del timer.
        """
        with self._lock:
            return {
                "fase_actual": self.fase_actual,
                "remaining_phase": self.remaining_phase,
                "elapsed_phase": self.elapsed_phase,
                "remaining_total": self.remaining_total,
                "elapsed_total": self.elapsed_total,
            }

    def _update_state_from_get_times(self):
        """
        Calcula y actualiza los atributos públicos (thread-safe).
        """
        fase_actual, remaining_phase, elapsed_phase, remaining_total, elapsed_total = self.get_times()
        with self._lock:
            self.fase_actual = fase_actual
            self.remaining_phase = remaining_phase
            self.elapsed_phase = elapsed_phase
            self.remaining_total = remaining_total
            self.elapsed_total = elapsed_total

    def start_periodic(self, update_interval: int):
        """
        Llama periódicamente al callback hasta que termine el tiempo.
        Este método está pensado para ejecutarse en un hilo aparte.
        """
        if not self.start_at:
            raise RuntimeError("El temporizador no ha sido iniciado. Llama a start() primero.")

        # Crear un event loop propio en este hilo para ejecutar la coroutine callback
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            while True:
                # Actualizar estado público (para que otros hilos lo puedan leer)
                self._update_state_from_get_times()

                print("se ejecuta ciclo del timer")
                if self.callback:
                    # ejecutar la coroutine de manera síncrona en este loop
                    # la callback es async def callback(...)
                    loop.run_until_complete(
                        self.callback(
                            self.fase_actual,
                            self.remaining_phase,
                            self.elapsed_phase,
                            self.remaining_total,
                            self.elapsed_total,
                        )
                    )

                if self.remaining_total <= 0:
                    print("se acabó el tiempo")
                    break

                # dormir en este hilo (no bloquea otros hilos)
                time.sleep(update_interval)
        finally:
            try:
                loop.stop()
                loop.close()
            except Exception:
                pass
