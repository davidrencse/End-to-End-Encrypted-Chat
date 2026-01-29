# E2EE Encrypted Chat (PGP)

End-to-end encrypted 1:1 chat using OpenPGP (PGPy). The relay runs as a Render web service; clients are PyQt desktop apps.

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

In the login dialog:
- Username: any name
- Server: `wss://YOUR-SERVICE.onrender.com`

## Render (server) setup
1) Push the repo to GitHub.
2) Render: New -> Web Service -> connect the repo.
3) Build Command: `pip install -r requirements.txt`
4) Start Command: `python server.py`
5) Health Check Path: `/health`

## Behavior
- Render free services sleep after ~15 minutes idle.
- Starting the client wakes the service; it auto-retries until it connects.
- The server only relays encrypted messages.
- No key verification is implemented (learning only).
