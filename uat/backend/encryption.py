"""Symmetric encryption for product secret columns (SDT1-118).

Encrypts and decrypts secret values stored in the ``products`` table -
Jira API tokens, GitHub tokens, Anthropic keys, Resend keys - using
Fernet symmetric encryption.

The encryption key is read from the ``SECRET_ENCRYPTION_KEY`` environment
variable at call time. It must be a valid Fernet key: 32 url-safe
base64-encoded bytes (44 characters including padding). Generate one
locally with::

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Then set ``SECRET_ENCRYPTION_KEY`` in the Railway backend service.

If the variable is missing or empty, ``encrypt_secret`` and
``decrypt_secret`` raise ``RuntimeError`` so callers fail fast rather
than silently storing plaintext.
"""

import os

from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    """Return a Fernet instance built from ``SECRET_ENCRYPTION_KEY``.

    Raises:
        RuntimeError: If ``SECRET_ENCRYPTION_KEY`` is unset or empty.
    """
    key = os.environ.get("SECRET_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "SECRET_ENCRYPTION_KEY environment variable is not set - "
            "cannot encrypt or decrypt product secrets. Generate a key "
            "with Fernet.generate_key() and set it on the backend service."
        )
    return Fernet(key.encode("utf-8") if isinstance(key, str) else key)


def encrypt_secret(value: str) -> str:
    """Encrypt a plaintext secret with the configured Fernet key.

    Args:
        value: Plaintext secret to encrypt.

    Returns:
        URL-safe base64-encoded Fernet token as a string, suitable for
        storage in a ``VARCHAR`` column.

    Raises:
        RuntimeError: If ``SECRET_ENCRYPTION_KEY`` is not set.
    """
    fernet = _get_fernet()
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    """Decrypt a Fernet ciphertext produced by :func:`encrypt_secret`.

    Args:
        value: URL-safe base64-encoded Fernet token previously written
            to the database.

    Returns:
        The original plaintext secret string.

    Raises:
        RuntimeError: If ``SECRET_ENCRYPTION_KEY`` is not set.
        cryptography.fernet.InvalidToken: If ``value`` is not a valid
            Fernet token for the configured key.
    """
    fernet = _get_fernet()
    return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
