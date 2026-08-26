#!/bin/bash

rm -f /tmp/ready

ollama serve &

# start ollama, wait for it to serve
echo "Starting Ollama..."
until curl -s http://localhost:11434 >/dev/null; do
  sleep 1
done

# all the models to install
MODELS="deepseek-r1:1.5b"

# pull and install models, or skip if they're present
for MODEL in $MODELS; do
  if ! ollama list | grep -q "$MODEL"; then
    echo "⚡️ Pulling model: $MODEL"
    ollama pull "$MODEL"
  else
    echo "⛳️ Model '$MODEL' already present."
  fi
done

# set container as ready
touch /tmp/ready

# start nginx
nginx -g "daemon off;"
