"""Small stable error contract, independent of validator-library messages."""

from pydantic import JsonValue


class ProtocolError(ValueError):
    def __init__(self, code: str, message: str, path: str = "", details: JsonValue = None):
        super().__init__(f"{code} at {path or '/'}: {message}")
        self.code = code
        self.message = message
        self.path = path
        self.details = details

    def as_dict(self) -> dict[str, JsonValue]:
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "details": self.details,
        }
