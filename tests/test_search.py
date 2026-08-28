from c4search.models import Doc
from c4search.search.fuse import rrf
from c4search.search.retrieve import Retrievers
from c4search.store import Store


def test_rrf_prefers_docs_ranked_well_everywhere():
    fused = rrf({"a": [1, 2, 3], "b": [2, 1, 4]}, k=60)
    order = [doc_id for doc_id, _ in fused]
    assert order[0] in (1, 2) and set(order[:2]) == {1, 2}
    assert order[2] == 3 or order[2] == 4


def test_bm25_finds_the_matching_doc(tmp_path):
    store = Store(tmp_path)
    store.add_docs([
        Doc("v", 0.0, 2.0, "transcript", "roll down your window please"),
        Doc("v", 5.0, 7.0, "transcript", "put your hands behind your back"),
        Doc("v", 9.0, 9.0, "frame", "", {"frame": "000001.jpg"}),
    ])
    retrievers = Retrievers(store, {})
    hits = retrievers.bm25("hands behind back", k=2)
    top = store.get_docs(hits[:1])[hits[0]]
    assert "hands behind" in top.text


def test_frame_docs_are_excluded_from_text_lists(tmp_path):
    store = Store(tmp_path)
    store.add_docs([Doc("v", 0.0, 0.0, "frame", "should not be searched")])
    retrievers = Retrievers(store, {})
    assert retrievers.texts == []
