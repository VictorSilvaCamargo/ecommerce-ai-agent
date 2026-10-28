from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ToolError(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(
        description="Código de erro legível por máquina (ex: CONFIRMATION_REQUIRED, NOT_FOUND)"
    )
    message: str = Field(description="Mensagem compreensível em português do Brasil")
    retryable: bool = Field(
        description="Indica se uma nova tentativa com parâmetros ajustados é recomendada"
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Metadados contextuais adicionais"
    )


class ToolResult[T](BaseModel):
    model_config = ConfigDict(frozen=True)

    success: bool
    data: T | None = None
    error: ToolError | None = None

    @classmethod
    def ok(cls, data: T) -> "ToolResult[T]":
        return cls(success=True, data=data, error=None)

    @classmethod
    def fail(
        cls, code: str, message: str, retryable: bool = False, details: dict[str, Any] | None = None
    ) -> "ToolResult[T]":
        return cls(
            success=False,
            data=None,
            error=ToolError(code=code, message=message, retryable=retryable, details=details or {}),
        )
