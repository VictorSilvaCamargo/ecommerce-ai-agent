from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from atendente.domain.models import ContractSLA, Customer, Invoice, Order, RefundRequest, Ticket
from atendente.infra.audit import AuditRepository, InMemoryAuditRepository, MongoAuditRepository
from atendente.infra.config import settings
from atendente.infra.db.database import DatabaseManager
from atendente.infra.db.repositories import (
    ContractRepository,
    CustomerRepository,
    InvoiceRepository,
    OrderRepository,
    RefundRepository,
    TicketRepository,
)
from atendente.tools.base import ToolResult
from atendente.tools.schemas import get_tool_definitions
from atendente.tools.service import (
    AbrirChamadoInput,
    BuscarBaseConhecimentoInput,
    ConsultarContratoSLAInput,
    ConsultarFaturaInput,
    ConsultarPedidoInput,
    IdentificarClienteInput,
    NovaLojaToolsService,
    SolicitarReembolsoInput,
    TransferirParaHumanoInput,
)
from atendente.workers.idempotency import IdempotencyStore, InMemoryIdempotencyStore
from atendente.workers.security import verify_webhook_hmac
from atendente.workers.tasks import (
    DLQEntry,
    DLQStore,
    InMemoryDLQStore,
    WebhookMessagePayload,
)

# Gerenciadores globais de infraestrutura
db_manager = DatabaseManager(settings.database_url)
audit_repository: AuditRepository = InMemoryAuditRepository()
idempotency_store: IdempotencyStore = InMemoryIdempotencyStore()
dlq_store: DLQStore = InMemoryDLQStore()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global audit_repository
    # Inicialização opcional do MongoDB se configurado e acessível
    try:
        if settings.mongodb_uri and "mongodb" in settings.mongodb_uri:
            audit_repository = MongoAuditRepository(settings.mongodb_uri, settings.mongodb_database)
    except Exception:
        audit_repository = InMemoryAuditRepository()
    yield
    await db_manager.engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API de Atendimento Inteligente da NovaLoja com Tools e Function Calling padronizado.",
    lifespan=lifespan,
)


# --- Tratamento Padronizado de Erros ---


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Parâmetros de entrada inválidos na requisição.",
                "retryable": True,
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
                "retryable": exc.status_code in (408, 429, 502, 503, 504),
                "details": {},
            }
        },
    )


# --- Dependências de Autenticação e Serviços ---


async def verify_api_key(
    x_api_key: str = Header(..., description="Chave de API secreta para acesso aos endpoints"),
) -> str:
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida ou não informada.",
        )
    return x_api_key


async def get_tools_service(
    session: AsyncSession = Depends(db_manager.get_session),
) -> NovaLojaToolsService:
    return NovaLojaToolsService(
        customer_repo=CustomerRepository(session),
        order_repo=OrderRepository(session),
        refund_repo=RefundRepository(session),
        ticket_repo=TicketRepository(session),
        contract_repo=ContractRepository(session),
        invoice_repo=InvoiceRepository(session),
        audit_repo=audit_repository,
    )


# --- Rotas Básicas e Metadados ---


