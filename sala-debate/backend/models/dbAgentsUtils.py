from sqlalchemy.orm import Session
from models.models import AgentPrompt
from sqlalchemy import select, func

def get_current_prompts(db: Session):
    """
    Retorna los prompts más recientes para cada agente.
    extrae el prompts de cada agente mas reciente creado
    """
    subquery = (
        select(
            AgentPrompt.agent_name,
            func.max(AgentPrompt.created_at).label("latest")
        )
        .group_by(AgentPrompt.agent_name)
        .subquery()
    )

    query = (
        select(AgentPrompt)
        .join(
            subquery,
            (AgentPrompt.agent_name == subquery.c.agent_name) &
            (AgentPrompt.created_at == subquery.c.latest)
        )
    )

    results = db.execute(query).scalars().all()

    # Convertir a dict
    return {p.agent_name: p.prompt for p in results}
