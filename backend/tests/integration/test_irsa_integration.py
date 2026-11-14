import os

import pytest

from astronomy_backend.irsa import IRSAClient, create_query


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_IRSA_INTEGRATION") != "1",
    reason="Set RUN_IRSA_INTEGRATION=1 to contact the live IRSA service.",
)
def test_live_irsa_query_returns_structured_results() -> None:
    result = IRSAClient(timeout_seconds=30).search(
        create_query(269.45208, 4.69339, 0.1, collection="spherex_dr1"),
        max_records=1,
    )

    assert isinstance(result, list)
