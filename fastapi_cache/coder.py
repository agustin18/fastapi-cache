import datetime
import json
import pickle  # nosec:B403
from decimal import Decimal
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Optional,
    TypeVar,
    Union,
    overload,
)

import pendulum
import pydantic
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from starlette.templating import (
    _TemplateResponse as TemplateResponse,  # pyright: ignore[reportPrivateUsage]
)

TypeAdapter = getattr(pydantic, "TypeAdapter", None)

_T = TypeVar("_T", bound=type)


CONVERTERS: Dict[str, Callable[[str], Any]] = {
    # Pendulum 3.0.0 adds parse to __all__, at which point these ignores can be removed
    "date": lambda x: pendulum.parse(x, exact=True),
    "datetime": lambda x: pendulum.parse(x, exact=True),
    "decimal": Decimal,
}


def _is_pydantic_v1_model(type_: Any) -> bool:
    v1 = getattr(pydantic, "v1", None)
    base: Any = getattr(v1, "BaseModel", None)
    return bool(base) and isinstance(type_, type) and issubclass(type_, base)


class JsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime.datetime):
            return {"val": str(o), "_spec_type": "datetime"}
        elif isinstance(o, datetime.date):
            return {"val": str(o), "_spec_type": "date"}
        elif isinstance(o, Decimal):
            return {"val": str(o), "_spec_type": "decimal"}
        else:
            return jsonable_encoder(o)


def object_hook(obj: Any) -> Any:
    _spec_type = obj.get("_spec_type")
    if not _spec_type:
        return obj

    if _spec_type in CONVERTERS:
        return CONVERTERS[_spec_type](obj["val"])
    else:
        raise TypeError(f"Unknown {_spec_type}")


class Coder:
    @classmethod
    def encode(cls, value: Any) -> bytes:
        raise NotImplementedError

    @classmethod
    def decode(cls, value: bytes) -> Any:
        raise NotImplementedError

    @overload
    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: _T) -> _T:
        ...

    @overload
    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: None) -> Any:
        ...

    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: Optional[_T]) -> Union[_T, Any]:
        """Decode value to the specific given type

        The default implementation uses the Pydantic model system to convert the value.

        """
        result = cls.decode(value)
        return result


class JsonCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        if isinstance(value, JSONResponse):
            return bytes(value.body)
        return json.dumps(value, cls=JsonEncoder).encode()

    @classmethod
    def decode(cls, value: bytes) -> Any:
        # explicitly decode from UTF-8 bytes first, as otherwise
        # json.loads() will first have to detect the correct UTF-
        # encoding used.
        return json.loads(value.decode(), object_hook=object_hook)


class TypedJsonCoder(JsonCoder):
    _type_adapter_cache: ClassVar[Dict[Any, Any]] = {}

    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: Any) -> Any:
        result = cls.decode(value)
        if type_ is None or _is_pydantic_v1_model(type_):
            return result

        type_adapter = TypeAdapter
        if type_adapter is None:
            return result

        adapter: Any
        try:
            adapter = cls._type_adapter_cache[type_]
        except KeyError:
            try:
                adapter = type_adapter(type_)
            except Exception:
                return result
            cls._type_adapter_cache[type_] = adapter
        try:
            return adapter.validate_python(result)
        except TypeError:
            return result


class PickleCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        if isinstance(value, TemplateResponse):
            value = value.body
        return pickle.dumps(value)

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return pickle.loads(value)  # noqa: S301

    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: Optional[_T]) -> Any:
        # Pickle already produces the correct type on decoding, no point
        # in paying an extra performance penalty for pydantic to discover
        # the same.
        return cls.decode(value)
