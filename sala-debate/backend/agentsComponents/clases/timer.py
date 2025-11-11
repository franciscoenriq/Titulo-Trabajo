import asyncio
import time
from datetime import datetime, timedelta
import threading

class Timer:
    def __init__(self):
        # Configuración básica
        self.start_time = None              # Momento en que se inicia el temporizador
        self.end_time = None                # Momento en que debería finalizar
        self.duration_seconds = 0           # Duración total del temporizador en segundos
        self.callback = None                # Función async a ejecutar periódicamente

        # Estado accesible desde otros hilos
        self.elapsed_seconds: int = 0       # Segundos transcurridos desde el inicio
        self.remaining_seconds: int = 0     # Segundos restantes

        # Control de hitos (1/4, 1/2, 3/4, 4/4)
        self.hitos_completados = set()  # guardará {25, 50, 75, 100}

        # Control de concurrencia
        self._lock = threading.Lock()

    def start(self, duration_seconds: int):
        """
        Inicia el temporizador con la duración total especificada.
        """
        self.duration_seconds = duration_seconds
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=self.duration_seconds)

        with self._lock:
            self.elapsed_seconds = 0
            self.remaining_seconds = duration_seconds

    def get_times(self) -> tuple[int, int]:
        """
        Devuelve:
        (segundos_transcurridos, segundos_restantes)
        """
        if not self.start_time:
            return 0, 0

        now = datetime.now()
        elapsed = (now - self.start_time).total_seconds()
        remaining = (self.end_time - now).total_seconds()

        elapsed = min(elapsed, self.duration_seconds)
        remaining = max(0, remaining)

        return int(elapsed), int(remaining)

    def get_state(self) -> dict:
        """
        Devuelve un snapshot thread-safe del estado actual del temporizador.
        """
        with self._lock:
            return {
                "elapsed_seconds": self.elapsed_seconds,
                "remaining_seconds": self.remaining_seconds,
            }
        
    def _check_hitos(self) -> int | None:
        """
        Verifica si se alcanzó algún hito (25%, 50%, 75%, 100%) y lo retorna.
        Solo retorna cada hito una vez.
        """
        if self.duration_seconds == 0:
            return None

        porcentaje_completado = (self.elapsed_seconds / self.duration_seconds) * 100

        # Definir hitos
        hitos = [25, 50, 75, 100]

        for hito in hitos:
            if porcentaje_completado >= hito and hito not in self.hitos_completados:
                with self._lock:
                    self.hitos_completados.add(hito)
                return hito

        return None


    def _update_state(self):
        """
        Calcula y actualiza los atributos públicos (thread-safe).
        """
        elapsed, remaining = self.get_times()
        with self._lock:
            self.elapsed_seconds = elapsed
            self.remaining_seconds = remaining

    def start_periodic(self, update_interval: int):
        """
        Ejecuta periódicamente el callback cada `update_interval` segundos
        hasta que el tiempo se agote.
        Este método debe correrse en un hilo separado.
        """
        if not self.start_time:
            raise RuntimeError("El temporizador no ha sido iniciado. Llama a start() primero.")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            while True:
                self._update_state()
                print(f"⏱️ Ciclo del timer ejecutado - Elapsed: {self.elapsed_seconds}s, Remaining: {self.remaining_seconds}s")
                hito_alcanzado = self._check_hitos()
                if self.callback:
                    loop.run_until_complete(
                        self.callback(
                            self.elapsed_seconds,
                            self.remaining_seconds,
                            hito_alcanzado
                        )
                    )

                if self.remaining_seconds <= 0:
                    print("⏰ Tiempo finalizado")
                    break

                time.sleep(update_interval)
        finally:
            try:
                loop.stop()
                loop.close()
            except Exception:
                pass
