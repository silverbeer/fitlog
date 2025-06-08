from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from fastapi._compat import ModelField
from fastapi.security.base import SecurityBase


@dataclass
class SecurityRequirement:
    security_scheme: SecurityBase
    scopes: Sequence[str] | None = None


@dataclass
class Dependant:
    path_params: list[ModelField] = field(default_factory=list)
    query_params: list[ModelField] = field(default_factory=list)
    header_params: list[ModelField] = field(default_factory=list)
    cookie_params: list[ModelField] = field(default_factory=list)
    body_params: list[ModelField] = field(default_factory=list)
    dependencies: list["Dependant"] = field(default_factory=list)
    security_requirements: list[SecurityRequirement] = field(default_factory=list)
    name: str | None = None
    call: Callable[..., Any] | None = None
    request_param_name: str | None = None
    websocket_param_name: str | None = None
    http_connection_param_name: str | None = None
    response_param_name: str | None = None
    background_tasks_param_name: str | None = None
    security_scopes_param_name: str | None = None
    security_scopes: list[str] | None = None
    use_cache: bool = True
    path: str | None = None
    cache_key: tuple[Callable[..., Any] | None, tuple[str, ...]] = field(init=False)

    def __post_init__(self) -> None:
        self.cache_key = (self.call, tuple(sorted(set(self.security_scopes or []))))
