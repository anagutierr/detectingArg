import json
from serpapi import GoogleSearch
from serpapi import BingSearch
import wikipedia
import concurrent.futures
import time

# Variable global api_key para la API de SERPAPI (usada en las búsquedas de GoogleSearch y Bing)
api_key = "" # Añadir aquí la API key de SERPAPI
# Endpoint de la API al modelo
model = "" # Añadir aquí el endpoint del modelo 


################### FUNCIONES AUXILIARES CONEXIÓN A APIS DE FUENTES DE INFORMACIÓN #################################################################################################################

# Función que obtiene el contexto de todas las "critical questions" y sus respectivas urls de búsqueda usando GoogleSearch
def retrieval_GS(dict_cq):
    urls = []
    dict_contextGS = {"CQ1":"", "CQ2": "", "CQ3": ""}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_cq = {executor.submit(search_GS, cq): num for num, cq in dict_cq.items()}        
        for future in concurrent.futures.as_completed(future_to_cq):
            num = future_to_cq[future]
            try:
                snippets, links = future.result()
                dict_contextGS[num] = snippets
                urls.extend(links)
            except Exception as exc:
                print(f'Error en la consulta {num}: {exc}')
    return dict_contextGS, urls

# Función que lanza una búsqueda en GoogleSearch, guardándose los resultados obtenidos y sus urls
def search_GS(cq):
    ini = time.time()
    params = {
        "q": cq,
        "location": "Austin, Texas, United States",
        "hl": "en",
        "gl": "us",
        "num": 1,
        "google_domain": "google.com",
        #"api_key": api_key
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    snippets = []
    urls = []
    for result in results.get("organic_results", []):
        if "snippet" in result:
            snippet = result["snippet"]
            snippets.append(snippet)
            if "link" in result:
                link = result["link"]
                urls.append(link)
    if not snippets:
        snippets = "No context found"
    fin = time.time()
    print("CQ GS: ", fin - ini)
    return snippets, urls

# Función que obtiene el contexto de todas las "critical questions" y sus respectivas urls de búsqueda usando Bing
def retrieval_BING(dict_cq):
    urls = []
    dict_contextBING = {"CQ1": "", "CQ2": "", "CQ3": ""}
    uule_austin_texas = "w+CAIQICIbQXVzdGluLCBUZXhhcywgVW5pdGVkIFN0YXRlcw"
    
    with concurrent.futures.ThreadPoolExecutor()as executor:
        future_to_cq = {executor.submit(search_BING, cq, uule_austin_texas): num for num, cq in dict_cq.items()}
        
        for future in concurrent.futures.as_completed(future_to_cq):
            num = future_to_cq[future]
            try:
                snippets, links = future.result()
                dict_contextBING[num] = snippets
                urls.extend(links)
            except Exception as exc:
                print(f'Error en la consulta {num}: {exc}')
    
    return dict_contextBING, urls

# Función que lanza una búsqueda en Bing, guardándose los resultados obtenidos y sus urls
def search_BING(cq, uule_austin_texas):
    ini = time.time()
    params = {
        "q": cq,
        "uule": uule_austin_texas,
        'count': 1,  
        #"api_key": api_key
    }    
    search = BingSearch(params)
    results = search.get_dict()
    snippets = []
    urls = []    
    for result in results.get("organic_results", []):
        if "snippet" in result:
            snippet = result["snippet"]
            snippets.append(snippet)
            if "link" in result:
                link = result["link"]
                urls.append(link)
    if not snippets:
        snippets = "No context found"    
    fin = time.time()
    print("CQ BING: ", fin-ini)
    return snippets, urls

# Función que obtiene el contexto de todas las "critical questions" y sus respectivas urls de búsqueda usando Wikipedia
def retrieval_WIKI(dict_cq):
    urls = []
    dict_contextWIKI = {"CQ1": [], "CQ2": [], "CQ3": []}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_cq = {executor.submit(search_WIKI, cq): num for num, cq in dict_cq.items()}        
        for future in concurrent.futures.as_completed(future_to_cq):
            num = future_to_cq[future]
            try:
                summaries, page_urls = future.result()
                dict_contextWIKI[num] = summaries
                urls.extend(page_urls)
            except Exception as exc:
                print(f'Error en la consulta {num}: {exc}')
    return dict_contextWIKI, urls

# Función que lanza una búsqueda en Bing, guardándose los resultados obtenidos y sus urls
def search_WIKI(cq):
    summaries = []
    page_urls = []
    ini = time.time()
    try:
        titles = wikipedia.search(cq, results=1)
        for page in titles:
            try:
                summary = wikipedia.summary(page, sentences=1)
                summaries.append(summary)
                page_urls.append(wikipedia.page(page).url)
            except wikipedia.PageError as e:
                print(f"Skipping {page} due to PageError: {e}")
    except wikipedia.DisambiguationError as e:
        print(f"Skipping {cq} due to DisambiguationError: {e.options}")
        # Por ejemplo, seleccionar el primer resultado:
        first_option = e.options[0]
        try:
            summary = wikipedia.summary(first_option, sentences=1)
            summaries.append(summary)
            page_urls.append(wikipedia.page(first_option).url)
        except wikipedia.PageError as pe:
            print(f"Skipping {first_option} due to PageError: {pe}")
    # Comprobamos que esté en un formato correcto:
    if not summaries:
        summaries = ["No context found"]
    fin = time.time()
    print("CQ WIKI: ", fin-ini)
    return summaries, page_urls



################### FUNCIONES AUXILIARES CONEXIÓN A LA API DE LLAMA #################################################################################################################

# Función que a través de una petición a LLAMA obtiene las "critical questions" en formato JSON personalizadas para la frase y el esquema de entrada
def get_cq(client, phrase, scheme):
    completion = client.chat.completions.create(model=model, messages=[{"role": "system", "content": "You will be given the definition of an argumentive scheme with its default critical questions and a phrase that matches that scheme. Reformulate the exact critical questions of the scheme using the information of the phrase and give me your answer directly."},
                                                                                { "role": "user", "content": f"This is the argumentative scheme with its critical questions: {scheme}"},
                                                                                { "role": "user", "content": f"This is the phrase: {phrase}"},
                                                                                {"role": "user",  "content": "You will have to follow this json output: {\"CQ1\": \"The first critical question\", \"CQ2\": \"The second critical question\", \"CQ3\": \"The third critical question\"}"},
                                                                                { "role": "user", "content": "Now give me your output as an assistant:"}],
                                                                                response_format={ "type": "json_object" })
    output = completion.model_dump()["choices"][0]["message"]["content"]
    dict_cq = json.loads(output)
    return dict_cq

# Función que a través de una petición a LLAMA obtiene las respuestas a las "critical questions" en formato JSON basándose en los contextos obtenidos en las fuentes de información previas
def get_anstocq(client, dict_cq, dict_contextGS, dict_contextBING, dict_contextWIKI):
    completion = client.chat.completions.create(model=model, messages=[
                                                                    {"role": "system", "content": "You will have to answer the following questions in a justified way, using the information extracted as context from Google Search, Wikipedia, and Bing."},
                                                                    {"role": "system", "content": f"This is the context for each critical question from Google Search: {dict_contextGS}"},
                                                                    {"role": "system", "content": f"This is the context for each critical question from Bing: {dict_contextBING}"},
                                                                    {"role": "system", "content": f"This is the context for each critical question from Wikipedia: {dict_contextWIKI}"},
                                                                    {"role": "system", "content": f"These are the critical questions: {dict_cq}"},
                                                                    {"role": "user",  "content": "You will have to follow this json output: {\"CQ1\": \"The answer to the first critical question\", \"CQ2\": \"The answer to the second critical question\", \"CQ3\": \"The answer to the third critical question\"}"},    
                                                                    {"role": "user", "content": "Now you have all the information, so give me your output as an assistant:"}],
                                                                    response_format={ "type": "json_object" })                
    dict_ans = completion.model_dump()["choices"][0]["message"]["content"]
    return dict_ans

# Función que a través de una petición a LLAMA obtiene la justificación completa de la veracidad de una frase que pertenece a un esquema argumentativo
def get_finaleval(client, phrase, scheme, dict_cq, dict_ans):
    completion = client.chat.completions.create(model=model, messages=[{"role": "system", "content": """You will have to act like an expert assistant in argumentational computation.
                                                                                    The aim is to determine the level of veracity that an input phrase has. To do this there is a procedure:
                                                                                    1. The phrase is going to be classified in an argumentative scheme
                                                                                    2. Given this argumentive scheme and its default critical questions, there is an adaptation to extract the critical questions personalized with the phrase.
                                                                                    3. Then, these critical questions are answered using different sources like Google Search, Bing and Wikipedia.
                                                                                    4. Finally, given these answers it is given a score to the original phrase that represents the level of veracity."""},
                                                                              { "role": "system", "content": "You will have to present all this information to me in a justify way and do your best to answer the critical questions using the answers I'm going to give you but you can contribute to this answers if you have more information."},
                                                                              { "role": "system", "content": f"This is the phrase: {phrase}"},
                                                                              { "role": "user", "content": f"This is the argumentative scheme with its critical questions: {scheme}"},
                                                                              { "role": "system", "content": f"These are the critical questions: {dict_cq}"},
                                                                              { "role": "system", "content": f"These are the answers to the critical questions: {dict_ans}"},
                                                                              { "role": "user", "content": "Now you have all the information, so give me your output as an assistant:"}],
                                                                              )
    output = completion.model_dump()["choices"][0]["message"]["content"]
    return output

# Función que a través de una petición a LLAMA obtiene la justificación completa de la veracidad de una frase que NO pertenece a un esquema argumentativo
def get_finaleval_noscheme(client, phrase, scheme, context_GS, context_BING, context_WIKI):
    completion = client.chat.completions.create(model=model, messages=[{"role": "system", "content": """You will have to act like an expert assistant in argumentational computation.
                                                                                    The aim is to determine the level of veracity that an input phrase has. To do this there is a procedure:
                                                                                    1. The phrase is going to be classified in an argumentative scheme if it belongs to any
                                                                                    2. Some searches will be done in different sources like Google Search, Bing and Wikipedia.
                                                                                    4. Finally, given these context it will be given a score to the original phrase that represents the level of veracity."""},
                                                                              { "role": "system", "content": "You will have to present all this information to me in a justify way and do your best to determine the level of veracity of the phrase."},
                                                                              { "role": "system", "content": f"This is the phrase: {phrase}"},
                                                                              { "role": "user", "content": f"This is the argumentative scheme with its critical questions: {scheme}"},
                                                                              { "role": "system", "content": f"These is the context extracted from Google: {context_GS}"},
                                                                              { "role": "system", "content": f"These is the context extracted from Bing: {context_BING}"},
                                                                              { "role": "system", "content": f"These is the context extracted from Wikipedia: {context_WIKI}"},
                                                                              { "role": "user", "content": "Now you have all the information, so give me your output as an assistant:"}],
                                                                              )
    output = completion.model_dump()["choices"][0]["message"]["content"]
    return output

# Función que a través de una petición a LLAMA obtiene el score final del nivel de veracidad de la frase sobre 1
def get_score(client, output):
    completion = client.chat.completions.create(model=model, messages=[
                                                                    {"role": "system", "content": "You will have to act like an expert assistant in argumentational computation. "},
                                                                    {"role": "system", "content": "Starting from a justification about the level of truthfulness of a sentence, you will have to extract the truthfulness score out of 1. If the score over 1 is already provided in the justification, return that exact value; if not, calculate it based on the provided justification and reasoning."},
                                                                    {"role": "system", "content": f"This is the justification given: {output}"},
                                                                    {"role": "user",  "content": "You will have to follow this json output: {\"score\": \"The score out of 1 representing the level of veracity of the sentence\"}"},    
                                                                    {"role": "user", "content": "Now you have all the information, so give me your output as an assistant:"}],
                                                                    response_format={ "type": "json_object" })
    dict_score = completion.model_dump()["choices"][0]["message"]["content"]
    return dict_score