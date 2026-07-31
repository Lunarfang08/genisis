from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError


class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    code: str


@dataclass
class ApiError(Exception):
    status: int
    title: str
    detail: str
    code: str


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(_request: Request, error: ApiError) -> JSONResponse:
        problem = ProblemDetail(
            title=error.title,
            status=error.status,
            detail=error.detail,
            code=error.code,
        )
        return JSONResponse(
            status_code=error.status,
            content=problem.model_dump(),
            media_type="application/problem+json",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, error: RequestValidationError
    ) -> JSONResponse:
        problem = ProblemDetail(
            title="Validation failed",
            status=422,
            detail="One or more request fields are invalid.",
            code="validation_failed",
        )
        content: dict[str, Any] = problem.model_dump()
        validation_errors = []
        for item in error.errors():
            serializable = dict(item)
            context = serializable.get("ctx")
            if isinstance(context, dict):
                serializable["ctx"] = {key: str(value) for key, value in context.items()}
            validation_errors.append(serializable)
        content["errors"] = validation_errors
        return JSONResponse(
            status_code=422,
            content=content,
            media_type="application/problem+json",
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(_request: Request, _error: SQLAlchemyError) -> JSONResponse:
        problem = ProblemDetail(
            title="Database unavailable",
            status=503,
            detail=(
                "GENESIS could not connect to PostgreSQL. "
                "Check the configured host and credentials."
            ),
            code="database_unavailable",
        )
        return JSONResponse(
            status_code=503,
            content=problem.model_dump(),
            media_type="application/problem+json",
        )
