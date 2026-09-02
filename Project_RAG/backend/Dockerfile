FROM python:3.12-slim

ENV OLLAMA_HOST=http://host.docker.internal:11434

RUN apt-get update

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2; ONNXMiniLM_L6_V2()._download_model_if_not_exists()"

COPY chroma.db/ chroma.db
COPY backend.py backend.py

CMD ["fastapi", "run", "backend.py", "--port", "8000"]

