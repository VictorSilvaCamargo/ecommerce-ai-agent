import hashlib
import hmac
import time


def compute_hmac_signature(secret: str, raw_body: bytes, timestamp: str | None = None) -> str:
    """Calcula a assinatura HMAC-SHA256 canônica no formato `sha256=<hex>`."""
    key_bytes = secret.encode("utf-8")
    message_to_sign = f"{timestamp}.".encode() + raw_body if timestamp else raw_body
    digest = hmac.new(key_bytes, message_to_sign, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_webhook_hmac(
    secret: str,
    signature_header: str,
    raw_body: bytes,
    timestamp_header: str | None = None,
    max_age_seconds: int = 300,
) -> bool:
    """Verifica a assinatura HMAC-SHA256 em tempo constante (`hmac.compare_digest`) e protege contra Replay Attacks."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    if timestamp_header is not None:
        try:
            req_ts = int(timestamp_header)
        except ValueError:
            return False

        now_ts = int(time.time())
        if abs(now_ts - req_ts) > max_age_seconds:
            return False

        expected_with_ts = compute_hmac_signature(secret, raw_body, timestamp=timestamp_header)
        if hmac.compare_digest(signature_header, expected_with_ts):
            return True

    # Fallback para clientes de webhook que assinam diretamente o raw_body (ex: GitHub/Meta padrão)
    expected_plain = compute_hmac_signature(secret, raw_body, timestamp=None)
    return hmac.compare_digest(signature_header, expected_plain)
