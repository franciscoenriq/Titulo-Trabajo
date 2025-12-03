'use client'

import { useState, useEffect } from 'react'

export default function PlotDayPage() {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL
  const [days, setDays] = useState<string[]>([])
  const [selectedDay, setSelectedDay] = useState('')
  const [imageUrl, setImageUrl] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${backend}/api/sessions/days`)
      .then(res => res.json())
      .then(data => setDays(data.days))
      .catch(console.error)
  }, [])

  const loadPlot = async () => {
    if (!selectedDay) return
    setImageUrl(`${backend}/api/sessions/plot-day/${selectedDay}`)
  }

  return (
    <main className="p-6 w-full max-w-7xl mx-auto flex flex-col gap-6">
      <h1 className="text-3xl font-bold mb-6">Gráfico de sesiones por día</h1>

      <div className="flex gap-3 items-center">
        <select
          className="border px-3 py-1 rounded-md"
          value={selectedDay}
          onChange={(e) => setSelectedDay(e.target.value)}
        >
          <option value="">-- elegir día --</option>
          {days.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>

        <button
          onClick={loadPlot}
          className="px-3 py-1 bg-blue-600 text-white rounded-md"
        >
          Ver gráfico
        </button>
      </div>

      {imageUrl && (
        <div className="overflow-x-auto border rounded-lg p-2 bg-white">
          <img src={imageUrl} alt="Gráfico del día" />
        </div>
      )}
    </main>
  )
}
