import asyncio
import time
from datetime import datetime, timedelta
class Timer:
    def __init__(self):
        self.start_at = None
        self.end_time = None
        self.total_duration_seconds = 0
        self.phases :list[int] = []
        self.callback = None  # async function

    def start(self, phases: list[int]):
        """
        Inicia el temporizador con múltiples fases.
        phases: lista de duraciones en segundos [fase1, fase2, ...]
        """
        self.phases = phases
        self.total_duration_seconds = sum(phases)
        self.start_at = datetime.now()
        self.end_time = self.start_at + timedelta(seconds=self.total_duration_seconds)

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
            return 0, 0, 0, 0
        
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
                    int(elapsed_total)
                )
            elapsed += phase_duration

        # Si ya terminó todo
        return len(self.phases), 0, self.phases[-1], 0, self.total_duration_seconds


    def start_periodic(self, update_interval:int):
        """
        Llama periódicamente al callback hasta que termine el tiempo.
        """
        if not self.start_at:
            raise RuntimeError("El temporizador no ha sido iniciado. Llama a start() primero.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            print("se ejecuta ciclo del timer")
            fase_actual, remaining_phase, elapsed_phase, remaining_total, elapsed_total = self.get_times()
            if self.callback:
                loop.run_until_complete(
                    self.callback(fase_actual, remaining_phase, elapsed_phase, remaining_total, elapsed_total)
                    )

            if remaining_total <= 0:
                print("se acabó el tiempo")
                break
            time.sleep(update_interval)


