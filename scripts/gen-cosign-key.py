#!/usr/bin/env python3
"""Generate a cosign-compatible key pair without the cosign binary.

Writes cosign.key (private, gitignored) and cosign.pub (public, committed) in the repo
root. The private key uses cosign's on-disk format: an ECDSA P-256 key in PKCS#8 DER,
encrypted with scrypt + NaCl secretbox and wrapped in a PEM block. The password is
empty, which is what GitHub Actions needs.

Requires: pip install --user pynacl cryptography
"""
import base64
import hashlib
import json
import os
import sys
import textwrap
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from nacl.secret import SecretBox

ROOT = Path(__file__).resolve().parent.parent
KEY_PATH = ROOT / "cosign.key"
PUB_PATH = ROOT / "cosign.pub"


def main() -> int:
    if KEY_PATH.exists():
        print(f"{KEY_PATH} already exists, refusing to overwrite.", file=sys.stderr)
        return 1

    private = ec.generate_private_key(ec.SECP256R1())
    der = private.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )

    password = b""  # cosign in CI needs an unencrypted-passphrase key
    salt = os.urandom(32)
    # N=32768, r=8 needs ~32 MiB; raise the OpenSSL cap above that.
    key = hashlib.scrypt(password, salt=salt, n=32768, r=8, p=1, dklen=32, maxmem=128 * 1024 * 1024)
    nonce = os.urandom(SecretBox.NONCE_SIZE)
    box = SecretBox(key)
    ciphertext = box.encrypt(der, nonce).ciphertext

    b64 = lambda b: base64.b64encode(b).decode()
    payload = json.dumps(
        {
            "kdf": {"name": "scrypt", "params": {"N": 32768, "r": 8, "p": 1}, "salt": b64(salt)},
            "cipher": {"name": "nacl/secretbox", "nonce": b64(nonce)},
            "ciphertext": b64(ciphertext),
        }
    ).encode()

    body = "\n".join(textwrap.wrap(b64(payload), 64))
    pem = f"-----BEGIN ENCRYPTED SIGSTORE PRIVATE KEY-----\n{body}\n-----END ENCRYPTED SIGSTORE PRIVATE KEY-----\n"
    KEY_PATH.write_text(pem)

    pub = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    PUB_PATH.write_bytes(pub)

    print(f"wrote {KEY_PATH.name} (keep private) and {PUB_PATH.name} (commit this)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
