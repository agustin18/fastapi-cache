import abc
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, Union

from starlette.requests import Request
from starlette.responses import Response
from typing_extensions import Protocol

_Func = Callable[..., Any]


class KeyBuilder(Protocol):
    def __call__(
        self,
        __function: _Func,
        __namespace: str = ...,
        *,
        request: Optional[Request] = ...,
        response: Optional[Response] = ...,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> Union[Awaitable[str], str]:
        ...


class Backend(abc.ABC):
    """Legacy backend protocol; capabilities vary by concrete adapter.

    No implicit resource ownership, automatic retry, or common exact TTL
    sentinel is guaranteed. Cancellation and backend exceptions propagate
    from direct calls; a failed write or clear may have had partial effects.
    See the D4 backend contract for supported and experimental operations.
    """

    @abc.abstractmethod
    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        raise NotImplementedError

    @abc.abstractmethod
    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def clear(self, namespace: Optional[str] = None, key: Optional[str] = None) -> int:
        raise NotImplementedError
