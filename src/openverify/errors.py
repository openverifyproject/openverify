"""Small stable error contract, independent of validator-library messages."""

from pydantic import JsonValue

from openverify.error_codes import VcpErrorCode
from openverify.provider_codes import ProviderErrorCode


class ProtocolError(ValueError):
    def __init__(self, code: str, message: str, path: str = "", details: JsonValue = None):
        code = str.__str__(code)
        super().__init__(f"{code} at {path or '/'}: {message}")
        # Provider-bound VCP execution may expose Provider Contract codes. Keep
        # ownership typed without merging the vocabularies or changing strings.
        self.code: VcpErrorCode | ProviderErrorCode | str = code
        for vocabulary in (VcpErrorCode, ProviderErrorCode):
            try:
                self.code = vocabulary(str.__str__(code))
                break
            except ValueError:
                continue
        self.message = message
        self.path = path
        self.details = details

    def as_dict(self) -> dict[str, JsonValue]:
        return {
            "code": str.__str__(self.code),
            "message": self.message,
            "path": self.path,
            "details": self.details,
        }
