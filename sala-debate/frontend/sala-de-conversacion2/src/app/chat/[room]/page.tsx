'use client'

import { useParams } from 'next/navigation'
import { useEffect, useState, useRef } from 'react'
import { io, Socket } from 'socket.io-client'

export default function ChatRoom() {
  type ChatMessage = {
    username?: string;
    content: string;
    system?: boolean;
  };
  
  type EvaluacionData = {
    evaluacion: string;
    agente: string;
    evaluado: string;
    intervencion?: string;
    respuesta?: string;
  };
  
  const params = useParams()
  const room = params.room as string
  const [evaluaciones, setEvaluaciones] = useState<string[]>([])
  const [username, setUsername] = useState('')
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<{ username?: string; content: string; system?: boolean }[]>([])
  const [joined, setJoined] = useState(false)
  const socketRef = useRef<Socket | null>(null)
  const [tema, setTema] = useState('')
  useEffect(() => {
    fetch(`http://localhost:5000/api/tema/${room}`)
    .then((res) => res.json())
    .then((data) => setTema(data.tema))
  }, [room])

  // Inicializa el socket una sola vez
  useEffect(() => {
    socketRef.current = io('/', {
      path: '/socket.io',
      transports: ['websocket'],
    });

    const socket = socketRef.current

    const handleMessage = (msg: ChatMessage) => {
      setMessages((prev) => [...prev, msg])
    }

    const handleStatus = (statusMsg: {msg:string}) => {
      setMessages((prev) => [...prev, { content: statusMsg.msg, system: true }])
    }

    const handleEvaluacion = (data: EvaluacionData) => {
      const { evaluacion, agente, evaluado, intervencion, respuesta } = data

      const mensaje = `${agente} evaluó lo que dijo ${evaluado}: ${evaluacion}`
      setEvaluaciones((prev) => [...prev, mensaje])

      if (intervencion && respuesta?.trim() ){
        const intervencionMsg = `${agente} interviene tras el mensaje de ${evaluado} y dijo: "${respuesta}"`
        setEvaluaciones((prev) => [...prev, intervencionMsg])
      }
    }

    socket.on('message', handleMessage)
    socket.on('status', handleStatus)
    socket.on('evaluacion', handleEvaluacion)

    return () => {
      socket.disconnect()
    }
  }, [])

  const joinRoom = () => {
    if (username && socketRef.current) {
      socketRef.current.emit('join', { room, username })
      setJoined(true)
    }
  }

  const sendMessage = () => {
    if (input.trim() && socketRef.current && username) {
      socketRef.current.emit('message', { room, username, content: input.trim() })
      setInput('')
    }
  }

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-4">Sala de chat: {room}</h1>
      {tema && (
        <div 
          className="mb-4 p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-900 rounded"
          style={{ maxHeight: '150px', overflowY: 'auto', whiteSpace: 'pre-wrap' }}
        >
          <strong>Tema de la sala:</strong><br />
           {tema}
        </div>
      )}
      {!joined ? (
        <div className="flex flex-col gap-2 max-w-sm">
          <label>Nombre de usuario:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Ingresa tu nombre"
            className="border p-2"
          />
          <button
            onClick={joinRoom}
            className="bg-green-600 text-white px-4 py-2 rounded"
            disabled={!username.trim()}
          >
            Unirse a la sala
          </button>
        </div>
      ) : (
        <>
          <div
            style={{ height: '300px', overflowY: 'auto', border: '1px solid gray', padding: '10px' }}
            className="mb-4"
          >
            {messages.map((m, i) => (
              <div key={i}>
                <b>{m.system ? '[Sistema]' : `${m.username}:`}</b> {m.content}
              </div>
            ))}
          </div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Escribe tu mensaje"
            className="border p-2 w-full"
          />
          <button onClick={sendMessage} className="mt-2 bg-blue-500 text-white px-4 py-2 rounded">
            Enviar
          </button>

          {evaluaciones.length > 0 && (
            <div className="mt-4">
            <h2 className="text-md font-semibold mb-2 text-gray-800">Evaluaciones e intervenciones</h2>
            <div
              style={{ maxHeight: '200px', overflowY: 'auto' }}
              className="p-3 border border-gray-300 rounded bg-gray-50"
            >
              <ul className="list-disc list-inside text-sm text-gray-700">
                {evaluaciones.map((e, idx) => (
                  <li key={idx}>{e}</li>
                ))}
              </ul>
            </div>
            </div>
          )}
        </>
      )}
    </main>
  )
}
