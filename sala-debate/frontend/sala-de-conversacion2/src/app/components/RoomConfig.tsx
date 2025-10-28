'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

interface DebateTopic {
  id: number
  titulo: string
  tema_text: string
  created_at?: string
}

interface Room {
  id: number
  name: string
}

interface RoomStatus {
  room_name: string
  status: string
}

interface RoomConfigProps {
  backend: string
}

export default function RoomConfig({ backend }: RoomConfigProps) {
  const router = useRouter()

  const [availableRooms, setAvailableRooms] = useState<Room[]>([])
  const [roomStatuses, setRoomStatuses] = useState<RoomStatus[]>([])
  const [debateTopics, setDebateTopics] = useState<DebateTopic[]>([])
  const [room, setRoom] = useState('')
  const [topic, setTopic] = useState('')
  const [selectedCaseKey, setSelectedCaseKey] = useState('')

  // Fetch de salas
  const fetchRooms = async () => {
    try {
      const res = await fetch(`${backend}/api/rooms`)
      if (!res.ok) throw new Error('Error al obtener salas')
      const data = await res.json()
      setAvailableRooms(data)
    } catch (error) {
      console.error('Error al cargar salas:', error)
    }
  }

  // Fetch de estado de salas
  const fetchStatuses = async () => {
    try {
      const res = await fetch(`${backend}/api/estado-salas`)
      if (!res.ok) throw new Error('Error al obtener estado de salas')
      const data = await res.json()
      setRoomStatuses(data)
    } catch (error) {
      console.error('Error al cargar estado de salas:', error)
    }
  }

  // Fetch de temas de debate
  const fetchDebateTopics = async () => {
    try {
      const res = await fetch(`${backend}/api/temas`)
      if (!res.ok) throw new Error('Error al obtener los temas de debate')
      const data = await res.json()
      setDebateTopics(data)
    } catch (error) {
      console.error(error)
    }
  }

  useEffect(() => {
    fetchRooms()
    fetchStatuses()
    fetchDebateTopics()
  }, [backend])

  // Selección de tema
  const handleCaseChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = parseInt(e.target.value)
    const selected = debateTopics.find((t) => t.id === id)
    if (selected) {
      setSelectedCaseKey(id.toString())
      setTopic(selected.tema_text)
    } else {
      setSelectedCaseKey('')
      setTopic('')
    }
  }

  const handleEnter = () => {
    if (!room || !topic) return
    sessionStorage.setItem('chatTopic', topic)
    sessionStorage.setItem('chatRoom', room)
    router.push(`/chat/${room}/lobby`)
  }

  const handleCloseRoom = async (roomName: string) => {
    if (!confirm(`¿Deseas cerrar la sala "${roomName}"?`)) return

    try {
      const res = await fetch(`${backend}/api/close-room`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room: roomName }),
      })

      if (!res.ok) {
        const errorData = await res.json()
        alert(`Error: ${errorData.error || 'No se pudo cerrar la sala'}`)
        return
      }

      alert(`Sala "${roomName}" cerrada exitosamente`)
      fetchStatuses()
    } catch (error) {
      console.error('Error al cerrar la sala:', error)
      alert('Error al cerrar la sala')
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Estado de salas */}
      <div className="border rounded-lg p-4 shadow bg-gray-50">
        <h2 className="text-lg font-semibold mb-2">Estado de salas</h2>
        {roomStatuses.length === 0 ? (
          <p className="text-sm text-gray-500">No hay información de salas.</p>
        ) : (
          <ul className="space-y-2">
            {roomStatuses.map((r, idx) => (
              <li key={idx} className="flex justify-between items-center border-b pb-1">
                <span>{r.room_name}</span>
                <span
                  className={`px-2 py-1 rounded text-xs font-semibold ${
                    r.status === 'active'
                      ? 'bg-green-200 text-green-800'
                      : 'bg-red-200 text-red-800'
                  }`}
                >
                  {r.status || 'sin sesión'}
                </span>
                {r.status === 'active' && (
                  <button
                    className="bg-red-500 text-white text-[10px] px-1.5 py-0.5 rounded hover:bg-red-600 transition"
                    onClick={() => handleCloseRoom(r.room_name)}
                  >
                    Cerrar
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Formulario central */}
      <div>
        <h1 className="text-2xl font-bold mb-6">Configuración de la Sala</h1>

        <div className="mb-4">
          <label className="block mb-2 text-sm font-medium">Elige la sala:</label>
          <select
            className="border p-2 w-full rounded cursor-pointer"
            value={room}
            onChange={(e) => setRoom(e.target.value)}
          >
            <option value="">-- Selecciona una sala --</option>
            {availableRooms.map((r) => (
              <option key={r.id} value={r.name}>
                {r.name}
              </option>
            ))}
          </select>
        </div>

        <div className="mb-4">
          <label className="block mb-2 text-sm font-medium">Elige un tema:</label>
          <select
            className="border p-2 w-full rounded"
            value={selectedCaseKey}
            onChange={handleCaseChange}
          >
            <option value="">-- Selecciona un tema --</option>
            {debateTopics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.titulo}
              </option>
            ))}
          </select>
        </div>

        <div className="mb-4">
          <label className="block mb-2 text-sm font-medium">O escribe tu propio tema:</label>
          <textarea
            className="border p-2 w-full rounded"
            rows={5}
            value={topic}
            onChange={(e) => {
              setTopic(e.target.value)
              setSelectedCaseKey('')
            }}
            placeholder="Tema inicial de la discusión"
          />
        </div>

        <div>
          <button
            onClick={handleEnter}
            className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 transition"
          >
            Entrar
          </button>
        </div>
      </div>
    </div>
  )
}
