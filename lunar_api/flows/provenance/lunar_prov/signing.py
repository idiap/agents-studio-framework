# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import base64
from typing import Dict, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa, padding
from cryptography.hazmat.backends import default_backend


def load_private_key(path: str, password: Optional[str] = None):
    with open(path, "rb") as f:
        pem = f.read()
    pw = password.encode("utf-8") if password else None
    return serialization.load_pem_private_key(
        pem, password=pw, backend=default_backend()
    )


def sign_bytes(private_key, message: bytes) -> Dict[str, str]:
    """Sign message bytes. Supports Ed25519 and RSA."""
    if isinstance(private_key, ed25519.Ed25519PrivateKey):
        sig = private_key.sign(message)
        algo = "Ed25519"
    elif isinstance(private_key, rsa.RSAPrivateKey):
        sig = private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        algo = "RSA-PSS-SHA256"
    else:
        raise TypeError(f"Unsupported key type: {type(private_key)}")
    pub = private_key.public_key().public_bytes(
        encoding=(
            serialization.Encoding.Raw
            if algo == "Ed25519"
            else serialization.Encoding.DER
        ),
        format=(
            serialization.PublicFormat.Raw
            if algo == "Ed25519"
            else serialization.PublicFormat.SubjectPublicKeyInfo
        ),
    )
    return {
        "algorithm": algo,
        "signature_b64": base64.b64encode(sig).decode("ascii"),
        "public_key_b64": base64.b64encode(pub).decode("ascii"),
    }
