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

- Username: any name
- Server: `wss://end-to-end-encrypted-chat.onrender.com`

Example: 

<img width="842" height="252" alt="image" src="https://github.com/user-attachments/assets/4b62e086-2f60-47f2-858a-5cf535bdc2df" />

### Result: 
<img width="2030" height="752" alt="image" src="https://github.com/user-attachments/assets/dbc720c4-9ab4-46b5-9d9a-029f4fcc3ca9" />

## Behavior
- Render free services sleep after ~15 minutes idle.
- Starting the client wakes the service; it auto-retries until it connects.
- The server only relays encrypted messages.
- No key verification is implemented (learning only).
