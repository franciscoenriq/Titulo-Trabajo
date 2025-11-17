'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'


export default function LoginPage() {
  const router = useRouter()

  const entrarComoAlumno = () => {
    router.push('/elegirChat')
  }

  const entrarComoMonitor = () => {
    router.push('/monitor')
  }

  return (
    <>
      <div className="container" id="container">
        <div className="form-container sign-in-container">
          <form>
            <h1>Entrar al Debate</h1>
            <p></p>
            <button
              type="button"
              onClick={entrarComoAlumno}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-600"
            > Debatir </button>
            <p></p>
            {/* 
            <button
              type="button"
              onClick={entrarComoMonitor}
              className="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-green-700"
            > Monitorear </button>
            <p></p>
            */}
          </form>
        </div>

        <div className="overlay-container">
          <div className="overlay">
            <div className="overlay-panel overlay-left">
              <button className="ghost" id="signIn">Sign In</button>
            </div>
            <div className="overlay-panel overlay-right">
              <h1>¡Hola, explorador ético!</h1>
              <p>
              Forma parte de conversaciones en salas de chat en las 
              que tus argumentos son examinados por un sistema multiagente 
              orientado al análisis y la evaluación de discusiones éticas.
              </p>
            </div>
          </div>
        </div>
      </div>

  </>
    


    
  )
}
