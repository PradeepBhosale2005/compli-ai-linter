"""
AI-Powered GxP Compliance Linter Service

Revolutionary approach using a single, intelligent AI auditor instead of hardcoded rules.
The AI acts as a comprehensive compliance expert that understands all GxP requirements.
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


def create_master_compliance_prompt(full_text: str, doc_sections: Dict[str, str]) -> str:
    """
    Creates the ultimate hybrid compliance prompt combining hardcoded core rules with dynamic user rules.
    
    This hybrid approach provides:
    1. Reliable baseline GxP compliance (hardcoded core rules)
    2. Configurable extensions (user-defined rules from frontend)
    3. Single powerful AI audit combining both
    
    Args:
        full_text: Complete document text
        doc_sections: Dictionary of section headers to content
        
    Returns:
        Complete hybrid prompt string for comprehensive AI analysis
    """
    
    # 1. CORE GxP RULES (Hardcoded - Non-negotiable baseline)
    core_gxp_rules = [
        "**MANDATORY SECTIONS:** The document must contain sections covering these 9 areas: Title, Purpose, Scope, Responsibilities, Definitions, Procedure, References, Revision History, and Approvals.",
        "**DOCUMENT ID:** The document must have a 'Document ID' in the format 'SOP-###' (e.g., SOP-001, SOP-123).",
        "**VERSION & DATE:** The document must have a 'Version/Revision' number and an 'Effective Date' in the format 'YYYY-MM-DD'.",
        "**REVISION HISTORY:** The 'Revision History' section must contain at least one entry with version, date, and description of changes.",
        "**PLACEHOLDER TEXT:** The document must not contain any placeholder text like 'TBD', 'TODO', 'lorem ipsum', 'insert text here', or 'add content'.",
        "**PROCEDURE CLARITY:** The 'Procedure' section must contain at least three distinct, numbered steps for proper execution clarity.",
        "**SIGNATURE LINES:** There must be clear signature lines for 'Prepared by', 'Reviewed by', and 'Approved by' with fields for name, title, date, and signature.",
        "**REFERENCE QUALITY:** All references must include publication years (e.g., 'ISO 13485:2016' not just 'ISO 13485') and should be current versions.",
        "**OUTDATED STANDARDS:** Flag outdated references like 'ISO 9001:1994' (replaced by ISO 9001:2015), old CFR parts, or undated ICH guidelines."
    ]
    
    # 2. DYNAMIC GxP RULES (User-defined from frontend)
    dynamic_gxp_rules = []
    rules_file_path = "gxp_rules.json"
    
    try:
        if os.path.exists(rules_file_path):
            with open(rules_file_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
                # Handle both old format (list) and new format (dict with rules array)
                if isinstance(rules_data, list):
                    for rule in rules_data:
                        if isinstance(rule, dict):
                            rule_text = rule.get('rule_text', '')
                            severity = rule.get('severity', 'Major')
                            dynamic_gxp_rules.append(f"**USER RULE [{severity}]:** {rule_text}")
                        elif isinstance(rule, str):
                            dynamic_gxp_rules.append(f"**USER RULE [Major]:** {rule}")
                elif isinstance(rules_data, dict) and 'rules' in rules_data:
                    for rule in rules_data['rules']:
                        if isinstance(rule, dict):
                            rule_text = rule.get('rule_text', '')
                            severity = rule.get('severity', 'Major')
                            formatted_rule = f"**USER RULE [{severity}]:** {rule_text}"
                            dynamic_gxp_rules.append(formatted_rule)
                
                logger.info(f"✅ Loaded {len(dynamic_gxp_rules)} dynamic user-defined rules")
        else:
            logger.info("No dynamic rules file found - using core rules only")
            
    except Exception as e:
        logger.error(f"Error loading dynamic rules: {str(e)}")
        dynamic_gxp_rules.append("**SYSTEM NOTE:** Could not load user-defined rules, using core rules only")
    
    # 3. COMBINE CORE + DYNAMIC RULES INTO MASTER LIST
    all_rules = core_gxp_rules + dynamic_gxp_rules
    total_rules = len(all_rules)
    
    # Format rules for the prompt
    formatted_rules = "\n".join(f"{i+1}. {rule}" for i, rule in enumerate(all_rules))
    
    # Create section summary for AI analysis
    sections_summary = ""
    if doc_sections:
        sections_summary = "**DOCUMENT SECTIONS FOUND:**\n"
        for header, content in doc_sections.items():
            # Truncate long content for prompt efficiency
            content_preview = content[:200] + "..." if len(content) > 200 else content
            sections_summary += f"\n## {header}\n{content_preview}\n"
    
    # 4. CREATE THE MASTER HYBRID PROMPT
    prompt = f"""You are an expert GxP compliance auditor with 20+ years of experience in pharmaceutical and medical device regulations. You will perform a comprehensive audit using both CORE regulatory requirements and CUSTOM user-defined rules.

