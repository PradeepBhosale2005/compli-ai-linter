"""
FastAPI application for CompliAI Linter - Healthcare compliance analysis service.

This module provides REST API endpoints for document analysis, compliance checking,
and scoring using AI-powered services and knowledge base integration.
"""

import os
import traceback
import logging
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import AzureOpenAI

# Import configuration and services
from config.settings import settings
from services.parser_service import parse_document
from services.ai_linter_service import run_all_checks, get_finding_summary
from services.scorer_service import calculate_score_detailed as calculate_score, get_score_explanation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for rule management
class Rule(BaseModel):
    rule_text: str
    rule_type: str = "Custom"
    severity: str = "Major"

# Rules file path
RULES_FILE = "gxp_rules.json"

# Database initialization
def init_database():
    """Initialize SQLite database for document history"""
    try:
        conn = sqlite3.connect('compliance_history.db')
        cursor = conn.cursor()
        
        # Create documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                upload_date DATETIME NOT NULL,
                analysis_result TEXT NOT NULL,
                compliance_score INTEGER NOT NULL,
                total_findings INTEGER NOT NULL,
                critical_findings INTEGER DEFAULT 0,
                major_findings INTEGER DEFAULT 0,
                minor_findings INTEGER DEFAULT 0,
                file_size INTEGER DEFAULT 0
            )
        ''')
        
        # Create document_rules table for document-specific rules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                rule_text TEXT NOT NULL,
                rule_type TEXT DEFAULT 'Custom',
                severity TEXT DEFAULT 'Major',
                created_at DATETIME NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

# Initialize database on startup
init_database()

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
    allow_origins=["*"],  # React development servers
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
        
        # Step 2: Run AI-powered compliance analysis
        logger.info("Step 2: Running AI-powered comprehensive GxP compliance analysis...")
        try:
            # Use new AI-powered linter service for comprehensive analysis
            findings = run_all_checks(
                parsed_data=parsed_data,
                client=azure_client,
                chat_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                embedding_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                document_id=None  # New analysis, no existing document ID
            )
            logger.info(f"AI analysis complete - Found {len(findings)} compliance findings")
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
            logger.debug(f"Scoring traceback: {traceback.format_exc()}")
            # Provide fallback scoring with more detail
            score_data = {
                "score": 50,
                "compliance_level": "Unknown - Scoring Error",
                "total_findings": len(findings),
                "error": str(e),
                "fallback": True
            }
            score_explanation = f"Error calculating detailed score: {str(e)}"
        
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
                "analysis_method": "Hybrid AI-Powered Audit",
                "core_gxp_rules": 9,  # Core mandatory regulatory rules
                "dynamic_user_rules": "Variable based on Rule Editor",
                "ai_hybrid_findings": sum(1 for f in findings if f.get("rule_type") in ["Core", "Dynamic", "AI-Hybrid"]),
                "system_issues": sum(1 for f in findings if f.get("rule_type") == "System"),
                "ai_model_used": settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                "hybrid_approach": "Core regulatory baseline + User-defined extensions"
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


# Re-analyze document with custom rules endpoint
@app.post("/reanalyze-document/{document_id}")
async def reanalyze_document(document_id: int, file: UploadFile = File(...)):
    """
    Re-analyze a document with its associated document-specific rules.
    
    This endpoint allows re-analyzing a document that was previously analyzed,
    applying both global rules and any document-specific rules that have been added.
    
    Args:
        document_id: ID of the document in the history
        file: The document file to re-analyze
        
    Returns:
        JSON response with enhanced analysis results including custom rule compliance
    """
    
    # Validate file
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file type
    allowed_extensions = ['.pdf', '.docx']
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_extension}. Supported types: {', '.join(allowed_extensions)}"
        )
    
    # Verify document exists in history
    try:
        conn = sqlite3.connect('compliance_history.db')
        cursor = conn.cursor()
        cursor.execute('SELECT filename FROM documents WHERE id = ?', (document_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found in history")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking document history: {str(e)}")
    
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Re-analyzing document {document_id}: {file.filename} with custom rules")
        
        # Step 1: Parse document
        logger.info("Step 1: Parsing document...")
        try:
            parsed_data = parse_document(temp_path)
            logger.info(f"Document parsed successfully - {len(parsed_data.get('sections', {}))} sections found")
        except Exception as e:
            logger.error(f"Parsing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Document parsing failed: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        # Initialize Azure OpenAI client
        azure_client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        # Step 2: Run AI-powered compliance analysis WITH document-specific rules
        logger.info(f"Step 2: Running AI-powered comprehensive GxP analysis with custom rules for document {document_id}...")
        try:
            findings = run_all_checks(
                parsed_data=parsed_data,
                client=azure_client,
                chat_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                embedding_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                document_id=document_id  # Pass document ID for future custom rules support
            )
            logger.info(f"AI analysis complete - Found {len(findings)} compliance findings")
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
            raise HTTPException(status_code=500, detail=f"Score calculation failed: {str(e)}")
        
        # Prepare response
        response_data = {
            "success": True,
            "message": f"Document re-analyzed successfully with custom rules for document {document_id}",
            "file_info": {
                "filename": file.filename,
                "file_type": file_extension,
                "file_size": len(content),
                "sections_found": len(parsed_data.get("sections", {}))
            },
            "compliance_analysis": {
                "findings": findings,
                "score": score_data,
                "score_explanation": score_explanation,
                "summary": get_finding_summary(findings)
            },
            "analysis_metadata": {
                "analysis_type": "ai_powered_reanalysis",
                "document_id": document_id,
                "timestamp": datetime.now().isoformat(),
                "ai_comprehensive_audit": True,
                "gxp_rules_checked": 24,
                "analysis_method": "AI-Powered Comprehensive Audit"
            }
        }
        
        logger.info(f"Re-analysis complete for document {document_id}")
        logger.info(f"Final score: {score_data.get('score', 'unknown')}/100")
        logger.info(f"Total findings: {len(findings)}")
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected errors
        error_detail = f"Unexpected error during re-analysis: {str(e)}"
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
                "analysis_id": f"failed_reanalysis_{int(os.times().elapsed)}"
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
    Get information about the Hybrid AI-powered analysis capabilities.
    """
    return {
        "system_name": "Compli-AI Linter",
        "system_version": "2.0.0 - Hybrid AI Architecture",
        "analysis_method": "Hybrid AI-Powered GxP Compliance Audit",
        "description": "Ultimate hybrid compliance system combining mandatory core GxP rules with AI-powered dynamic user extensions",
        
        "core_gxp_rules": {
            "count": 9,
            "type": "Hardcoded regulatory baseline",
            "immutable": True,
            "description": "Essential 21 CFR Part 11 and GxP requirements that cannot be disabled",
            "rules": [
                {
                    "name": "Electronic Signature Requirements",
                    "description": "Validates electronic signature components and 21 CFR Part 11 compliance",
                    "severity": "Critical",
                    "type": "Core"
                },
                {
                    "name": "Audit Trail Completeness", 
                    "description": "Ensures comprehensive audit trail documentation and traceability",
                    "severity": "Critical",
                    "type": "Core"
                },
                {
                    "name": "Data Integrity Controls",
                    "description": "Validates ALCOA+ principles and data integrity measures",
                    "severity": "Critical",
                    "type": "Core"
                },
                {
                    "name": "System Validation Documentation",
                    "description": "Checks for proper computer system validation protocols",
                    "severity": "Critical",
                    "type": "Core"
                },
                {
                    "name": "Access Control and Security",
                    "description": "Validates user access controls and security measures",
                    "severity": "Major",
                    "type": "Core"
                },
                {
                    "name": "Change Control Procedures",
                    "description": "Ensures proper change control and configuration management",
                    "severity": "Major",
                    "type": "Core"
                },
                {
                    "name": "Documentation and Record Keeping",
                    "description": "Validates documentation standards and record retention",
                    "severity": "Major",
                    "type": "Core"
                },
                {
                    "name": "Training and Competency Requirements",
                    "description": "Checks for proper training documentation and competency assessment",
                    "severity": "Major",
                    "type": "Core"
                },
                {
                    "name": "Deviation and CAPA Management",
                    "description": "Validates deviation handling and corrective action procedures",
                    "severity": "Major",
                    "type": "Core"
                }
            ]
        },
        
        "dynamic_ai_extensions": {
            "source": "User-defined rules via Rule Editor",
            "flexibility": "Fully customizable per document type",
            "ai_integration": "Intelligent interpretation and enforcement",
            "storage": "gxp_rules.json with real-time updates",
            "rule_types": ["Global Rules", "Document-Specific Rules"],
            "customization_level": "Complete - users can define any compliance requirement"
        },
        
        "hybrid_approach_benefits": {
            "regulatory_compliance": "Core rules ensure baseline regulatory adherence",
            "flexibility": "Dynamic rules allow customization for specific needs",
            "ai_intelligence": "Single AI auditor understands both rule types contextually",
            "scalability": "Easy addition of new requirements without code changes",
            "consistency": "Unified analysis approach for all rule types"
        },
        
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
        
        "ai_capabilities": {
            "model": "Azure OpenAI GPT-4",
            "hybrid_prompting": "Core rules + Dynamic rules in single comprehensive analysis",
            "intelligent_rule_application": "Context-aware compliance assessment",
            "structured_findings": "Categorized by rule type (Core/Dynamic) and severity",
            "features": [
                "Adaptive rule interpretation for both core and dynamic rules",
                "Context-aware analysis based on document type",
                "Natural language understanding of user-defined requirements",
                "Comprehensive GxP knowledge base",
                "Structured findings with actionable recommendations"
            ]
        },
        
        "compliance_standards": {
            "primary_focus": "GxP (Good Practice) Compliance",
            "regulatory_frameworks": [
                "FDA 21 CFR Part 11",
                "ICH Guidelines", 
                "ISO 13485:2016",
                "EU GMP Guidelines"
            ],
            "document_types": [
                "Standard Operating Procedures (SOPs)",
                "Validation Protocols",
                "Work Instructions",
                "Quality Manuals",
                "Training Materials",
                "Change Control Documents"
            ]
        },
        
        "rule_management": {
            "core_rules": "Immutable regulatory requirements - always enforced",
            "user_rules": "Configurable via frontend Rule Editor",
            "global_rules": "Apply to all documents",
            "document_specific": "Targeted to specific document types",
            "real_time_updates": "Changes in Rule Editor immediately affect analysis"
        }
    }

# Document History Management Endpoints

@app.post("/save-analysis-result")
async def save_analysis_result(request: dict):
    """Save analysis result to document history"""
    try:
        conn = sqlite3.connect('compliance_history.db')
        cursor = conn.cursor()
        
        # Extract data from request
        file_info = request.get('file_info', {})
        compliance_analysis = request.get('compliance_analysis', {})
        score_data = compliance_analysis.get('score', {})
        findings = compliance_analysis.get('findings', [])
        
        # Count findings by severity
        critical_count = sum(1 for f in findings if f.get('severity') == 'Critical')
        major_count = sum(1 for f in findings if f.get('severity') == 'Major')
        minor_count = sum(1 for f in findings if f.get('severity') == 'Minor')
        
        cursor.execute('''
            INSERT INTO documents 
            (filename, file_type, upload_date, analysis_result, compliance_score, 
             total_findings, critical_findings, major_findings, minor_findings, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            file_info.get('filename', 'unknown'),
            file_info.get('file_type', 'unknown'),
            datetime.now().isoformat(),
            json.dumps(request),
            score_data.get('score', 0),
            len(findings),
            critical_count,
            major_count,
            minor_count,
            file_info.get('file_size', 0)
        ))
        
        document_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Analysis result saved with document ID: {document_id}")
        return {
            "success": True,
            "document_id": document_id,
            "message": "Analysis result saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving analysis result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save analysis: {str(e)}")

