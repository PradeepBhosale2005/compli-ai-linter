"""
FastAPI application for CompliAI Linter - Healthcare compliance analysis service.

This module provides REST API endpoints for document analysis, compliance checking,
and scoring using AI-powered services and knowledge base integration.
"""

import os
import traceback
import logging
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import AzureOpenAI

# Import configuration and services
from config.settings import settings
from services.parser_service import parse_document
from services.linter_service import run_all_checks, get_finding_summary
from services.scorer_service import calculate_score, get_score_explanation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Azure OpenAI client using configuration values
azure_client = AzureOpenAI(
    api_key=settings.OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
)

# Create FastAPI app instance
app = FastAPI(
    title="CompliAI Linter API",
    description="AI-powered compliance analysis for healthcare technology documents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
async def root():
    """
    Health check endpoint to verify API is running.
    """
    return {
        "message": "CompliAI Linter API is running",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze-document",
            "docs": "/docs",
            "health": "/"
        }
    }

# Health check endpoint with service status
@app.get("/health")
async def health_check():
    """
    Comprehensive health check including service dependencies.
    """
    health_status = {
        "api": "healthy",
        "azure_openai": "unknown",
        "knowledge_base": "unknown",
        "timestamp": str(int(os.times().elapsed))
    }
    
    try:
        # Test Azure OpenAI connection
        test_response = azure_client.embeddings.create(
            model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            input="test"
        )
        if test_response:
            health_status["azure_openai"] = "healthy"
    except Exception as e:
        health_status["azure_openai"] = f"error: {str(e)[:100]}"
    
    try:
        # Test knowledge base availability
        from services.rag_service import RAGService
        rag_service = RAGService()
        collection_info = rag_service.get_collection_info()
        if collection_info.get("available", False):
            health_status["knowledge_base"] = f"healthy ({collection_info.get('document_count', 0)} docs)"
        else:
            health_status["knowledge_base"] = "unavailable"
    except Exception as e:
        health_status["knowledge_base"] = f"error: {str(e)[:100]}"
    
    overall_status = "healthy" if all(
        status == "healthy" or status.startswith("healthy") 
        for key, status in health_status.items() 
        if key not in ["timestamp"]
    ) else "degraded"
    
    return {
        "status": overall_status,
        "services": health_status
    }

