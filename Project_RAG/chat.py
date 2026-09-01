import requests

class Chat:
    def __init__(self, name:str, rag:bool):
        self.name = name
        self.rag = rag
        self.messages = []

    def chat(self, message):
        self.messages.append(
            {
            "role": "user",
            "content": message
            })
        r = requests.post(
                "http://127.0.0.1:8000/chat/",
                json={
                    "messages": self.messages,
                    "rag": str(self.rag) 
                    },
            )
        
        r.raise_for_status()
        data = r.json()
        response = data["response"]["message"]["content"]
        self.messages.append({"role": "assistant", "content": response})
        print(response)
        return(response)

    def clear_chat(self):
        self.messages.clear()

    