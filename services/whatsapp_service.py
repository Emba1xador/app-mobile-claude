from __future__ import annotations

import os
import subprocess
import webbrowser

from services.formatting import encode_whatsapp_message, sanitize_phone


class WhatsAppService:
    def build_url(self, phone: str, message: str) -> str:
        sanitized = sanitize_phone(phone)
        return f"https://wa.me/55{sanitized}?text={encode_whatsapp_message(message)}"

    def open_message(self, phone: str, message: str) -> str:
        url = self.build_url(phone, message)
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for chrome in chrome_paths:
            if chrome and os.path.exists(chrome):
                subprocess.Popen([chrome, url])
                return url
        webbrowser.open(url)
        return url
