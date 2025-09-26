import streamlit as st
import json
from openai import OpenAI
import openai
import time
import modul1
import modul2
import concurrent.futures


################### VARIABLES DE SESIÓN #################################################################################################################

st.session_state["context_GS"] = None
st.session_state["context_BING"] = None
st.session_state["context_WIKI"]  = None
st.session_state["urls_GS"] = None
st.session_state["urls_BING"] = None
st.session_state["urls_WIKI"]  = None
st.session_state["urls"] = None
st.session_state["phrase"]=None
st.session_state["scheme"]=None
st.session_state["cq"]=None
st.session_state["ans_cq"]=None
st.session_state["output"] = None
st.session_state["score"] = None



################### FUNCIONES AUXILIARES #################################################################################################################

# Función para reiniciar las variables del sistema
def load_new_state():
    st.session_state["context_GS"] = None
    st.session_state["context_BING"] = None
    st.session_state["context_WIKI"]  = None
    st.session_state["urls_GS"] = None
    st.session_state["urls_BING"] = None
    st.session_state["urls_WIKI"]  = None
    st.session_state["urls"] = None

    st.session_state["phrase"]=None
    st.session_state["scheme"]=None
    st.session_state["cq"]=None
    st.session_state["ans_cq"]=None
    st.session_state["output"] = None
    st.session_state["score"] = None


# Función que activa el MÓDULO 1: Iniciamos el sistema clasificador para obtener el esquema argumentativo al que pertenece la frase de entrada
def action_button1():
    scheme_pred = modul1.classification(st.session_state.phrase)

    # Accedemos al json donde está la información de cada esquema y extraemos los datos del esquema predicho
    with open("schemes.json", "r") as archivo_json:
        esquemas_dict = json.load(archivo_json)
    scheme = esquemas_dict[scheme_pred]
    st.session_state["scheme"] = scheme

    #Formatemos el scheme
    scheme = scheme.replace("\\", "\n")
    scheme_format = scheme.splitlines()
    scheme_name = scheme_format[0]

    scheme_name = f"<strong>{scheme_name[:-1]}:</strong>"
    scheme_content = "\n".join([f"<p>\t{line}</p>" for line in scheme_format[1:]])

    # Crear un bloque de texto con fondo coloreado
    #with container_mod1:
    with container_mod1:
        cont_container_mod1 = f"""<div style='background-color: #FFCF96; padding: 20px; border-radius: 5px; border: 2px solid salmon;'>
                <p>{scheme_name}</p>
                <p>{scheme_content}</p>
            </div>"""
        st.session_state["cont_container_mod1"] = cont_container_mod1
        container_mod1.markdown(cont_container_mod1, unsafe_allow_html=True)

#Función general para buscar contexto en varias fuentes dependiendo del tipo de workflow
def search_context(search_function, workflow, search=None):
    print(f"Calculating {search_function.__name__}")
    ini_time = time.time()
    context, urls = search_function(workflow, search)
    fin_time = time.time()
    print(f"Total time for {search_function.__name__}: {fin_time - ini_time}")
    return context, urls

#Función que busca contexto dependiendo del tipo de workflow en GoogleSearch
def search_GS(workflow, search=None):
    if workflow == "noscheme":
        return modul2.search_GS(search)
    else:
        print(search)
        return modul2.retrieval_GS(search)
    
#Función que busca contexto dependiendo del tipo de workflow en Bing
def search_BING(workflow, search=None):
    if workflow == "noscheme":
        return modul2.search_BING(search, "w+CAIQICIbQXVzdGluLCBUZXhhcywgVW5pdGVkIFN0YXRlcw")
    else:
        return modul2.retrieval_BING(search)

#Función que busca contexto dependiendo del tipo de workflow en Wikipedia
def search_WIKI(workflow, search=None):
    if workflow == "noscheme":
        return modul2.search_WIKI(search)
    else:
        return modul2.retrieval_WIKI(search)
   
