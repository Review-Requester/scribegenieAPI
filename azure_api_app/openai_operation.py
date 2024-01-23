import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class OpenAIOperation:

    BASE_MODEL_FILE = "file-DllSkQR8i9MYQCg77H6JS8wE"
    BASE_MODEL = "ft:gpt-3.5-turbo-1106:urbahealth-llc:one-tune-def:8egMtqnt"
    
    # Open ai APIs
    COMPLETION_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self):
        OPENAI_KEY = os.environ.get('OPENAI_KEY')
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {OPENAI_KEY}',
        }
        self.headers = headers


    def generate_gpt_response(self, system_prompt, user_prompt):
        try:
            payload = json.dumps({
                "model": self.BASE_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
            })

            response = requests.request("POST", self.COMPLETION_URL, headers=self.headers, data=payload)
            response_data = response.json()

            if response.status_code == 200:
                assistant_message = response_data['choices'][0]['message']['content']
                return True, assistant_message
            else:
                return False, response_data
        except:
            return False, False

        
