FROM ollama/ollama:latest

ENV OLLAMA_HOST=0.0.0.0:11434 \
    OLLAMA_MODELS=/models \
    OLLAMA_KEEP_ALIVE=-1 \
    OLLAMA_NUM_PARALLEL=2

RUN mkdir -p /models

# Source - https://stackoverflow.com/a/78818696
# Posted by Gustavo Corrêia
# Retrieved 2026-09-02, License - CC BY-SA 4.0

RUN ollama serve & sleep 5 && ollama pull ibm/granite4:350m

ENTRYPOINT ["/bin/ollama"]
CMD ["serve"]
