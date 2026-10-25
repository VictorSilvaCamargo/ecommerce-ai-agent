from __future__ import annotations

import hashlib
import hmac
import json
import time
from uuid import uuid4

from locust import HttpUser, between, task  # type: ignore[import-not-found]

API_KEY = "dev-secret-api-key-12345"
WEBHOOK_SECRET = "dev-webhook-secret-key"


class AtendenteIAUser(HttpUser):  # type: ignore[misc]
    """Simula tráfego concorrente B2C e B2B nas rotas de Tools, Webhooks e Observabilidade."""

    wait_time = between(0.1, 0.5)

    @task(3)
    def check_health(self) -> None:
        self.client.get("/health")

    @task(2)
    def fetch_tool_schemas(self) -> None:
        self.client.get("/tools/schemas")

    @task(4)
    def send_signed_webhook_message(self) -> None:
        ts = str(int(time.time()))
        msg_id = f"msg_locust_{uuid4().hex[:12]}"
        payload = {
            "message_id": msg_id,
            "thread_id": f"thr_{uuid4().hex[:8]}",
            "customer_document": "52998224725",
            "channel": "whatsapp",
            "text": "Olá, qual o status do meu pedido ord_b2c_recent?",
        }
        raw_body = json.dumps(payload).encode("utf-8")
        signed_payload = f"{ts}.".encode() + raw_body
        digest = hmac.new(
            WEBHOOK_SECRET.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()

        self.client.post(
            "/webhook/messages",
            data=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": f"sha256={digest}",
                "X-Webhook-Timestamp": ts,
            },
        )

    @task(1)
    def scrape_prometheus_metrics(self) -> None:
        self.client.get("/metrics")