# Función que obtiene el contexto deseado en varias fuentes de información según el workflow establecido
def perform_context_search(workflow, search=None):    
    ini_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        if st.session_state.context_GS is None:
            future_GS = executor.submit(search_GS, workflow, search)

        if st.session_state.context_BING is None:
            future_BING = executor.submit(search_BING, workflow, search)

        if st.session_state.context_WIKI is None:
            future_WIKI = executor.submit(search_WIKI, workflow, search)

        # Esperar a que todas las búsquedas se completen
        if st.session_state.context_GS is None:
            st.session_state["context_GS"], st.session_state["urls_GS"] = future_GS.result()
            print("CONTEXTO GOOGLE SEARCH: ", st.session_state.context_GS )
            print("URLS GOOGLE SEARCH: ", st.session_state.urls_GS)

        if st.session_state.context_BING is None:
            st.session_state["context_BING"], st.session_state["urls_BING"] = future_BING.result()
            print("CONTEXTO BING ", st.session_state.context_BING)
            print("URLS BING: ", st.session_state.urls_BING)

        if st.session_state.context_WIKI is None:
            st.session_state["context_WIKI"], st.session_state["urls_WIKI"] = future_WIKI.result()
            print("CONTEXTO WIKIPEDIA: ", st.session_state.context_WIKI)
            print("URLS WIKIPEDIA: ", st.session_state.urls_WIKI)
    
    if st.session_state.urls is None:
        st.session_state["urls"] = list(set(st.session_state.urls_GS + st.session_state.urls_BING + st.session_state.urls_WIKI))
    fin_time = time.time()
    print("Total time for performing context search: ", fin_time - ini_time)



# Función MÓDULO 2: obtención de las sucesivas respuestas del chatbot de LLAMA dependiendo de si la frase pertenece a un esquema argumentativo
def chatbot_response():
    client = OpenAI(
                    base_url="",  #Añadir aquí la url de Ollama
                    api_key="")    #Añadir aquí la API key de Ollama
    frase = st.session_state.phrase

    #WORKFLOW ESPECÍFICO
    if st.session_state.scheme == "This argument does not belong to any specific argumentative schemee": 
        #FASE 1: Recuperamos información de diferentes fuentes como contexto a la frase directamente presentada
        workflow = "noscheme"
        perform_context_search(workflow, frase)

        #FASE 2: Obtenemos la evaluación de la veracidad y justificación final de LLAMA
        if st.session_state.output is None:
            st.session_state["output"] = modul2.get_finaleval_noscheme(client, st.session_state.phrase, st.session_state.scheme, st.session_state.context_GS, st.session_state.context_BING, st.session_state.context_WIKI)
            print("RESPUESTA COMPLETA DE LLAMA", st.session_state.output)
        
        #FASE 3: Obtenemos en un json el score sobre 1
        if st.session_state.score is None:
            st.session_state["score"] = modul2.get_score(client, st.session_state.output)

    
    #WORKFLOW GENERAL
    else: 
        #FASE 1: Obtenemos las cuestiones críticas
        if st.session_state.cq is None:
            st.session_state["cq"] = modul2.get_cq(client, st.session_state.phrase, st.session_state.scheme)
            print("CUESTIONES CRÍTICAS: ", st.session_state.cq)
        
        #FASE 2: Recuperamos información de diferentes fuentes como contexto a las cuestiones críticas
        workflow = "scheme"
        perform_context_search(workflow, st.session_state.cq)
    
        #FASE 3: Obtenemos las respuestas a las cuestiones críticas dado el contexto anterior
        if st.session_state.ans_cq is None:
            st.session_state["ans_cq"] = modul2.get_anstocq(client, st.session_state.cq, st.session_state.context_GS, st.session_state.context_BING, st.session_state.context_WIKI)
            print("RESPUESTAS A LAS CUESTIONES CRÍTICAS: ", st.session_state.ans_cq)

        #FASE 4: Obtenemos la evaluación de la veracidad y justificación final de LLAMA
        if st.session_state.output is None:
            st.session_state["output"] = modul2.get_finaleval(client, st.session_state.phrase, st.session_state.scheme, st.session_state.cq, st.session_state.ans_cq)
            print("RESPUESTA COMPLETA DE LLAMA", st.session_state.output)

        #FASE 5: Obtenemos en un json el score sobre 1
        if st.session_state.score is None:
            st.session_state["score"] = modul2.get_score(client, st.session_state.output)

    return st.session_state.output, st.session_state.score


