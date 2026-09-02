FROM python:3.12-slim

RUN apt-get update

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY chat.py chat.py
COPY streamlit_app.py streamlit_app.py


CMD ["streamlit", "run", "--server.port", "8080"]

