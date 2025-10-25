'use client'

import { useParams, useRouter } from 'next/navigation'
import { useEffect, useRef, useState } from 'react'
import { io, Socket } from 'socket.io-client'

export default function LobbyPage() {
  const params = useParams()
  const room = params.room as string
  const router = useRouter()
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL
  const socketRef = useRef<Socket | null>(null)

  const [username, setUsername] = useState('')
  const [joined, setJoined] = useState(false)
  const [participants, setParticipants] = useState<string[]>([])
  const [statusMessages, setStatusMessages] = useState<string[]>([])
  const [starting, setStarting] = useState(false)

  // Conexión socket (solo en el lobby)
  useEffect(() => {
    socketRef.current = io(backend, {
      path: '/socket.io',
      transports: ['websocket'],
    })
    const socket = socketRef.current

    socket.on('connect', () => {
      console.log('Lobby socket connected', socket.id)
    })

    socket.on('status', (data: { msg: string }) => {
      setStatusMessages(prev => [...prev, data.msg])
    })

    // Lista de participantes (requiere que el backend emita 'users_update')
    socket.on('users_update', (users: string[]) => {
      setParticipants(users || [])
    })

    // Evento que indica que la sala ya fue inicializada (requiere backend)
    socket.on('start_session', (data: any) => {
      // navegar al chat principal
      router.push(`/chat/${room}`)
    })

    return () => {
      socket.disconnect()
    }
  }, [room])

  const joinLobby = () => {
    if (!username.trim() || !socketRef.current) return
    socketRef.current.emit('join', { room, username })
    setJoined(true)
    sessionStorage.setItem('chatUser', JSON.stringify({ room, username }))
  }

  const leaveLobby = () => {
    if (!socketRef.current || !username) return
    socketRef.current.emit('leave', { room, username })
    setJoined(false)
    sessionStorage.removeItem('chatUser')
  }

  const startRoom = async () => {
    // Empieza la sala: POST a /api/init-topic
    if (!socketRef.current) return
    setStarting(true)
    try {
      const prompt = sessionStorage.getItem('chatTopic') || ''
      const res = await fetch(`${backend}/api/init-topic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room, prompt_inicial: prompt }),
      })
      if (!res.ok) {
        const err = await res.json().catch(()=>({}))
        console.error('Error init-topic', err)
        alert('No se pudo iniciar la sala')
        setStarting(false)
        return
      }
      // El backend debería emitir 'start_session' a la sala. Redirigimos localmente también.
      router.push(`/chat/${room}`)
    } catch (e) {
      console.error('Error al iniciar sala', e)
      alert('Error al iniciar la sala')
      setStarting(false)
    }
  }

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-4">Lobby — Sala: {room}</h1>

      {!joined ? (
        <div className="max-w-sm flex flex-col gap-2">
          <label>Nombre de usuario (lobby):</label>
          <input value={username} onChange={(e)=>setUsername(e.target.value)} placeholder="Tu nombre" className="border p-2" />
          <button onClick={joinLobby} disabled={!username.trim()} className="bg-green-600 text-white px-4 py-2 rounded">Unirse al lobby</button>
        </div>
      ) : (
        <>
          <div className="mb-4">
            <strong>Participantes:</strong>
            <ul className="mt-2 list-disc list-inside">
              {participants.length === 0 ? <li>Esperando participantes...</li> : participants.map(p => <li key={p}>{p}</li>)}
            </ul>
            <div className="mt-3">
              <button onClick={startRoom} className="bg-blue-600 text-white px-4 py-2 rounded mr-2" disabled={starting}>
                {starting ? 'Iniciando...' : 'Empezar sala'}
              </button>
              <button onClick={leaveLobby} className="bg-red-600 text-white px-3 py-2 rounded">Salir del lobby</button>
            </div>
          </div>

          <div className="mt-4">
            <strong>Mensajes de sistema:</strong>
            <div className="mt-2 border p-2 max-h-40 overflow-y-auto bg-gray-50">
              {statusMessages.map((m, i) => <div key={i} className="text-sm text-gray-700">{m}</div>)}
            </div>
          </div>
        </>
      )}
    </main>
  )
}