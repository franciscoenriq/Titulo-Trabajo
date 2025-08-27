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
    <>
      <div className="container" id="container">
        <div className="form-container sign-up-container">
          <form action="#">
            <h1>Create Account</h1>
            <span>or use your email for registration</span>
            <input type="text" placeholder="Name" />
            <input type="email" placeholder="Email" />
            <input type="password" placeholder="Password" />
            <button>Sign Up</button>
          </form>
        </div>

        <div className="form-container sign-in-container">
          <form onSubmit={handleLogin}>
            <h1>Sign in</h1>
            
            <span>or use your account</span>
            <p></p>
            <input 
              type="text"
              placeholder="Usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required 
            />
            <input 
              type="password" 
              placeholder="Contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required

            />
            {/*<a href="#">Forgot your password?</a>*/}
            <p></p>
            <button type='submit'>
              Entrar
            </button>
          </form>
        </div>

        <div className="overlay-container">
          <div className="overlay">
            <div className="overlay-panel overlay-left">
              <h1>Welcome Back!</h1>
              <p>To keep connected with us please login with your personal info</p>
              <button className="ghost" id="signIn">Sign In</button>
            </div>
            <div className="overlay-panel overlay-right">
              <h1>Hello, Friend!</h1>
              <p>Enter your personal details and start journey with us</p>
              {/*<button className="ghost" id="signUp">Sign Up</button>*/}
            </div>
          </div>
        </div>
        {error && <p className="text-red-600 mt-2">{error}</p>}
      </div>
      {/*<Script src="/js/login.js" strategy="afterInteractive" /> */}

  </>
    


    
  )
}
