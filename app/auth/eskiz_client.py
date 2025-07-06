import time
import requests
from app.core.config import settings

class EskizClient:
    def __init__(self):
        self.token = None
        self.token_expiry = 0  # timestamp in seconds

    def _get_new_token(self):
        url = 'https://notify.eskiz.uz/api/auth/login'
        data = {
            'email': settings.ESKIZ_EMAIL,
            'password': settings.ESKIZ_PASSWORD
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()

        self.token = result['data']['token']
        self.token_expiry = time.time() + 3500  # token ~1 soat, 3500s xavfsiz oraliq

    def _ensure_token(self):
        if not self.token or time.time() > self.token_expiry:
            self._get_new_token()

    def send_sms(self, phone, message):
        self._ensure_token()
        url = 'https://notify.eskiz.uz/api/message/sms/send'
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        data = {
            'mobile_phone': phone,
            'message': message,
            'from': '4546',
            'callback_url': ''
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
