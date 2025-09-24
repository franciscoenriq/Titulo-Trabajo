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
    agente: string;
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
  const [typingUsers,setTypingUsers] = useState<string[]>([])
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL;
  useEffect(() => {
    fetch(`${backend}/api/tema/${room}`)
    .then((res) => res.json())
    .then((data) => setTema(data.tema))
  }, [room])
// Hook para cargar mensajes históricos al unirse
useEffect(() => {
  if (!joined || !username) return;

  const fetchHistoricalMessages = async () => {
    try {
      const res = await fetch(`${backend}/api/room-messages/${room}`);
      if (!res.ok) return; // si no hay mensajes o error, no hacemos nada

      const data: {
        username?: string;
        content: string;
        system?: boolean;
        agente?: string;
        intervencion?: string;
        timestamp?: string;
      }[] = await res.json();

      if (!data || data.length === 0) return;

      // Separar mensajes de agentes y normales
      const normalMessages: ChatMessage[] = [];
      const agentMsgs: ChatMessage[] = [];

      data.forEach((m) => {
        if (m.agente) {
          // Curador -> panel de agentes
          if (m.agente.toLowerCase() === 'curador') {
            agentMsgs.push({ username: m.agente, content: m.content });
          } else {
            // Orientador -> chat normal
            normalMessages.push({ username: m.agente, content: m.content });
          }
        } else {
          // Mensajes históricos normales
          const isOwn = m.username === username; // Si coincide con el usuario actual
          normalMessages.push({
            username: m.username,
            content: m.content,
            system: m.system,
          });
        }
      });

      // Actualizar estado
      setMessages((prev) => [...normalMessages, ...prev]);
      setAgentMessages((prev) => [...agentMsgs, ...prev]);
    } catch (error) {
      console.error('Error al cargar mensajes históricos:', error);
    }
  };

  fetchHistoricalMessages();
}, [joined, room, backend, username]);


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

    const handleEvaluacion = (data: EvaluacionData[]|EvaluacionData) => {
      const mensajes = Array.isArray(data) ? data : [data];

      mensajes.forEach(({agente, respuesta}) => {
        if (!respuesta?.trim()) return;
    
        if (agente.toLowerCase() === "orientador") {
          //orientador -> chat general
          setMessages((prev) => [...prev, { username: agente, content: respuesta }]);
        } 
        // curador -> va al panel de agentes
        else if (agente.toLowerCase() === "curador") {
          setAgentMessages((prev) => [...prev, { username: agente, content: respuesta }]);
        }
        else if (agente.toLowerCase() === "resumidor") {
          // Resumidor -> chat general 
          setMessages((prev) => [...prev, { username: agente, content: respuesta }]);
        }
      })
    };

    // usuarios que escriben
    socket.on('typing', (data: { username: string }) => {
      setTypingUsers((prev) => {
        if (!prev.includes(data.username)) {
          return [...prev, data.username]
        }
        return prev
      })
    })

    socket.on('stop_typing', (data: { username: string }) => {
      setTypingUsers((prev) => prev.filter((u) => u !== data.username))
    })

    
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
      sessionStorage.setItem('chatUser', JSON.stringify({ room, username }))
    }
  }
  useEffect(() => {
    const saved = sessionStorage.getItem('chatUser')
    if (saved) {
      const { room: savedRoom, username: savedUser } = JSON.parse(saved)
      if (savedRoom === room) {
        setUsername(savedUser)
        setJoined(true)
        socketRef.current?.emit('join', { room, username: savedUser })
      }
    }
  }, [room])

  const sendMessage = () => {
    if (input.trim() && socketRef.current && username) {
      socketRef.current.emit('message', { room, username, content: input.trim() })
      socketRef.current.emit('stop_typing',{room,username})
      setInput('')
    }
  }
  // Detectar cuando el usuario escribe
  const handleTyping = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)

    if (socketRef.current && username) {
      if (e.target.value.length > 0) {
        socketRef.current.emit('typing', { room, username })
      } else {
        socketRef.current.emit('stop_typing', { room, username })
      }
    }
  }

  useEffect(() => {
    const socket = socketRef.current;
    if (!socket || !username || !joined) return;
  
    const handleBeforeUnload = () => {
      socket.emit("leave", { room, username });
    };
  
    window.addEventListener("beforeunload", handleBeforeUnload);
  
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [joined, username, room]);
  

  const leaveRoom = () => {
    if (socketRef.current && username) {
      socketRef.current.emit("leave", { room, username });
      setJoined(false);
      setMessages([]);
      setAgentMessages([]);
      sessionStorage.removeItem('chatUser')
    }
  };
  

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
                {typingUsers.length > 0 && (
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-start',
                    marginBottom: '5px',
                  }}
                >
                  <div
                    style={{
                      backgroundColor: '#f1f0f0',
                      color: 'gray',
                      padding: '6px 10px',
                      borderRadius: '20px',
                      fontStyle: 'italic',
                    }}
                  >
                    <span className="mr-2">💬</span>
                    {typingUsers.join(', ')} {typingUsers.length > 1 ? 'están' : 'está'} escribiendo...
                  </div>
                </div>
              )}

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
            onChange={handleTyping}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Escribe tu mensaje"
            className="border p-2 w-full"
          />
          <button onClick={sendMessage} className="mt-2 bg-blue-500 text-white px-4 py-2 rounded">
            Enviar
          </button>
          <button 
            onClick={leaveRoom} 
            className="mt-2 bg-red-600 text-white px-4 py-2 rounded"
          >
            Salir de la sala
          </button>

        </>
      )}
    </main>
  )
  
  
}
