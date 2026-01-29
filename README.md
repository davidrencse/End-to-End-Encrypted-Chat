# E2EE Encrypted Chat (PGP)

End-to-end encrypted 1:1 chat using OpenPGP encryption with PGPy.

## Setup
```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run (local server)
Start the relay server:
```sh
python server.py
```

Start two clients (two terminals):
```sh
python client.py
```

## Run (hosted server)
If you deployed the server (example: Render), you only run the clients locally.

Start two clients (two terminals):
```sh
python client.py
```

In the login dialog, set Server to your hosted WebSocket URL, e.g.:
```
wss://YOUR-SERVICE.onrender.com
```

## Deploy to Render (free tier)
1) Push this repo to GitHub.
2) In Render: New -> Web Service -> connect your repo.
3) Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python server.py`
   - Instance Type: Free
4) Set Health Check Path to `/health` in Settings -> Health & Alerts.
5) Deploy.

Notes:
- Render free services sleep after ~15 minutes idle; first reconnect may take time.
- Use `wss://` in clients for hosted connections.
- Starting `python client.py` will wake the Render service; the client auto-retries until it connects.

## Notes
- This uses OpenPGP encryption via PGPy (public key per user).
- Server relays messages only; it does not decrypt.
- No key verification is implemented (for learning only).
