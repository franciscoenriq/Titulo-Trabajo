from .pipeLine_ejecucion import CascadaPipeline
from .factory_agents import ReActAgentFactory
from .pipeLine_Nuevo import Pipeline
factory = ReActAgentFactory()

class Intermediario:
    def __init__(self,tamañoVentana:int,prompt_agenteEntrada:str,prompt_agenteSalida:str):
        self.tamañoVentana = tamañoVentana
        self.mensajesTotales = []
        self.pipeLine = CascadaPipeline(factory, prompt_agenteEntrada,prompt_agenteSalida)
        self.numeroMensajesTotales = 0
        self.newPipeline = Pipeline(factory,prompt_agenteSalida)
    
    async def agregarMensage(self, userName:str, message:str) -> list[dict] | None:
        await self.pipeLine.entrar_mensaje_al_hub({
            "userName":userName,
            "content":message
        })

        await self.newPipeline.analizar_mensaje(userName,message)
        #if(respuesta_enrutador):
        #    return respuesta_enrutador

        self.numeroMensajesTotales += 1 
        print(self.numeroMensajesTotales)
        if (self.numeroMensajesTotales == self.tamañoVentana):
            #result = await self.pipeLine.analizar_argumento_cascada()
            result = await self.newPipeline.analizar_argumento_cascada()
            self.numeroMensajesTotales = 0
            return result
        else: 
            return 
    
    async def start_session(self,topic:str)->None:
        await self.pipeLine.start_session(topic)
        await self.newPipeline.start_session(topic)
    
    async def stop_session(self):
        await self.pipeLine.stop_session()
        await self.newPipeline.stop_session()

    async def anunciar_entrada_participante(self,userName:str) -> None:
        await self.pipeLine.anunciar_entrada_participante(userName)

    async def anunciar_salida_participante(self,userName:str) -> None:
        await self.pipeLine.anunciar_salida_participante(userName)
            



    

