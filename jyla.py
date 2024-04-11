from llama_index.core import VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.readers.web import SimpleWebPageReader
from llama_index.core import Settings, Document
from llama_index.llms.ollama import Ollama
from duckduckgo_search import DDGS
import nltk
from nltk.tokenize import word_tokenize
import gradio as gr 
from time import sleep

nltk.download('punkt')  # Only needed the first time

Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text",
    base_url="http://localhost:11434",
)
documents = []
documents.append(Document(text="You are a AI assistant named JYLA and you respond in a formal manner without using emojis.  Answer based on the context given.  If you don't know the answer respond with \'I'm not sure, can you provide clarification?"))

# Initialize your LLM
Settings.llm = llm = Ollama(model="mistral:instruct", temperature=3, request_timeout=120.0)

# Prompt the user for their search query
urls = []
history = []
index = VectorStoreIndex.from_documents(documents)
prompt_history = ""

def tokenize(text):
    nltk.download('punkt', quiet=True)
    return word_tokenize(text)

def update_history(query, response, max_tokens=7500):
    global urls
    global history
    global prompt_history

    # Create a new history entry
    new_entry = {"query": query, "response": response}
    history.append(new_entry)
    
    # Update prompt_history and check token count
    prompt_history = "\n".join([f"Q: {item['query']} A: {item['response']}" for item in history])
    
    # Keep removing the oldest entries until the token count is under the limit
    while len(tokenize(prompt_history)+tokenize(query)) > max_tokens:
        history.pop(0)  # Remove the oldest history entry
        prompt_history = "\n".join([f"Q: {item['query']} A: {item['response']}" for item in history])
    
    return history, prompt_history

def clear_chat():
    global history, prompt_history, urls, documents, index
    history = []
    prompt_history = ""
    urls = []
    documents = []
    documents.append(Document(text="You are a AI assistant named JYLA and you respond in a formal manner without using emojis.  Answer based on the context given.  If you don't know the answer respond with \'I'm not sure, can you provide clarification?"))
    index = VectorStoreIndex.from_documents(documents)


def generate_response(query,gr_history):
    global urls
    global history
    global documents
    global prompt_history
    global index

    generate_search = f"Can you create a duckduckgo search query for the following question? Respond with the search query and no other words.\nContext: {prompt_history}\nQuery: {query}"
    response = llm.complete(generate_search)
    #print(response)
    #links = DDGS().text(str(response).strip("\n").strip('\"').strip("\'"), max_results=2)
    try:
        links = DDGS().text("{}".format(str(response).strip('\"')), max_results=2)
        for url in links:
            #print(url['href'])
            urls.append(url['href'])
    except:
        pass
    
    documents = SimpleWebPageReader(html_to_text=True).load_data(urls)

    for doc in documents:
        index.insert(doc)
    index.refresh_ref_docs(documents)

    # set Logging to DEBUG for more detailed outputs
    query_engine = index.as_query_engine()

    #prompt = f"Context: {prompt_history}\n\n\nCurrent Question:\n{query}"
    response = query_engine.query(query)
    history, prompt_history = update_history(query, response)
    if not urls:
        final_response = "{}\n".format(response)
    else:
        final_response = "{}\n\nUseful Resources: \n{}".format(response, '\n'.join(urls))
    urls.clear()
    documents.clear()
    message = ""
    for token in final_response:
        sleep(0.01)
        message += token
        yield message


chatbot = gr.ChatInterface(
                generate_response,
                chatbot=gr.Chatbot([[None, "Welcome Friend! What is on your mind?"]], avatar_images=["img/jyla-user-image.png", "img/jyla-chatbot.png"],height=550),
                title="JYLA (Just Your Lazy AI)",
                description="Feel free to ask any question.",
                submit_btn="Send",
                clear_btn="Clear Screen",
                undo_btn=None,
                retry_btn=None,
)
chatbot.launch()