**HYBRID GxP COMPLIANCE RULES ({total_rules} total rules):**
{formatted_rules}

{sections_summary}

**FULL DOCUMENT TEXT:**
---
{full_text[:4000]}{"..." if len(full_text) > 4000 else ""}
---

**COMPREHENSIVE AUDIT INSTRUCTIONS:**
1. Systematically check the document against ALL {total_rules} rules above
2. Apply both regulatory baseline requirements (Core Rules 1-{len(core_gxp_rules)}) and custom organizational rules (User Rules {len(core_gxp_rules)+1}-{total_rules})
3. Look for missing elements, inadequate implementations, and non-compliance issues
4. Consider regulatory audit trail requirements and quality assurance perspectives
5. Provide specific, actionable recommendations for each finding

**RESPONSE FORMAT:**
Respond with ONLY a valid JSON array of finding objects. Each finding must have exactly these keys:
- "type": Brief category (e.g., "missing_mandatory_section", "inadequate_procedure", "user_rule_violation")
- "severity": Must be exactly "Critical", "Major", or "Minor"
- "description": Clear, professional description of the compliance issue
- "details": Detailed explanation of what's wrong and why it matters for GxP compliance
- "location": Where in the document this issue occurs
- "rule_reference": Which rule number (1-{total_rules}) this violation relates to
- "rule_type": "Core" for baseline GxP rules or "Dynamic" for user-defined rules
- "recommendation": Specific, actionable steps to fix this issue

**SEVERITY GUIDELINES:**
- Critical: Missing mandatory sections, missing approvals, major regulatory non-compliance
- Major: Inadequate content, missing metadata, poor procedure clarity, user rule violations
- Minor: Formatting issues, minor omissions that don't significantly affect compliance

If the document is fully compliant with all {total_rules} rules, return an empty array [].

