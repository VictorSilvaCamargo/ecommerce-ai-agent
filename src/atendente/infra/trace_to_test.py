from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from atendente.infra.observability import TraceRecord


def convert_trace_to_eval_case(
    trace: TraceRecord,
    dataset_path: Path | None = None,
) -> dict[str, Any]:
    """Converte um TraceRecord (ex.: com feedback negativo ou anomalia) em caso de teste de regressão."""
    first_tool = trace.tool_calls[0] if trace.tool_calls else {}
    expected_tool = first_tool.get("tool_name") if first_tool else None
    expected_args = first_tool.get("args", {}) if first_tool else {}

    eval_case: dict[str, Any] = {
        "case_id": f"trace_{trace.trace_id}",
        "source_trace_id": trace.trace_id,
        "segment": trace.segment or "B2C",
        "user_message": trace.user_message,
        "expected_intent": trace.intent or "duvida_geral",
        "expected_tool": expected_tool,
        "expected_args": expected_args,
        "requires_confirmation": trace.requires_confirmation,
        "expected_handoff": trace.handoff_triggered,
        "expected_abstention": trace.abstained,
        "reference_answer": trace.assistant_response,
        "prompt_version_captured": trace.prompt_version,
        "feedback_score": trace.feedback_score,
        "feedback_comment": trace.feedback_comment,
    }

    if dataset_path is not None:
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        existing: list[dict[str, Any]] = []
        if dataset_path.exists():
            raw_text = dataset_path.read_text(encoding="utf-8").strip()
            if raw_text:
                existing = json.loads(raw_text)

        updated = False
        for idx, item in enumerate(existing):
            if item.get("case_id") == eval_case["case_id"]:
                existing[idx] = eval_case
                updated = True
                break
        if not updated:
            existing.append(eval_case)

        dataset_path.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return eval_case


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Converte um trace_id em caso de teste na suite de evals."
    )
    parser.add_argument("--trace-id", required=True, help="ID do trace a converter")
    parser.add_argument(
        "--dataset",
        default="evals/datasets/regression_from_traces.json",
        help="Caminho do arquivo JSON de regressao",
    )
    args = parser.parse_args()

    sample_trace = TraceRecord(
        trace_id=args.trace_id,
        thread_id=f"thr-{args.trace_id}",
        entry_point="cli_trace_to_test",
        prompt_version="v3.0.0",
        segment="B2C",
        intent="consultar_pedido",
        user_message=f"Consulta capturada do trace {args.trace_id} para o pedido PED-1001",
        assistant_response="Seu pedido PED-1001 esta com status DELIVERED.",
        tool_calls=[
            {
                "tool_name": "consultar_pedido",
                "args": {"order_id": "PED-1001"},
                "status": "success",
            }
        ],
    )
    case = convert_trace_to_eval_case(sample_trace, Path(args.dataset))
    print(f"Trace {args.trace_id} convertido com sucesso em {args.dataset}: {case['case_id']}")


if __name__ == "__main__":
    main()
