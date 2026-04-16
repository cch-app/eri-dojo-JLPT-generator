from __future__ import annotations

import base64
import json
import zlib
from dataclasses import dataclass
from typing import Any

from itsdangerous import BadSignature, URLSafeSerializer


class TokenDecodeError(ValueError):
    pass


@dataclass(frozen=True)
class TokenCodec:
    serializer: URLSafeSerializer

    @staticmethod
    def from_secret(*, secret_key: str, salt: str = "jlpt-session-v1") -> "TokenCodec":
        if not secret_key.strip():
            raise ValueError("secret_key must be non-empty")
        return TokenCodec(
            serializer=URLSafeSerializer(secret_key=secret_key, salt=salt)
        )

    def encode(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(
            payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        )
        compressed = zlib.compress(raw.encode("utf-8"), level=9)
        b64 = base64.urlsafe_b64encode(compressed).decode("ascii")
        return self.serializer.dumps(b64)

    def decode(self, token: str) -> dict[str, Any]:
        try:
            b64 = self.serializer.loads(token)
        except BadSignature as e:
            raise TokenDecodeError("Invalid or tampered session token.") from e
        try:
            compressed = base64.urlsafe_b64decode(b64.encode("ascii"))
            raw = zlib.decompress(compressed).decode("utf-8")
            obj = json.loads(raw)
        except Exception as e:  # noqa: BLE001
            raise TokenDecodeError("Corrupted session token.") from e
        if not isinstance(obj, dict):
            raise TokenDecodeError("Invalid session token payload.")
        return obj  # type: ignore[return-value]
