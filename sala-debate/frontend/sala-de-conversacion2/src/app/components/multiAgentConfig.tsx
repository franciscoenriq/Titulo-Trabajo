'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function MultiAgentConfigPage() {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL
  const router = useRouter()

  const [ventanaMensajes, setVentanaMensajes] = useState(5)
  const [faseMin, setFaseMin] = useState(10);
  const [faseSeg, setFaseSeg] = useState(0);
  const [updateInterval, setUpdateInterval] = useState(5)

  useEffect(() => {
    fetch(`${backend}/api/multiagent-config`)
      .then(res => res.json())
      .then(data => {
        setVentanaMensajes(data.ventana_mensajes);
        setFaseMin(Math.floor(data.fase_segundos / 60));
        setFaseSeg(data.fase_segundos % 60);
        setUpdateInterval(data.update_interval);
      })
      .catch(err => console.error(err));
  }, [backend]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const faseTotal = (faseMin || 0) * 60 + (faseSeg || 0);
  
    try {
      const res = await fetch(`${backend}/api/multiagent-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ventana_mensajes: ventanaMensajes,
          fase_segundos: faseTotal,
          update_interval: updateInterval
        })
      });
      if (!res.ok) throw new Error('Error al actualizar configuración');
      alert('Configuración actualizada correctamente');
    } catch (err) {
      console.error(err);
      alert('Error al actualizar configuración');
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Configuración Multiagente</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block mb-1 font-medium">Ventana de Mensajes</label>
          <input type="number" min={1} value={ventanaMensajes || 0} onChange={e => setVentanaMensajes(Math.max(1, +e.target.value))} className="border p-2 rounded w-full" />
        </div>
        <div>
          <label className="block mb-1 font-medium">Fase</label>
          <div className="flex gap-2">
            <input
              type="number"
              min={0}
              value={faseMin || 0}
              onChange={e => setFaseMin(Math.max(0, +e.target.value))}
              className="border p-2 rounded w-full"
              placeholder="Minutos"
            />
            <input
              type="number"
              min={0}
              max={59}
              value={faseSeg || 0}
              onChange={e => setFaseSeg(Math.min(59, Math.max(0, +e.target.value)))}
              className="border p-2 rounded w-full"
              placeholder="Segundos"
            />
          </div>
        </div>
        <div>
          <label className="block mb-1 font-medium">Intervalo de actualización (segundos)</label>
          <input type="number" min={1} value={updateInterval || 0} onChange={e => setUpdateInterval(Math.max(1, +e.target.value))} className="border p-2 rounded w-full" />
        </div>

        <button type="submit" className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 transition">
          Guardar Configuración
        </button>
      </form>
    </div>
  )
}
