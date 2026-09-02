import fastapi
import os
import signal
from ollama import Client, AsyncClient
from pydantic import BaseModel
import chromadb

chroma_client = chromadb.PersistentClient("chroma.db")
collection = chroma_client.get_or_create_collection(name="numpy_docs")
class Query(BaseModel):
    messages: list = []
    rag: str

app = fastapi.FastAPI()
client = AsyncClient(host=os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434"))
def get_context(message, n_results=10):
  results = collection.query(query_texts=[message], n_results=n_results)
  return results

@app.post("/chat/")
async def chat(query: Query):
  rag = query.rag == "True"
  
  context = []
  if rag and len(query.messages) == 1:
     context = get_context(query.messages[0]["content"])
     context = "\n\n<->\n\n".join(context['documents'][0])
     query.messages.insert(0,
                           {"role": "system", "content": f"""Answer this questions using only this context.
                           {context}
                           If the answer is not in this context say:' The answer is not in this context.' and do not answer any further.
                           Only use examples from the context"""})
 
  response = await client.chat(
     model='ibm/granite4:350m',
     messages=query.messages,
     think=False,
     options={
        "num_ctx": 32768,         
        "temperature": 0.2,         
        "top_p": 0.8,
        "repeat_penalty": 1.05,
    },)            
  query.messages.append({"role": "assistant", "content": response["message"]["content"]}) 
  return {"messages": query.messages}

@app.post("/shutdown")
async def shutdown():
    os.kill(os.getpid(), signal.SIGTERM)
    return fastapi.Response(status_code=200, content='Server shutting down...')
