"""
GxP Compliance Linter Service

Provides comprehensive compliance analysis combining rule-based checks
and AI-powered analysis for healthcare technology documents.
"""

import re
import os
import json
import logging
from typing import Dict, List, Any, Optional
import openai
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


def check_missing_sections(doc_sections: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Core rule-based function to check for mandatory GxP sections.
    
    Robustly checks for the presence of mandatory sections with case-insensitive
    matching and whitespace handling.
    
    Args:
        doc_sections: Dictionary of section headers to content
        
    Returns:
        List of findings for missing mandatory sections
    """
    # Define mandatory sections for GxP compliance
    mandatory_sections = [
        "Purpose",
        "Scope", 
        "Responsibilities",
        "Revision History",
        "Approvals"
    ]
    
    findings = []
    
    # Normalize section headers for comparison (lowercase, strip whitespace)
    normalized_sections = {
        key.lower().strip(): key for key in doc_sections.keys()
    }
    
    # Check for each mandatory section
    for required_section in mandatory_sections:
        # Check if the required section exists (case-insensitive)
        section_found = False
        
        for normalized_key in normalized_sections.keys():
            # Check for exact match or if the required section is contained in the key
            if (required_section.lower() in normalized_key or 
                normalized_key in required_section.lower()):
                section_found = True
                break
        
        if not section_found:
            findings.append({
                "type": "missing_section",
                "severity": "Critical",
                "section": required_section,
                "description": f"Missing mandatory section: '{required_section}'",
                "details": f"GxP documents must include a '{required_section}' section for compliance.",
                "location": "Document structure",
                "rule_type": "Core"
            })
    
    return findings


def check_placeholders(full_text: str) -> List[Dict[str, Any]]:
    """
    Core rule-based function to detect placeholder text that indicates incomplete documentation.
    
    Searches for specific placeholder strings in a case-insensitive manner.
    
    Args:
        full_text: Complete text content of the document
        
    Returns:
        List of findings for placeholder text detected
    """
    # Define placeholder patterns to search for
    placeholder_patterns = [
        "TBD",
        "lorem ipsum", 
        "to be decided",
        "TODO",
        "FIXME",
        "placeholder",
        "insert text here",
        "add content",
        "fill in",
        "replace this"
    ]
    
    findings = []
    
    # Search for each placeholder pattern (case-insensitive)
    for pattern in placeholder_patterns:
        # Use regex for case-insensitive search with word boundaries
        matches = re.finditer(rf'\b{re.escape(pattern)}\b', full_text, re.IGNORECASE)
        
        for match in matches:
            # Get context around the match (50 characters before and after)
            start_pos = max(0, match.start() - 50)
            end_pos = min(len(full_text), match.end() + 50)
            context = full_text[start_pos:end_pos].strip()
            
            findings.append({
                "type": "placeholder_text",
                "severity": "Major",
                "pattern": pattern,
                "description": f"Placeholder text detected: '{pattern}'",
                "details": f"Document contains incomplete content marked with placeholder '{pattern}'",
                "context": context,
                "position": match.start(),
                "rule_type": "Core"
            })
    
    return findings


def check_reference_staleness(references_text: str, client: AzureOpenAI, chat_deployment: str) -> List[Dict[str, Any]]:
    """
    AI-powered function for checking stale references using Azure OpenAI.
    
    Analyzes reference text to identify potentially outdated references.
    
    Args:
        references_text: Text containing references to analyze
        client: Initialized AzureOpenAI client
        chat_deployment: Name of the chat deployment to use
        
    Returns:
        List of findings for outdated references
    """
    if not references_text or not references_text.strip():
        return []
    
    findings = []
    
    try:
        # Create a strict prompt for reference analysis
        prompt = f"""
You are a regulatory compliance expert analyzing document references for staleness.

INSTRUCTIONS:
1. Analyze the following references for potential staleness
2. Consider a reference outdated if it:
   - References very old versions of standards (more than 5 years old)
   - Uses deprecated terminology
   - References superseded regulations
   - Contains obviously outdated dates or version numbers

3. Respond ONLY with a JSON array. No explanatory text.
4. Each object must have exactly these keys:
   - "reference": the original reference text
   - "is_outdated": boolean (true if outdated, false if current)

REFERENCES TO ANALYZE:
{references_text}

RESPONSE FORMAT (JSON only):
"""

        # Call Azure OpenAI
        response = client.chat.completions.create(
            model=chat_deployment,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a regulatory compliance expert. Respond only with valid JSON arrays as requested."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=1000
        )
        
        # Extract and parse the response
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        try:
            # Handle potential markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Parse JSON response
            analysis_results = json.loads(response_text)
            
            # Process results and create findings
            for item in analysis_results:
                if isinstance(item, dict) and item.get("is_outdated", False):
                    findings.append({
                        "type": "outdated_reference",
                        "severity": "Major",
                        "reference": item.get("reference", "Unknown reference"),
                        "description": f"Potentially outdated reference detected",
                        "details": f"The reference '{item.get('reference', 'Unknown')}' may be outdated and should be reviewed for current versions.",
                        "rule_type": "AI"
                    })
        
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse AI response as JSON: {e}")
            print(f"Response was: {response_text}")
            
    except Exception as e:
        print(f"Error in AI reference checking: {str(e)}")
        # Add a finding about the analysis failure
        findings.append({
            "type": "analysis_error",
            "severity": "Minor", 
            "description": "Could not analyze references for staleness",
            "details": f"AI analysis failed: {str(e)}",
            "rule_type": "AI"
        })
    
    return findings


def run_all_checks(parsed_data: Dict[str, Any], client: AzureOpenAI, chat_deployment: str, embedding_deployment: str) -> List[Dict[str, Any]]:
    """
    Master function to run all compliance checks and enrich findings with RAG explanations.
    
    Orchestrates core rule-based checks, AI-powered analysis, and knowledge base enrichment.
    
    Args:
        parsed_data: Parsed document data from parser service
        client: Initialized AzureOpenAI client
        chat_deployment: Name of the chat deployment
        embedding_deployment: Name of the embedding deployment
        
    Returns:
        List of enriched findings with explanations
    """
    # Initialize findings list
    all_findings = []
    
    print("🔍 Starting comprehensive GxP compliance analysis...")
    
    # Run Core rule-based checks
    print("📋 Running core rule-based checks...")
    
    # Check for missing sections
    doc_sections = parsed_data.get("sections", {})
    missing_section_findings = check_missing_sections(doc_sections)
    all_findings.extend(missing_section_findings)
    print(f"   • Found {len(missing_section_findings)} missing section issues")
    
    # Check for placeholders
    full_text = parsed_data.get("full_text", "")
    placeholder_findings = check_placeholders(full_text)
    all_findings.extend(placeholder_findings)
    print(f"   • Found {len(placeholder_findings)} placeholder text issues")
    
    # Run AI-powered reference checking
    print("🤖 Running AI-powered reference analysis...")
    
    # Extract references text (try multiple possible section names)
    references_text = ""
    reference_section_names = ["references", "reference", "bibliography", "citations"]
    
    for section_name, section_content in doc_sections.items():
        if any(ref_name in section_name.lower() for ref_name in reference_section_names):
            references_text = section_content
            break
    
    if references_text:
        # Split references by common delimiters and analyze each
        reference_delimiters = ['\n', ';', '|']
        references_list = [references_text]
        
        for delimiter in reference_delimiters:
            new_refs = []
            for ref in references_list:
                new_refs.extend([r.strip() for r in ref.split(delimiter) if r.strip()])
            references_list = new_refs
        
        # Analyze each reference
        for reference in references_list:
            if len(reference) > 10:  # Only analyze substantial references
                ref_findings = check_reference_staleness(reference, client, chat_deployment)
                all_findings.extend(ref_findings)
        
        print(f"   • Analyzed {len(references_list)} references")
    else:
        print("   • No references section found")
    
    # Initialize RAG service and enrich findings with explanations
    print("📚 Enriching findings with knowledge base explanations...")
    
    try:
        # Import RAG service (will create placeholder if it doesn't exist yet)
        try:
            from services.rag_service import RAGService
            rag_service = RAGService()
            rag_available = True
        except ImportError:
            print("   ⚠️  RAG service not yet available, skipping explanations")
            rag_available = False
        
        # Enrich each finding with contextual explanation
        if rag_available:
            for finding in all_findings:
                try:
                    # Create query based on finding type and description
                    query = f"{finding['type']} {finding['description']} GxP compliance"
                    explanation = rag_service.query(query)
                    finding["explanation"] = explanation
                except Exception as e:
                    finding["explanation"] = f"Could not retrieve explanation: {str(e)}"
        else:
            # Add placeholder explanations
            for finding in all_findings:
                finding["explanation"] = "Knowledge base explanation will be available once RAG service is implemented."
    
    except Exception as e:
        print(f"   ⚠️  Error enriching findings: {str(e)}")
        # Add basic explanations as fallback
        for finding in all_findings:
            finding["explanation"] = f"Basic explanation: {finding['details']}"
    
    # Final summary
    print(f"\n✅ Compliance analysis complete!")
    print(f"📊 Total findings: {len(all_findings)}")
    
    # Count by severity
    severity_counts = {}
    for finding in all_findings:
        severity = finding.get("severity", "Unknown")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    for severity, count in severity_counts.items():
        print(f"   • {severity}: {count}")
    
    return all_findings


def get_finding_summary(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Utility function to generate a summary of findings.
    
    Args:
        findings: List of findings from compliance analysis
        
    Returns:
        Dictionary with summary statistics
    """
    summary = {
        "total_findings": len(findings),
        "by_severity": {},
        "by_type": {},
        "by_rule_type": {}
    }
    
    for finding in findings:
        # Count by severity
        severity = finding.get("severity", "Unknown")
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        
        # Count by type
        finding_type = finding.get("type", "Unknown")
        summary["by_type"][finding_type] = summary["by_type"].get(finding_type, 0) + 1
        
        # Count by rule type
        rule_type = finding.get("rule_type", "Unknown")
        summary["by_rule_type"][rule_type] = summary["by_rule_type"].get(rule_type, 0) + 1
    
    return summary