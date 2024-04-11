from llama_index.core.llms import ChatMessage
from llama_index.llms.ollama import Ollama
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.embeddings.ollama import OllamaEmbedding
import gradio as gr
from time import sleep

Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text",
    base_url="http://localhost:11434",
)
documents = []
# Initialize your LLM
Settings.llm = llm = Ollama(model="llama2", request_timeout=30.0)
documents.append(Document(text="You are a AI assistant named JYLA and you respond in a formal manner without using emojis. Answer from your pretrained knowledge.  If you don't know the answer respond with \'I'm not sure, can you provide clarification?\'"))

index = VectorStoreIndex.from_documents(documents)


memory = ChatMemoryBuffer.from_defaults(token_limit=4000)

chat_engine = index.as_chat_engine(
    chat_mode="context",
    memory=memory,
    system_prompt=(
        "You are a AI assistant named JYLA and you respond in a formal manner without using emojis. Answer from your pretrained knowledge.  If you don't know the answer respond with \'I'm not sure, can you provide clarification?\'"
    ),
)

def generate_response (msg, history):
    response = str(chat_engine.chat(msg))
    message = ""
    for token in response:
        sleep(0.01)
        message += token
        yield message

chatbot = gr.ChatInterface(
                generate_response,
                chatbot=gr.Chatbot([[None, "Welcome Friend! What is on your mind?"]], avatar_images=["img/jyla-user-image.png", "img/jyla-chatbot.png"],height=550),
                title="JYLA (Just Your Lazy AI)",
                description="Feel free to ask any question.",
                submit_btn="Send",
                clear_btn="Clear Chat",
                undo_btn=None,
                retry_btn=None
)

chatbot.launch()