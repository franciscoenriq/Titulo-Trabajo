import pandas as pd
from moduloIA.multiagent_evaluador import *
from datetime import datetime
from tqdm import tqdm
import os 
base_dir = os.path.abspath(os.path.dirname(__file__))
filename = os.path.join(base_dir, "chat_complete.csv")
# Cargar el CSV
df = pd.read_csv(filename, sep=';')

# Ordenar los mensajes por tiempo
df["time"] = pd.to_datetime(df["time"])
df_ordenado = df.sort_values(by=["team_id", "time"])

#df_ordenado.to_csv("data_ordenada.csv", index=False, sep=";")
 

tres_grupos = list(df_ordenado.groupby("team_id"))[:3]

resultados = []
# Recorrer cada grupo de conversación
for team_id, mensajes in tqdm(tres_grupos, desc="Procesando salas"):
    promt_inicial = """
      ¿Se debería o no ayudar a Sebastian?
      Contexto del caso:
      Creo que me fue bien en la prueba de matemáticas. Eso sí, en la parte de álgebra lineal tan bien no me fue, pero creo que salvé con las otras preguntas. 
      Justo estaba por salir a tomarme unas cervezas a la casa de una amiga, cuando me llamó Sebastián, mi mejor amigo, para decirme que estaba complicado con el examen de contabilidad; que había estudiado harto pero que creía que no iba a lograr la nota para aprobar el curso. Lo entiendo, el curso es bastante difícil. Es cierto que yo me eximí, pero de que lo pasé mal durante el semestre con los ejercicios y las solemnes, lo pasé mal. 
      Durante la conversación, Sebastián se notaba muy nervioso y angustiado; tan angustiado que yo mismo comencé a angustiarme. No es para menos, si reprueba el curso se atrasa un año y no tendrá dinero para pagar el cuota de la carrera (Sebastián estudia con gratuidad completa). Muchas veces hemos discutido esto con los papás de Sebastián cuando estamos almorzando o cenando en su casa. Ellos son una familia esforzada: ambos papás trabajan para poder sacar adelante a la Francisca y a Sebastián. No entienden por qué han puesto esta regla de financiar sólo los 5 años que dura la carrera (de acuerdo al plan de estudios), cuando todos sabemos que la mayoría de los estudiantes no logra terminarla en ese tiempo. 
      A pesar de todo el esfuerzo que realizan, los papás de Sebastián, Alberto y Alejandra, son muy generosos y acogedores. Me recibieron durante un par de meses en plena pandemia, cuando tenía problemas con mi propia familia, sin poner complicaciones cuando Sebastián preguntó si acaso podía quedarme con ellos un tiempo. En ese tiempo me di cuenta de que Alberto, Alejandra, Sebastián y Francisca son una familia trabajadora y honrada, que no quiere nada regalado.   
      Durante mi estadía con la familia de Sebastián, estudiamos juntos en múltiples ocasiones. Con el tiempo, él me ayudó en los ramos que más me costaban, y viceversa. Pero había un ramo con el cual Sebastián batallaba incesantemente: contabilidad. Volví a mi casa, arreglé las cosas con mi familia y, en unos meses, la pandemia comenzó a menguar: había menos restricciones para moverse y era más fácil salir de la casa, pero, por seguridad, los ramos los seguíamos teniendo online. Por eso no me extrañó que, visiblemente incómodo, Sebastián me pidiera que lo ayudara a contestar el examen de contabilidad. Me imagino la angustia y vergüenza que debe haber tenido para pedírmelo. Ahí entendí por qué me había llamado por teléfono y no había venido a la casa para hablar un tema tan importante.
      Le pregunté a Sebastián por qué tenía tanta vergüenza. Me dijo que, al hablar con su papá, éste le dijo que no podía darse el lujo de reprobar un ramo, que tenía que pasarlo sí o sí, estudiando día y noche, o de otro modo la familia se vería en serios problemas financieros. Pero le dejó muy claro, también que: “en esta familia nos ganamos las cosas, nadie nos regaló nada y no hacemos las cosas a medias o tomando atajos; trabaja duro y verás los resultados”. Y Alejandra, su mamá, le sugirió que hablara conmigo, para que lo ayudara. Después de todo, Sebastián me había ayudado “en las malas”, ¿por qué no iba a hacer lo mismo por él? Sebastián me dijo que estaba muy confundido, sabe que lo que pide me compromete, pero no ve mucha salida al problema. 
      Ni a Sebastián ni a mí nos gusta esto de la copia. De hecho, muchas veces hemos peleado con algunos compañeros porque nos hemos sentido perjudicados por su comportamiento: “ustedes sacan mejor nota que nosotros que no copiamos”, es lo que siempre les decimos. Incluso lo hemos hablado con varios profesores, porque nos molesta mucho que las conductas deshonestas finalmente sean premiadas. Parece que nos gusta vivir en un país en el que “hacerse el vivo” es una cualidad positiva. Los docentes siempre nos han dicho que, al final, por mucho que nuestros compañeros saquen mejores notas, serán siempre peores profesionales que nosotros: primero porque saldremos de la carrera literalmente sabiendo más (y, por consiguiente, mejor preparados); en segundo lugar, porque la honestidad y el trabajo esforzado son virtudes tremendamente deseables en el ámbito laboral. De todas formas, siempre quedamos con la sensación desagradable de que los compañeros que hacen trampa nos pasan a llevar. 
      En fin, me complica mucho la situación de Sebastián y francamente estoy confundido. Y yo que estaba tan contento por el examen de matemáticas. Ahora estoy metido en un lío. Este periodo de exámenes no lo olvidaré fácilmente. Realmente no sé qué hacer. Me siento muy angustiado.” 
      """
    inicializar_conversacion_cascada(team_id, promt_inicial)

    a2_intervino = False
    mensajes_antes_intervencion = 0
    for i, row in mensajes.iterrows():
        print(f"\n🟩 Analizando mensajes de la sala: {team_id}")
        print(f"💬 Mensaje: {row['message']}")
        user_input = row["message"]
        user_name = f"user_{row['user_id']}"

        if not isinstance(user_input, str) or user_input.strip() == "":
            continue  # ignorar mensajes vacíos

        resultado = analizar_argumento_cascada(
            room=team_id,
            user_input=user_input,
            user_name=user_name
        )

        if resultado["intervencion"] and not a2_intervino:
            a2_intervino = True
            resultados.append({
                "team_id": team_id,
                "mensaje_indice": i,
                "user_name": user_name,
                "mensaje": user_input,
                "respuesta_a2": resultado["respuesta"],
                "agente": resultado["agente"],
                "evaluacion": resultado["evaluacion"],
                "tiempo_mensaje": row["time"],
                "mensajes_antes_intervencion": mensajes_antes_intervencion,
            })
            break  # Solo nos interesa el primer momento de intervención
        mensajes_antes_intervencion += 1
# Guardar resultados
resultados_df = pd.DataFrame(resultados)
resultados_df.to_csv("resultados_intervenciones.csv", index=False)
print("✅ Resultados guardados en 'resultados_intervenciones.csv'")
