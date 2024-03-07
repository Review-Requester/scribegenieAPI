import os
import json
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv


logger = logging.getLogger(__name__)
load_dotenv()


class OpenAIOperation:

    # BASE_MODEL_FILE = "file-BvXCucNfZ6gsg4qr4MwaK5cH"
    # BASE_MODEL = "ft:gpt-3.5-turbo-1106:newgate-software-inc:customer-ai-model:8ngwFYGQ"
    BASE_MODEL_FILE = "file-xZRv79vGvlK5S7U0cn03piXR"
    BASE_MODEL = "ft:gpt-3.5-turbo-1106:newgate-software-inc:customer-ai-model:8sSTTY5U"
    
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


    def generate_gpt_response(self, system_prompt=None, user_prompt=None, payload=False, is_only_msg=False):
        try:
            if system_prompt and user_prompt:
                payload = json.dumps({
                    "model": self.BASE_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                })
            
            if not payload:
                return False, False

            response = requests.request("POST", self.COMPLETION_URL, headers=self.headers, data=payload)
            response_data = response.json()

            if response.status_code == 200:
                assistant_message = response_data['choices'][0]['message']['content'] if is_only_msg else response_data
                return True, assistant_message
            else:
                return False, response_data
        except Exception as e:
            logger.error(f'\n------------- ERROR (generate gpt response) -------------\n{datetime.now()}\n{str(e)}\n--------------------------------------------------------------\n')
            return False, False

        
    def generate_scribe_simple_response(self, user_message):
        atleast_one_proceed = False
        current_directory = os.path.dirname(os.path.realpath(__file__))
        system_prompt_file = os.path.join(current_directory, "system_prompt/system_prompt.json")

        if not os.path.isfile(system_prompt_file):
            return False, {'status': 'error', 'message': 'System prompt file not found.'}, atleast_one_proceed

        scribe_simple_data = []

        try:
            with open(system_prompt_file, 'r') as file:
                prompts_data_list = json.load(file)

                for prompt_data in prompts_data_list:
                    # Get system prompt data
                    title = prompt_data.get("title", None)
                    system_prompt = prompt_data.get("system_prompt", None)
                    gpt_status, gpt_response = self.generate_gpt_response(system_prompt=system_prompt, user_prompt=user_message, is_only_msg=True)

                    # Validate gpt response
                    if not gpt_status:
                        gpt_response = "We’re sorry, something has gone wrong. Please try later."
                        # return False, {'status': 'error', 'message': f'Something went wrong. Do not generate response for {title}. Try again in a while..!'}, atleast_one_proceed
                    else:
                        atleast_one_proceed = True

                    # Create GPT response JSON to store in firebase
                    gpt_data = {
                        "title": title,
                        "body_text": gpt_response,
                    }

                    scribe_simple_data.append(gpt_data)
            
            if not scribe_simple_data:
                return False, {'status': 'error', 'message': 'No data generated for system prompts.'}, atleast_one_proceed

            return True, scribe_simple_data, atleast_one_proceed

        except Exception as e:
            logger.error(f'\n----------- ERROR (generate scribe simple response) -----------\n{datetime.now()}\n{str(e)}\n--------------------------------------------------------------\n')
            return False, {'status': 'error', 'message': f'Error loading system prompts: {str(e)}'}, False