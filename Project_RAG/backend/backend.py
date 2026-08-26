import fastapi
import os
import signal
from ollama import Client, AsyncClient
from pydantic import BaseModel
class Query(BaseModel):
    question: str

app = fastapi.FastAPI()

@app.post("/chat/")
async def chat(query: Query):
  message = {'role': 'user', 'content': query.question}
  response = Client().chat(model='qwen3:4b', messages=[message])
  return {"response": response}

@app.post("/shutdown")
async def shutdown():
    os.kill(os.getpid(), signal.SIGTERM)
    return fastapi.Response(status_code=200, content='Server shutting down...')
