import os
from typing import Optional, Tuple


DATA_DIR = "data"
KEY_DIR = os.path.join(DATA_DIR, "keys")


def ensure_dirs() -> None:
    os.makedirs(KEY_DIR, exist_ok=True)


def key_paths(username: str) -> Tuple[str, str]:
    pub_path = os.path.join(KEY_DIR, f"{username}.pub.asc")
    priv_path = os.path.join(KEY_DIR, f"{username}.priv.asc")
    return pub_path, priv_path


def load_keys(username: str) -> Optional[Tuple[str, str]]:
    pub_path, priv_path = key_paths(username)
    if not (os.path.exists(pub_path) and os.path.exists(priv_path)):
        return None
    with open(pub_path, "r", encoding="utf-8") as f:
        pub = f.read()
    with open(priv_path, "r", encoding="utf-8") as f:
        priv = f.read()
    return pub, priv


def save_keys(username: str, pub: str, priv: str) -> None:
    ensure_dirs()
    pub_path, priv_path = key_paths(username)
    with open(pub_path, "w", encoding="utf-8") as f:
        f.write(pub)
    with open(priv_path, "w", encoding="utf-8") as f:
        f.write(priv)

