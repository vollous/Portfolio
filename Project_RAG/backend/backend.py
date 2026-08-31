import fastapi
import os
import signal
from ollama import Client, AsyncClient
from pydantic import BaseModel
class Query(BaseModel):
    messages: list = []
    rag: str

app = fastapi.FastAPI()
client = AsyncClient()

@app.post("/chat/")
async def chat(query: Query):
  rag = query.rag == "True"
  print("Complete query:", query.messages)
  response = await client.chat(model='qwen3:1.7b', messages=query.messages)
  return {"response": response}

@app.post("/shutdown")
async def shutdown():
    os.kill(os.getpid(), signal.SIGTERM)
    return fastapi.Response(status_code=200, content='Server shutting down...')
