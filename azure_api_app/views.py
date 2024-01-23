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

# Other
import os
import json


class FineTuneModelCompletion(APIView):

    @handle_exceptions()
    def post(self, request, *args, **kwargs):
        # Get Data
        user_message = request.data.get('message', '').strip()
        system_prompt = request.data.get('system_prompt', '').strip()
        if (not user_message) or (not system_prompt):
            return Response({'status': 'error', 'message': "User message or system prompt not found..!"}, status=status.HTTP_400_BAD_REQUEST)

        # Call GPT API to get response
        open_ai_object = OpenAIOperation()
        res_status, response = open_ai_object.generate_gpt_response(system_prompt, user_message, is_only_msg=True)

        # Return response
        if not res_status:
            return Response({'status': 'error', 'message': response or "Something Went Wrong..! Response Not Generated..!"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(response, status=status.HTTP_200_OK)


class AssemblyAIAudioToText(APIView):

    @handle_exceptions()
    def post(self, request, *args, **kwargs):
        # Get data
        file = request.FILES.get('file', None)
        if not file:
            return Response({'error': 'File not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the file to a temporary location 
        file_path = self.save_file(file)
        if not file_path:
            return Response({'error': 'Something Went Wrong..! Please, Try Again..!'}, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        return Response(transcribe_response, status=status.HTTP_200_OK)


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


class AssemblyAIAudioToTextStatus(APIView):

    @handle_exceptions()
    def get(self, request, transcript_id=None, *args, **kwargs):
        # Validate transcript_id
        if not transcript_id:
            return Response({'status':'error', 'message': "Transcript Id Not Found..!"}, status=status.HTTP_404_NOT_FOUND)

        # Create Assembly AI object
        assembly_object = AssemblyAIOperation()

        # Get polling data
        transcription_result = assembly_object.polling_transcript(transcript_id)
        transcription_status = transcription_result.get('status', None)

        # Return response
        if transcription_status == 'error':
            message = f"Transcription failed: {transcription_result['error']}"
            return Response({'status':'error', 'message': message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if transcription_status == 'completed':
            response_data = {'status': 'success', 'data': transcription_result['text']}
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(transcription_result, status=status.HTTP_400_BAD_REQUEST)


class ChatBotCompletion(APIView):

    @handle_exceptions()
    def post(self, request, *args, **kwargs):
        # Get Data
        model = request.data.get('model', '').strip() # Required
        messages = request.data.get('messages', '') # Required
        temperature = request.data.get('temperature', 0.8)
        presence_penalty = request.data.get('presence_penalty', 0)

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