# Main document analysis endpoint
@app.post("/analyze-document")
async def analyze_document(file: UploadFile = File(...)):
    """
    Comprehensive document analysis endpoint.
    
    Analyzes uploaded documents for GxP compliance using:
    - Document parsing (DOCX/PDF support)
    - Core rule-based compliance checks
    - AI-powered reference analysis
    - Knowledge base enrichment
    - Compliance scoring
    
    Args:
        file: Uploaded document file (DOCX or PDF)
        
    Returns:
        JSON response with analysis results, findings, and compliance score
    """
    
    # Validate file
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file type
    allowed_extensions = ['.pdf', '.docx']
    file_extension = os.path.splitext(file.filename.lower())[1]
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    try:
        logger.info(f"Starting analysis for: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="File appears to be empty")
        
        logger.debug(f"File size: {len(file_content)} bytes")
        
        # Step 1: Parse the document
        logger.info("Step 1: Parsing document...")
        try:
            parsed_data = parse_document(file.filename, file_content)
            logger.info(f"Parsed successfully - Found {len(parsed_data.get('sections', {}))} sections")
        except Exception as e:
            logger.error(f"Parsing failed: {str(e)}")
            raise HTTPException(status_code=422, detail=f"Failed to parse document: {str(e)}")
        
        # Step 2: Run compliance checks
        logger.info("Step 2: Running compliance analysis...")
        try:
            findings = run_all_checks(
                parsed_data=parsed_data,
                client=azure_client,
                chat_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                embedding_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            logger.info(f"Analysis complete - Found {len(findings)} findings")
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Compliance analysis failed: {str(e)}")
        
        # Step 3: Calculate compliance score
        logger.info("Step 3: Calculating compliance score...")
        try:
            score_data = calculate_score(findings)
            score_explanation = get_score_explanation(score_data)
            logger.info(f"Score calculated: {score_data['score']}/100 ({score_data['compliance_level']})")
        except Exception as e:
            logger.error(f"Scoring failed: {str(e)}")
            # Provide fallback scoring
            score_data = {
                "score": 50,
                "compliance_level": "Unknown",
                "total_findings": len(findings),
                "error": str(e)
            }
            score_explanation = "Error calculating detailed score."
        
        # Step 4: Generate summary
        logger.info("Step 4: Generating analysis summary...")
        try:
            finding_summary = get_finding_summary(findings)
        except Exception as e:
            logger.warning(f"Summary generation failed: {str(e)}")
            finding_summary = {"total_findings": len(findings), "error": str(e)}
        
        # Prepare final response
        response_data = {
            "success": True,
            "analysis_id": f"analysis_{int(os.times().elapsed)}",
            "file_info": {
                "filename": file.filename,
                "file_type": file_extension,
                "file_size": len(file_content),
                "sections_found": len(parsed_data.get("sections", {}))
            },
            "parsing_results": {
                "document_type": parsed_data.get("document_type", "unknown"),
                "section_count": len(parsed_data.get("sections", {})),
                "total_text_length": len(parsed_data.get("full_text", "")),
                "metadata": parsed_data.get("metadata", {})
            },
            "compliance_analysis": {
                "score": score_data,
                "findings": findings,
                "summary": finding_summary,
                "explanation": score_explanation
            },
            "processing_info": {
                "total_findings": len(findings),
                "core_rules_applied": sum(1 for f in findings if f.get("rule_type") == "Core"),
                "ai_analysis_applied": sum(1 for f in findings if f.get("rule_type") == "AI"),
                "knowledge_base_enriched": sum(1 for f in findings if "explanation" in f and f["explanation"])
            }
        }
        
        logger.info(f"Analysis complete for {file.filename}")
        logger.info(f"Final score: {score_data.get('score', 'unknown')}/100")
        logger.info(f"Total findings: {len(findings)}")
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected errors
        error_detail = f"Unexpected error during analysis: {str(e)}"
        logger.error(error_detail)
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": error_detail,
                "file_info": {
                    "filename": file.filename if file else "unknown",
                    "file_type": file_extension if 'file_extension' in locals() else "unknown"
                },
                "analysis_id": f"failed_analysis_{int(os.times().elapsed)}"
            }
        )

# Additional utility endpoints

@app.get("/supported-formats")
async def get_supported_formats():
    """
    Get list of supported document formats.
    """
    return {
        "supported_formats": [
            {
                "extension": ".pdf",
                "description": "Portable Document Format",
                "features": ["text_extraction", "basic_structure_detection"]
            },
            {
                "extension": ".docx", 
                "description": "Microsoft Word Document",
                "features": ["text_extraction", "section_detection", "metadata_extraction"]
            }
        ],
        "max_file_size": "50MB",
        "analysis_features": [
            "missing_section_detection",
            "placeholder_text_detection", 
            "reference_staleness_analysis",
            "knowledge_base_enrichment",
            "compliance_scoring"
        ]
    }

@app.get("/analysis-info")
async def get_analysis_info():
    """
    Get information about the analysis capabilities.
    """
    return {
        "core_checks": [
            {
                "name": "Missing Sections",
                "description": "Detects missing mandatory GxP sections",
                "severity": "Critical",
                "type": "Rule-based"
            },
            {
                "name": "Placeholder Text",
                "description": "Finds incomplete content markers like TBD, TODO",
                "severity": "Major", 
                "type": "Rule-based"
            }
        ],
        "ai_checks": [
            {
                "name": "Reference Staleness",
                "description": "AI analysis of potentially outdated references",
                "severity": "Major",
                "type": "AI-powered"
            }
        ],
        "scoring_system": {
            "base_score": 100,
            "penalties": {
                "Critical": 20,
                "Major": 10,
                "Minor": 5
            },
            "levels": [
                {"range": "90-100", "level": "Excellent", "color": "green"},
                {"range": "75-89", "level": "Good", "color": "blue"},
                {"range": "60-74", "level": "Fair", "color": "yellow"},
                {"range": "40-59", "level": "Poor", "color": "orange"},
                {"range": "0-39", "level": "Critical", "color": "red"}
            ]
        },
        "knowledge_base": {
            "sources": [
                "21 CFR Part 11",
                "FDA Software Validation Guidance"
            ],
            "features": ["contextual_explanations", "semantic_search"]
        }
    }

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )