from factory_agents import * 
from agentscope.message import Msg
import asyncio
import json
prompt = """ Eres un agente experto en revisiones de conversaciones éticas. 
    Tu objetivo es analizar como se comportó un sistema multiagente para poder realizar intervenciones
    en conversaciones de estudiatnes que discuten un tema ético. 
    El agente que realmente se está comunicando con los estudiantes es el agente llamado Agente Orientador. 
    El agente validador es el que actualiza el vector de avance argumentativo de cada participante de la conversacion. 
    Esto lo hace en relacion al modelo de Toulmin, el cual describe las partes de un argumento.
    Luego el agente CUrador decide o no si hay que intervenir o no. 
    Debes ser lo más sincer@ y objetivo posible en tu análisis.
    ten en cuenta los timestamps de como se entraron los mensjaes del agente , orientador, validador y curador. 
    ocurrió que hubo un problema de threads y esto provocó de que en algunos casos los mensjaes del agente validador, curador y oreintador tengan delay
    se te proveeran conversaciones y tu debes realizar un análisis detallado de los siguientes aspectos:
    para cada item debes dedar aspecto positivos como negativos. No seas condecendiente. Se objetivo y claro. 
    El objetivo es evaluar esto criticamente. tenen en cuenta los timestamps de los mensajes. el agente orientador puede estar respondiendo muy tarde 
    a algo que ya se habia dicho y que los estufdiantes ya habian respondido.
    1. Pertinencia temática

¿El agente se refiere al contenido del dilema o conversación en curso?

¿Evita temas irrelevantes o tangenciales?

Indicadores posibles: uso de términos clave del dilema; referencia explícita a argumentos o preguntas previas.

2. Pertinencia temporal (oportunidad)

¿El momento de la intervención es adecuado?

¿Evita interrumpir saludos, momentos de pausa natural o intercambios argumentativos en curso?

Indicadores posibles: número de turnos previos, tiempo desde inicio de la conversación, si el grupo ha comenzado o no a discutir el dilema.

3. Pertinencia funcional

¿La intervención tiene un propósito claro y beneficioso para el grupo?

Ejemplos: solicitar clarificación, resumir, invitar a reflexionar, fomentar participación equitativa.

Evita funciones innecesarias o confusas (como repetir lo que ya se dijo).

4. Adecuación comunicativa

¿Está formulada en un tono conversacional, amable, neutral o adaptado al estilo del grupo?

¿Evita parecer autoritaria, forzada o artificial?

Indicadores posibles: uso de lenguaje informal/formal según contexto; evitar jerga técnica; uso de expresiones típicas del grupo humano.

5. Aceptabilidad social

¿Los participantes reaccionan positivamente o integran la intervención en la conversación?

¿La ignoran? ¿La rechazan? ¿Se genera incomodidad?

Este es un criterio posterior a la intervención, pero esencial para validarla.

  """

prompt = """Eres un agente experto en análisis de sistemas multiagente y en evaluación de conversaciones éticas entre estudiantes. 
Se te entregará una transcripción de una sesión de chat en la que los estudiantes discuten un dilema ético: el caso de Sebastián, 
un estudiante que podría necesitar ayuda durante un examen. 

En la sesión participan distintos agentes del sistema:
- El agente Orientador, que interactúa directamente con los estudiantes para guiar la discusión.
- El agente Curador, que analiza los argumentos de los estudiantes siguiendo el modelo de Toulmin, identificando 
  las partes de cada argumento (Claim, Evidence, Warrant) y sugiriendo acciones al agente Orientador.
- El agente Validador, que actualiza el avance argumentativo de los participantes (aunque en este análisis no se incluirá su contenido).

Tu tarea es realizar un análisis **descriptivo y crítico** de la conversación, enfocándote en los siguientes puntos:
1. Para cada mensaje del agente Curador, analiza cómo identificó patrones faltantes en los argumentos de los estudiantes.
2. Evalúa la relación entre las recomendaciones del Curador y la respuesta que da efectivamente el agente Orientador.
3. Señala aciertos y limitaciones del sistema en términos de:
   - Pertinencia temática: si se enfoca correctamente en el dilema y evita temas irrelevantes.
   - Pertinencia temporal: si las intervenciones ocurren en momentos adecuados y oportunos.
   - Pertinencia funcional: si las intervenciones cumplen un propósito claro y beneficioso.
   - Adecuación comunicativa: claridad y tono de las intervenciones.
4. Ten en cuenta posibles retrasos o desincronización en las respuestas debido a la dinámica del sistema multiagente y del timer.
5. Haz un análisis imparcial, señalando aspectos positivos y negativos de manera objetiva.
6. Al final, proporciona un resumen general sobre el desempeño del sistema multiagente en esta sesión de chat.

A continuación recibirás la transcripción de la conversación, actúa como un analista experto y genera un informe detallado siguiendo los criterios anteriores.
finalmente te daré el caso que estan discutiendo los alumnos :


¿Se debería o no ayudar a Sebastian?: Creo que me fue bien en la prueba de matemáticas. Eso sí, en la parte de álgebra lineal tan bien no me fue, pero creo que salvé con las otras preguntas. Justo estaba por salir a tomarme unas cervezas a la casa de una amiga, cuando me llamó Sebastián, mi mejor amigo, para decirme que estaba complicado con el examen de contabilidad; que había estudiado harto pero que creía que no iba a lograr la nota para aprobar el curso. Lo entiendo, el curso es bastante difícil. Es cierto que yo me eximí, pero de que lo pasé mal durante el semestre con los ejercicios y las solemnes, lo pasé mal. Durante la conversación, Sebastián se notaba muy nervioso y angustiado; tan angustiado que yo mismo comencé a angustiarme. No es para menos, si reprueba el curso se atrasa un año y no tendrá dinero para pagar el cuota de la carrera (Sebastián estudia con gratuidad completa). Muchas veces hemos discutido esto con los papás de Sebastián cuando estamos almorzando o cenando en su casa. Ellos son una familia esforzada: ambos papás trabajan para poder sacar adelante a la Francisca y a Sebastián. No entienden por qué han puesto esta regla de financiar sólo los 5 años que dura la carrera (de acuerdo al plan de estudios), cuando todos sabemos que la mayoría de los estudiantes no logra terminarla en ese tiempo.  A pesar de todo el esfuerzo que realizan, los papás de Sebastián, Alberto y Alejandra, son muy generosos y acogedores. Me recibieron durante un par de meses en plena pandemia, cuando tenía problemas con mi propia familia, sin poner complicaciones cuando Sebastián preguntó si acaso podía quedarme con ellos un tiempo. En ese tiempo me di cuenta de que Alberto, Alejandra, Sebastián y Francisca son una familia trabajadora y honrada, que no quiere nada regalado.  Durante mi estadía con la familia de Sebastián, estudiamos juntos en múltiples ocasiones. Con el tiempo, él me ayudó en los ramos que más me costaban, y viceversa. Pero había un ramo con el cual Sebastián batallaba incesantemente: contabilidad. Volví a mi casa, arreglé las cosas con mi familia y, en unos meses, la pandemia comenzó a menguar: había menos restricciones para moverse y era más fácil salir de la casa, pero, por seguridad, los ramos los seguíamos teniendo online. Por eso no me extrañó que, visiblemente incómodo, Sebastián me pidiera que lo ayudara a contestar el examen de contabilidad. Me imagino la angustia y vergüenza que debe haber tenido para pedírmelo. Ahí entendí por qué me había llamado por teléfono y no había venido a la casa para hablar un tema tan importante. Le pregunté a Sebastián por qué tenía tanta vergüenza. Me dijo que, al hablar con su papá, éste le dijo que no podía darse el lujo de reprobar un ramo, que tenía que pasarlo sí o sí, estudiando día y noche, o de otro modo la familia se vería en serios problemas financieros. Pero le dejó muy claro, también que: “en esta familia nos ganamos las cosas, nadie nos regaló nada y no hacemos las cosas a medias o tomando atajos; trabaja duro y verás los resultados”. Y Alejandra, su mamá, le sugirió que hablara conmigo, para que lo ayudara. Después de todo, Sebastián me había ayudado “en las malas”, ¿por qué no iba a hacer lo mismo por él? Sebastián me dijo que estaba muy confundido, sabe que lo que pide me compromete, pero no ve mucha salida al problema.  Ni a Sebastián ni a mí nos gusta esto de la copia. De hecho, muchas veces hemos peleado con algunos compañeros porque nos hemos sentido perjudicados por su comportamiento: “ustedes sacan mejor nota que nosotros que no copiamos”, es lo que siempre les decimos. Incluso lo hemos hablado con varios profesores, porque nos molesta mucho que las conductas deshonestas finalmente sean premiadas. Parece que nos gusta vivir en un país en el que “hacerse el vivo” es una cualidad positiva. Este periodo de exámenes no lo olvidaré fácilmente. Realmente no sé qué hacer. Me siento muy angustiado.
"""