@app.get("/document-history")
async def get_document_history(limit: int = 50):
    """Get document analysis history"""
    try:
        conn = sqlite3.connect('compliance_history.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, file_type, upload_date, compliance_score, 
                   total_findings, critical_findings, major_findings, minor_findings, file_size
            FROM documents 
            ORDER BY upload_date DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        documents = []
        for row in rows:
            documents.append({
                "id": row[0],
                "filename": row[1],
                "file_type": row[2],
                "upload_date": row[3],
                "compliance_score": row[4],
                "total_findings": row[5],
                "critical_findings": row[6],
                "major_findings": row[7],
                "minor_findings": row[8],
                "file_size": row[9]
            })
        
        return {
            "success": True,
            "documents": documents,
            "total_count": len(documents)
        }
    except Exception as e:
        logger.error(f"Error fetching document history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

@app.get("/document-details/{document_id}")
async def get_document_details(document_id: int):
    """Get detailed analysis for a specific document"""
    try:
        conn = sqlite3.connect('compliance_history.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT analysis_result FROM documents WHERE id = ?
        ''', (document_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        analysis_result = json.loads(row[0])
        conn.close()
        
        return {
            "success": True,
            "analysis_result": analysis_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch details: {str(e)}")

# Rule Management Endpoints

def load_rules() -> List[Dict]:
    """Load rules from the JSON file."""
    try:
        if os.path.exists(RULES_FILE):
            with open(RULES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both formats for backward compatibility
                if isinstance(data, list):
                    # Old format - flat array
                    rules = data
                elif isinstance(data, dict) and 'rules' in data:
                    # New format - object with rules array
                    rules = data['rules']
                else:
                    rules = []
                logger.info(f"Loaded {len(rules)} rules from {RULES_FILE}")
                return rules
        else:
            logger.info(f"Rules file {RULES_FILE} not found, returning empty list")
            return []
    except Exception as e:
        logger.error(f"Error loading rules: {str(e)}")
        return []

def save_rules(rules: List[Dict]) -> bool:
    """Save rules to the JSON file."""
    try:
        # Save in the expected format with "rules" wrapper
        data = {"rules": rules}
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(rules)} rules to {RULES_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving rules: {str(e)}")
        return False

@app.post("/add-rule/")
async def add_rule(rule: Rule):
    """
    Add a new custom compliance rule.
    
    Args:
        rule: Rule object containing rule_text, rule_type, and severity
        
    Returns:
        JSON response confirming rule addition
    """
    try:
        # Load existing rules
        rules = load_rules()
        
        # Generate a better ID
        max_id = 0
        if rules:
            for existing_rule in rules:
                if isinstance(existing_rule, dict) and 'id' in existing_rule:
                    max_id = max(max_id, existing_rule['id'])
        
        # Create new rule entry
        new_rule = {
            "id": max_id + 1,
            "name": f"Custom Rule {max_id + 1}",  # Add a name field for consistency
            "description": rule.rule_text[:100] + "..." if len(rule.rule_text) > 100 else rule.rule_text,
            "rule_text": rule.rule_text,
            "rule_type": rule.rule_type,
            "severity": rule.severity,
            "created_at": datetime.now().isoformat()  # Better timestamp format
        }
        
        # Add new rule to the list
        rules.append(new_rule)
        
        # Save updated rules
        if save_rules(rules):
            logger.info(f"Added new rule: {rule.rule_text[:50]}...")
            return {
                "success": True,
                "message": "Rule added successfully",
                "rule_id": new_rule["id"],
                "total_rules": len(rules)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save rule")
            
    except Exception as e:
        logger.error(f"Error adding rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add rule: {str(e)}")

@app.get("/get-rules")
async def get_rules():
    """
    Retrieve all custom compliance rules.
    
    Returns:
        JSON response with list of all rules
    """
    try:
        rules = load_rules()
        
        return {
            "success": True,
            "rules": rules,
            "total_rules": len(rules)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rules: {str(e)}")

@app.delete("/delete-rule/{rule_id}")
async def delete_rule(rule_id: int):
    """
    Delete a specific compliance rule.
    
    Args:
        rule_id: ID of the rule to delete
        
    Returns:
        JSON response confirming rule deletion
    """
    try:
        # Load existing rules
        rules = load_rules()
        
        # Find and remove the rule
        original_count = len(rules)
        rules = [rule for rule in rules if rule.get("id") != rule_id]
        
        if len(rules) == original_count:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Save updated rules
        if save_rules(rules):
            logger.info(f"Deleted rule with ID: {rule_id}")
            return {
                "success": True,
                "message": "Rule deleted successfully",
                "total_rules": len(rules)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save updated rules")
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete rule: {str(e)}")

# Document-Specific Rule Management Endpoints

@app.post("/add-document-rule/{document_id}")
async def add_document_rule(document_id: int, rule: Rule):
    """Add a rule specific to a document"""
    try:
        conn = sqlite3.connect('compliance_history.db')
        cursor = conn.cursor()
        
        # Verify document exists
        cursor.execute('SELECT id FROM documents WHERE id = ?', (document_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Document not found")
        
        cursor.execute('''
            INSERT INTO document_rules (document_id, rule_text, rule_type, severity, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (document_id, rule.rule_text, rule.rule_type, rule.severity, datetime.now().isoformat()))
        
        rule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Document-specific rule added with ID: {rule_id}")
        return {
            "success": True,
            "rule_id": rule_id,
            "message": "Document-specific rule added successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding document rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add rule: {str(e)}")

@app.get("/document-rules/{document_id}")
async def get_document_rules(document_id: int):
    """Get rules specific to a document"""
    try:
        conn = sqlite3.connect('compliance_history.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, rule_text, rule_type, severity, created_at
            FROM document_rules 
            WHERE document_id = ?
            ORDER BY created_at DESC
        ''', (document_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        rules = []
        for row in rows:
            rules.append({
                "id": row[0],
                "rule_text": row[1],
                "rule_type": row[2],
                "severity": row[3],
                "created_at": row[4]
            })
        
        return {
            "success": True,
            "rules": rules,
            "document_id": document_id,
            "total_rules": len(rules)
        }
    except Exception as e:
        logger.error(f"Error fetching document rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch rules: {str(e)}")

@app.delete("/delete-document-rule/{rule_id}")
async def delete_document_rule(rule_id: int):
    """Delete a document-specific rule"""
    try:
        conn = sqlite3.connect('compliance_history.db')
        cursor = conn.cursor()
        
        # Check if rule exists
        cursor.execute('SELECT id FROM document_rules WHERE id = ?', (rule_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Document rule not found")
        
        # Delete the rule
        cursor.execute('DELETE FROM document_rules WHERE id = ?', (rule_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Document rule deleted with ID: {rule_id}")
        return {
            "success": True,
            "message": "Document rule deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete rule: {str(e)}")

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