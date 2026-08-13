import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass

from app.auth.models import UserRole


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    """使用带随机盐的 scrypt 保存密码，绝不记录明文。"""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
    )
    return f"{_base64url_encode(salt)}:{_base64url_encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_value, digest_value = encoded.split(":", maxsplit=1)
        expected = _base64url_decode(digest_value)
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_base64url_decode(salt_value),
            n=2**14,
            r=8,
            p=1,
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


@dataclass(frozen=True)
class TokenClaims:
    session_id: str
    user_id: str
    role: UserRole
    expires_at: int


def issue_token(claims: TokenClaims, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "jti": claims.session_id,
        "sub": claims.user_id,
        "role": claims.role.value,
        "exp": claims.expires_at,
    }
    encoded_header = _base64url_encode(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    encoded_payload = _base64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def decode_token(token: str, secret: str) -> TokenClaims | None:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(
            _base64url_decode(encoded_signature), expected_signature
        ):
            return None

        header = json.loads(_base64url_decode(encoded_header))
        payload = json.loads(_base64url_decode(encoded_payload))
        if header != {"alg": "HS256", "typ": "JWT"}:
            return None
        return TokenClaims(
            session_id=str(payload["jti"]),
            user_id=str(payload["sub"]),
            role=UserRole(str(payload["role"])),
            expires_at=int(payload["exp"]),
        )
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None

