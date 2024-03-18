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


    def get_customer_data(self, customer_id):
        data = stripe.Customer.retrieve(customer_id)
        return data if data else {}
    

    def get_payment_methods(self, customer_id):
        data = stripe.Customer.list_payment_methods(customer_id)
        return data if data else {}
    

    def retrieve_payment_method_data(self, payment_method_id):
        payment_method_data = stripe.PaymentMethod.retrieve(payment_method_id)
        s_payment_method_id = payment_method_data.get('id', None) 
        if s_payment_method_id == payment_method_id:
            return payment_method_data
        return {}
    

    def get_payment_method_data(self, customer_id):
        customer_data = self.get_customer_data(customer_id)

        default_payment_method = customer_data.get('invoice_settings', {}).get('default_payment_method', '')
        if default_payment_method:
            payment_method_data = self.retrieve_payment_method_data(default_payment_method)
            payment_method_list = [payment_method_data]
        else:
            payment_method_data = self.get_payment_methods(customer_id)
            payment_method_list = payment_method_data.get("data", [])
        
        return payment_method_list


    def auto_payment(self, amount, customer_id):
        payment_method_data_list = self.get_payment_method_data(customer_id)
        payment_method_dict = payment_method_data_list[0] if payment_method_data_list else {}
        payment_method_id = payment_method_dict.get('id', None)

        if not all([amount, customer_id, payment_method_id]):
            return False

        payment_intent = stripe.PaymentIntent.create(
            amount=(amount*100),
            currency="usd",
            customer=customer_id,
            description="Automatic payment",
            payment_method=payment_method_id,
            confirm=True,
            automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'
                } 
            )
        
        if payment_intent.status == 'succeeded':
            return True
        return False
    

    @staticmethod
    def get_billing_portal_session(customer_id):
        data = stripe.billing_portal.Session.create(customer=customer_id)
        return data if data else {}
    
    
    @staticmethod
    def checkout_session(customer_id, price_id):
        data = stripe.checkout.Session.create(
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            currency="usd",
            allow_promotion_codes=True,
            success_url="https://app.scribegenie.io/success",
            cancel_url="https://app.scribegenie.io/cancel",
        )
        return data if data else {}
    
    @staticmethod
    def cancel_subscription(subscription_id):
        response = stripe.Subscription.cancel(subscription_id)
        return response if response else {}