import os
from dotenv import load_dotenv
from agentscope.agent import ReActAgent
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit, ToolResponse
load_dotenv()
api_key = os.getenv("API_KEY")


class ReActAgentFactory:

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model_name

    def create_agent(self, name: str, sys_prompt: str) -> ReActAgent:
        return ReActAgent(
            name=name,
            sys_prompt=sys_prompt,
            model=OpenAIChatModel(
                model_name=self.model_name,
                api_key=self.api_key,
                stream=False
            ),
            formatter=OpenAIChatFormatter(),
            memory=InMemoryMemory()
        )
    
    def create_agent_with_toolkit(self,name: str, sys_prompt: str,toolkit:Toolkit) -> ReActAgent:
        return ReActAgent(
            name=name,
            sys_prompt=sys_prompt,
            model=OpenAIChatModel(
                model_name=self.model_name,
                api_key=self.api_key,
                stream=False
            ),
            formatter=OpenAIChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=toolkit
        )


