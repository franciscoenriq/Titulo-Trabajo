'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { login } from '@/api/auth' // ajusta si la ruta es distinta

export default function LoginPage() {
  const router = useRouter()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      const response = await login(username, password)
      const { user } = response

      if (!user?.rol) {
        throw new Error('El usuario no tiene rol definido.')
      }

      // Guarda al usuario
      localStorage.setItem('user', JSON.stringify(user))

      // Redirige según el rol
      if (user.rol === 'alumno') {
        router.push('/elegirChat') // formulario sala/tema
      } else if (user.rol === 'monitor') {  
        router.push('/monitor') // página especial para monitor
      } else {
        throw new Error('Rol no reconocido')
      }

    } catch (err: any) {
      setError(err.message || 'Error al iniciar sesión')
    }
  }

  return (
    <div className="max-w-md mx-auto mt-16 p-6 border rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Iniciar Sesión</h2>
      <form onSubmit={handleLogin}>
        <input
          type="text"
          placeholder="Usuario"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          className="w-full p-2 border mb-3 rounded"
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full p-2 border mb-3 rounded"
        />
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition"
        >
          Entrar
        </button>
      </form>
      {error && <p className="text-red-600 mt-2">{error}</p>}
    </div>
  )
}
