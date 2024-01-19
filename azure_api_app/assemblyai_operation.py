import os
import json
import requests
from dotenv import load_dotenv

# From utils
from azure_api_app.utils import handle_exceptions

load_dotenv()


class AssemblyAIOperation:

    BASE_URL = "https://api.assemblyai.com/v2"
    UPLOAD_URL = f"{BASE_URL}/upload"
    TRANSCRIPT_URL = f"{BASE_URL}/transcript"

    def __init__(self):
        ASSEMBLY_AI_TOKEN = os.environ.get('ASSEMBLY_AI_TOKEN')
        headers = {
            "authorization": ASSEMBLY_AI_TOKEN,
            "Content-Type": "application/json"
        }
        self.headers = headers


    @handle_exceptions(is_status=True)
    def upload_file(self, file_path):
        audio_file = open(file_path, "rb") 
    
        response = requests.post(self.UPLOAD_URL, headers=self.headers, data=audio_file)

        response_data = False
        if response.status_code == 200:
            response_data = response.json()
        return response_data
    

    @handle_exceptions(is_status=True)
    def transcribe_file(self, upload_url):
        data = {
            "audio_url": upload_url, 
            "language_code": "en_us",
            "disfluencies": True,
            "speaker_labels": True,
            "punctuate": True,
        }

        transcript_response = requests.post(self.TRANSCRIPT_URL, json=data, headers=self.headers)

        response_data = False
        if transcript_response.status_code == 200:
            response_data = transcript_response.json()
        return response_data
    

    def polling_transcript(self, transcript_id):
        try:
            polling_url = f"{self.TRANSCRIPT_URL}/{transcript_id}"

            transcription_response = requests.get(polling_url, headers=self.headers)

            transcription_result = transcription_response.json()
            return transcription_result
        except Exception as e:
            return {'status': 'error', 'error': str(e)}