// src/api/auth.ts
export async function login(username: string, password: string) {
    const response = await fetch('http://127.0.0.1:5000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });
  
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Error desconocido');
    }
    return data;
  }
  