Return ONLY the JSON array - no explanatory text, no markdown formatting, no additional comments.
"""
    
    return prompt


def run_ai_audit(full_text: str, doc_sections: Dict[str, str], client: AzureOpenAI, chat_deployment: str) -> List[Dict[str, Any]]:
    """
    Performs comprehensive GxP compliance audit using AI.
    
    This replaces all hardcoded compliance checks with intelligent AI analysis
    that understands GxP requirements and can adapt to different document types.
    
    Args:
        full_text: Complete document text
        doc_sections: Dictionary of section headers to content
        client: Initialized AzureOpenAI client
        chat_deployment: Name of the chat deployment
        
    Returns:
        List of compliance findings from AI audit
    """
    findings = []
    
    try:
        print("🧠 Starting Hybrid AI-powered GxP compliance audit...")
        print("   • Combining core regulatory rules + user-defined rules...")
        
        # Create the master compliance prompt
        prompt = create_master_compliance_prompt(full_text, doc_sections)
        
        print("   • Analyzing document against comprehensive rule set...")
        
        # Call Azure OpenAI with the comprehensive prompt
        response = client.chat.completions.create(
            model=chat_deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert GxP compliance auditor. Always respond with valid JSON arrays only. Never include explanatory text outside the JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            #temperature=0.1,  # Low temperature for consistent compliance analysis
            #max_completion_tokens=3000,  # Allow for comprehensive findings - updated parameter name
            #top_p=0.9
        )
        
        # Extract and parse the AI response
        response_text = response.choices[0].message.content.strip()
        
        print(f"   • Hybrid AI audit completed, processing response...")
        
        # Clean up response text - remove any markdown formatting
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        # Parse JSON response
        try:
            ai_findings = json.loads(response_text)
            
            # Validate that we got a list
            if isinstance(ai_findings, list):
                # Process and enrich each finding
                for finding in ai_findings:
                    if isinstance(finding, dict):
                        # Ensure all required fields are present
                        enriched_finding = {
                            "type": finding.get("type", "compliance_issue"),
                            "severity": finding.get("severity", "Major"),
                            "description": finding.get("description", "Compliance issue detected"),
                            "details": finding.get("details", "Hybrid AI-detected compliance concern"),
                            "location": finding.get("location", "Document"),
                            "rule_reference": finding.get("rule_reference", "General"),
                            "rule_type": finding.get("rule_type", "AI-Hybrid"),
                            "recommendation": finding.get("recommendation", "Review and update as needed")
                        }
                        findings.append(enriched_finding)
                
                print(f"   • ✅ Hybrid AI audit found {len(findings)} compliance issues")
                
                # Log findings summary by rule type
                rule_type_counts = {}
                severity_counts = {}
                for finding in findings:
                    rule_type = finding.get("rule_type", "Unknown")
                    rule_type_counts[rule_type] = rule_type_counts.get(rule_type, 0) + 1
                    
                    severity = finding.get("severity", "Unknown")
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                print(f"     📊 By rule type:")
                for rule_type, count in rule_type_counts.items():
                    print(f"       - {rule_type}: {count}")
                    
                print(f"     📊 By severity:")
                for severity, count in severity_counts.items():
                    print(f"       - {severity}: {count}")
                    
            else:
                print(f"   • ⚠️ Warning: Expected list of findings, got {type(ai_findings)}")
                logger.warning(f"Hybrid AI audit returned unexpected format: {type(ai_findings)}")
                
        except json.JSONDecodeError as e:
            print(f"   • ❌ Error: Could not parse hybrid AI audit response as JSON")
            logger.error(f"JSON parsing failed: {str(e)}")
            logger.debug(f"Response was: {response_text[:500]}...")
            
            # Add a finding about the parsing failure
            findings.append({
                "type": "audit_parsing_error",
                "severity": "Minor",
                "description": "Hybrid AI audit response could not be parsed",
                "details": f"The hybrid AI compliance audit completed but the response format was invalid: {str(e)}",
                "location": "System",
                "rule_reference": "System",
                "rule_type": "System",
                "recommendation": "Retry the audit or contact system administrator"
            })
            
    except Exception as e:
        print(f"   • ❌ Error during AI audit: {str(e)}")
        logger.error(f"AI audit failed: {str(e)}")
        
        # Add a finding about the audit failure
        findings.append({
            "type": "audit_system_error", 
            "severity": "Minor",
            "description": "AI compliance audit system error",
            "details": f"The AI compliance audit could not be completed due to a system error: {str(e)}",
            "location": "System",
            "rule_reference": "System", 
            "recommendation": "Retry the audit or contact system administrator",
            "rule_type": "System"
        })
    
    return findings


def run_all_checks(parsed_data: Dict[str, Any], client: AzureOpenAI, chat_deployment: str, embedding_deployment: str, document_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Master function that orchestrates the Hybrid AI-powered compliance audit.
    
    This combines reliable hardcoded core GxP rules with dynamic user-defined rules
    from the frontend, creating the ultimate flexible yet robust compliance system.
    
    Args:
        parsed_data: Parsed document data from parser service
        client: Initialized AzureOpenAI client
        chat_deployment: Name of the chat deployment
        embedding_deployment: Name of the embedding deployment (kept for compatibility)
        document_id: Optional document ID for potential future custom rules
        
    Returns:
        List of comprehensive compliance findings from hybrid AI audit
    """
    
    print("🚀 Starting Hybrid AI-powered GxP compliance analysis...")
    print("   💡 Using Core Regulatory Rules + User-Defined Extensions")
    
    # Extract document data
    full_text = parsed_data.get("full_text", "")
    doc_sections = parsed_data.get("sections", {})
    
    if not full_text.strip():
        return [{
            "type": "empty_document",
            "severity": "Critical", 
            "description": "Document appears to be empty or unreadable",
            "details": "No text content could be extracted from the document for analysis",
            "location": "Document",
            "rule_reference": "System",
            "rule_type": "System",
            "recommendation": "Ensure the document contains readable content and try uploading again"
        }]
    
    print(f"   • Document loaded: {len(full_text)} characters, {len(doc_sections)} sections")
    
    # Run the hybrid AI audit (core + dynamic rules)
    all_findings = run_ai_audit(full_text, doc_sections, client, chat_deployment)
    
    # Add any document-specific rules if document_id is provided (future enhancement)
    if document_id:
        print(f"   • Note: Document-specific rules for ID {document_id} can be integrated in future versions")
    
    # Final summary
    print(f"\n✅ Hybrid AI-powered compliance analysis complete!")
    print(f"📊 Total findings: {len(all_findings)}")
    
    if all_findings:
        print("📋 Summary by rule origin:")
        rule_type_counts = {}
        severity_counts = {}
        for finding in all_findings:
            rule_type = finding.get("rule_type", "Unknown")
            rule_type_counts[rule_type] = rule_type_counts.get(rule_type, 0) + 1
            
            severity = finding.get("severity", "Unknown") 
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for rule_type, count in rule_type_counts.items():
            print(f"   • {rule_type}: {count}")
            
        print("📋 Summary by severity:")
        for severity, count in severity_counts.items():
            print(f"   • {severity}: {count}")
    else:
        print("🎉 Document appears to be fully GxP compliant across all rules!")
    
    return all_findings


def get_finding_summary(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Utility function to generate a summary of findings.
    
    Args:
        findings: List of findings from AI compliance audit
        
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