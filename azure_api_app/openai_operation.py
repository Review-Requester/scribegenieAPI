import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class OpenAIOperation:

    BASE_MODEL_FILE = "file-DllSkQR8i9MYQCg77H6JS8wE"
    BASE_MODEL = "ft:gpt-3.5-turbo-1106:urbahealth-llc:one-tune-def:8egMtqnt"
    SYSTEM_PROMPT = """You are a healthcare professional and you will be given a transcript of a conversation between a doctor and a patient.
                        Your task is to create medical notes for the categories: Subjective, Objective, and Assessment & Plan, adhering to a specific writing
                        style.\n\nWriting Style: The medical note should be written in a formal, clear, and much more informative. It is written in a 
                        professional tone, using medical terminology and jargon. The note is organized into three sections: subjective, objective, 
                        and assessment & plan. \n\nIn the subjective section, the patient's symptoms and complaints are described in detail, 
                        including the onset, duration, severity, and triggers of the symptoms. The patient's own words are used to describe the 
                        symptoms, and the information is presented in a logical and chronological order.\n\nThe objective section is missing in 
                        this note, which would typically include the findings from the physical examination and any relevant test results.\n\nIn the 
                        assessment & plan section, the possible diagnoses are listed based on the patient's symptoms and history. For each potential 
                        diagnosis, a plan of action is outlined, including diagnostic tests, treatments, and patient education. The plans are specific, 
                        actionable, and tailored to the patient's individual needs. \n\nOverall, the writing style is objective and focused, providing a 
                        comprehensive and coherent summary of the patient's condition and care plan.\n\nIf you are unable to find the necessary information 
                        for a particular categories, please WIRITE \"UNABLE TO FIND THESE DETAILS\" INSTEAD.\n\n#Please provide your response in JSON format, 
                        with corresponding name keys for each category."""
    
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


    def generate_gpt_response(self, user_prompt):
        try:
            payload = json.dumps({
                "model": self.BASE_MODEL,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
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

        