@app.get("/health", tags=["Sistema"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


@app.get("/tools/schemas", tags=["Tools"])
async def list_tool_schemas() -> list[dict[str, Any]]:
    """Exporta os esquemas canônicos de function calling das 8 Tools."""
    return get_tool_definitions()


# --- Endpoints REST das 8 Tools ---


@app.post(
    "/tools/identificar-cliente",
    response_model=ToolResult[Customer],
    tags=["Tools"],
    dependencies=[Depends(verify_api_key)],
)
async def api_identificar_cliente(
    payload: IdentificarClienteInput, service: NovaLojaToolsService = Depends(get_tools_service)
) -> ToolResult[Customer]:
    return await service.identificar_cliente(payload)


@app.post(
    "/tools/consultar-pedido",
    response_model=ToolResult[Order],
    tags=["Tools"],
    dependencies=[Depends(verify_api_key)],
)
async def api_consultar_pedido(
    payload: ConsultarPedidoInput, service: NovaLojaToolsService = Depends(get_tools_service)
) -> ToolResult[Order]:
    return await service.consultar_pedido(payload)


@app.post(
    "/tools/solicitar-reembolso",
    response_model=ToolResult[RefundRequest],
    tags=["Tools"],
    dependencies=[Depends(verify_api_key)],
)
async def api_solicitar_reembolso(
    payload: SolicitarReembolsoInput, service: NovaLojaToolsService = Depends(get_tools_service)
) -> ToolResult[RefundRequest]:
    return await service.solicitar_reembolso(payload)


@app.post(
    "/tools/abrir-chamado",
    response_model=ToolResult[Ticket],
    tags=["Tools"],
    dependencies=[Depends(verify_api_key)],
)
async def api_abrir_chamado(
    payload: AbrirChamadoInput, service: NovaLojaToolsService = Depends(get_tools_service)
) -> ToolResult[Ticket]:
    return await service.abrir_chamado(payload)


@app.post(
    "/tools/consultar-contrato-sla",
    response_model=ToolResult[ContractSLA],
    tags=["Tools"],
    dependencies=[Depends(verify_api_key)],
)
async def api_consultar_contrato_sla(
    payload: ConsultarContratoSLAInput, service: NovaLojaToolsService = Depends(get_tools_service)
) -> ToolResult[ContractSLA]:
    return await service.consultar_contrato_sla(payload)


@app.post(
    "/tools/consultar-fatura",
    response_model=ToolResult[list[Invoice]],
    tags=["Tools"],
    dependencies=[Depends(verify_api_key)],
)
async def api_consultar_fatura(
    payload: ConsultarFaturaInput, service: NovaLojaToolsService = Depends(get_tools_service)
) -> ToolResult[list[Invoice]]:
    return await service.consultar_fatura(payload)


@app.post(
    "/tools/buscar-base-conhecimento",
    response_model=ToolResult[list[dict[str, Any]]],
    tags=["Tools"],
    dependencies=[Depends(verify_api_key)],
)
async def api_buscar_base_conhecimento(
    payload: BuscarBaseConhecimentoInput, service: NovaLojaToolsService = Depends(get_tools_service)
) -> ToolResult[list[dict[str, Any]]]:
    return await service.buscar_base_conhecimento(payload)


@app.post(
    "/tools/transferir-para-humano",
    response_model=ToolResult[dict[str, Any]],
    tags=["Tools"],
    dependencies=[Depends(verify_api_key)],
)
async def api_transferir_para_humano(
    payload: TransferirParaHumanoInput, service: NovaLojaToolsService = Depends(get_tools_service)
) -> ToolResult[dict[str, Any]]:
    return await service.transferir_para_humano(payload)


# --- Endpoints de Webhooks Assíncronos e DLQ (Fase 4) ---


@app.post("/webhook/messages", tags=["Webhooks"])
async def receive_webhook_message(
    request: Request,
    x_hub_signature_256: str = Header(
        default="", description="Assinatura HMAC-SHA256 no formato sha256=<hex>"
    ),
    x_webhook_timestamp: str | None = Header(
        default=None, description="Timestamp Unix da emissão do evento para proteção anti-replay"
    ),
) -> JSONResponse:
    raw_body = await request.body()

    if not verify_webhook_hmac(
        secret=settings.webhook_secret,
        signature_header=x_hub_signature_256,
        raw_body=raw_body,
        timestamp_header=x_webhook_timestamp,
        max_age_seconds=300,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura HMAC inválida ou timestamp expirado (proteção anti-replay).",
        )

    payload = WebhookMessagePayload.model_validate_json(raw_body)

    acquired = await idempotency_store.check_and_lock(payload.message_id, ttl_seconds=86400)
    if not acquired:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "duplicate_ignored",
                "message_id": payload.message_id,
                "thread_id": payload.thread_id,
            },
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "status": "queued",
            "message_id": payload.message_id,
            "thread_id": payload.thread_id,
        },
    )


@app.get(
    "/webhook/dlq",
    response_model=list[DLQEntry],
    tags=["Webhooks"],
    dependencies=[Depends(verify_api_key)],
)
async def inspect_dlq_messages() -> list[DLQEntry]:
    """Lista mensagens irrecuperáveis encaminhadas para a Dead Letter Queue."""
    return await dlq_store.list_entries()
