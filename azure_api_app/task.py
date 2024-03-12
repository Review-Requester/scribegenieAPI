# From utils
from utils import handle_exceptions

# From assemblyai_operation
from assemblyai_operation import AssemblyAIOperation

# From whisperai_operation
from whisperai_operation import WhisperAIOperation

# From openai_operation
from openai_operation import OpenAIOperation

# Firebase Authorization
from firebase_operation import FirebaseOperations

# Other
import os
import sys
import time
import json
import logging
import datetime
from pathlib import Path


# Configure the logging settings
BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)
log_file_path = f"{BASE_DIR}/error.log"  

logging.basicConfig(
    filename=log_file_path,
    level=logging.ERROR,  
)


class TranscriptGPTOperation:

    def __init__(self, file_path, patient_name, user_id, visit_type):
        self.file_path = file_path
        self.patient_name = patient_name
        self.user_id = user_id
        self.visit_type = visit_type

        self.transcription_data = ''
        self.clinical_note = []
        self.patient_instruction = ''
        self.provider_recommendation = ''
        self.scribe_simple_prompt_data = []
        self.system_prompt_data = []

        self.gpt_response_generated = False

        self.data_to_update_in_db = {
            "clinical_note": self.clinical_note,
            "is_succeed": False,
            "patient_instruction": self.patient_instruction,
            "patient_name": self.patient_name,
            "provider_recommendation": self.provider_recommendation,
            "transcription": self.transcription_data,
            "visit_name": self.visit_type,
            "visit_time": datetime.datetime.now()
        }


    def perform_operation(self):
        self.generate_default_clinical_data_for_firebase()

        is_transcript_generated = self.generate_transcript()
        if not is_transcript_generated:
            self.firebase_operation()
            return True

        is_response_generated = self.generate_transcript_gpt_response()
        if not is_response_generated:
            self.firebase_operation()
            return True
        
        self.data_to_update_in_db['is_succeed'] = True
        fb_operation = self.firebase_operation()
        return fb_operation


    def generate_default_clinical_data_for_firebase(self):
        # Retrieve default system prompt information for provider recommandations and patient instructions
        pr_pi_prompts_data_list = []
        current_directory = os.path.dirname(os.path.realpath(__file__))
        system_prompt_file = os.path.join(current_directory, "system_prompt/system_prompt.json")
        if os.path.isfile(system_prompt_file):
            with open(system_prompt_file, 'r') as file:
                pr_pi_prompts_data_list = json.load(file)

        # Retrieve visit type data from firebase
        fb_operation_obj = FirebaseOperations()
        visit_type_document = fb_operation_obj.get_visit_type(self.visit_type, self.user_id)
        visit_type_data = visit_type_document.to_dict() if visit_type_document else {}
        visit_type_section_data_list = visit_type_data.get('sections', [])
        
        self.system_prompt_data = visit_type_section_data_list + pr_pi_prompts_data_list

        # Create default prompt data list to perform add operations with firebase
        default_value = "We’re sorry, something has gone wrong. Please try later."

        for prompt_data in self.system_prompt_data:
            title = prompt_data.get("title", None)
            prompt_note_data = {
                "title": title,
                "body_text": default_value,
            }
            
            self.scribe_simple_prompt_data.append(prompt_note_data)
            
            if title == "Patient instruction":
                self.patient_instruction = default_value
                continue

            if title == "Provider Recommendation":
                self.provider_recommendation = default_value
                continue

            self.clinical_note.append(prompt_note_data)

        # Update dict of storing data in firebase
        self.data_to_update_in_db.update({
            "clinical_note": self.clinical_note,
            "patient_instruction": self.patient_instruction,
            "provider_recommendation": self.provider_recommendation,
        })


    @handle_exceptions(is_status=True)
    def generate_transcript_using_whisper_ai(self):
        """Perform Audio To Text Translation using whisper AI"""

        # Create Whisper AI object
        assembly_object = WhisperAIOperation()

        # Generate transcript
        transcript_data = assembly_object.generate_transcription(self.file_path)
         
        # Delete temporary file after completing all operations
        self.delete_temp_file(self.file_path)
        
        if not transcript_data:
            return False

        sorted_transcript_data = sorted(transcript_data, key=lambda x: x["id"])
        formatted_transcript_data = '\n'.join(item["text"].strip() for item in sorted_transcript_data)
        self.transcription_data = formatted_transcript_data
        return True

    @handle_exceptions(is_status=True)
    def generate_transcript(self):
        """Perform Audio To Text Translation"""

        # Create Assembly AI object
        assembly_object = AssemblyAIOperation()

        # Upload file using Assembly
        upload_response = assembly_object.upload_file(self.file_path)
        if not upload_response:
            return False
        upload_url = upload_response.get("upload_url", '')
        
        # Transcript file uploaded
        transcribe_response = assembly_object.transcribe_file(upload_url)
        if not transcribe_response:
            return False
        
        # Delete temporary file after completing all operations
        self.delete_temp_file(self.file_path)

        # Get transcript id
        transcript_id = transcribe_response.get('id', None)
        if not transcript_id:
            return False
        
        # Get polling data
        while (True):
            transcription_result = assembly_object.polling_transcript(transcript_id)
            transcription_status = transcription_result.get('status', None)

            if not transcription_status:
                return False

            if transcription_status == 'completed':
                utterances = self.sequences(transcription_result.get('utterances', []))
                self.transcription_data = utterances or transcription_result.get('text', '')
                break

            elif transcription_status == 'error':
                message = f"Transcription failed: {transcription_result['error']}"
                return False

            else:
                time.sleep(2)
        return True


    @handle_exceptions(is_status=True)
    def generate_transcript_gpt_response(self):
        """Generate user_prompt for all system prompts like Subjective, Objective etc"""
        # Call GPT API to get response for all system prompts like Subjective, Objective etc
        open_ai_object = OpenAIOperation()
        res_status, response = open_ai_object.generate_scribe_simple_response(self.transcription_data, self.system_prompt_data)

        # Return response
        if not res_status:
            return False
        
        self.scribe_simple_prompt_data = response
        self.gpt_response_generated = True
        return True


    @handle_exceptions(is_status=True)
    def firebase_operation(self):
        """Add document in firebase"""
        clinical_note_list = []
        for ss_prompt_data in self.scribe_simple_prompt_data:
            title = ss_prompt_data.get("title", "")
            if title.lower() == "patient instruction":
                self.patient_instruction = ss_prompt_data.get("body_text", "")
                continue
            
            if title.lower() == "provider recommendation":
                self.provider_recommendation = ss_prompt_data.get("body_text", "")
                continue
            
            clinical_note_list.append(ss_prompt_data)

        self.clinical_note = clinical_note_list if clinical_note_list else self.clinical_note
        self.data_to_update_in_db['clinical_note'] = self.clinical_note
        self.data_to_update_in_db['patient_instruction'] = self.patient_instruction
        self.data_to_update_in_db['provider_recommendation'] = self.provider_recommendation
        self.data_to_update_in_db['transcription'] = self.transcription_data

        fb_operation_obj = FirebaseOperations()
        fb_status = fb_operation_obj.create_user_history(self.data_to_update_in_db, self.user_id)
        if not fb_status:
            return False
        
        if self.transcription_data and self.gpt_response_generated:
            is_managed = fb_operation_obj.manage_user_balance(self.data_to_update_in_db, self.user_id)
            return is_managed

        return True


    @handle_exceptions(is_status=True)
    def delete_temp_file(self, file_path):
        os.remove(file_path)


    @staticmethod
    def sequences(utterance_data):
        try:
            response_list = sorted(utterance_data, key=lambda x: x['start'])
            transcript = ''
            for e in response_list:
                transcript += f"{e['text']}\n"
                # transcript += f"Person {e['speaker']}: {e['text']}\n\n"
            return transcript
        except:
            return []


def main():
    arguments = sys.argv[1].split(',')
    audio_file_path = arguments[0]
    patient_name = arguments[1]
    user_id = arguments[2]
    visit_type = arguments[3]

    # Create an instance of TranscriptGPTTask
    transcript_gpt_task = TranscriptGPTOperation(audio_file_path, patient_name, user_id, visit_type)

    # Perform the operation
    transcript_gpt_task.perform_operation()


if __name__ == "__main__":
   main()