from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pytest
from pydantic import BaseModel, ValidationError, field_validator
from pydantic.v1 import BaseModel as V1BaseModel
from starlette.responses import JSONResponse, Response

from fastapi_cache.coder import Coder, JsonCoder, PickleCoder, TypedJsonCoder


@dataclass
class DCItem:
    name: str
    price: float
    description: Optional[str] = None
    tax: Optional[float] = None


class PDItem(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    tax: Optional[float] = None


@pytest.mark.parametrize(
    "value",
    [
        1,
        "some_string",
        (1, 2),
        [1, 2, 3],
        {"some_key": 1, "other_key": 2},
        DCItem(name="foo", price=42.0, description="some dataclass item", tax=0.2),
        PDItem(name="foo", price=42.0, description="some pydantic item", tax=0.2),
    ],
)
def test_pickle_coder(value: Any) -> None:
    encoded_value = PickleCoder.encode(value)
    assert isinstance(encoded_value, bytes)
    decoded_value = PickleCoder.decode(encoded_value)
    assert decoded_value == value


@pytest.mark.parametrize(
    ("value", "return_type"),
    [
        (1, None),
        ("some_string", None),
        ((1, 2), Tuple[int, int]),
        ([1, 2, 3], None),
        ({"some_key": 1, "other_key": 2}, None),
        (DCItem(name="foo", price=42.0, description="some dataclass item", tax=0.2), DCItem),
        (PDItem(name="foo", price=42.0, description="some pydantic item", tax=0.2), PDItem),
        (
            [PDItem(name="foo", price=42.0, description="some pydantic item", tax=0.2)],
            List[PDItem],
        ),
    ],
)
def test_json_coder(value: Any, return_type: Any) -> None:
    encoded_value = TypedJsonCoder.encode(value)
    assert isinstance(encoded_value, bytes)
    decoded_value = TypedJsonCoder.decode_as_type(encoded_value, type_=return_type)
    assert decoded_value == value


def test_json_coder_default_is_legacy() -> None:
    value = PDItem(name="foo", price=42.0, description="some pydantic item", tax=0.2)
    encoded_value = JsonCoder.encode(value)
    decoded_value = JsonCoder.decode_as_type(encoded_value, type_=PDItem)
    assert isinstance(decoded_value, dict)


def test_json_coder_validation_error() -> None:
    invalid = b'{"name": "incomplete"}'
    with pytest.raises(ValidationError):
        TypedJsonCoder.decode_as_type(invalid, type_=PDItem)


class V1Item(V1BaseModel):
    name: str
    price: float


class TypeErrorItem(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def check_quantity(cls, value: int) -> int:
        raise TypeError("validator error")


def test_typed_json_coder_propagates_v2_validator_type_error() -> None:
    encoded = b'{"quantity": 1}'
    with pytest.raises(TypeError, match="validator error"):
        TypedJsonCoder.decode_as_type(encoded, type_=TypeErrorItem)


def test_json_coder_unsupported_annotations_fall_back() -> None:
    value = {"ok": True}
    encoded = TypedJsonCoder.encode(value)
    for type_ in (Response, JSONResponse):
        decoded = TypedJsonCoder.decode_as_type(encoded, type_=type_)
        assert decoded == value


def test_json_coder_pydantic_v1_falls_back() -> None:
    encoded = b'{"name": "foo", "price": 1.0}'
    decoded = TypedJsonCoder.decode_as_type(encoded, type_=V1Item)
    assert isinstance(decoded, dict)
    assert decoded["name"] == "foo"


def test_typed_json_coder_pydantic_v1_composite_falls_back() -> None:
    encoded_list = b'[{"name": "foo", "price": 1.0}]'
    decoded_list = TypedJsonCoder.decode_as_type(encoded_list, type_=List[V1Item])
    assert isinstance(decoded_list, list)
    assert decoded_list[0]["name"] == "foo"

    encoded_optional = b'{"name": "foo", "price": 1.0}'
    decoded_optional = TypedJsonCoder.decode_as_type(encoded_optional, type_=Optional[V1Item])
    assert isinstance(decoded_optional, dict)
    assert decoded_optional["name"] == "foo"


def test_json_coder_without_type_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("fastapi_cache.coder.TypeAdapter", None)
    encoded = TypedJsonCoder.encode({"a": 1})
    assert TypedJsonCoder.decode_as_type(encoded, type_=Dict[str, int]) == {"a": 1}


class CustomCoder(JsonCoder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        return b"custom:" + super().encode(value)

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return super().decode(value[len(b"custom:") :])


def test_custom_coder_legacy_decode() -> None:
    encoded = CustomCoder.encode({"a": 1})
    assert CustomCoder.decode_as_type(encoded, type_=None) == {"a": 1}


def test_coder_base_methods_raise() -> None:
    with pytest.raises(NotImplementedError):
        Coder.encode(1)
    with pytest.raises(NotImplementedError):
        Coder.decode(b"1")