# --- FUNCIÓN PARA NORMALIZAR RESPUESTA ---
def ensure_text(msg):
    """Convierte cualquier estructura de Agentscope (list, dict, Msg, etc.)
    en un string simple, evitando estructuras anidadas."""
    try:
        if hasattr(msg, "to_dict"):
            msg = msg.to_dict()
    except:
        pass

    if isinstance(msg, list):
        return "\n".join(ensure_text(m) for m in msg)

    if isinstance(msg, dict):

        if "text" in msg and isinstance(msg["text"], str):
            return msg["text"]

        if "content" in msg and isinstance(msg["content"], str):
            return msg["content"]

        if "value" in msg and isinstance(msg["value"], str):
            return msg["value"]

        return json.dumps(msg, ensure_ascii=False)

    return str(msg)


# --- CONFIGURACIÓN DE CARPETAS ---
CARPETA_CONVERSACIONES = "salas_txt"
CARPETA_RESPUESTAS = "respuestas"

os.makedirs(CARPETA_RESPUESTAS, exist_ok=True)


factory = ReActAgentFactory()
agenteRevisor = factory.create_agent(
    name="agente_revisor",   # ← nombre 100% válido para OpenAI
    sys_prompt=prompt
)


# --- PROCESAMIENTO ---
async def procesar_conversaciones():
    
    archivos = [f for f in os.listdir(CARPETA_CONVERSACIONES) if f.endswith(".txt")]
    archivo = "sala_92e5445e-7af0-4fbe-b53d-9e080f65d176LISTA.txt"
    ruta = os.path.join(CARPETA_CONVERSACIONES, archivo)
    """ 
    for archivo in archivos:
        ruta = os.path.join(CARPETA_CONVERSACIONES, archivo)

        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read()

        msg = Msg(
            name="input",   # ← nombre seguro, sin espacios
            role="system",
            content=f"A continuación se te entrega la conversación completa:\n\n{contenido}"
        )

        # --- LLAMAR AL AGENTE ---
        respuesta = await agenteRevisor(msg)

        # --- ASEGURAR TEXTO LIMPIO ---
        respuesta_texto = ensure_text(respuesta.content)

        # --- GUARDAR RESPUESTA ---
        ruta_salida = os.path.join(CARPETA_RESPUESTAS, f"respuesta_{archivo}")
        with open(ruta_salida, "w", encoding="utf-8") as f:
            f.write(respuesta_texto)

        print(f"✓ Procesado y guardado: {archivo}")
    """


    # Leer la conversación
    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read()
    # Crear mensaje para el agente
    msg = Msg(
        name="input",   # nombre seguro
        role="system",
        content=f"A continuación se te entrega la conversación completa:\n\n{contenido}"
    )
    respuesta = await agenteRevisor(msg)

    # --- ASEGURAR TEXTO LIMPIO ---
    respuesta_texto = ensure_text(respuesta.content)

    # --- GUARDAR RESPUESTA ---
    ruta_salida = os.path.join(CARPETA_RESPUESTAS, f"respuesta_{archivo}_analisis")
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(respuesta_texto)

    print(f"✓ Procesado y guardado: {archivo}")
asyncio.run(procesar_conversaciones())




