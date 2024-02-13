# Firestore to work with firebase
from firebase_admin import credentials, firestore, initialize_app, auth

# Other
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Global variables
firebase_initialized = False


class FirebaseOperations:
    
    def __init__(self, firebase_db=None):
        if not firebase_db:
            global firebase_initialized
            if not firebase_initialized:
                current_directory = os.path.dirname(os.path.realpath(__file__))
                json_file_path = os.path.join(current_directory, "firebase_cred/serviceAccountKey.json")

                cred = credentials.Certificate(json_file_path)
                initialize_app(cred)
                firebase_initialized = True
            
            firebase_db = firestore.client()
        self.db = firebase_db
        

    def create_user_history(self, data, user_id):
        try:
            collection_name_1 = "users"
            collection_name_2 = "history"    

            self.db.collection(collection_name_1).document(user_id)\
                    .collection(collection_name_2).document().create(data)
            
            return True
        except Exception as e:
            logger.error(f'\n--------------- ERROR (firebase) ---------------\n{datetime.now()}\n{str(e)}\n--------------------------------------------------------------\n')
            return False