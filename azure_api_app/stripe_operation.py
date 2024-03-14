import os
import stripe
import logging
from dotenv import load_dotenv


logger = logging.getLogger(__name__)
load_dotenv()


class StripeOperation:

    def __init__(self):
        STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
        stripe.api_key = STRIPE_API_KEY

    @staticmethod
    def get_customer_data(customer_id):
        data = stripe.Customer.retrieve(customer_id)
        return data if data else {}
    
    @staticmethod
    def get_payment_methods(customer_id):
        data = stripe.Customer.list_payment_methods(customer_id)
        return data if data else {}