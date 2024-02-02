# Firestore to work with firebase
from firebase_admin import credentials, firestore, initialize_app, auth

# From rest_framework 
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import permissions

# Other
import os

# Global variables
firebase_initialized = False


def initialize_firestore_client():
    """ Initialize Firebase app and Firestore client """
    global firebase_initialized
    if not firebase_initialized:
        current_directory = os.path.dirname(os.path.realpath(__file__))
        json_file_path = os.path.join(current_directory, "firebase_cred/serviceAccountKey.json")

        cred = credentials.Certificate(json_file_path)
        initialize_app(cred)
        firebase_initialized = True
    
    return firestore.client()


class FirebaseAuthorization(permissions.BasePermission):

    def authenticate(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return None

            token = auth_header.split(' ')[-1]
            db_obj = initialize_firestore_client()

            decoded_token = auth.verify_id_token(token)
            decoded_user_id = decoded_token['uid']
            user = auth.get_user(decoded_user_id)

            request.user_id = decoded_user_id
            request.db = db_obj
            return user
        except Exception as e:
            raise AuthenticationFailed(f"Token verification failed: {str(e)}")

    def has_permission(self, request, view):
        user = self.authenticate(request)
        request.user = user  # Set the authenticated user in the request
        return user is not None
