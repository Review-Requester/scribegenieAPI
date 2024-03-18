# Firestore to work with firebase
from firebase_admin import credentials, firestore, initialize_app, auth
from google.cloud.firestore_v1.base_query import FieldFilter

# Other
import os
import logging
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

# Global variables
firebase_initialized = False


def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f'\n--------------- ERROR (firebase) ---------------\n{datetime.now()}\n{str(e)}\n--------------------------------------------------------------\n')
            return False
    return wrapper


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
        

    @handle_exceptions
    def create_user_history(self, data, user_id):
        collection_name_1 = "users"
        collection_name_2 = "history"    

        self.db.collection(collection_name_1).document(user_id)\
                .collection(collection_name_2).document().create(data)
        
        return True


    @handle_exceptions
    def manage_user_balance(self, data, user_id, stripe_obj):
        collection_name_1 = "users"  
        collection_name_2 = "subscriptions"

        # Check if user has active subscriptions
        active_subscription = self.db.collection(collection_name_1) \
            .document(user_id) \
            .collection(collection_name_2) \
            .where(filter=FieldFilter('status', '==', "active")) \
            .get()

        # If active subscription then do nothing
        if active_subscription:
            return True

        # If not active subscription then update balance or trials
        user_snapshot =  self.db.collection(collection_name_1).document(user_id).get()
        user_json = user_snapshot.to_dict()

        add_on_balance = user_json.get('add_on_balance', 0)
        remaining_trials = user_json.get('remaining_trials', 0)

        if add_on_balance > 1.5:
            # Update add on balance
            update_add_on_balance = add_on_balance - 1.5
            self.db.collection(collection_name_1).document(user_id).update({
                'add_on_balance': update_add_on_balance
            })

            # Update add on balance if auto payment is done
            auto_payment_status, credit_amount = self.stripe_auto_payment(add_on_balance, user_id, stripe_obj)
            if auto_payment_status:
                self.db.collection(collection_name_1).document(user_id).update({
                    'add_on_balance': update_add_on_balance + float(credit_amount)
                })

            return True
        else:
            # No sufficient balance then update it by auto payment first
            auto_payment_status, credit_amount = self.stripe_auto_payment(add_on_balance, user_id, stripe_obj)
            if auto_payment_status:
                # Add balance by auto payment
                self.db.collection(collection_name_1).document(user_id).update({
                    'add_on_balance': add_on_balance + float(credit_amount)
                })
                
                # Retrieve updated balance
                user_snapshot =  self.db.collection(collection_name_1).document(user_id).get()
                user_json = user_snapshot.to_dict()
                new_add_on_balance = user_json.get('add_on_balance', 0)

                # Now minus balance 
                if new_add_on_balance > 1.5:
                    new_update_add_on_balance = new_add_on_balance - 1.5
                    self.db.collection(collection_name_1).document(user_id).update({
                        'add_on_balance': new_update_add_on_balance
                    })

                    return True

        if remaining_trials > 0:
            self.db.collection(collection_name_1).document(user_id).update({
                'remaining_trials': remaining_trials - 1
            })
            return True
        
        return False
    

    def stripe_auto_payment(self, balance, user_id, stripe_obj):
        try:
            # Default variable
            credit_amount = 0

            # Get user data to check if has enable auto pay or not ?
            collection_name_1 = "users"  
            user_data = self.db.collection(collection_name_1) \
                    .document(user_id).get()
            user_data_dict = user_data.to_dict() if user_data else {}

            # Check auto pay enable or not ?
            auto_pay_data = user_data_dict.get('auto_pay', {})
            is_auto_pay_enabled = auto_pay_data.get('enable_auto_pay', False)
            if is_auto_pay_enabled:
                threshold = auto_pay_data.get('threshold', 0)
                if float(balance) <= float(threshold):
                    credit_amount = auto_pay_data.get('credit', 0)
                    stripe_customer_id = user_data_dict.get("stripeId", '')
                    
                    # Credit amount to stripe
                    payment_status = stripe_obj.auto_payment(credit_amount, stripe_customer_id)
                    return payment_status, credit_amount
            return False, credit_amount
        except:
            return False, 0



    @handle_exceptions
    def get_visit_type(self, visit_type, user_id):
        collection_name_1 = "users"  
        collection_name_2 = "visits"

        # Check if entry with specified visit_type exists in collection ?
        visit_type_document = self.db.collection(collection_name_1) \
            .document(user_id) \
            .collection(collection_name_2) \
            .where(filter=FieldFilter('name', '==', visit_type)) \
            .get()

        if visit_type_document:
            return visit_type_document[-1]
        return False


    @handle_exceptions
    def get_stripe_customer_id(self, user_id):
        collection_name_1 = "users"  
        user_data = self.db.collection(collection_name_1) \
                .document(user_id).get()
        
        user_data_dict = user_data.to_dict() if user_data else {}
        customer_id = user_data_dict.get("stripeId", '')
        return customer_id
    

    @handle_exceptions
    def check_subscription(self, user_id, subscription_id):
        collection_name_1 = "users"  
        collection_name_2 = "subscriptions"

        # Check if user has subscriptions
        active_subscription = self.db.collection(collection_name_1) \
            .document(user_id) \
            .collection(collection_name_2) \
            .document(subscription_id) \
            .get()
        
        active_subscription_data = active_subscription.to_dict()
        return True if active_subscription_data else False