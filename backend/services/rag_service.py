"""
RAG (Retrieval-Augmented Generation) Service

Provides semantic search capabilities over healthcare compliance knowledge base
using Azure OpenAI embeddings and ChromaDB vector search.
"""

import chromadb
import openai
import logging
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI

from config.settings import settings

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation service for querying the knowledge base.
    
    Provides semantic search capabilities using Azure OpenAI embeddings
    and ChromaDB vector search for healthcare compliance documents.
    """
    
    def __init__(self):
        """Initialize the RAG service with Azure OpenAI client and ChromaDB connection."""
        try:
            self.azure_client = AzureOpenAI(
                api_key=settings.OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            
            self.chroma_client = chromadb.PersistentClient(path="chroma_db")
            self.collection = self.chroma_client.get_collection(name="healthtech_kb")
            
            logger.info("RAG Service initialized successfully")
            logger.info(f"Knowledge base collection: {self.collection.name}")
            
            try:
                collection_count = self.collection.count()
                logger.info(f"Available documents: {collection_count}")
            except Exception as e:
                logger.warning(f"Could not get collection count: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error initializing RAG Service: {str(e)}")
            raise Exception(f"Failed to initialize RAG Service: {str(e)}")
    
    def _generate_query_embedding(self, query_text: str) -> Optional[List[float]]:
        """Generate embedding for query text using Azure OpenAI."""
        try:
            response = self.azure_client.embeddings.create(
                model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                input=query_text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return None
    
    def query(self, query_text: str, n_results: int = 3) -> List[str]:
        """
        Query the knowledge base using semantic search.
        
        Args:
            query_text: The text query to search for
            n_results: Number of results to return
            
        Returns:
            List of relevant document texts from the knowledge base
        """
        if not query_text or not query_text.strip():
            return ["No query provided."]
        
        try:
            logger.debug(f"Processing query: '{query_text[:50]}{'...' if len(query_text) > 50 else ''}'")
            
            query_embedding = self._generate_query_embedding(query_text)
            
            if query_embedding is None:
                return ["Could not generate embedding for query. Please try again."]
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            if results and 'documents' in results and results['documents']:
                documents = results['documents'][0]
                
                if documents:
                    logger.debug(f"Found {len(documents)} relevant documents")
                    return documents
                else:
                    logger.warning("No relevant documents found")
                    return ["No relevant information found in the knowledge base."]
            else:
                logger.warning("Empty results from knowledge base")
                return ["No relevant information found in the knowledge base."]
                
        except Exception as e:
            error_msg = f"Error querying knowledge base: {str(e)}"
            logger.error(error_msg)
            return [f"Search error: {error_msg}"]
    
    def query_with_metadata(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Enhanced query method that returns results with metadata.
        
        Args:
            query_text: The text query to search for
            n_results: Number of results to return
            
        Returns:
            List of dictionaries containing document text, metadata, and relevance scores
        """
        if not query_text or not query_text.strip():
            return [{"text": "No query provided.", "metadata": {}, "distance": 1.0}]
        
        try:
            logger.debug(f"Processing enhanced query: '{query_text[:50]}{'...' if len(query_text) > 50 else ''}'")
            
            query_embedding = self._generate_query_embedding(query_text)
            
            if query_embedding is None:
                return [{"text": "Could not generate embedding for query.", "metadata": {}, "distance": 1.0}]
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            
            if results and 'documents' in results and results['documents']:
                documents = results['documents'][0]
                metadatas = results.get('metadatas', [[]])[0]
                distances = results.get('distances', [[]])[0]
                
                for i, doc in enumerate(documents):
                    result = {
                        "text": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "distance": distances[i] if i < len(distances) else 1.0,
                        "relevance_score": 1.0 - (distances[i] if i < len(distances) else 1.0)
                    }
                    formatted_results.append(result)
                
                logger.debug(f"Found {len(formatted_results)} relevant documents with metadata")
                return formatted_results
            else:
                return [{"text": "No relevant information found in the knowledge base.", "metadata": {}, "distance": 1.0}]
                
        except Exception as e:
            error_msg = f"Error querying knowledge base: {str(e)}"
            logger.error(error_msg)
            return [{"text": f"Search error: {error_msg}", "metadata": {}, "distance": 1.0}]
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the knowledge base collection.
        
        Returns:
            Dictionary with collection statistics and metadata
        """
        try:
            collection_count = self.collection.count()
            
            # Get a sample of documents to understand the collection
            sample_results = self.collection.peek(limit=5)
            
            info = {
                "collection_name": self.collection.name,
                "document_count": collection_count,
                "sample_documents": len(sample_results.get('documents', [])),
                "available": True
            }
            
            # Add metadata if available
            if sample_results.get('metadatas'):
                sample_metadata = sample_results['metadatas'][0] if sample_results['metadatas'] else {}
                info["sample_metadata_keys"] = list(sample_metadata.keys())
            
            return info
            
        except Exception as e:
            return {
                "collection_name": "healthtech_kb",
                "document_count": 0,
                "error": str(e),
                "available": False
            }
    
    def search_by_source(self, source_file: str, query_text: str = "", n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents from a specific source file.
        
        Args:
            source_file: Name of the source file to filter by
            query_text: Optional text query for semantic search within the source
            n_results: Number of results to return
            
        Returns:
            List of documents from the specified source
        """
        try:
            if query_text:
                # Semantic search within specific source
                query_embedding = self._generate_query_embedding(query_text)
                if query_embedding is None:
                    return []
                
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results * 2,  # Get more results to filter
                    include=['documents', 'metadatas', 'distances'],
                    where={"source_file": source_file}
                )
            else:
                # Just get documents from the source
                results = self.collection.get(
                    limit=n_results,
                    include=['documents', 'metadatas'],
                    where={"source_file": source_file}
                )
            
            # Format results
            formatted_results = []
            if results and 'documents' in results:
                documents = results['documents'] if isinstance(results['documents'][0], str) else results['documents'][0]
                metadatas = results.get('metadatas', [])
                if metadatas and isinstance(metadatas[0], list):
                    metadatas = metadatas[0]
                
                distances = results.get('distances', [[]])[0] if 'distances' in results else []
                
                for i, doc in enumerate(documents):
                    result = {
                        "text": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "distance": distances[i] if i < len(distances) else 0.0
                    }
                    formatted_results.append(result)
            
            return formatted_results[:n_results]
            
        except Exception as e:
            logger.error(f"Error searching by source: {str(e)}")
            return []


def get_rag_service() -> RAGService:
    """Get a singleton instance of the RAG service."""
    global _rag_service_instance
    
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    
    return _rag_service_instance


# Singleton instance
_rag_service_instance = None