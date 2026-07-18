"""
Minimal SendPulse Chatbot API client (Telegram channel).

NOTE: verify field/endpoint names against the current docs before going live:
https://api.sendpulse.com/.well-known/openapi/  (or your account's API tab)
The oauth, send and getByTag calls below match the current published docs.
setVariable / tagAdd are the commonly documented shapes but double-check them.
"""

import os
import time
import requests

API_BASE = "https://api.sendpulse.com"


class SendPulseClient:
    def __init__(self, client_id=None, client_secret=None, bot_id=None):
        self.client_id = client_id or os.environ["SENDPULSE_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["SENDPULSE_CLIENT_SECRET"]
        self.bot_id = bot_id or os.environ.get("SENDPULSE_BOT_ID")
        self._token = None
        self._token_expires_at = 0

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token
        resp = requests.post(
            f"{API_BASE}/oauth/access_token",
            json={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600)
        return self._token

    def _headers(self):
        return {"Authorization": f"Bearer {self._get_token()}"}

    def send_photo(self, contact_id: str, photo_url: str, caption: str = ""):
        payload = {
            "contact_id": contact_id,
            "message": {"type": "photo", "photo": photo_url, "caption": caption},
        }
        resp = requests.post(
            f"{API_BASE}/telegram/contacts/send",
            json=payload, headers=self._headers(), timeout=20,
        )
        resp.raise_for_status()
        return resp.json()

    def send_text(self, contact_id: str, text: str):
        payload = {"contact_id": contact_id, "message": {"type": "text", "text": text}}
        resp = requests.post(
            f"{API_BASE}/telegram/contacts/send",
            json=payload, headers=self._headers(), timeout=20,
        )
        resp.raise_for_status()
        return resp.json()

    def set_variable(self, contact_id: str, variable_name: str, variable_value):
        payload = {
            "contact_id": contact_id,
            "variable_name": variable_name,
            "variable_value": str(variable_value),
        }
        resp = requests.post(
            f"{API_BASE}/telegram/contacts/setVariable",
            json=payload, headers=self._headers(), timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def add_tag(self, contact_id: str, tag: str):
        resp = requests.post(
            f"{API_BASE}/telegram/contacts/tagAdd",
            json={"contact_id": contact_id, "tag_name": tag},
            headers=self._headers(), timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def get_contacts_by_tag(self, tag: str):
        resp = requests.get(
            f"{API_BASE}/telegram/contacts/getByTag",
            params={"tag": tag, "bot_id": self.bot_id},
            headers=self._headers(), timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
