FROM python:3.12-slim

ENV OLLAMA_HOST=http://host.docker.internal:11434

RUN apt-get update

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY chroma.db/ chroma.db
COPY backend.py backend.py

EXPOSE 8000

CMD ["fastapi", "run", "backend.py", "--port", "8000"]

