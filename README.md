# E2EE Encrypted Chat (PGP)

End-to-end encrypted 1:1 chat using OpenPGP (PGPy). The relay runs on Render; clients are PyQt desktop apps.

## Install
```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the client
```sh
python client.py
```

Use these settings in the login dialog:
<img width="475" height="230" alt="image" src="https://github.com/user-attachments/assets/0f9119fa-5db3-4432-9920-0f133550f7cb" />

- Username: any name
- Server: `wss://end-to-end-encrypted-chat.onrender.com`

## Behavior
- Render free services sleep after ~15 minutes idle.
- Starting the client wakes the service; it auto-retries until it connects.
- The server only relays encrypted messages.
- No key verification is implemented (learning only).
