import json
from pathlib import Path

from atendente.infra.observability import TraceRecord
from atendente.infra.trace_to_test import convert_trace_to_eval_case
from atendente.rag.monitor import RetrievalMonitor


def test_retrieval_monitor_detects_zero_results_low_relevance_and_orphan_chunks() -> None:
    all_chunk_ids = ["chk-01", "chk-02", "chk-03", "chk-04"]
    monitor = RetrievalMonitor(registered_chunk_ids=all_chunk_ids, low_relevance_threshold=0.45)

    # Query 1: boa relevância, recupera chk-01 e chk-02
    monitor.record_query(
        query="Qual o prazo de devolução B2C?",
        segment="B2C",
        retrieved_chunk_ids=["chk-01", "chk-02"],
        top_score=0.88,
        abstained=False,
    )
    # Query 2: baixa relevância, recupera chk-03
    monitor.record_query(
        query="Desconto especial black friday",
        segment="B2C",
        retrieved_chunk_ids=["chk-03"],
        top_score=0.35,
        abstained=False,
    )
    # Query 3: zero resultados / abstenção
    monitor.record_query(
        query="Receita de lasanha",
        segment="B2C",
        retrieved_chunk_ids=[],
        top_score=0.10,
        abstained=True,
    )

    report = monitor.generate_report()
    assert report.total_queries == 3
    assert report.zero_result_queries == ["Receita de lasanha"]
    assert report.low_relevance_queries == ["Desconto especial black friday"]
    assert report.orphan_chunk_ids == ["chk-04"]
    assert len(report.tuning_recommendations) >= 2


def test_convert_trace_to_eval_case_appends_to_dataset(tmp_path: Path) -> None:
    dataset_file = tmp_path / "eval_cases.json"
    dataset_file.write_text("[]", encoding="utf-8")

    trace = TraceRecord(
        trace_id="trc-bug-99",
        thread_id="thr-bug-99",
        entry_point="webhook",
        prompt_version="v3.0.0",
        prompt_hash="hash-v3",
        segment="B2C",
        intent="solicitar_reembolso",
        user_message="Quero estornar o pedido PED-1001 por defeito",
        assistant_response="Para confirmar o estorno do pedido PED-1001, digite CONFIRMO.",
        latency_ms=35.0,
        prompt_tokens=250,
        completion_tokens=40,
        cost_usd=0.001,
        retrieved_chunks=[{"chunk_id": "chk-01", "source": "politica_reembolso.md", "score": 0.90}],
        tool_calls=[
            {
                "tool_name": "solicitar_reembolso",
                "args": {"order_id": "PED-1001", "motivo": "defeito"},
                "status": "pending_confirmation",
            }
        ],
        requires_confirmation=True,
        feedback_score=-1,
        feedback_comment="O cliente achou confuso",
    )

    eval_case = convert_trace_to_eval_case(trace, dataset_path=dataset_file)
    assert eval_case["case_id"] == "trace_trc-bug-99"
    assert eval_case["expected_intent"] == "solicitar_reembolso"
    assert eval_case["expected_tool"] == "solicitar_reembolso"
    assert eval_case["requires_confirmation"] is True

    saved_cases = json.loads(dataset_file.read_text(encoding="utf-8"))
    assert len(saved_cases) == 1
    assert saved_cases[0]["case_id"] == "trace_trc-bug-99"

    # Idempotência: converter o mesmo trace novamente atualiza sem duplicar
    convert_trace_to_eval_case(trace, dataset_path=dataset_file)
    saved_cases_after = json.loads(dataset_file.read_text(encoding="utf-8"))
    assert len(saved_cases_after) == 1
