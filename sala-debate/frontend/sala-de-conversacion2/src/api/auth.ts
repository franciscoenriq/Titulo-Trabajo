// src/api/auth.ts
const backend = process.env.NEXT_PUBLIC_BACKEND_URL;
export async function login(username: string, password: string) {
    const response = await fetch(`${backend}/api/auth/login`, {
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
  