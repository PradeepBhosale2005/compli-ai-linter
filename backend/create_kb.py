"""
Knowledge Base Builder for Healthcare Compliance Documents

This module creates and manages a vector database using ChromaDB and Azure OpenAI
for healthcare technology compliance documents.
"""

import chromadb
import os
import time
import logging
from typing import List, Optional
from pypdf import PdfReader
from openai import AzureOpenAI
import openai

from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeBaseBuilder:
    """
    Knowledge base builder using ChromaDB and Azure OpenAI.
    
    Provides functionality for:
    - Text chunking with paragraph-based splitting and overlap
    - Retry logic for rate limit handling
    - Document processing checkpointing
    - Vector embedding generation and storage
    """
    
    def __init__(self):
        """Initialize the knowledge base builder with Azure OpenAI and ChromaDB clients."""
        self.azure_client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        self.chroma_client = chromadb.PersistentClient(path="chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(
            name="healthtech_kb",
            metadata={"description": "Healthcare technology compliance knowledge base"}
        )
        
        self.data_folder = "data"
        self.pdf_files = [
            "21 CFR Part 11 (up to date as of 2-01-2024).pdf",
            "General-Principles-of-Software-Validation---Final-Guidance-for-Industry-and-FDA-Staff.pdf",
        ]
        
        logger.info("Knowledge Base Builder initialized")
        logger.info(f"Data folder: {self.data_folder}")
        logger.info(f"ChromaDB collection: {self.collection.name}")
        logger.info(f"Files to process: {len(self.pdf_files)}")

    def get_embedding_with_retry(self, text: str, max_retries: int = 3) -> Optional[List[float]]:
        """
        Generate embedding for text with retry logic for rate limit errors.
        
        Args:
            text: The text to embed
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of embedding values or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                response = self.azure_client.embeddings.create(
                    model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                    input=text
                )
                return response.data[0].embedding
                
            except openai.RateLimitError:
                wait_time = 60
                logger.warning(f"Rate limit error on attempt {attempt + 1}/{max_retries}")
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Error getting embedding (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    
        logger.error(f"Failed to get embedding after {max_retries} attempts")
        return None

    def split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into chunks with paragraph-based splitting and overlap.
        
        Args:
            text: The input text to split
            chunk_size: Target size for each chunk in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks with preserved context
        """
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Handle very long paragraphs by splitting them further
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= chunk_size:
                final_chunks.append(chunk)
            else:
                sentences = chunk.split('. ')
                temp_chunk = ""
                
                for sentence in sentences:
                    if len(temp_chunk) + len(sentence) > chunk_size and temp_chunk:
                        final_chunks.append(temp_chunk.strip())
                        temp_chunk = sentence
                    else:
                        if temp_chunk:
                            temp_chunk += ". " + sentence
                        else:
                            temp_chunk = sentence
                
                if temp_chunk.strip():
                    final_chunks.append(temp_chunk.strip())
        
        return final_chunks

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from a PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {str(e)}")
            return ""

    def process_documents(self):
        """Process all documents and build the knowledge base."""
        logger.info("Starting knowledge base creation process...")
        
        total_chunks_processed = 0
        total_chunks_skipped = 0
        
        for file_name in self.pdf_files:
            file_path = os.path.join(self.data_folder, file_name)
            
            if not file_name.lower().endswith('.pdf'):
                logger.info(f"Skipping non-PDF file: {file_name}")
                continue
                
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
            
            logger.info(f"Processing: {file_name}")
            
            text = self.extract_text_from_pdf(file_path)
            if not text:
                logger.error(f"No text extracted from {file_name}")
                continue
            
            chunks = self.split_text(text)
            logger.info(f"Created {len(chunks)} chunks from {file_name}")
            
            for i, chunk in enumerate(chunks, 1):
                chunk_id = f"{os.path.splitext(file_name)[0]}_chunk_{i}"
                
                try:
                    existing = self.collection.get(ids=[chunk_id])
                    if existing['ids']:
                        logger.debug(f"Chunk {i}/{len(chunks)} already exists, skipping...")
                        total_chunks_skipped += 1
                        continue
                except Exception:
                    pass
                
                logger.debug(f"Processing chunk {i}/{len(chunks)} (ID: {chunk_id})")
                embedding = self.get_embedding_with_retry(chunk)
                
                if embedding is None:
                    logger.error(f"Failed to get embedding for chunk {i}, skipping...")
                    continue
                
                try:
                    self.collection.add(
                        documents=[chunk],
                        embeddings=[embedding],
                        ids=[chunk_id],
                        metadatas=[{
                            "source_file": file_name,
                            "chunk_number": i,
                            "total_chunks": len(chunks),
                            "chunk_size": len(chunk)
                        }]
                    )
                    logger.debug(f"Successfully added chunk {i}/{len(chunks)}")
                    total_chunks_processed += 1
                    
                except Exception as e:
                    logger.error(f"Error adding chunk {i} to collection: {str(e)}")
        
        logger.info("Knowledge base creation complete!")
        logger.info(f"Total chunks processed: {total_chunks_processed}")
        logger.info(f"Total chunks skipped (already existed): {total_chunks_skipped}")
        logger.info(f"Collection name: {self.collection.name}")
        logger.info("ChromaDB path: chroma_db/")
        
        try:
            collection_count = self.collection.count()
            logger.info(f"Total documents in collection: {collection_count}")
        except Exception as e:
            logger.error(f"Could not get collection count: {str(e)}")


def main():
    """Main entry point for the knowledge base builder."""
    try:
        kb_builder = KnowledgeBaseBuilder()
        kb_builder.process_documents()
    except Exception as e:
        logger.error(f"Fatal error in knowledge base creation: {str(e)}")
        raise


if __name__ == "__main__":
    main()