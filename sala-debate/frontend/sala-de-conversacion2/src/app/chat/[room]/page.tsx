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
    respuesta: string;
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
  const [agentMessages, setAgentMessages] = useState<ChatMessage[]>([])
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL;
  useEffect(() => {
    fetch(`${backend}/api/tema/${room}`)
    .then((res) => res.json())
    .then((data) => setTema(data.tema))
  }, [room])

  // Inicializa el socket una sola vez
  useEffect(() => {
    socketRef.current = io(backend, {
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
      const { evaluacion, agente, evaluado, intervencion, respuesta } = data;
    
      // Mensaje de intervención (si aplica)
      if (intervencion && respuesta?.trim()) {
        const mensajeIntervencion: ChatMessage = {
          username: agente,
          content: respuesta,
        };
        setMessages((prev) => [...prev, mensajeIntervencion]);
        return;
      }

      const mensajeEvaluacion: ChatMessage = {
        username: agente,     
        content: respuesta,  
      };
      setAgentMessages((prev) => [...prev, mensajeEvaluacion]);

    };
    
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
          {/* Layout con 2 columnas */}
          <div className="grid grid-cols-[2fr_1fr] gap-4 mb-4 items-start">
            {/* Columna izquierda - Chat normal */}
            <div className="min-w-0 border p-3 rounded w-[1000px]"> {/* el [500px] arregló el problema del contenedor */}
              <h2 className="font-semibold mb-2">Chat</h2>
              <div  className="mt-5 border h-[500px] overflow-y-auto p-2 break-words"
              style={
                { marginTop: 20, 
                border: '1px solid gray', 
                height: 500, //cambiar esto para poder setear la altura del contenedor
                maxHeight: 500, // esto igual 
                width: '100%',
                overflowY: 'auto', 
                padding: '10px',
                overflowWrap: 'break-word',
                wordBreak: 'break-word'
                }}>
                {messages.map((m, i) => {
                  const isOwn = m.username === username; // mensaje propio
                  const isSystem = m.system;
                  return (
                    <div
                      key={i}
                      style={{
                        display: 'flex',
                        justifyContent: isSystem ? 'center' : isOwn ? 'flex-end' : 'flex-start',
                        marginBottom: '5px',
                      }}
                    >
                      <div
                        style={{
                          backgroundColor: isSystem ? '#e0e0e0' : isOwn ? '#4caf50' : '#f1f0f0',
                          color: isOwn ? 'white' : 'black',
                          padding: '8px 12px',
                          borderRadius: '20px',
                          maxWidth: '60%',
                          wordBreak: 'break-word',
                        }}
                      >
                        {!isSystem && !isOwn && <b>{m.username}: </b>}
                        {m.content}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Columna derecha - Mensajes del agente */}
            <div className="min-w-0 border p-3 rounded bg-gray-50">
              <h2 className="font-semibold mb-2 text-blue-700">Agente</h2>
              <div className="space-y-2 min-w-0 h-[500px] overflow-y-auto overflow-x-hidden break-words">

                {agentMessages.length === 0 ? (
                  <p className="text-gray-500 text-sm">Sin mensajes del agente todavía.</p>
                ) : (
                  agentMessages.map((m, i) => (
                    <div 
                    key={i}
                    className="w-full min-w-0 max-w-full p-2 rounded bg-blue-100 text-sm text-blue-800"
                    >
                      <b>{m.username}:</b> {m.content}
                    </div>

                  ))
                )}
              </div>
            </div>
          </div>

          {/* Input de mensajes */}
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
        </>
      )}
    </main>
  )
  
  
}
