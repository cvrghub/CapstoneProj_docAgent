"""Vendor name semantic matching using ChromaDB + rapidfuzz."""

from __future__ import annotations

from typing import Optional

import chromadb
from chromadb.utils import embedding_functions
from rapidfuzz import fuzz, process

from config import CHROMA_PERSIST_DIR, FUZZY_VENDOR_THRESHOLD, VENDOR_COLLECTION


class VendorMatcher:
    def __init__(self):
        self._client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        self._ef = embedding_functions.DefaultEmbeddingFunction()
        self._collection = self._client.get_or_create_collection(
            name=VENDOR_COLLECTION,
            embedding_function=self._ef,
        )

    def add_vendors(self, vendors: list[str]) -> None:
        existing = set(self._collection.get()["documents"] or [])
        new = [v for v in vendors if v not in existing]
        if new:
            self._collection.add(
                documents=new,
                ids=[f"vendor_{i}" for i in range(len(existing), len(existing) + len(new))],
            )

    def match(self, vendor_name: str, top_k: int = 3) -> Optional[str]:
        """Return best matched vendor or None if below threshold."""
        if self._collection.count() == 0:
            return vendor_name  # no reference data yet

        results = self._collection.query(query_texts=[vendor_name], n_results=min(top_k, self._collection.count()))
        candidates = results["documents"][0] if results["documents"] else []

        if not candidates:
            return None

        best, score, _ = process.extractOne(vendor_name, candidates, scorer=fuzz.token_sort_ratio)
        return best if score >= FUZZY_VENDOR_THRESHOLD else None

    def is_known_vendor(self, vendor_name: str) -> tuple[bool, Optional[str]]:
        matched = self.match(vendor_name)
        return (matched is not None), matched
