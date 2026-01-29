from typing import Optional, Tuple

from pgpy import PGPKey, PGPMessage, PGPUID
from pgpy.constants import (
    CompressionAlgorithm,
    HashAlgorithm,
    KeyFlags,
    PubKeyAlgorithm,
    SymmetricKeyAlgorithm,
)


def generate_keypair(username: str, passphrase: Optional[str]) -> Tuple[str, str]:
    key = PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 3072)
    uid = PGPUID.new(username)
    key.add_uid(
        uid,
        usage={KeyFlags.Sign, KeyFlags.EncryptCommunications, KeyFlags.EncryptStorage},
        hashes=[HashAlgorithm.SHA256],
        ciphers=[SymmetricKeyAlgorithm.AES256],
        compression=[CompressionAlgorithm.ZLIB],
    )
    if passphrase:
        key.protect(passphrase, SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)
    pubkey = key.pubkey
    return str(pubkey), str(key)


def load_key(armored: str) -> PGPKey:
    key, _ = PGPKey.from_blob(armored)
    return key


def encrypt_message(
    plaintext: str, recipient_pubkey: PGPKey, signer_privkey: Optional[PGPKey] = None
) -> str:
    message = PGPMessage.new(plaintext)
    if signer_privkey is not None:
        signature = signer_privkey.sign(message)
        message |= signature
    encrypted = recipient_pubkey.encrypt(message)
    return str(encrypted)


def decrypt_message(armored: str, privkey: PGPKey) -> str:
    message = PGPMessage.from_blob(armored)
    decrypted = privkey.decrypt(message)
    return decrypted.message
