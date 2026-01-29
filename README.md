# E2EE Encrypted Chat (PGP)

End-to-end encrypted 1:1 chat using OpenPGP encryption with PGPy.

## Setup
```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
Start the relay server:
```sh
python server.py
```

Start two clients (two terminals):
```sh
python client.py
```

## Notes
- This uses OpenPGP encryption via PGPy (public key per user).
- Server relays messages only; it does not decrypt.
- No key verification is implemented (for learning only).
