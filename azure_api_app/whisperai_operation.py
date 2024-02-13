import os
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class WhisperAIOperation:
    
    def __init__(self):
        OPENAI_KEY = os.environ.get('OPENAI_KEY')
        self.client = OpenAI(api_key=OPENAI_KEY)

    
    def generate_transcription(self, audio_file_path):
        try:
            audio_file = open(audio_file_path, "rb")
            
            transcript = self.client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                response_format='verbose_json',
                                language='en',
                                temperature=0.3,
                                prompt='correct all pronunciation, grammar, and spelling mistakes.'
                            )
            if transcript:
                # return transcript.text
                return transcript.segments
            return False
        except Exception as e:
            logger.error('\n--------------------- ERROR (whisper ai) ---------------------\n' + str(e) + '\n--------------------------------------------------------------\n')
            return False
    

