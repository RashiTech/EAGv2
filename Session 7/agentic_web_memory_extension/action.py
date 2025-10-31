import re
from collections import Counter
from typing import Dict, List, Tuple

from memory import MemoryStore
from utils.embedding_store import EmbeddingStore
from utils.llm_interface import LLMInterface



class Actions:
    def __init__(self, data_dir: str) -> None:
        self.memory = MemoryStore(data_dir)
        self.llm = LLMInterface()
        self.store = EmbeddingStore(data_dir)

    def store_page(self, url: str, text: str) -> Dict:
        chunks = self.chunk_text(text)
        vectors = [self.llm.embed_text(c) for c in chunks]
        metas = [{"url": url, "chunk": c} for c in chunks]
        self.store.add(vectors, metas)
        summary = self.llm.summarize(text)
        self.memory.add_page(url, summary)
        return {"status": "ok", "chunks": len(chunks)}
    
    def chunk_text(self,text: str, max_tokens: int = 800) -> List[str]:
        """Naive chunker by sentences to ~max_tokens words per chunk."""
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks: List[str] = []
        cur: List[str] = []
        count = 0
        for s in sentences:
            words = s.split()
            if count + len(words) > max_tokens and cur:
                chunks.append(" ".join(cur))
                cur = []
                count = 0
            cur.append(s)
            count += len(words)
        if cur:
            chunks.append(" ".join(cur))
        return chunks or [text]


    def extract_highlight_phrases(self,query: str, matched_text: str, top_n: int = 5) -> List[str]:
        """Simple keyword-based phrases to highlight from the matched text."""
        tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9]{3,}", query)]
        counts = Counter(tokens)
        key_terms = [w for w, _ in counts.most_common(8)]
        highlights: List[str] = []
        for term in key_terms:
            pattern = re.compile(rf"(.{{0,40}}\b{re.escape(term)}\b.{{0,40}})", re.IGNORECASE)
            m = pattern.search(matched_text)
            if m:
                highlights.append(m.group(1))
            if len(highlights) >= top_n:
                break
        return highlights or key_terms[:top_n]



    def find_relevant_page(self, query: str, top_k: int = 5) -> Dict:
        print(f"Searching for query: {query}")
        qv = self.llm.embed_text(query)
        results: List[Tuple[float, Dict[str, str]]] = self.store.search(qv, top_k=top_k)
        
        if not results:
            print("No results found")
            return {"status": "empty", "url": None, "highlights": []}
            
        # Filter out low-quality matches and duplicates
        filtered_results = []
        seen_urls = set()
        for score, meta in results:
            url = meta["url"]
            # Skip duplicates and search result pages
            if (url in seen_urls or 
                "google.com/search" in url or 
                "search?" in url):
                continue
            seen_urls.add(url)
            filtered_results.append((score, meta))
            
        if not filtered_results:
            print("No valid results after filtering")
            return {"status": "empty", "url": None, "highlights": []}
            
        best_score, best_meta = filtered_results[0]
        url = best_meta["url"]
        matched_text = best_meta["chunk"]
        highlights = self.extract_highlight_phrases(query, matched_text)
        
        print(f"Best match: {url} with score {best_score}")
        return {
            "status": "ok",
            "url": url,
            "score": best_score,
            "highlights": highlights,
            "matchedText": matched_text,
        }


