"""Estado de uma tentativa de previsão, independente da interface Streamlit."""


def new_attempt(customer: dict) -> dict:
    """Cada tentativa mantém somente os próprios eventos e medições."""
    return {
        "customer": customer.copy(),
        "phase": "running",
        "events": [],
        "history": [],
        "chromosome": None,
        "evaluated_subsets": 0,
        "search_started_at": None,
        "elapsed_seconds": None,
    }


def record_evaluation(attempt: dict, event: dict) -> None:
    """O contador de avaliações distintas vem do cache do algoritmo."""
    attempt["chromosome"] = tuple(int(bit) for bit in event["cromossomo"])
    attempt["evaluated_subsets"] = int(event["avaliados"])


def record_generation(attempt: dict, record: dict) -> None:
    attempt["history"].append(dict(record))


def start_search(attempt: dict, now: float) -> None:
    attempt["search_started_at"] = now
    attempt["elapsed_seconds"] = 0.0


def finish_search(attempt: dict, elapsed_seconds: float) -> None:
    attempt["elapsed_seconds"] = elapsed_seconds
    attempt["search_started_at"] = None


def fail_attempt(attempt: dict, now: float) -> None:
    """Congela apenas a medição da busca; falha anterior à busca não tem tempo."""
    started = attempt["search_started_at"]
    if started is not None:
        finish_search(attempt, max(0.0, now - started))
    attempt["phase"] = "failed"


def view_state(*, running: bool, customer: dict | None,
               last_success: dict | None, attempt: dict | None) -> str:
    """Deriva disponibilidade sem tratar uma previsão antiga como atual."""
    if running:
        return "running"
    if customer is None:
        return "invalid"
    if attempt is not None and attempt["phase"] == "failed":
        return "error"
    if last_success is None:
        return "idle"
    return "complete" if customer == last_success["customer"] else "stale"
