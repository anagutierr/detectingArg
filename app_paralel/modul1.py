import asyncio
from rasa.core.agent import Agent
from rasa.shared.utils.io import json_to_string
import json
import os

# Clase para la carga de los modelos entrenados como clasificadores en RASA
class Model:
        def __init__(self, model_path: str) -> None:
            self.agent = Agent.load(model_path)
            print("NLU model loaded")


        def message(self, message: str) -> str:
            message = message.strip()
            result = asyncio.run(self.agent.parse_message(message))
            return json_to_string(result)
        

# Funicón que dada un frase la clasifica en un esquema argumentativo usando un sistema de clasificadores en 2 capas/niveles
def classification(phrase):    
    # CAPA 1   
    current_dir = os.path.dirname(os.path.abspath(__file__))
    modelo_rel_path = r'ClasificadorCAPA1\rasaBot\models\nlu-20240412-100510-elegant-miso.tar.gz'
    modelo_abs_path = os.path.join(current_dir, modelo_rel_path)

    # Cargar el modelo
    mdl_CAPA1 = Model(modelo_abs_path)
    output_json = mdl_CAPA1.message(phrase)
    output_dict = json.loads(output_json)
    grupo_pred = output_dict['intent']['name']

    print("Dada la frase: ", output_dict['text'])
    print("El clasificador de la CAPA1 ha predicho que es el de: ", grupo_pred)
    print("con una confianza de ", output_dict['intent']['confidence'])


    #CAPA 2
    print("Ahora se activa el clasificador de: ")

    if grupo_pred == "grupo0":
        print("CAPA 2: es del grupo0, no pertenece a ningún esquema argumentativo")
        scheme_pred = "grupo0"
    else:
            if grupo_pred == "grupo1":
                print("CAPA 2: Clasificador GRUPO1")                
                modelo_rel_path = r'ClasificadorCAPA2\rasaBotGrupo1\models\nlu-20240322-115051-flat-lens.tar.gz'
                modelo_abs_path = os.path.join(current_dir, modelo_rel_path)
                mdl_CAPA2 = Model(modelo_rel_path)
            elif grupo_pred == "grupo2":
                print("CAPA 2: Clasificador GRUPO2")
                modelo_rel_path = r'ClasificadorCAPA2\rasaBotGrupo2\models\nlu-20240413-110103-burning-literal.tar.gz'
                modelo_abs_path = os.path.join(current_dir, modelo_rel_path)
                mdl_CAPA2 = Model(modelo_rel_path)
            elif grupo_pred == "grupo3":
                print("CAPA 2: Clasificador GRUPO3")
                modelo_rel_path = r'ClasificadorCAPA2\rasaBotGrupo3\models\nlu-20240413-124421-camel-cliff.tar.gz'
                modelo_abs_path = os.path.join(current_dir, modelo_rel_path)
                mdl_CAPA2 = Model(modelo_rel_path)
                
            output_json = mdl_CAPA2.message(phrase)
            output_dict = json.loads(output_json)
            scheme_pred = output_dict['intent']['name']
          
            print("Dada la frase: ", output_dict['text'])
            print("El clasificador de la CAPA2 ha predicho que su esquema argumentativo es: ", scheme_pred)
            print("con una confianza de ", output_dict['intent']['confidence'])

    return scheme_pred


