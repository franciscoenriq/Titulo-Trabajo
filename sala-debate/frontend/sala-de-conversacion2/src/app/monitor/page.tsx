'use client'

import { useAuthGuard } from '../hooks/useAuthGuard'

export default function MonitorPage() {
  const { user, isLoading } = useAuthGuard('monitor')

  if (isLoading) return <p className="text-center mt-10">Cargando...</p>

  return (
    <main className="max-w-xl mx-auto mt-16 p-6 border rounded shadow text-center">
      <h1 className="text-2xl font-bold mb-4">Hola monitor 👋</h1>
      <p className="text-gray-700">Bienvenido a tu panel de control.</p>
    </main>
  )
}
