import asyncio
import json
import os

from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.module import StateModule
from agentscope.session import JSONSession
from agentscope.tool import Toolkit


class ClassA(StateModule):
    def __init__(self) -> None:
        super().__init__()
        self.cnt = 123
        # register cnt attribute as state
        self.register_state("cnt")


class ClassB(StateModule):
    def __init__(self) -> None:
        super().__init__()

        # attribute "a" inherits from StateModule
        self.a = ClassA()

        # register attribute "c" as state manually
        self.c = "Hello, world!"
        self.register_state("c")


obj_b = ClassB()

print("State of obj_b.a:")
print(obj_b.a.state_dict())

print("\nState of obj_b:")
print(json.dumps(obj_b.state_dict(), indent=4))