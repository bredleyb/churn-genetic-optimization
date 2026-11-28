"""Contratos puros da tentativa, do timer e da disponibilidade."""
from src.workflow_state import (
    fail_attempt, finish_search, new_attempt, record_evaluation,
    record_generation, start_search, view_state,
)


def test_attempt_isolated_from_snapshot_and_other_attempts():
    customer = {"tenure": 1}
    attempt = new_attempt(customer)
    second = new_attempt(customer)
    customer["tenure"] = 2
    assert attempt["customer"] == {"tenure": 1}
    attempt["events"].append("evento")
    assert second["events"] == []
    assert second["chromosome"] is None


def test_failure_before_search_has_no_elapsed_time():
    attempt = new_attempt({})
    fail_attempt(attempt, 100)
    assert attempt["elapsed_seconds"] is None
    assert attempt["phase"] == "failed"


def test_partial_search_preserves_real_candidate_count_and_history():
    attempt = new_attempt({})
    start_search(attempt, 10.0)
    event = {"cromossomo": (1, 0, 1), "avaliados": 3}
    record_evaluation(attempt, event)
    record_generation(attempt, {"geracao": 1, "melhor_f1_cv": 0.6})
    fail_attempt(attempt, 12.5)
    assert attempt["chromosome"] == (1, 0, 1)
    assert attempt["evaluated_subsets"] == 3
    assert len(attempt["history"]) == 1
    assert attempt["elapsed_seconds"] == 2.5
    assert attempt["search_started_at"] is None


def test_failure_after_search_does_not_change_search_time():
    attempt = new_attempt({})
    start_search(attempt, 10)
    finish_search(attempt, 2.7)
    fail_attempt(attempt, 80)
    assert attempt["elapsed_seconds"] == 2.7


def test_view_state_priorities_and_snapshot_recovery():
    customer = {"tenure": 1}
    last = {"customer": customer.copy()}
    attempt = new_attempt(customer)
    def state(current=customer, success=last, running=False, current_attempt=None):
        return view_state(running=running, customer=current,
                          last_success=success, attempt=current_attempt)
    assert state(success=None) == "idle"
    assert state(running=True) == "running"
    assert state() == "complete"
    assert state({"tenure": 2}) == "stale"
    assert state(None) == "invalid"
    assert state() == "complete"
    fail_attempt(attempt, 1)
    assert state(current_attempt=attempt) == "error"
    assert state(None, current_attempt=attempt) == "invalid"
