def apply_placeholders(prompt: str, values: dict) -> str:
    """
    Reemplaza placeholders del tipo {clave} por sus valores.
    No usa .format() para evitar KeyError con llaves no deseadas.
    """
    for key, val in values.items():
        prompt = prompt.replace(f"{{{key}}}", str(val))
    return prompt
