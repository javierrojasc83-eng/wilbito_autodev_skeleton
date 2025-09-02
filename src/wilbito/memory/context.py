from typing import List, Dict, Any
from wilbito.memory.vectorstore import VectorStore

def retrieve_context(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    vs = VectorStore()
    hits = vs.search(query, top_k=top_k)
    return hits
