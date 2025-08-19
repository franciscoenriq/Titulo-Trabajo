import pandas as pd
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
columnas_a_eliminar = ['df', 'title',"opt_left","opt_right","rut"]
df_ordenado = df_ordenado.drop(columns=columnas_a_eliminar)
df_ordenado.to_csv("data_filtrada.csv", index=False, sep=";")