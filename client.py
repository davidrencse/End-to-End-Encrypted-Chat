import asyncio
import json
import sys
from typing import Dict, Optional

import websockets
from pgpy import PGPKey, PGPMessage
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from crypto_pgp import generate_keypair, load_key
from storage import ensure_dirs, load_keys, save_keys


DEFAULT_SERVER = "ws://localhost:8765"


class WSClient(QThread):
    message = pyqtSignal(dict)
    connected = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url: str, username: str):
        super().__init__()
        self.url = url
        self.username = username
        self._loop = None
        self._ws = None

    async def _send(self, data: dict) -> None:
        if not self._ws:
            return
        await self._ws.send(json.dumps(data))

    def send_json(self, data: dict) -> None:
        if not self._loop:
            return
        asyncio.run_coroutine_threadsafe(self._send(data), self._loop)

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._main())

    async def _main(self) -> None:
        try:
            async with websockets.connect(self.url) as ws:
                self._ws = ws
                await ws.send(json.dumps({"type": "register", "username": self.username}))
                self.connected.emit()
                async for raw in ws:
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    self.message.emit(data)
        except Exception as exc:
            self.error.emit(str(exc))


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.username_input = QLineEdit()
        self.passphrase_input = QLineEdit()
        self.passphrase_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.server_input = QLineEdit(DEFAULT_SERVER)

        form = QFormLayout()
        form.addRow("Username", self.username_input)
        form.addRow("Passphrase (optional)", self.passphrase_input)
        form.addRow("Server", self.server_input)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def values(self):
        return (
            self.username_input.text().strip(),
            self.passphrase_input.text(),
            self.server_input.text().strip(),
        )


class ChatWindow(QMainWindow):
    def __init__(self, username: str, passphrase: str, server_url: str):
        super().__init__()
        self.username = username
        self.passphrase = passphrase
        self.server_url = server_url
        self.pubkeys: Dict[str, PGPKey] = {}

        self.pubkey, self.privkey = self._load_or_create_keys()

        self.ws = WSClient(server_url, username)
        self.ws.connected.connect(self._on_connected)
        self.ws.message.connect(self._on_message)
        self.ws.error.connect(self._on_error)
        self.ws.start()

        self.setWindowTitle(f"E2EE Chat - {username}")
        self._build_ui()

    def _build_ui(self) -> None:
        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        self.user_label = QLabel(f"You: {self.username}")
        self.to_input = QLineEdit()
        self.msg_input = QLineEdit()
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._send_message)
        keys_btn = QPushButton("Show Keys")
        keys_btn.clicked.connect(self._show_keys)

        top = QFormLayout()
        top.addRow(self.user_label)
        top.addRow("To", self.to_input)

        bottom = QHBoxLayout()
        bottom.addWidget(self.msg_input)
        bottom.addWidget(send_btn)
        bottom.addWidget(keys_btn)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.chat_view)
        layout.addLayout(bottom)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def _log(self, text: str) -> None:
        self.chat_view.append(text)

    def _load_or_create_keys(self) -> (PGPKey, PGPKey):
        ensure_dirs()
        existing = load_keys(self.username)
        if existing:
            pub_armored, priv_armored = existing
            pubkey = load_key(pub_armored)
            privkey = load_key(priv_armored)
            if privkey.is_protected and not self.passphrase:
                QMessageBox.critical(self, "Key Error", "Passphrase required for this key.")
                sys.exit(1)
            return pubkey, privkey

        pub_armored, priv_armored = generate_keypair(self.username, self.passphrase or None)
        save_keys(self.username, pub_armored, priv_armored)
        pubkey = load_key(pub_armored)
        privkey = load_key(priv_armored)
        return pubkey, privkey

    def _encrypt_for_peer(self, peer: str, plaintext: str) -> Optional[str]:
        peer_key = self.pubkeys.get(peer)
        if not peer_key:
            return None
        message = PGPMessage.new(plaintext)
        if self.passphrase:
            with self.privkey.unlock(self.passphrase):
                signature = self.privkey.sign(message)
        else:
            signature = self.privkey.sign(message)
        message |= signature
        encrypted = peer_key.encrypt(message)
        return str(encrypted)

    def _decrypt_message(self, armored: str) -> str:
        message = PGPMessage.from_blob(armored)
        if self.passphrase:
            with self.privkey.unlock(self.passphrase):
                decrypted = self.privkey.decrypt(message)
        else:
            decrypted = self.privkey.decrypt(message)
        return decrypted.message

    def _on_connected(self) -> None:
        self._log("Connected to server.")

    def _on_error(self, msg: str) -> None:
        self._log(f"Connection error: {msg}")

    def _on_message(self, data: dict) -> None:
        msg_type = data.get("type")
        if msg_type == "pubkey_request":
            target = data.get("from")
            if target:
                self.ws.send_json(
                    {
                        "type": "pubkey_response",
                        "to": target,
                        "pubkey": str(self.pubkey),
                    }
                )
        elif msg_type == "pubkey_response":
            sender = data.get("from")
            armored = data.get("pubkey")
            if sender and armored:
                self.pubkeys[sender] = load_key(armored)
                self._log(f"Received public key from {sender}.")
        elif msg_type == "msg":
            sender = data.get("from")
            armored = data.get("pgp")
            if sender and armored:
                try:
                    plaintext = self._decrypt_message(armored)
                    self._log(f"{sender}: {plaintext}")
                except Exception as exc:
                    self._log(f"Failed to decrypt from {sender}: {exc}")
        elif msg_type == "error":
            self._log(f"Server error: {data.get('message')}")

    def _send_message(self) -> None:
        target = self.to_input.text().strip()
        plaintext = self.msg_input.text().strip()
        if not target or not plaintext:
            return
        encrypted = self._encrypt_for_peer(target, plaintext)
        if not encrypted:
            self._log(f"No public key for {target}. Requesting...")
            self.ws.send_json({"type": "pubkey_request", "to": target})
            return
        self.ws.send_json({"type": "msg", "to": target, "pgp": encrypted})
        self._log(f"me -> {target}: {plaintext}")
        self.msg_input.clear()

    def _show_keys(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Your Keys")
        layout = QVBoxLayout()
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(
            "Public key:\n"
            f"{self.pubkey}\n\n"
            "Private key:\n"
            f"{self.privkey}\n\n"
            "Session key:\n"
            "OpenPGP uses a fresh per-message session key, which PGPy does not expose."
        )
        layout.addWidget(text)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.setLayout(layout)
        dialog.resize(600, 500)
        dialog.exec()


def main() -> None:
    app = QApplication(sys.argv)
    dialog = LoginDialog()
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return
    username, passphrase, server_url = dialog.values()
    if not username:
        QMessageBox.critical(None, "Login Error", "Username is required.")
        return
    window = ChatWindow(username, passphrase, server_url or DEFAULT_SERVER)
    window.resize(700, 500)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
