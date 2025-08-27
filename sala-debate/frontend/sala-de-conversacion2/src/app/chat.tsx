import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';


type ChatMessage = {
  username?: string;
  content: string;
  system?: boolean // para qe cuando haya un mensaje del sistema lo podamos reconocer. 
}
type StatusMessage = {
  msg: string
}
function Chat() {
  const [socket, SetSocket] = useState<any>(null);
  const [room, setRoom] = useState('sala1');
  const [username, setUsername] = useState('Usuario');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  
  useEffect(() => {
    const newSocket = io(process.env.NEXT_PUBLIC_BACKEND_URL,{
      path: '/socket.io',
      transports: ['websocket', 'polling'],
    })
    SetSocket(newSocket);
    return () =>{
      newSocket.disconnect();
    }
  }, [])

  useEffect(() => {
    // Unirse a una sala
    socket.emit('join', { room, username });

    // Escuchar mensajes
    socket.on('message', (data: ChatMessage) => {
      setMessages((prev) => [...prev, data]);
    });

    socket.on('status', (data: StatusMessage) => {
      setMessages((prev) => [...prev, { content: data.msg, system: true }]);
    });

    return () => {
      socket.emit('leave', { room, username });
    };
  }, [room, username]);

  const sendMessage = () => {
    if (message.trim()) {
      socket.emit('message', { room, username, content: message });
      setMessage('');
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Chat en sala: {room}</h2>

      <div>
        <label>Usuario:</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} />
        <label>Sala:</label>
        <input value={room} onChange={(e) => setRoom(e.target.value)} />
      </div>

      <div style={{ marginTop: 20, border: '1px solid gray', height: 300, overflowY: 'scroll' }}>
        {messages.map((m, i) => (
          <div key={i}>
            <b>{m.system ? '[Sistema]' : m.username + ':'}</b> {m.content}
          </div>
        ))}
      </div>

      <div style={{ marginTop: 10 }}>
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button onClick={sendMessage}>Enviar</button>
      </div>
    </div>
  );
}


export default Chat;
