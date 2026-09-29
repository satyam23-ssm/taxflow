import hashlib
import hmac
import json
import re

import requests
from django.conf import settings


class WhatsAppAPIError(Exception):
    pass


def normalize_phone(phone_number):
    digits = re.sub(r'\D+', '', phone_number or '')
    if not digits:
        return ''
    return f'+{digits}'


def phone_variants(phone_number):
    normalized = normalize_phone(phone_number)
    digits = normalized.lstrip('+')
    variants = {phone_number, normalized, digits}
    if digits.startswith('91'):
        variants.add(digits[2:])
        variants.add(f'+{digits[2:]}')
    return {item for item in variants if item}


def verify_meta_signature(raw_body, signature_header, app_secret):
    if not app_secret:
        return True
    if not signature_header or not signature_header.startswith('sha256='):
        return False

    expected = hmac.new(
        app_secret.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    received = signature_header.split('=', 1)[1]
    return hmac.compare_digest(expected, received)


def extract_messages_from_webhook(payload):
    events = []
    for entry in payload.get('entry', []):
        for change in entry.get('changes', []):
            value = change.get('value', {})
            metadata = value.get('metadata', {})
            for message in value.get('messages', []):
                message_type = message.get('type', 'unknown')
                media_payload = message.get(message_type, {}) if message_type in {'image', 'document', 'audio', 'video'} else {}
                text_payload = message.get('text', {}) if message_type == 'text' else {}

                events.append({
                    'message_id': message.get('id'),
                    'sender_phone': normalize_phone(message.get('from')),
                    'message_type': message_type,
                    'text_body': text_payload.get('body', ''),
                    'media_id': media_payload.get('id', ''),
                    'media_mime_type': media_payload.get('mime_type', ''),
                    'phone_number_id': metadata.get('phone_number_id', ''),
                    'display_phone_number': metadata.get('display_phone_number', ''),
                    'timestamp': message.get('timestamp'),
                    'raw_message': message,
                    'raw_change': change,
                })
    return events


class WhatsAppCloudClient:
    def __init__(self):
        self.api_version = settings.WHATSAPP_GRAPH_API_VERSION
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.base_url = f'https://graph.facebook.com/{self.api_version}'

    @property
    def missing_config(self):
        missing = []
        if not self.access_token:
            missing.append('WHATSAPP_ACCESS_TOKEN')
        if not self.phone_number_id:
            missing.append('WHATSAPP_PHONE_NUMBER_ID')
        return missing

    @property
    def is_configured(self):
        return not self.missing_config

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }

    def send_text(self, to_phone, body):
        if not self.is_configured:
            raise WhatsAppAPIError(f'Missing config: {", ".join(self.missing_config)}')

        url = f'{self.base_url}/{self.phone_number_id}/messages'
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': normalize_phone(to_phone).lstrip('+'),
            'type': 'text',
            'text': {
                'preview_url': False,
                'body': body,
            },
        }
        response = requests.post(url, headers=self._headers(), data=json.dumps(payload), timeout=20)
        if response.status_code >= 400:
            raise WhatsAppAPIError(response.text)
        return response.json()

    def get_media_url(self, media_id):
        if not self.is_configured:
            raise WhatsAppAPIError(f'Missing config: {", ".join(self.missing_config)}')

        response = requests.get(f'{self.base_url}/{media_id}', headers=self._headers(), timeout=20)
        if response.status_code >= 400:
            raise WhatsAppAPIError(response.text)
        return response.json()

    def download_media(self, media_url):
        if not self.access_token:
            raise WhatsAppAPIError('Missing config: WHATSAPP_ACCESS_TOKEN')

        response = requests.get(
            media_url,
            headers={'Authorization': f'Bearer {self.access_token}'},
            timeout=30
        )
        if response.status_code >= 400:
            raise WhatsAppAPIError(response.text)
        return response.content, response.headers.get('Content-Type', '')
