import os
import json
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv


logger = logging.getLogger(__name__)
load_dotenv()


class OpenAIOperation:

    BASE_MODEL_FILE = "file-soeaA8uJsLhEN375RvNAbyOT"
    BASE_MODEL = "ft:gpt-3.5-turbo-1106:newgate-software-inc:scribe-ai-model:90MgF1zN"
    
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


    def generate_gpt_response(self, system_prompt=None, user_prompt=None, payload=False, is_only_msg=False, is_json_res=False):
        try:
            if system_prompt and user_prompt:
                payload_json = {
                    "model": self.BASE_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                }

                if is_json_res:
                    payload_json["response_format"] = { "type": "json_object" }

                payload = json.dumps(payload_json)
            
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

   
    def generate_scribe_simple_response(self, user_message, system_prompt_list):

        scribe_simple_data = []
        try:
            system_prompt_string = '### Section Definitions:\n'

            # Sections string
            system_titles = [item["title"] for item in system_prompt_list]
            title_result_string = ', '.join([f"`'{title}'`" for title in system_titles[:-1]]) + f" and `'{system_titles[-1]}'`"
            total_sections = len(system_titles)
            
            # Sections definitions string in prompt
            for index, data in enumerate(system_prompt_list):
                index += 1
                title = data.get("title", "").lower().replace(" ", "_")
                body_text = data.get("body_text", "")
                result_string = f"\n    \"{title}\": \"{body_text}\""

                if index == 1:
                    system_prompt_string += ('```json\n{' + result_string + ',')
                
                elif index == total_sections:
                    system_prompt_string += (result_string + '\n}\n```')

                else:
                    system_prompt_string += f'{result_string},'
            
            # Generate dynamic system prompt
            system_messages_content = f"### Task:\nYou will be provided with a CONVERSATION between the healthcare provider and the patient.\nBased on the conversation provide a detailed, comprehensive, and informative response for the sections {title_result_string}.  keeping in mind the definitions and you must have to generate responses for all the {total_sections} sections.\n\n{system_prompt_string}\n\n## Note:\n\tYou have to Extract as much as Possible Details from the CONVERSATION and Provide it in Particular section Using Layperson terms. If you are unable to find the necessary information for Any of the {total_sections} Sections, please WRITE `'UNABLE TO FIND THESE DETAILS'` INSTEAD,\n\n# Response Format:\n\tWrite Your Response in JSON Format (object with the following keys (Section name) and values). as Encodeded JSON String."
           
            # User prompt
            user_message_prompt = f"## CONVERSATION:\n\n{user_message}"

            gpt_status, gpt_response = self.generate_gpt_response(system_prompt=system_messages_content, user_prompt=user_message_prompt, is_only_msg=True, is_json_res=True)

            # Validate gpt response
            if gpt_status:
                gpt_content_data = json.loads(gpt_response)
                for gpt_c_title, gpt_c_message in gpt_content_data.items():
                    gpt_c_title = gpt_c_title.replace("_", " ").title()
                    gpt_data = {
                        "title": gpt_c_title,
                        "body_text": gpt_c_message,
                    }
                    scribe_simple_data.append(gpt_data)
            else:
                default_gpt_string = "We’re sorry, something has gone wrong. Please try later."
                for system_data in system_prompt_list:
                    gpt_title = system_data.get("title", "")
                    if gpt_title:
                        gpt_data = {
                            "title": gpt_title,
                            "body_text": default_gpt_string,
                        }
                        scribe_simple_data.append(gpt_data)
           
            if not scribe_simple_data:
                return False, {'status': 'error', 'message': 'No data generated for system prompts.'}

            return True, scribe_simple_data
        except Exception as e:
            logger.error(f'\n----------- ERROR (generate scribe simple response) -----------\n{datetime.now()}\n{str(e)}\n--------------------------------------------------------------\n')
            return False, {'status': 'error', 'message': f'Error loading system prompts: {str(e)}'}