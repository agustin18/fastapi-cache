"""Narrow, opt-in argument filtering; never change legacy key generation."""

import hashlib
import json
import math
import re
from inspect import Parameter, Signature, signature
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi.params import Depends
from fastapi.security.base import SecurityBase
from starlette.requests import Request
from typing_extensions import Annotated, get_args, get_origin

_PROTECTED = {
    "auth", "authorization", "cookie", "credential", "credentials", "identity",
    "language", "locale", "permission", "permissions", "principal", "role",
    "roles", "scope", "scopes", "session", "tenant", "token", "user",
    "access", "account", "apikey", "accesskey", "authentication", "authn",
    "authz", "bearer", "body", "header", "jwt", "key", "password", "path",
    "payload", "query", "secret", "subject", "username", "userid", "tenantid",
}


def _service_dependency(parameter: Parameter) -> bool:
    """Accept only an explicit, zero-argument Depends provider.

    This is a structural restriction, not proof of business/identity safety.
    """
    marker = parameter.default
    if get_origin(parameter.annotation) is Annotated:
        metadata = get_args(parameter.annotation)[1:]
        if len(metadata) != 1 or parameter.default is not Parameter.empty:
            return False
        marker = metadata[0]
    if type(marker) is not Depends:
        return False
    provider = marker.dependency
    if provider is None or isinstance(provider, SecurityBase):
        return False
    try:
        return not signature(provider).parameters
    except (TypeError, ValueError):
        return False


def validate_exclusions(
    signature: Signature, names: Tuple[str, ...], request_name: str, response_name: str
) -> None:
    seen = set()
    for name in names:
        if type(name) is not str or name in seen or name not in signature.parameters:
            raise ValueError("Invalid or duplicate excluded parameter")
        seen.add(name)
        parameter = signature.parameters[name]
        words = set(re.findall(r"[a-z0-9]+", re.sub(r"([a-z])([A-Z])", r"\1_\2", name).lower()))
        if (
            name in (request_name, response_name)
            or parameter.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD)
            or words & _PROTECTED
        ):
            raise ValueError("Cannot exclude protected or variadic parameter")
        if not _service_dependency(parameter):
            raise ValueError("Excluded parameter must be an explicit zero-argument service Depends")


def _scalar(value: Any) -> Optional[Tuple[str, str]]:
    if value is None:
        return ("none", "")
    if type(value) is bool:
        return ("bool", "1" if value else "0")
    if type(value) is int:
        return ("int", str(value))
    if type(value) is float:
        if not math.isfinite(value):
            return None
        return ("float", value.hex())
    if type(value) is str:
        return ("str", value.encode("utf-8").hex())
    if type(value) is bytes:
        return ("bytes", value.hex())
    return None


def filtered_key(
    func: Callable[..., Any],
    signature: Signature,
    exclusions: Tuple[str, ...],
    namespace: str,
    request: Optional[Request],
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> Optional[str]:
    """Return a versioned key, or None to bypass unsupported input."""
    if any(
        p.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD)
        for p in signature.parameters.values()
    ):
        return None
    try:
        bound = signature.bind(*args, **kwargs)
        if any(name not in bound.arguments for name in exclusions):
            return None
        bound.apply_defaults()
        values: List[Tuple[str, Tuple[str, str]]] = []
        for name, value in bound.arguments.items():
            if name in exclusions:
                # Scalar dependency results may be identity or response inputs;
                # never discard them, even if explicitly declared as Depends.
                if value is None or type(value) in (bool, int, float, str, bytes):
                    return None
                continue
            scalar = _scalar(value)
            if scalar is None:
                return None
            values.append((name, scalar))
        route: Tuple[str, ...] = ()
        if request is not None:
            scope = request.scope
            method, path, root = scope.get("method"), scope.get("path"), scope.get("root_path", "")
            if not isinstance(method, str) or not isinstance(path, str) or not isinstance(root, str):
                return None
            hosts = request.headers.getlist("host")
            if len(hosts) != 1 or not hosts[0].strip():
                return None
            # Overrides can introduce request-derived inputs not visible in the
            # original dependency signature. Do not assume they are equivalent.
            if getattr(scope.get("app"), "dependency_overrides", None):
                return None
            route = (hosts[0].lower(), method, root, path)
        elif (
            "<locals>" in func.__qualname__
            or func.__name__ == "<lambda>"
            or getattr(func, "__wrapped__", None) is not None
            or bool(getattr(getattr(func, "__code__", None), "co_freevars", ()))
        ):
            return None
        payload = json.dumps(
            (func.__module__, func.__qualname__, sorted(exclusions), values, route),
            ensure_ascii=False, separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        return None
    return f"{namespace}:filter-v1:{hashlib.sha256(payload).hexdigest()}"
