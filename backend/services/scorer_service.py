"""
Compliance Scoring Service

Calculates compliance scores based on findings severity and provides
detailed breakdown information for healthcare technology documents.
"""

from typing import List, Dict, Any


def calculate_score(findings: list) -> int:
    """
    Calculate compliance score based on findings severity.
    
    Args:
        findings: List of findings from compliance analysis
        
    Returns:
        Integer compliance score (0-100)
    """
    weights = {"Critical": 3, "Major": 2, "Minor": 1}
    total_penalty = 0
    
    for finding in findings:
        severity = finding.get('severity', 'Minor')
        total_penalty += weights.get(severity, 1)
    
    score = max(0, 100 - total_penalty)
    return score


def calculate_score_detailed(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate detailed compliance score with breakdown information.
    
    Args:
        findings: List of findings from compliance analysis
        
    Returns:
        Dictionary containing score and breakdown information
    """
    score = calculate_score(findings)
    weights = {"Critical": 3, "Major": 2, "Minor": 1}
    
    severity_counts = {"Critical": 0, "Major": 0, "Minor": 0}
    total_penalty = 0
    
    for finding in findings:
        severity = finding.get("severity", "Minor")
        if severity in severity_counts:
            severity_counts[severity] += 1
        penalty = weights.get(severity, 1)
        total_penalty += penalty
    
    if score >= 90:
        compliance_level = "Excellent"
        compliance_color = "green"
    elif score >= 75:
        compliance_level = "Good"
        compliance_color = "blue"
    elif score >= 60:
        compliance_level = "Fair"
        compliance_color = "yellow"
    elif score >= 40:
        compliance_level = "Poor"
        compliance_color = "orange"
    else:
        compliance_level = "Critical"
        compliance_color = "red"
    
    rule_type_counts = {"Core": 0, "AI": 0}
    for finding in findings:
        rule_type = finding.get("rule_type", "Core")
        if rule_type in rule_type_counts:
            rule_type_counts[rule_type] += 1
    
    return {
        "score": score,
        "max_score": 100,
        "total_penalty": total_penalty,
        "compliance_level": compliance_level,
        "compliance_color": compliance_color,
        "total_findings": len(findings),
        "severity_breakdown": severity_counts,
        "rule_type_breakdown": rule_type_counts,
        "scoring_details": {
            "base_score": 100,
            "weights": weights,
            "calculation": f"Base (100) - Penalty ({total_penalty}) = Final ({score})"
        }
    }


def get_score_explanation(score_data: Dict[str, Any]) -> str:
    """Generate human-readable explanation of the compliance score."""
    score = score_data["score"]
    level = score_data["compliance_level"]
    total_findings = score_data["total_findings"]
    severity_breakdown = score_data["severity_breakdown"]
    
    explanation = f"Compliance Score: {score}/100 ({level})\n\n"
    
    if total_findings == 0:
        explanation += "Perfect compliance! No issues found in the document."
    else:
        explanation += f"Found {total_findings} compliance issue(s):\n"
        
        for severity, count in severity_breakdown.items():
            if count > 0:
                explanation += f"  • {severity}: {count} issue(s)\n"
        
        explanation += f"\nRecommendation: "
        if score >= 90:
            explanation += "Document shows excellent compliance with minor improvements needed."
        elif score >= 75:
            explanation += "Document is well-structured with some areas for improvement."
        elif score >= 60:
            explanation += "Document needs attention to meet full compliance standards."
        elif score >= 40:
            explanation += "Document requires significant improvements for compliance."
        else:
            explanation += "Document needs comprehensive review and major revisions."
    
    return explanation


def calculate_trend_score(historical_scores: List[float]) -> Dict[str, Any]:
    """Calculate compliance trend based on historical scores."""
    if len(historical_scores) < 2:
        return {
            "trend": "insufficient_data",
            "trend_direction": "neutral",
            "improvement": 0,
            "message": "Need at least 2 scores to calculate trend"
        }
    
    recent_scores = historical_scores[-5:]
    
    if len(recent_scores) >= 2:
        improvement = recent_scores[-1] - recent_scores[0]
        
        if improvement > 5:
            trend = "improving"
            direction = "up"
        elif improvement < -5:
            trend = "declining"
            direction = "down"
        else:
            trend = "stable"
            direction = "neutral"
        
        return {
            "trend": trend,
            "trend_direction": direction,
            "improvement": round(improvement, 1),
            "recent_average": round(sum(recent_scores) / len(recent_scores), 1),
            "best_score": max(historical_scores),
            "worst_score": min(historical_scores),
            "message": f"Compliance trend is {trend} with {abs(improvement):.1f} point {'increase' if improvement > 0 else 'decrease'}"
        }
    
    return {
        "trend": "insufficient_data",
        "trend_direction": "neutral", 
        "improvement": 0,
        "message": "Need more historical data for trend analysis"
    }