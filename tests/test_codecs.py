from dataclasses import dataclass
from typing import Any, Optional, Tuple, Type

import pytest
from pydantic import BaseModel, ValidationError

from fastapi_cache.coder import JsonCoder, PickleCoder


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
        pytest.param(
            (1, 2),
            Tuple[int, int],
            marks=pytest.mark.xfail(
                strict=True, reason="P0-05: tuple decode is not implemented yet"
            ),
        ),
        ([1, 2, 3], None),
        ({"some_key": 1, "other_key": 2}, None),
        pytest.param(
            DCItem(name="foo", price=42.0, description="some dataclass item", tax=0.2),
            DCItem,
            marks=pytest.mark.xfail(
                strict=True, reason="P0-05: dataclass decode is not implemented yet"
            ),
        ),
        pytest.param(
            PDItem(name="foo", price=42.0, description="some pydantic item", tax=0.2),
            PDItem,
            marks=pytest.mark.xfail(
                strict=True, reason="P0-05: Pydantic decode is not implemented yet"
            ),
        ),
    ],
)
def test_json_coder(value: Any, return_type: Type[Any]) -> None:
    encoded_value = JsonCoder.encode(value)
    assert isinstance(encoded_value, bytes)
    decoded_value = JsonCoder.decode_as_type(encoded_value, type_=return_type)
    assert decoded_value == value


@pytest.mark.xfail(
    strict=True, reason="P0-05: validation is not implemented yet"
)
def test_json_coder_validation_error() -> None:
    invalid = b'{"name": "incomplete"}'
    with pytest.raises(ValidationError):
        JsonCoder.decode_as_type(invalid, type_=PDItem)
