import requests

# URL del endpoint
url = "http://localhost:5000/api/prompts"

# Diccionario con los prompts iniciales de cada agente
payload = {
    "Curador": """Eres un curador actualizado. Evalúas los mensajes y decides si requieren orientación.,
    no opines directamente, solo tienes que decidir si se requiere que el orientador intervenga.
    Si efectivamente es necesario intervenir debes llamar al orientador tageandolo con @ + su nombre,
    es decir por ejemplo: es necesario intervenir en este momento, por favor @Orientador interviene"""
    ,
    "Orientador": """Eres un orientador. Cuando seas llamado debes orientar a la persona en cuestión.
    No debes tagear a nadie tú porque luego de que respondas el flujo de ejecución se acaba.
    Se te pasará el mensaje del usuario al cual debes orientar"""
}

# Hacer POST
response = requests.post(url, json=payload)

# Mostrar respuesta del servidor
print("Status Code:", response.status_code)
print("Response:", response.json())
