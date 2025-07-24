'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export function useAuthGuard(expectedRole: string | null = null) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const userString = localStorage.getItem('user')
    if (!userString) {
      router.push('/') // Redirige al login si no está autenticado
      return
    }

    try {
      const parsedUser = JSON.parse(userString)

      if (expectedRole && parsedUser.rol !== expectedRole) {
        router.push(expectedRole === 'alumno' ? '/elegirChat' : '/monitor') // redirige a su home si rol no coincide
        return
      }

      setUser(parsedUser)
      setIsLoading(false)
    } catch (err) {
      console.error('Error leyendo usuario del localStorage:', err)
      router.push('/')
    }
  }, [expectedRole, router])

  return { user, isLoading }
}
