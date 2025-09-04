import requests

# URL de tu backend
url = "http://localhost:5000/api/prompts"

try:
    response = requests.get(url)
    response.raise_for_status()  # Lanza excepción si el status no es 200
    prompts = response.json()
    print("Prompts actuales de los agentes:")
    for agente, prompt in prompts.items():
        print(f"{agente}: {prompt}")
except requests.exceptions.RequestException as e:
    print("Error al consultar el endpoint:", e)
