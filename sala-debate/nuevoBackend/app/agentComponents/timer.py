# agentComponents/timer.py
import asyncio
from datetime import datetime, timedelta
from typing import Optional

class Timer:
    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.duration_seconds: int = 0
        self.end_time: Optional[datetime] = None
        self.callback = None  # debe ser async def callback(elapsed, remaining, hito)
        self.elapsed_seconds: int = 0
        self.remaining_seconds: int = 0
        self.hitos_completados = set()
        self._running = False

    async def run(self, duration_seconds: int, update_interval: int):
        """
        Coroutine que corre en background (crear con asyncio.create_task(timer.run(...))).
        update_interval en segundos.
        """
        self.duration_seconds = duration_seconds
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=duration_seconds)
        self.elapsed_seconds = 0
        self.remaining_seconds = duration_seconds
        self.hitos_completados = set()
        self._running = True

        try:
            while self._running:
                now = datetime.now()
                elapsed = int((now - self.start_time).total_seconds())
                remaining = int((self.end_time - now).total_seconds())
                elapsed = min(elapsed, self.duration_seconds)
                remaining = max(0, remaining)

                self.elapsed_seconds = elapsed
                self.remaining_seconds = remaining

                # comprobar hitos
                hito = self._check_hitos()
                if self.callback:
                    # llamar callback async (no esperamos a que termine necesariamente)
                    asyncio.create_task(self._safe_callback(self.elapsed_seconds,
                                                            self.remaining_seconds,
                                                            hito))
                if self.remaining_seconds <= 0:
                    break

                await asyncio.sleep(update_interval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[Timer error]: {e}")
        finally:
            self._running = False

    async def _safe_callback(self, elapsed, remaining, hito):
        try:
            await asyncio.wait_for(self.callback(elapsed, remaining, hito), timeout=5)
        except asyncio.TimeoutError:
            print("[Timer] callback timeout")
        except Exception as e:
            print(f"[Timer callback error]: {e}")

    def _check_hitos(self) -> Optional[int]:
        if self.duration_seconds == 0:
            return None
        porcentaje = (self.elapsed_seconds / self.duration_seconds) * 100
        for h in [25, 50, 75, 100]:
            if porcentaje >= h and h not in self.hitos_completados:
                self.hitos_completados.add(h)
                return h
        return None

    def get_state(self):
        return {
            "elapsed_seconds": self.elapsed_seconds,
            "remaining_seconds": self.remaining_seconds
        }
    
    def stop(self):
        self._running = False
