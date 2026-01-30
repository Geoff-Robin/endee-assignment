import os
from typing import List, Any
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from endee import Endee

load_dotenv()

class EndeeRetriever(BaseRetriever):
    """Retriever for Endee Vector Store."""
    
    index_name: str = "codebase"
    top_k: int = 5
    client: Any = None
    embeddings: Any = None
    
    def __init__(self, index_name: str = "codebase", top_k: int = 5, **kwargs: Any):
        super().__init__(**kwargs)
        self.index_name = index_name
        self.top_k = top_k
        self.client = Endee()
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )

    def search(self, query: str, filters: dict = None) -> List[Document]:
        """
        Public method to search with optional filters.
        """
        return self._search_internal(query, filters)

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        """Get documents relevant to the query (standard interface)."""
        return self._search_internal(query)

    def _search_internal(self, query: str, filters: dict = None) -> List[Document]:
        """Internal search logic."""
        try:
            embedding = self.embeddings.embed_query(query)
            
            index = self.client.get_index(self.index_name)
            if not index:
                print(f"Warning: Index '{self.index_name}' not found.")
                return []
                
            search_args = {
                "query": embedding, 
                "top_k": self.top_k
            }
            if filters:
                search_args["filter"] = filters

            results = index.search(**search_args)
            
            documents = []
            for match in results:
                if isinstance(match, dict):
                    meta = match.get("meta", {})
                    content = meta.get("code", "")
                    score = match.get("score", 0.0)
                    metadata = {k: v for k, v in meta.items() if k != "code"}
                    metadata["score"] = score
                else:
                    meta = getattr(match, "meta", {})
                    if isinstance(meta, dict):
                         content = meta.get("code", "")
                    else:
                         content = getattr(meta, "code", "")
                         try:
                             meta = vars(meta)
                         except:
                             meta = {}

                    score = getattr(match, "score", 0.0)
                    metadata = meta.copy()
                    if "code" in metadata:
                        del metadata["code"]
                    metadata["score"] = score

                if content:
                     documents.append(Document(page_content=content, metadata=metadata))
            
            return documents
            
        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []

def get_retriever(codebase_name: str, top_k: int = 5):
    return EndeeRetriever(index_name=codebase_name, top_k=top_k)
