import numpy as np

from c4search.models import Doc
from c4search.store import Store


def make_doc(t_start: float = 1.0, modality: str = "transcript") -> Doc:
    return Doc(
        video_id="video_1",
        t_start=t_start,
        t_end=t_start + 2.0,
        modality=modality,
        text="you have the right to remain silent",
        extra={"speaker": "officer"},
    )


def test_docs_roundtrip(tmp_path):
    store = Store(tmp_path)
    ids = store.add_docs([make_doc(1.0), make_doc(5.0, modality="caption")])
    assert len(ids) == 2

    rows = store.docs(video_id="video_1")
    assert [doc.t_start for _, doc in rows] == [1.0, 5.0]
    assert rows[0][1].extra == {"speaker": "officer"}

    only_captions = store.docs(modality="caption")
    assert len(only_captions) == 1


def test_delete_docs_is_scoped(tmp_path):
    store = Store(tmp_path)
    store.add_docs([make_doc(), make_doc(modality="caption")])
    store.delete_docs("video_1", "transcript")
    remaining = store.docs()
    assert [doc.modality for _, doc in remaining] == ["caption"]


def test_vectors_roundtrip(tmp_path):
    store = Store(tmp_path)
    ids = store.add_docs([make_doc(1.0), make_doc(3.0)])
    vectors = np.arange(8, dtype=np.float32).reshape(2, 4)
    store.save_vectors("frames", ids, vectors)

    loaded_ids, loaded_vectors = store.load_vectors("frames")
    assert loaded_ids.tolist() == ids
    assert np.array_equal(loaded_vectors, vectors)
