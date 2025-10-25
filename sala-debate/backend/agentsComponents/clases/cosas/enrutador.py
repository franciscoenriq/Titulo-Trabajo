
from pydantic import BaseModel, Field
from typing import Literal,Optional

from agentscope.message import Msg
import json
import asyncio
from factory_agents import ReActAgentFactory

factory = ReActAgentFactory()
router = factory.create_agent(
            name="Router",
            sys_prompt="You're a routing agent. Your target is to route the user query to the right follow-up task."
        )
class RoutingChoice(BaseModel):
    tu_eleccion: Optional[Literal["Curador", "Resumidor"]] = Field(
        description="Choose the right follow-up task, or None if no suitable task."
    )
    task_description: str | None = Field(
        description="The task description",
        default=None,
    )
        


async def example_router_explicit() -> None:
    """Example of explicit routing with structured output."""
    msg_user = Msg(
    "user",
    "Help me to write a poem",
    "user",
    )

    # Route the query
    msg_res = await router(
    msg_user,
    structured_model=RoutingChoice,
    )

    # The structured output is stored in the metadata field
    print("The structured output:")
    print(json.dumps(msg_res.metadata, indent=4, ensure_ascii=False))


asyncio.run(example_router_explicit())