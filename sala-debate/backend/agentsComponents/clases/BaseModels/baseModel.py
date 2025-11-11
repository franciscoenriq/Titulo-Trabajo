from pydantic import BaseModel, Field, RootModel
from typing import List, Dict
import json


class BaseModelEstudiante(BaseModel):
    """
    Modelo base que representa el estado del análisis de un estudiante
    según el modelo de Toulmin.
    """
    Claim: int = Field(0, description="0 si no se ha identificado afirmación; 1 si se ha detectado una afirmación.")
    Evidence: int = Field(-1, description="-1 si no hay evidencia identificada; 1 si la hay.")
    Warrant: int = Field(-1, description="-1 si no hay justificación identificada; 1 si la hay.")
    Qualifier: int = Field(0, description="0 si no se detecta calificativo; 1 o 2 según el grado de certeza.")
    fuentes: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "Claim": [],
            "Evidence": [],
            "Warrant": [],
            "Qualifier": []
        },
        description="Diccionario con listas de IDs de mensajes que sustentan cada componente."
    )
    explicacion: str = Field(
        "",
        description="Texto breve que justifica el cambio más reciente de estado detectado por el Validador."
    )


class BaseModelValidador(RootModel[Dict[str, BaseModelEstudiante]]):
    """
    Modelo base del agente Validador.
    Contiene dinámicamente un diccionario plano donde cada clave es un estudiante.
    Ejemplo de salida:
    {
        "estudiante1": {...},
        "estudiante2": {...}
    }
    """

    @classmethod
    def crear_modelo_inicial(cls, lista_estudiantes: List[str]) -> "BaseModelValidador":
        """
        Construye el estado inicial del Validador según la cantidad de participantes en la sala.
        Cada estudiante queda al nivel superior del JSON.
        """
        data = {nombre: BaseModelEstudiante() for nombre in lista_estudiantes}
        return cls(data)

    def model_dump_json(self, *args, **kwargs) -> str:
        """
        Devuelve el JSON serializado en formato plano y 100% serializable.
        """
        # Convertir los modelos internos a dict antes de hacer json.dumps
        data_dict = {k: v.model_dump() for k, v in self.root.items()}
        return json.dumps(data_dict, indent=2, ensure_ascii=False)


