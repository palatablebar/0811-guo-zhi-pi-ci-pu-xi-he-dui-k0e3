import json

import pytest
from conftest import csv_data

from app.business import DomainIssue
from app.evidence.render import artifact
from app.modules.pipeline import run
from app.review.service import execute, review


def shared_rows(draw_a=60, draw_b=60, stock_a=80, stock_b=80, extra=None):
    rows = [
        ["000101", "0001", "stock", "1", "0", str(stock_a), "原料批入库"],
        ["000102", "0001", "blend", "10", "0", str(draw_a), "果汁批次一"],
        ["000103", "0001", "feed", "10", "1", str(draw_a), "领用原料批"],
        ["000104", "0001", "check", "10", "0", str(draw_a), "批次一检验"],
        ["000201", "0002", "stock", "1", "0", str(stock_b), "同一原料批入库"],
        ["000202", "0002", "blend", "20", "0", str(draw_b), "果汁批次二"],
        ["000203", "0002", "feed", "20", "1", str(draw_b), "领用同一原料批"],
        ["000204", "0002", "check", "20", "0", str(draw_b), "批次二检验"],
    ]
    return csv_data(rows + (extra or []))


@pytest.fixture
def shared():
    return shared_rows()


def test_joint_overdraw_blocks_every_involved_batch(shared):
    result = run(shared)
    assert [case["status"] for case in result["cases"]] == ["READY", "READY"]
    balance = result["balance"]
    assert balance["blocked"] == ["0001", "0002"] and not balance["releasable"]
    (row,) = balance["shared"]
    assert row["material"] == "1" and row["over"] is True
    assert (row["available"], row["consumed"], row["surplus"]) == (80, 120, -40)
    assert row["cases"] == ["0001", "0002"]


def test_joint_draw_within_quota_stays_releasable():
    result = run(shared_rows(draw_a=30, draw_b=40))
    balance = result["balance"]
    assert balance["blocked"] == [] and balance["releasable"] is True
    (row,) = balance["shared"]
    assert (row["available"], row["consumed"], row["over"]) == (80, 70, False)


def test_available_quota_takes_largest_declaration():
    result = run(shared_rows(draw_a=30, draw_b=40, stock_b=50))
    (row,) = result["balance"]["shared"]
    assert row["available"] == 80 and row["consumed"] == 70 and not row["over"]


def test_uninvolved_batch_is_not_blocked():
    extra = [
        ["000301", "0003", "stock", "2", "0", "30", "另一原料批"],
        ["000302", "0003", "blend", "30", "0", "20", "果汁批次三"],
        ["000303", "0003", "feed", "30", "2", "20", "领用另一原料批"],
        ["000304", "0003", "check", "30", "0", "20", "批次三检验"],
    ]
    result = run(shared_rows(extra=extra))
    balance = result["balance"]
    assert balance["blocked"] == ["0001", "0002"]
    by_material = {row["material"]: row for row in balance["shared"]}
    assert by_material["2"]["cases"] == ["0003"] and not by_material["2"]["over"]


def test_rejected_case_draws_are_not_counted():
    extra = [
        ["000301", "0003", "blend", "30", "0", "20", "循环投料一"],
        ["000302", "0003", "blend", "31", "0", "20", "循环投料二"],
        ["000303", "0003", "feed", "30", "31", "20", "循环边一"],
        ["000304", "0003", "feed", "31", "30", "20", "循环边二"],
        ["000305", "0003", "check", "30", "0", "20", "循环检验"],
    ]
    result = run(shared_rows(draw_a=30, draw_b=40, extra=extra))
    case3 = next(case for case in result["cases"] if case["case"] == "0003")
    assert case3["status"] == "BLEND_CYCLE" and "measure" not in case3
    (row,) = result["balance"]["shared"]
    assert row["consumed"] == 70 and row["cases"] == ["0001", "0002"]


def test_overdrawn_run_stays_held_for_review(store, shared):
    batch = execute(store, shared)
    with pytest.raises(DomainIssue, match="UNRESOLVED_ISSUES"):
        review(store, batch["id"], dict(revision=0, status="APPROVED", note="尝试签发"))
    current = store.load(batch["id"])
    assert current["status"] == "PENDING" and current["revision"] == 0


def test_identical_rerun_never_double_counts(store, shared):
    first = execute(store, shared)
    second = execute(store, shared)
    assert first["id"] == second["id"] and len(store.list()) == 1
    (row,) = first["report"]["balance"]["shared"]
    assert row["consumed"] == 120 and row["available"] == 80


def test_approved_batch_keeps_frozen_verdict_after_source_update(store, clean, shared):
    approved = execute(store, clean)
    review(store, approved["id"], dict(revision=0, status="APPROVED", note="复核通过"))
    frozen = artifact(store.load(approved["id"]))
    updated = execute(store, shared)
    assert updated["id"] != approved["id"]
    after = store.load(approved["id"])
    assert after["status"] == "APPROVED" and artifact(after) == frozen
    assert after["report"]["balance"]["releasable"] is True
    assert store.load(updated["id"])["report"]["balance"]["blocked"] == ["0001", "0002"]


def test_old_and_current_basis_remain_traceable(store, clean, shared):
    from app.config import RULE_VERSION

    older = execute(store, clean)
    newer = execute(store, shared)
    history = {item["id"] for item in store.list()}
    assert {older["id"], newer["id"]} <= history
    for batch_id, source in ((older["id"], clean), (newer["id"], shared)):
        manifest = store.load(batch_id)["report"]["manifest"]
        assert manifest["version"] == RULE_VERSION
        import hashlib

        assert manifest["sha256"] == hashlib.sha256(source).hexdigest()


def test_evidence_exports_shared_occupancy(store, shared):
    packet = json.loads(artifact(execute(store, shared)))
    (row,) = packet["balance"]["shared"]
    assert row["material"] == "1" and row["over"] is True
    assert packet["balance"]["blocked"] == ["0001", "0002"]


def test_balance_stage_response_exposes_shared_verdict(client):
    response = client.post("/api/stages/balance", data={"sample": "shared"})
    assert response.status_code == 200
    balance = response.json["balance"]
    assert balance["blocked"] == ["0001", "0002"] and not balance["releasable"]
    assert balance["shared"][0]["cases"] == ["0001", "0002"]


def test_shared_sample_is_downloadable(client):
    response = client.get("/examples/shared")
    assert response.status_code == 200 and b"000201" in response.data
