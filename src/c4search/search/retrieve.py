"""Recall-oriented first-stage retrievers.

Four cheap lists per query: BM25 and dense embeddings over every text-bearing
Doc, SigLIP text-to-frame similarity, and CLAP text-to-audio similarity.
Precision comes later (rerank, verify) - these only have to not miss.
"""

from c4search.store import Store

TEXT_FREE_MODALITIES = {"frame", "audio_window"}  # searched via vectors instead

# Loaded models survive across queries in one process; an eval sweep must not
# pay from_pretrained once per query.
_MODELS: dict[str, object] = {}


def cached(key: str, loader):
    if key not in _MODELS:
        _MODELS[key] = loader()
    return _MODELS[key]


class Retrievers:
    def __init__(self, store: Store, config: dict):
        self.store = store
        self.config = config
        # An explicit modality allow-list makes ablation rungs pure config:
        # transcript-only search is `modalities: [transcript]`, nothing else.
        allowed = config.get("modalities")
        rows = [
            (doc_id, doc) for doc_id, doc in store.docs()
            if doc.text and doc.modality not in TEXT_FREE_MODALITIES
            and (allowed is None or doc.modality in allowed)
        ]
        self.text_ids = [doc_id for doc_id, _ in rows]
        self.texts = [doc.text for _, doc in rows]
        self._bm25 = None

    def bm25(self, query: str, k: int) -> list[int]:
        import bm25s

        if self._bm25 is None:
            self._bm25 = bm25s.BM25()
            self._bm25.index(bm25s.tokenize(self.texts, show_progress=False))
        hits, _scores = self._bm25.retrieve(
            bm25s.tokenize(query, show_progress=False),
            k=min(k, len(self.texts)), show_progress=False,
        )
        return [self.text_ids[index] for index in hits[0]]

    def dense_text(self, query: str, k: int) -> list[int]:
        from sentence_transformers import SentenceTransformer

        model_id = self.config.get("text_model", "BAAI/bge-small-en-v1.5")
        model = cached(f"st:{model_id}", lambda: SentenceTransformer(model_id))
        query_vector = model.encode(
            query, normalize_embeddings=True, show_progress_bar=False)
        return self._vector_hits(".text", query_vector, k)

    def frames(self, query: str, k: int) -> list[int]:
        import torch
        from transformers import AutoModel, AutoProcessor

        model_id = self.config.get("frame_model", "google/siglip2-base-patch16-256")
        model = cached(f"hf:{model_id}",
                       lambda: AutoModel.from_pretrained(model_id).eval())
        processor = cached(f"hfp:{model_id}",
                           lambda: AutoProcessor.from_pretrained(model_id))
        with torch.no_grad():
            inputs = processor(text=[query], padding="max_length", return_tensors="pt")
            features = model.get_text_features(**inputs)
            features = features if torch.is_tensor(features) else features.pooler_output
            query_vector = torch.nn.functional.normalize(features, dim=-1).numpy()[0]
        return self._vector_hits(".frames", query_vector, k)

    def audio(self, query: str, k: int) -> list[int]:
        import torch
        from transformers import ClapModel, ClapProcessor

        model_id = self.config.get("audio_model", "laion/clap-htsat-unfused")
        model = cached(f"clap:{model_id}",
                       lambda: ClapModel.from_pretrained(model_id).eval())
        processor = cached(f"clapp:{model_id}",
                           lambda: ClapProcessor.from_pretrained(model_id))
        with torch.no_grad():
            inputs = processor(text=[query], return_tensors="pt", padding=True)
            features = model.get_text_features(**inputs)
            features = features if torch.is_tensor(features) else features.pooler_output
            query_vector = torch.nn.functional.normalize(features, dim=-1).numpy()[0]
        return self._vector_hits(".audio_events", query_vector, k)

    def _vector_hits(self, suffix: str, query_vector, k: int) -> list[int]:
        """Brute-force cosine over every stored vector set with this suffix."""
        import numpy as np

        scored = []
        for name in self.store.vector_names():
            if not name.endswith(suffix):
                continue
            ids, vectors = self.store.load_vectors(name)
            scores = vectors @ query_vector
            for index in np.argsort(-scores)[:k]:
                scored.append((float(scores[index]), int(ids[index])))
        scored.sort(reverse=True)
        return [doc_id for _, doc_id in scored[:k]]
