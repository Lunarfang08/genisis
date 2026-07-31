from datetime import date


class DomainValidationError(ValueError):
    """Raised when a civilization command violates a domain invariant."""


def normalized_name(value: str, *, field: str = "name", maximum: int = 120) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise DomainValidationError(f"{field} must not be blank")
    if len(normalized) > maximum:
        raise DomainValidationError(f"{field} must be at most {maximum} characters")
    return normalized


def validate_score(value: int, *, field: str, minimum: int = 0, maximum: int = 100) -> int:
    if not minimum <= value <= maximum:
        raise DomainValidationError(f"{field} must be between {minimum} and {maximum}")
    return value


def validate_birth_date(birth_date: date, simulation_date: date) -> date:
    if birth_date > simulation_date:
        raise DomainValidationError("birth_date cannot be after the world's simulation date")
    return birth_date
