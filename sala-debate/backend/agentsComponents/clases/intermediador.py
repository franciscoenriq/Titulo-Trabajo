from .pipeLine_ejecucion import CascadaPipeline
class Intermediario:
    def __init__(self,tamañoVentana:int,pipeLine:CascadaPipeline):
        self.tamañoVentana = tamañoVentana
        self.mensajesTotales = []
        self.pipeLine = pipeLine
    

    async def agregarMensage(self, userName:str, message:str):
        self.mensajesTotales.append({
            "userName":userName,
            "content":message
        })
        if(len(self.mensajesTotales) == self.tamañoVentana):
            result = await self.pipeLine.analizar_argumento_cascada(self.mensajesTotales)
            return result
        else: 
            return 
            



    