# Función que activa el MÓDULO 2: Iniciamos el sistema generador de LLAMA para obtener el score de veracidad y la justificación del chatbot 
def action_button2(): 
    while True:
        try:
            bot_response, score = chatbot_response()
            break  # Salir del bucle si no hay error
        except openai.BadRequestError as e:
            print("Se ha producido un error:", e)
            print("Volviendo a intentar...")
            
    score = json.loads(score)
    
    # JUSTIFICACIÓN CHAT
    # Escribir el mensaje del chatbot
    messages = st.container(height=900) 
    messages.chat_message("assistant").write(f"{bot_response}")

    # SCORE VISUAL
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("")
        st.write('<p style="font-size:18px; font-weight:bold;">📊 Veracity Score:</p>', unsafe_allow_html=True)
        score = score["score"]
        st.progress(score)         
    with col2:           
        if score >= 0.7:
            color = 'green'
            emoji = '✅'
        elif score >= 0.4:
            color = 'orange'
            emoji = '⚠️'
        else:
            color = 'red'
            emoji = '❌'
        st.write("")
        st.write("")
        st.markdown(f'<p style="text-align: center; color:{color}; font-size:30px; font-weight:bold;">\t{score} <span style="color:black; font-weight:bold; font-size:20px">/1 {emoji}</span></p>', unsafe_allow_html=True)
        
    # URLS USADAS COMO CONTEXTO
    cont_container_mod2 = f"""<div style='background-color:#FFCF96; border-radius: 5px; border: 2px solid salmon; padding: 20px'>                            
                            <p style="font-size:18px; font-weight:bold;"> 🔗 Links to Used Sources:</p>
                            <ul>"""
    for url in st.session_state.urls:
        cont_container_mod2 += f"<li><a href='{url}' target='_blank'>{url}</a></li>"

    cont_container_mod2 += "</ul></div>"
    container_mod2 = st.container()
    container_mod2.markdown(cont_container_mod2, unsafe_allow_html=True) 


    

################### CONTENIDO DE LA WEB #################################################################################################################

# Estilo personalizado para el fondo
background_style = """
        <style>
            .stApp {
                background: linear-gradient(to bottom, rgb(205, 250, 219), rgba(255, 255, 255, 0.9)); /* Gradiente de azul a blanco con transparencia */
            }
        </style>
    """
st.markdown(background_style, unsafe_allow_html=True)

# Título
st.markdown("<h1 style='text-align: center;'>🌍 Detecting Disinformation 🔍</h1>", unsafe_allow_html=True)
st.write("")
# Subtítulo
st.markdown("""
        <strong> Have you ever wondered if what you're reading online is really true? </strong>🤔
        With so many news and opinions circulating on the internet, it can be difficult to discern between <strong>truth and disinformation</strong>.
""", unsafe_allow_html=True)
# Descripción e imagen
col1, col2 = st.columns([2, 2])
with col1:
    st.markdown("""            
                
        This disinformation detection system is here to assist you with that task. It focuses on detecting potential fallacies that could lead to deception and the spread of disinformation.
        It uses a system that analyzes the reasoning pattern or argumentative scheme of each sentence you present to it.
        Then, it delves deeper with critical questions to determine the truthfulness of the content.

        So, come on! 🎉 <strong>Try our chatbot specialized in computational argumentation!</strong> 💻
    
    """, unsafe_allow_html=True)
with col2:
    imagen_path = "images/hero2.png"
    st.image(imagen_path, width=450)
st.write("---")

# Contenedor explicación del funcionamiento
container_mod1 = None
cont_container_mod1 = None
with st.container():
  st.header("💡 How it works?")
  st.markdown("""Provide the sentence you want to evaluate. 💬
              Our system will classify it into an argumentative scheme based on its structure, and once classified, our chatbot will respond with a justified assessment of its truthfulness.""")
  
  # Área de entrada de texto para el usuario
  label = "Write the argument to be analyzed:"
  phrase = st.text_area(label, height=150)
    
  # Estilo personalizado para el botón
  button_style = """
        <style>
            .stButton>button {
                background-color: #fceb68; /* Cambia el color de fondo */
                color: black; /* Cambia el color del texto */
            }
        </style>
    """
  st.markdown(button_style, unsafe_allow_html=True)
  if st.button("Send"):
        # Reiniciar las variables de estado a None
        load_new_state()

        st.session_state["phrase"] = phrase
        container_mod1 = st.container()        
        with st.spinner('Classifying the sentence...'):
            ini_mod1 = time.time()
            action_button1()
            fin_mod1 = time.time()
            tiempo_mod1 = fin_mod1-ini_mod1
            print("Tiempo MÓDULO 1: ", tiempo_mod1)
 
        bot_response = None
        tiempo_mod2=None
        st.write("")
        with st.spinner('Thinking response...'):
                ini_mod2 = time.time()
                action_button2()
                fin_mod2 = time.time()
                tiempo_mod2 = fin_mod2-ini_mod2
                print("Tiempo MÓDULO 2: ", tiempo_mod2)