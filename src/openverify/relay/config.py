"""Trusted host settings, separate from graph-authored configuration."""

from dataclasses import dataclass, field
from math import isfinite

from openverify.model import ProviderBinding


@dataclass(frozen=True)
class RuntimeConfig:
    max_concurrency: int = 8
    timeout: float = 30.0
    bindings: dict[str, ProviderBinding] = field(
        default_factory=lambda: dict[str, ProviderBinding]()
    )

    def __post_init__(self) -> None:
        if type(self.max_concurrency) is not int or self.max_concurrency < 1:
            raise ValueError("max_concurrency must be a positive integer")
        if not isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("timeout must be finite and positive")
