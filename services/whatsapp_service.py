from __future__ import annotations

import os
import platform
import shutil
import subprocess
import webbrowser

from services.formatting import encode_whatsapp_message, sanitize_phone


class WhatsAppService:
    def build_url(self, phone: str, message: str) -> str:
        sanitized = sanitize_phone(phone)
        return f"https://wa.me/55{sanitized}?text={encode_whatsapp_message(message)}"

    def open_message(self, phone: str, message: str) -> str:
        url = self.build_url(phone, message)
        chrome = self._find_chrome()
        if chrome:
            subprocess.Popen([chrome, url])
            return url
        webbrowser.open(url)
        return url

    def _find_chrome(self) -> str | None:
        system = platform.system()
        if system == "Windows":
            candidates = [
                os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            ]
            return next((p for p in candidates if p and os.path.exists(p)), None)
        if system == "Darwin":
            mac_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            return mac_path if os.path.exists(mac_path) else shutil.which("google-chrome")
        return shutil.which("google-chrome") or shutil.which("chromium-browser") or shutil.which("chromium")
