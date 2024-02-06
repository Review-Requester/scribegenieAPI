# From rest_framework 
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

# From openai_operation
from azure_api_app.openai_operation import OpenAIOperation

# From utils
from azure_api_app.utils import handle_exceptions

# Firebase Authorization
from azure_api_app.firebase_auth import FirebaseAuthorization


# Other
import os
import json
import subprocess


class FineTuneModelOperation(APIView):
    """Based on audio file, generate transcript using transcript generate GPT response for different system prompt and make entry in firebase user history.

    Args:
        file: audio file (mp3) -> Required 
        patient_name: name of the patient (string) -> Required

    Returns:
        DRF Response
    """

    permission_classes = [FirebaseAuthorization]

    @handle_exceptions()
    def post(self, request, *args, **kwargs):
        user_id = request.user_id

        # Get data
        file = request.FILES.get('file', None)
        patient_name = request.data.get('patient_name', '').strip()
        if not file or not patient_name:
            return Response({'error': 'File or patient name not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the file to a temporary location 
        file_path = self.save_file(file)
        if not file_path:
            return Response({'error': 'Something Went Wrong..! Please, Try Again..!'}, status=status.HTTP_400_BAD_REQUEST)

        # Call your background task using subprocess
        subprocess.Popen(['python3', 'azure_api_app/task.py', f'{file_path},{patient_name},{user_id}'])
        
        return Response({"status": "success", "message": "Audio uploaded and process started successfully..!"}, status=status.HTTP_200_OK)


    @handle_exceptions(is_status=True)
    def save_file(self, file):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        file_name = f"audio_files/{file.name}" 
        file_path = os.path.join(current_directory, file_name)

        with open(file_path, 'wb') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        return file_path


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