"""
Document Parser Service

Universal document parser supporting DOCX and PDF files with intelligent
section detection and metadata extraction.
"""

import io
import logging
from typing import Dict, List
from docx import Document
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def _parse_docx(file_content: bytes) -> Dict[str, any]:
    """
    Parse DOCX files with intelligent section detection.
    
    Args:
        file_content: Raw bytes of the DOCX file
        
    Returns:
        Dictionary containing sections, full text, and metadata
    """
    try:
        file_stream = io.BytesIO(file_content)
        doc = Document(file_stream)
        
        sections = {}
        full_text = ""
        current_section = "Introduction"
        current_content = []
        
        metadata = {
            "title": doc.core_properties.title or "Untitled",
            "author": doc.core_properties.author or "Unknown",
            "created": str(doc.core_properties.created) if doc.core_properties.created else None,
            "modified": str(doc.core_properties.modified) if doc.core_properties.modified else None,
            "subject": doc.core_properties.subject or "",
        }
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            
            if not text:
                continue
                
            full_text += text + "\n"
            
            is_heading = False
            
            if paragraph.style.name.startswith('Heading'):
                is_heading = True
            elif len(text) < 100 and (
                text.isupper() or
                text.istitle() or
                text.endswith(':') or
                any(keyword in text.lower() for keyword in [
                    'section', 'chapter', 'part', 'introduction', 'conclusion',
                    'overview', 'summary', 'background', 'purpose', 'scope',
                    'requirements', 'procedures', 'guidelines', 'standards'
                ])
            ):
                is_heading = True
            
            if is_heading:
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                
                current_section = text
                current_content = []
            else:
                current_content.append(text)
        
        if current_content:
            sections[current_section] = "\n".join(current_content)
        
        if not sections and full_text.strip():
            sections["Document Content"] = full_text.strip()
        
        return {
            "sections": sections,
            "full_text": full_text.strip(),
            "metadata": metadata,
            "document_type": "docx",
            "section_count": len(sections)
        }
        
    except Exception as e:
        raise ValueError(f"Error parsing DOCX file: {str(e)}")


def _parse_pdf(file_content: bytes) -> Dict[str, any]:
    """
    Private helper function to parse PDF files.
    
    Uses pypdf to extract all text. Since PDFs lack clear structure,
    it concatenates all text and returns a dictionary where 'full_text'
    contains everything and 'sections' is initially empty.
    
    Args:
        file_content: The raw bytes of the PDF file
        
    Returns:
        Dictionary containing:
        - 'sections': Empty dict (PDFs don't have clear section structure)
        - 'full_text': Complete document text
        - 'metadata': PDF metadata
        - 'page_count': Number of pages
    """
    try:
        # Create a BytesIO object from the file content
        file_stream = io.BytesIO(file_content)
        
        # Create PDF reader
        pdf_reader = PdfReader(file_stream)
        
        # Extract text from all pages
        full_text = ""
        page_texts = []
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text.strip():  # Only add non-empty pages
                    page_texts.append(f"--- Page {page_num} ---\n{page_text}")
                    full_text += page_text + "\n"
            except Exception as e:
                print(f"Warning: Could not extract text from page {page_num}: {str(e)}")
                continue
        
        # Extract PDF metadata
        metadata = {}
        try:
            if pdf_reader.metadata:
                metadata = {
                    "title": pdf_reader.metadata.get("/Title", "Untitled"),
                    "author": pdf_reader.metadata.get("/Author", "Unknown"),
                    "subject": pdf_reader.metadata.get("/Subject", ""),
                    "creator": pdf_reader.metadata.get("/Creator", ""),
                    "producer": pdf_reader.metadata.get("/Producer", ""),
                    "creation_date": str(pdf_reader.metadata.get("/CreationDate", "")),
                    "modification_date": str(pdf_reader.metadata.get("/ModDate", "")),
                }
        except Exception as e:
            print(f"Warning: Could not extract PDF metadata: {str(e)}")
            metadata = {"title": "Untitled", "author": "Unknown"}
        
        # Attempt basic section detection for PDFs based on common patterns
        sections = {}
        
        # Try to identify sections based on common PDF section markers
        lines = full_text.split('\n')
        current_section = "Document Content"
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for potential section headers in PDFs
            is_section_header = False
            
            # Look for numbered sections (1., 2., 1.1, etc.)
            if line and (
                line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or
                line.startswith(('I.', 'II.', 'III.', 'IV.', 'V.', 'VI.', 'VII.', 'VIII.', 'IX.', 'X.')) or
                line.startswith(('A.', 'B.', 'C.', 'D.', 'E.', 'F.', 'G.', 'H.'))
            ) and len(line) < 150:  # Section headers are typically shorter
                is_section_header = True
            
            # Look for common section keywords
            elif any(keyword in line.lower() for keyword in [
                'introduction', 'background', 'purpose', 'scope', 'definitions',
                'requirements', 'procedures', 'guidelines', 'standards', 'conclusion',
                'summary', 'overview', 'section', 'chapter', 'part'
            ]) and len(line) < 150:
                is_section_header = True
            
            if is_section_header:
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                
                # Start new section
                current_section = line
                current_content = []
            else:
                current_content.append(line)
        
        # Save the last section
        if current_content:
            sections[current_section] = "\n".join(current_content)
        
        # If no clear sections found, use page-based sections as fallback
        if len(sections) <= 1 and len(page_texts) > 1:
            sections = {}
            for i, page_text in enumerate(page_texts, 1):
                sections[f"Page {i}"] = page_text.replace(f"--- Page {i} ---\n", "")
        
        return {
            "sections": sections,
            "full_text": full_text.strip(),
            "metadata": metadata,
            "document_type": "pdf",
            "page_count": len(pdf_reader.pages),
            "section_count": len(sections)
        }
        
    except Exception as e:
        raise ValueError(f"Error parsing PDF file: {str(e)}")


def parse_document(filename: str, file_content: bytes) -> Dict[str, any]:
    """
    Main public function to parse documents of different types.
    
    Checks the filename extension and calls the appropriate parser.
    
    Args:
        filename: The name of the file (used to determine file type)
        file_content: The raw bytes of the file
        
    Returns:
        Dictionary containing parsed document data:
        - 'sections': Dictionary of section headers to content
        - 'full_text': Complete document text
        - 'metadata': Document metadata
        - 'document_type': Type of document (docx/pdf)
        - Additional type-specific fields
        
    Raises:
        ValueError: If the file type is unsupported or parsing fails
    """
    # Get file extension and normalize it
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Route to appropriate parser based on file extension
    if file_extension == 'docx':
        return _parse_docx(file_content)
    elif file_extension == 'pdf':
        return _parse_pdf(file_content)
    else:
        supported_types = ['docx', 'pdf']
        raise ValueError(
            f"Unsupported file type: '{file_extension}'. "
            f"Supported types are: {', '.join(supported_types)}"
        )


# Utility function for testing and debugging
def get_supported_file_types() -> List[str]:
    """
    Returns a list of supported file types.
    
    Returns:
        List of supported file extensions
    """
    return ['docx', 'pdf']


def validate_file_type(filename: str) -> bool:
    """
    Validates if a file type is supported.
    
    Args:
        filename: The name of the file to validate
        
    Returns:
        True if the file type is supported, False otherwise
    """
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    return file_extension in get_supported_file_types()