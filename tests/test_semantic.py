import hashlib

import numpy as np

from core import semantic


def test_embedding_cache_merges_updates_and_keeps_normalised_vectors(tmp_path, monkeypatch) -> None:
    path = tmp_path / "embeddings.npz"
    semantic._STORES.clear()
    monkeypatch.setattr(semantic, "_store_path", lambda model: path)
    monkeypatch.setattr(
        semantic.local_ai,
        "embed",
        lambda texts, model, **kwargs: [[float(len(text)), 1.0] for text in texts],
    )

    first = semantic.embed_cached(["uno"], model="test")
    external_key = hashlib.sha1("due".encode("utf-8")).hexdigest()
    semantic._save_store(path, {external_key: np.array([0.0, 1.0], dtype=np.float32)})
    semantic.embed_cached(["tre"], model="test")

    with np.load(path) as saved:
        assert len(saved.files) == 3
    assert np.isclose(np.linalg.norm(first[0]), 1.0)
