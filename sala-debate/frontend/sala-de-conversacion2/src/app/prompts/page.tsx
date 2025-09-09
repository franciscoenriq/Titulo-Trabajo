'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthGuard } from '../hooks/useAuthGuard'

export default function PromptsPage() {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL

  const router = useRouter()
  const [prompts, setPrompts] = useState<{ agenteEntrada: string; agenteRespuesta: string } | null>(null)
  const [loadingPrompts, setLoadingPrompts] = useState(false)
  const [saving, setSaving] = useState(false)

  const fetchPrompts = async () => {
    try {
      setLoadingPrompts(true)
      const res = await fetch(`${backend}/api/prompts`)
      if (!res.ok) throw new Error('Error al obtener prompts')
      const data = await res.json()
      setPrompts({
        agenteEntrada: data.Curador || '',
        agenteRespuesta: data.Orientador || '',
      })
    } catch (error) {
      console.error('Error al cargar prompts:', error)
    } finally {
      setLoadingPrompts(false)
    }
  }

  const handleSavePrompts = async () => {
    if (!prompts) return
    try {
      setSaving(true)
      await fetch(`${backend}/api/prompts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          Curador: prompts.agenteEntrada,
          Orientador: prompts.agenteRespuesta,
        }),
      })
      await fetchPrompts()
    } catch (error) {
      console.error('Error al guardar prompts:', error)
    } finally {
      setSaving(false)
    }
  }

  useEffect(() => {
    fetchPrompts()
  }, [backend])


  return (
    <main className="p-8 w-full max-w-7xl mx-auto">
        {/* Contenedor horizontal para los prompts */}
        <div className="flex flex-row gap-6 w-full">
            <div className="w-1/2 border rounded-lg p-4 shadow">
            <h2 className="text-lg font-semibold mb-2">Prompt Agente Entrada</h2>
            <textarea
                className="w-full border p-2 rounded"
                rows={12}
                value={prompts?.agenteEntrada || ''}
                onChange={(e) =>
                setPrompts((prev) => prev ? { ...prev, agenteEntrada: e.target.value } : prev)
                }
            />
            </div>

            <div className="w-1/2 border rounded-lg p-4 shadow">
            <h2 className="text-lg font-semibold mb-2">Prompt Agente Respuesta</h2>
            <textarea
                className="w-full border p-2 rounded"
                rows={12}
                value={prompts?.agenteRespuesta || ''}
                onChange={(e) =>
                setPrompts((prev) => prev ? { ...prev, agenteRespuesta: e.target.value } : prev)
                }
            />
            </div>
        </div>

        {/* Contenedor para los botones */}
        <div className="mt-4 flex justify-between">
            <button
            onClick={() => router.back()}
            className="bg-gray-300 text-gray-800 px-4 py-2 rounded hover:bg-gray-400 transition"
            >
            ← Volver
            </button>

            <button
            onClick={handleSavePrompts}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
            disabled={saving}
            >
            {saving ? 'Guardando...' : 'Guardar cambios'}
            </button>
        </div>
    </main>

  )
}
