'use client'

import { useState, useEffect, useRef } from 'react'

type ChatMessage = {
  username?: string
  content: string
  system?: boolean
  timestamp?: string  
}

export default function HistoricalChatPage() {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL

  const [days, setDays] = useState<string[]>([])
  const [selectedDay, setSelectedDay] = useState('')

  const [sessions, setSessions] = useState<any[]>([])
  const [selectedSession, setSelectedSession] = useState('')

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [agentMessages, setAgentMessages] = useState<ChatMessage[]>([])

  const chatContainerRef = useRef<HTMLDivElement | null>(null)
  const agentContainerRef = useRef<HTMLDivElement | null>(null)

  // ----------------------------
  // 1. Cargar días disponibles
  // ----------------------------
  useEffect(() => {
    fetch(`${backend}/api/sessions/days`)
      .then(r => r.json())
      .then(data => setDays(data.days))
      .catch(console.error)
  }, [])

  // ----------------------------
  // 2. Cargar sesiones por día
  // ----------------------------
  const loadSessions = async () => {
    if (!selectedDay) return

    const res = await fetch(`${backend}/api/sessions/by-day/${selectedDay}`)
    const data = await res.json()
    setSessions(data.sessions)
    setSelectedSession('')
    setMessages([])
    setAgentMessages([])
  }

  // ----------------------------
  // 3. Cargar mensajes por sesión
  // ----------------------------
  const loadMessages = async () => {
    if (!selectedSession) return

    const res = await fetch(`${backend}/api/sessions/messages/${selectedSession}`)
    const data = await res.json()

    const normal: ChatMessage[] = []
    const agents: ChatMessage[] = []

    data.messages.forEach((msg: any) => {
      const time = new Date(msg.created_at).toLocaleTimeString()
    
      // Si el mensaje viene de un agente
      if (msg.agent_name) {
        const name = msg.agent_name.toLowerCase()
    
        // Todo lo que sea "orientador" va al chat principal
        if (name.includes('orientador')) {
          normal.push({
            username: msg.agent_name,
            content: msg.content,
            timestamp: time
          })
        } else {
          // Cualquier otro agente → panel agentes
          agents.push({
            username: msg.agent_name,
            content: msg.content,
            timestamp: time
          })
        }
      } else {
        // Mensajes de usuario o sistema
        normal.push({
          username: msg.user_id || 'user',
          content: msg.content,
          system: msg.sender_type === 'system',
          timestamp: time
        })
      }
    })
    

    setMessages(normal)
    setAgentMessages(agents)
  }


  return (
    <main className="p-6 w-full max-w-7xl mx-auto min-h-screen flex flex-col">
      <h1 className="text-3xl font-bold mb-6">Historial de conversaciones</h1>

      {/* Selector Día y Sesión */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow-sm flex flex-col md:flex-row md:items-center md:gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <label className="font-medium">Selecciona un día:</label>
          <select
            className="ml-3 border px-3 py-1 rounded-md"
            value={selectedDay}
            onChange={(e) => setSelectedDay(e.target.value)}
          >
            <option value="">-- elegir día --</option>
            {days.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>

          <button
            onClick={loadSessions}
            className="px-3 py-1 bg-blue-600 text-white rounded-md"
          >
            Cargar sesiones
          </button>
        </div>

        {sessions.length > 0 && (
          <div className="flex flex-wrap items-center gap-3 mt-3 md:mt-0">
            <label className="font-medium">Selecciona sesión:</label>
            <select
              className="ml-3 border px-3 py-1 rounded-md"
              value={selectedSession}
              onChange={(e) => setSelectedSession(e.target.value)}
            >
              <option value="">-- elegir sesión --</option>
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.room_name} / {new Date(s.created_at).toLocaleString()}
                </option>
              ))}
            </select>

            <button
              onClick={loadMessages}
              className="px-3 py-1 bg-green-600 text-white rounded-md"
            >
              Ver conversación
            </button>
          </div>
        )}
      </div>

      {/* Grid Chat */}
      <div className="grid grid-cols-1 md:grid-cols-[2fr_1fr] gap-4 flex-grow min-h-[450px]">
        {/* Chat Principal */}
      <div className="flex flex-col w-full border rounded-lg bg-white shadow-sm overflow-hidden">
        <div className="p-3 border-b bg-gray-100">
          <h2 className="font-semibold text-gray-800">Chat</h2>
        </div>
        <div
          ref={chatContainerRef}
          className=" flex-1 overflow-y-auto px-4 py-3 bg-gray-50 break-words scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-200 scroll-smooth h-[450px]"
        >
          {messages.map((m, i) => {
            const isSystem = m.system
            const isOrientador = m.username?.toLowerCase() === 'orientador'
            return (
             <div
              key={i}
              className={`flex mb-2 ${isSystem ? 'justify-center' : 'justify-start'}`}
            >
              <div
                className={`px-3 py-2 rounded-2xl max-w-[80%] break-words ${
                  isSystem
                    ? 'bg-gray-200 text-gray-700'
                    : isOrientador
                    ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                    : 'bg-white border border-gray-200 text-gray-800'
                }`}
              >
                {!isSystem && m.username && (
                  <b className="block text-sm mb-0.5">{m.username}</b>
                )}
                <div>{m.content}</div>
                {m.timestamp && (
                  <div className="text-right text-sm text-gray-500 mt-1">
                    {m.timestamp}
                  </div>
                )}
              </div>
            </div>

            )
          })}
        </div>
      </div>

      {/* Panel Agentes */}
      <div className="flex flex-col w-full border rounded-lg bg-white shadow-sm overflow-hidden">
        <div className="p-3 border-b bg-blue-50">
          <h2 className="font-semibold text-blue-700">Agentes</h2>
        </div>
        <div
          ref={agentContainerRef}
          className="flex-1 overflow-y-auto px-4 py-3 bg-gray-50 break-words scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-200 scroll-smooth h-[450px]"
        >
          {agentMessages.length === 0 ? (
            <p className="text-gray-500 text-sm">Sin mensajes del agente todavía.</p>
          ) : (
            agentMessages.map((m, i) => (
              <div
                key={i}
                className="p-2 rounded bg-blue-100 text-blue-800 text-sm w-full max-w-full break-words mb-2"
              >
                <div className="flex justify-between items-start">
                  <b>{m.username}:</b>
                  {m.timestamp && (
                    <span className="text-xs text-gray-500 ml-2">{m.timestamp}</span>
                  )}
                </div>
                <div>{m.content}</div>
              </div>
            ))
            
          )}
        </div>
      </div>

      </div>
    </main>
  )
}
