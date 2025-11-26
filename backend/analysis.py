import pandas as pd
import numpy as np
from typing import List, Dict, Any

def analyze_logs(logs_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not logs_list:
        return {
            "summary": "No logs available for analysis.",
            "threat_score": 0.0,
            "recommendations": ["Ensure log collection agents are active."],
            "flagged_logs": []
        }
    
    # Load logs into DataFrame
    # Ensure keys match what pandas expects if coming from Pydantic dumps (camelCase vs snake_case)
    # The frontend expects camelCase in response, so inputs might vary.
    # We will normalize to snake_case for analysis if needed, or just use what we have.
    # If logs come from DB (ORM objects), we should convert them to dicts first in main.py.
    
    df = pd.DataFrame(logs_list)
    
    # Normalize column names if necessary (handle riskLevel vs risk_level)
    if 'riskLevel' in df.columns:
        df['risk_level'] = df['riskLevel']
    
    if 'risk_level' not in df.columns:
         # Fallback if no risk info
         return {
            "summary": "Logs missing risk level information.",
            "threat_score": 0.0,
            "recommendations": ["Check log format."],
            "flagged_logs": []
        }

    total_logs = len(df)
    
    # Calculate threat score based on % of 'CRITICAL' logs
    critical_logs = df[df['risk_level'] == 'CRITICAL']
    critical_count = len(critical_logs)
    
    high_logs = df[df['risk_level'] == 'HIGH']
    high_count = len(high_logs)
    
    # Heuristic: (Critical * 10 + High * 5) / Total * 10
    # Adjusted to not explode with few logs
    if total_logs > 0:
        raw_score = ((critical_count * 10) + (high_count * 5)) / total_logs * 100
        # Normalize to 0-100 but keep it sensitive
        threat_score = min(100.0, raw_score)
    else:
        threat_score = 0.0

    # Generate Summary
    summary = f"Analyzed {total_logs} events. Detected {critical_count} critical and {high_count} high-severity anomalies."
    if threat_score > 50:
        summary += " System is under significant threat pressure."
    else:
        summary += " System status is within nominal parameters."

    # Generate Recommendations
    recommendations = []
    if critical_count > 0:
        recommendations.append(f"IMMEDIATE: Investigate {critical_count} critical incidents.")
        recommendations.append("Initiate lockdown for affected users.")
    
    if high_count > 5:
        recommendations.append("Review firewall rules and access control lists.")
        recommendations.append("Audit user permissions for high-risk accounts.")
        
    if threat_score < 20:
        recommendations.append("Continue standard monitoring protocols.")
        recommendations.append("Update threat signatures.")

    if not recommendations:
        recommendations.append("No immediate actions required.")

    # Flagged Logs (return IDs)
    flagged_logs = critical_logs['id'].tolist() if not critical_logs.empty else []

    return {
        "summary": summary,
        "threat_score": round(threat_score, 2),
        "recommendations": recommendations,
        "flagged_logs": flagged_logs
    }
