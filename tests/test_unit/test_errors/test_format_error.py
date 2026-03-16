from http import HTTPStatus

import pytest
from django.conf import LazySettings

from dmr.errors import ErrorType, format_error
from dmr.exceptions import (
    InternalServerError,
    NotAcceptableError,
    NotAuthenticatedError,
    RequestSerializationError,
    ResponseSchemaError,
    ValidationError,
)


def test_format_error_from_string() -> None:
    """Ensures plain string is wrapped into a detail entry."""
    result = format_error('something went wrong')
    assert result == {'detail': [{'msg': 'something went wrong'}]}


def test_format_error_from_string_with_loc() -> None:
    """Ensures ``loc`` parameter is included as a list in the detail entry."""
    result = format_error('bad value', loc='body')
    assert result == {'detail': [{'msg': 'bad value', 'loc': ['body']}]}


def test_format_error_from_string_with_error_type() -> None:
    """Ensures ``error_type`` parameter is included in the detail entry."""
    result = format_error('bad value', error_type=ErrorType.user_msg)
    assert result == {'detail': [{'msg': 'bad value', 'type': 'user_msg'}]}


def test_format_error_from_string_with_loc_and_error_type() -> None:
    """Ensures both ``loc`` and ``error_type`` are included together."""
    result = format_error(
        'bad value',
        loc='field',
        error_type=ErrorType.value_error,
    )
    assert result == {
        'detail': [
            {'msg': 'bad value', 'loc': ['field'], 'type': 'value_error'},
        ],
    }


def test_format_error_from_string_error_type_as_str() -> None:
    """Ensures ``error_type`` accepts plain strings."""
    result = format_error('oops', error_type='custom_type')
    assert result == {'detail': [{'msg': 'oops', 'type': 'custom_type'}]}


def test_format_error_from_validation_error() -> None:
    """Ensures ``ValidationError`` payload is returned as-is."""
    payload = [{'msg': 'too short', 'loc': ['name'], 'type': 'value_error'}]
    exc = ValidationError(payload, status_code=HTTPStatus.UNPROCESSABLE_ENTITY)

    result = format_error(exc)

    assert result == {'detail': payload}


def test_format_error_from_request_serialization_error() -> None:
    """Ensures ``RequestSerializationError`` gets ``value_error`` type."""
    exc = RequestSerializationError('cannot parse body')

    result = format_error(exc)

    assert result == {
        'detail': [{'msg': 'cannot parse body', 'type': 'value_error'}],
    }


def test_format_error_from_response_schema_error() -> None:
    """Ensures ``ResponseSchemaError`` gets ``value_error`` type."""
    exc = ResponseSchemaError('schema mismatch')

    result = format_error(exc)

    assert result == {
        'detail': [{'msg': 'schema mismatch', 'type': 'value_error'}],
    }


def test_format_error_from_not_acceptable_error() -> None:
    """Ensures ``NotAcceptableError`` gets ``value_error`` type."""
    exc = NotAcceptableError('unsupported media type')

    result = format_error(exc)

    assert result == {
        'detail': [{'msg': 'unsupported media type', 'type': 'value_error'}],
    }


def test_format_error_from_not_authenticated_error() -> None:
    """Ensures ``NotAuthenticatedError`` gets ``security`` type."""
    exc = NotAuthenticatedError('token expired')

    result = format_error(exc)

    assert result == {
        'detail': [{'msg': 'token expired', 'type': 'security'}],
    }


def test_format_error_from_not_authenticated_error_default_msg() -> None:
    """Ensures ``NotAuthenticatedError`` uses default message."""
    exc = NotAuthenticatedError()

    result = format_error(exc)

    assert result == {
        'detail': [{'msg': 'Not authenticated', 'type': 'security'}],
    }


def test_format_error_from_internal_server_error_debug(
    settings: LazySettings,
) -> None:
    """Ensures ``InternalServerError`` shows details in DEBUG mode."""
    settings.DEBUG = True
    exc = InternalServerError('database is down')

    result = format_error(exc)

    assert result == {'detail': [{'msg': 'database is down'}]}


def test_format_error_from_internal_server_error_no_debug(
    settings: LazySettings,
) -> None:
    """Ensures ``InternalServerError`` hides details without DEBUG."""
    settings.DEBUG = False
    exc = InternalServerError('database is down')

    result = format_error(exc)

    assert result == {
        'detail': [{'msg': InternalServerError.default_message}],
    }


def test_format_error_unknown_exception_raises() -> None:
    """Ensures unhandled exception types raise ``NotImplementedError``."""
    with pytest.raises(NotImplementedError, match='Cannot format error'):
        format_error(ValueError('unexpected'))  # type: ignore[arg-type]
