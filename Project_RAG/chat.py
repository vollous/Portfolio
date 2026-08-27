import requests

class Chat:
    def __init__(self, name:str, rag:bool):
        self.name = name
        self.rag = rag
        self.history = []

    def chat(self, message):
        print("Entering chat API call")
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": 2})
        return "2"
        r = requests.post(
                "http://127.0.0.1:8000/chat/",
                json={"question": message},
                timeout=300,     
            )
        
        r.raise_for_status()
        data = r.json()
        response = data["response"]["message"]["content"]
        self.history.append({"role": "assistant", "content": response})
        print(response)
        return(response)

    def clear_chat(self):
        self.history.clear()