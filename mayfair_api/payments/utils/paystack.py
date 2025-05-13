import json
import requests
from django.conf import settings
from requests.exceptions import RequestException


class PayStack:

    PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
    PAYSTACK_PUBLIC_KEY = settings.PAYSTACK_PUBLIC_KEY

    base_url = "https://api.paystack.co"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    def initialize_transaction(self, email, **kwargs):
        path = f"/transaction/initialize"
        url = self.base_url + path

        payload = {
            "email": email,
            "amount": kwargs["amount"],
            "callback_url": settings.PAYSTACK_CALLBACK_URL,
        }

        # Add metadata if provided
        if "metadata" in kwargs:
            payload["metadata"] = kwargs["metadata"]

        response = requests.post(url, data=json.dumps(payload), headers=self.headers)

        if response.status_code == 200:
            response_data = response.json()
            return response_data["status"], response_data["data"]

        response_data = response.json()
        return response_data["status"], response_data["message"]

    # def initialize_transaction(self, email, **kwargs):
    #     path = f"/transaction/initialize"

    #     url = self.base_url + path

    #     payload = {
    #         "email": email,
    #         "amount": kwargs["amount"],
    #         "callback_url": settings.PAYSTACK_CALLBACK_URL,
    #     }

    #     response = requests.post(url, data=json.dumps(payload), headers=self.headers)

    #     if response.status_code == 200:
    #         response_data = response.json()
    #         print(response_data["data"])

    #         return response_data["status"], response_data["data"]
    #     response_data = response.json()
    #     print(response_data["message"])

    #     return response_data["status"], response_data["message"]

    def confirm_transaction(self, reference):

        path = f"/transaction/verify/{reference}"

        url = self.base_url + path
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            response_data = response.json()
            print(response_data["data"])

            return response_data["status"], response_data["data"]
        response_data = response.json()
        print("Nooooooo")
        print(response_data["message"])

        return response_data["status"], response_data["message"]
        # raise RequestException(response.json())
