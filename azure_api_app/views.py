from django.shortcuts import render

# From rest_framework 
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

# From openai_operation
from azure_api_app.openai_operation import OpenAIOperation

# From assemblyai_operation
from azure_api_app.assemblyai_operation import AssemblyAIOperation

# From utils
from azure_api_app.utils import handle_exceptions

# Firebase Authorization
from azure_api_app.firebase_auth import FirebaseAuthorization
from azure_api_app.firebase_operation import FirebaseOperations

# Other
import os
import json
import time
import datetime


class FineTuneModelOperation(APIView):
    """Based on audio file, generate transcript using transcript generate GPT response for different system prompt and make entry in firebase user history.

    Args:
        file: audio file (mp3) -> Required 
        patient_name: name of the patient (string) -> Required

    Returns:
        True/False     """

    permission_classes = [FirebaseAuthorization]

    @handle_exceptions()
    def post(self, request, *args, **kwargs):
        user_id = request.user_id
        firebase_obj = request.db

        # Get data
        file = request.FILES.get('file', None)
        patient_name = request.data.get('patient_name', '').strip()
        if not file or not patient_name:
            return Response({'error': 'File or patient name not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the file to a temporary location 
        file_path = self.save_file(file)
        if not file_path:
            return Response({'error': 'Something Went Wrong..! Please, Try Again..!'}, status=status.HTTP_400_BAD_REQUEST)
        
        # ------------- Audio To Text Translation -------------

        # Create Assembly AI object
        assembly_object = AssemblyAIOperation()

        # Upload file using Assembly
        upload_response = assembly_object.upload_file(file_path)
        if not upload_response:
            return Response({'status':'error', 'message': "Audio file is not uploaded ..! Please, try with another audio file..!"}, status=status.HTTP_404_NOT_FOUND)
        upload_url = upload_response["upload_url"]
        
        # Transcript file uploaded
        transcribe_response = assembly_object.transcribe_file(upload_url)
        if not transcribe_response:
            return Response({'status':'error', 'message': "Audio transcription failed."}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete temporary file after completing all operations
        self.delete_temp_file(file_path)

        # ------------- Polling start -------------

        # Get transcript id
        transcript_id = transcribe_response.get('id', None)
        if not transcript_id:
            return Response({'status':'error', 'message': "Transcript Id Not Found..!"}, status=status.HTTP_404_NOT_FOUND)

        # Get polling data
        while (True):
            transcription_result = assembly_object.polling_transcript(transcript_id)
            transcription_status = transcription_result.get('status', None)

            if not transcription_status:
                return Response({'status':'error', 'message': "Something went wrong..!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if transcription_status == 'completed':
                utterances = self.sequences(transcription_result.get('utterances', []))
                transcription_data = utterances or transcription_result.get('text', '')
                break

            elif transcription_status == 'error':
                message = f"Transcription failed: {transcription_result['error']}"
                return Response({'status':'error', 'message': message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            else:
                time.sleep(2)

        # ------------- Generate GPT Response -------------
                
        if not transcription_data:
            return Response({'status': 'error', 'message': "Transcription data not found..!"}, status=status.HTTP_400_BAD_REQUEST)

        # Call GPT API to get response for all system prompts like Subjective, Objective etc
        open_ai_object = OpenAIOperation()
        res_status, response = open_ai_object.generate_scribe_simple_response(transcription_data)

        # Return response
        if not res_status:
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ------------- Make entry for user data in firebase -------------

        # Data to update in firebase
        scribe_simple_prompt_data = response
        clinical_note_list = []
        patient_instruction = ""
        provider_recommendation = ""

        for ss_prompt_data in scribe_simple_prompt_data:
            title = ss_prompt_data.get("title", None)
            if title == "Patient instruction":
                patient_instruction = ss_prompt_data.get("body_text", "")
                continue
            
            if title == "Provider Recommendation":
                provider_recommendation = ss_prompt_data.get("body_text", "")
                continue
            
            clinical_note_list.append(ss_prompt_data)

        data_to_update_in_db = {
            "clinical_note": clinical_note_list,
            "is_succeed": True,
            "patient_instruction": patient_instruction,
            "patient_name": patient_name,
            "provider_recommendation": provider_recommendation,
            "transcription": transcription_data,
            "visit_name": "SOAP Note",
            "visit_time": datetime.datetime.now()
        }
        fb_operation_obj = FirebaseOperations(firebase_obj)
        fb_status = fb_operation_obj.create_user_history(data_to_update_in_db, user_id)
        if not fb_status:
            return Response({"status": "error", "message": "Something went wrong. Firebase data insert operation failed..!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"status": "success", "message": "Data added in firebase successfully..!"}, status=status.HTTP_200_OK)


    @handle_exceptions(is_status=True)
    def save_file(self, file):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        file_name = f"audio_files/{file.name}" 
        file_path = os.path.join(current_directory, file_name)

        with open(file_path, 'wb') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        return file_path
    

    @handle_exceptions(is_status=True)
    def delete_temp_file(self, file_path):
        os.remove(file_path)


    @staticmethod
    def sequences(utterance_data):
        try:
            response_list = sorted(utterance_data, key=lambda x: x['start'])
            transcript = ''
            for e in response_list:
                transcript += f"{e['text']}\n\n"
                # transcript += f"Person {e['speaker']}: {e['text']}\n\n"
            return transcript
        except:
            return []


class ChatBotCompletion(APIView):
    """Generate GPT responses for input given

    Args:
        model: GPT model name (required)
        messages: Message list (required)
        temperature: temperature value for gpt model
        presence_penalty: presence penalty value

    Returns:
        Response return by GPT model
    """

    permission_classes = [FirebaseAuthorization]

    @handle_exceptions()
    def post(self, request, *args, **kwargs):
        # Get Data
        model = request.data.get('model', '').strip() # Required
        messages = json.loads(request.data.get('messages', []))  # Required
        temperature = float(request.data.get('temperature', 0.8))
        presence_penalty = float(request.data.get('presence_penalty', 0))

        # Validation
        if (not model) or (not messages):
            return Response({'status': 'error', 'message': "Model or user message not found..!"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Call GPT API to get response
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "presence_penalty": presence_penalty,
        }
        payload = json.dumps(payload, indent=2)
        open_ai_object = OpenAIOperation()
        res_status, response = open_ai_object.generate_gpt_response(payload=payload)

        # Return response
        if not res_status:
            return Response({'status': 'error', 'message': response or "Something Went Wrong..! Response Not Generated..!"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(response, status=status.HTTP_200_OK)