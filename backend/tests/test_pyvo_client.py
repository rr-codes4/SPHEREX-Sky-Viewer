from unittest.mock import Mock

from astronomy_backend.irsa import create_query
from astronomy_backend.pyvo_client import execute_sia2_search


def test_execute_sia2_search_passes_sia2_parameters() -> None:
    service = Mock()
    query = create_query(12.5, -4.25, 0.1, collection="example")

    execute_sia2_search(service, query, max_records=5)

    service.search.assert_called_once_with(
        pos=(12.5, -4.25, 0.1),
        collection="example",
        maxrec=5,
        res_format="VOTABLE",
    )
