from .pipeLine_ejecucion import CascadaPipeline
from .factory_agents import ReActAgentFactory
factory = ReActAgentFactory()

class Intermediario:
    def __init__(self,tamañoVentana:int,prompt_agenteEntrada:str,prompt_agenteSalida:str):
        self.tamañoVentana = tamañoVentana
        self.mensajesTotales = []
        self.pipeLine = CascadaPipeline(factory, prompt_agenteEntrada,prompt_agenteSalida)
    
    async def agregarMensage(self, userName:str, message:str) -> list[dict] | None:
        print("se agrega un mensjae")
        self.mensajesTotales.append({
            "userName":userName,
            "content":message
        })
        if(len(self.mensajesTotales) == self.tamañoVentana):
            print("se llama al pipeline")

            result = await self.pipeLine.analizar_argumento_cascada(self.mensajesTotales)
            self.mensajesTotales = []
            return result
        else: 
            return 
    
    async def start_session(self,topic:str)->None:
        await self.pipeLine.start_session(topic)
    
    async def stop_session(self):
        await self.pipeLine.stop_session()

    async def anunciar_entrada_participante(self,userName:str) -> None:
        await self.pipeLine.anunciar_entrada_participante(userName)

    async def anunciar_salida_participante(self,userName:str) -> None:
        await self.pipeLine.anunciar_salida_participante(userName)
            



    

