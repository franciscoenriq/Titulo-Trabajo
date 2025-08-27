import agentscope
from agentscope.agents import AgentBase
from agentscope.message import Msg
from typing import Optional, Union, Sequence
import os 


base_dir = os.path.dirname(os.path.abspath(__file__))
model_config_path = os.path.join(base_dir, "configs", "model_configs.json")
npc_agents = agentscope.init(
    model_configs=model_config_path)


class EvaluatorAgent(AgentBase):
    def __init__(
            self,
            name, 
            sys_prompt:str, 
            model_config_name :str, 
            use_memory = True):
        super().__init__(name, 
                         sys_prompt, 
                         model_config_name, 
                         use_memory
                         )
        self.memory.add(Msg(self.name, self.sys_prompt, "system"))

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        self.memory.add(x)

        prompt = self.model.format(self.memory.get_memory())

        res = self.model(prompt)

        # Print the streaming message in the terminal and Studio
        # (if registered)

        # The stream filed is a generator that yields the streaming text
        self.speak(res.stream)

        # The text field of the response will be filled with the full response
        # text after the streaming is finished
        msg_returned = Msg(self.name, res.text, "assistant")

        self.memory.add(msg_returned)

        return msg_returned
