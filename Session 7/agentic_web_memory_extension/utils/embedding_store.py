import json
import os
from typing import Dict, List, Tuple

import faiss  # type: ignore
import numpy as np


class EmbeddingStore:
    """FAISS-backed vector store that persists to disk.

    Each vector id maps to metadata: {"url": str, "chunk": str} stored in a sidecar JSON.
    """

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.index_path = os.path.join(self.data_dir, "embeddings.index")
        self.meta_path = os.path.join(self.data_dir, "embeddings_meta.json")
        self.index = None  # type: ignore
        self.metadata: Dict[int, Dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
            except Exception:
                # If there's any error loading the index, start fresh
                print("Warning: Could not load existing index, creating new one")
                os.remove(self.index_path)
                self.index = None
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self.metadata = {int(k): v for k, v in raw.items()}

    def _save(self) -> None:
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def _ensure_index(self, dim: int) -> None:
        if self.index is None:
            # Use inner product with normalized vectors -> cosine similarity
            # Wrap IndexFlatIP in IndexIDMap to support add_with_ids
            base_index = faiss.IndexFlatIP(dim)
            self.index = faiss.IndexIDMap(base_index)

    @staticmethod
    def _normalize(vecs: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
        return vecs / norms

    def add(self, vectors: List[List[float]], metadatas: List[Dict[str, str]]) -> List[int]:
        arr = np.array(vectors, dtype=np.float32)
        arr = self._normalize(arr)
        
        # Check if we need to recreate the index due to dimension mismatch
        if self.index is not None and self.index.d != arr.shape[1]:
            print(f"Warning: Vector dimension changed from {self.index.d} to {arr.shape[1]}, recreating index")
            self.index = None
            if os.path.exists(self.index_path):
                os.remove(self.index_path)
        
        self._ensure_index(arr.shape[1])
        start_id = len(self.metadata)
        ids = list(range(start_id, start_id + arr.shape[0]))
        id_array = np.array(ids, dtype=np.int64)
        self.index.add_with_ids(arr, id_array)
        for i, meta in zip(ids, metadatas):
            self.metadata[i] = meta
        self._save()
        return ids

    def search(self, vector: List[float], top_k: int = 5) -> List[Tuple[float, Dict[str, str]]]:
        if self.index is None:
            return []
            
        # Print total number of vectors in index for debugging
        print(f"Total vectors in index: {self.index.ntotal}")
        print(f"Current metadata keys: {list(self.metadata.keys())}")
        
        arr = np.array([vector], dtype=np.float32)
        arr = self._normalize(arr)
        scores, ids = self.index.search(arr, top_k)
        
        # Print raw search results for debugging
        print(f"Raw search scores: {scores[0]}")
        print(f"Raw search IDs: {ids[0]}")
        
        results: List[Tuple[float, Dict[str, str]]] = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            meta = self.metadata.get(int(idx))
            if not meta:
                print(f"Warning: No metadata found for index {idx}")
                continue
                
            # Only include results with high enough similarity
            if score < 0.5:  # Minimum similarity threshold
                print(f"Skipping result with low score: {score}")
                continue
                
            results.append((float(score), meta))
            
        # Print final results for debugging
        print(f"Final results: {[(score, meta['url']) for score, meta in results]}")
        return results


