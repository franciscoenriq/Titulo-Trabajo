'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
export default function Home() {
  const [room, setRoom] = useState('')
  const [topic,setTopic] = useState('')
  const router = useRouter()
  
  const handleEnter = async () =>{
    if (!room || !topic) return
    try {
      await fetch('http://localhost:5000/api/init-topic', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          room,
          prompt_inicial: topic,
        }),
      })

      router.push(`/chat/${room}`)
    } catch (error) {
      console.error('Error al inicializar la conversación:', error)
    }
  }

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-4">Ingresa el nombre de la sala</h1>
        <div className="flex gap-2 mb-4">
        <input
          type="text"
          className="border p-2 w-64"
          value={room}
          onChange={(e) => setRoom(e.target.value)}
          placeholder="Nombre de la sala"
        />
        <textarea
          className="border p-2"
          rows={4}
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Tema inicial de la discusión"
        />
        <button onClick={handleEnter} className="bg-green-600 text-white px-4 py-2 rounded">
          Entrar
        </button>
      </div>
    </main>
  )
}
