import pandas as pd
import numpy as np
from typing import List, Dict, Any
import ml_engine

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

    # Generate SHAP explanations for high-risk logs
    explanations = {}
    high_risk_df = df[df['risk_level'].isin(['HIGH', 'CRITICAL'])]
    
    for _, row in high_risk_df.iterrows():
        try:
            # We need to pass a dict or object to extract_features
            # row is a Series, let's convert to dict
            log_dict = row.to_dict()
            features = ml_engine.extract_features(log_dict)
            explanation = ml_engine.explain_prediction(features)
            if explanation:
                explanations[row['id']] = explanation
        except Exception as e:
            print(f"Error explaining log {row.get('id')}: {e}")

    return {
        "summary": summary,
        "threat_score": round(threat_score, 2),
        "recommendations": recommendations,
        "flagged_logs": flagged_logs,
        "explanations": explanations
    }

def analyze_network_traffic(traffic_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not traffic_list:
        return {
            "summary": "No network traffic data available.",
            "anomaly_score": 0.0,
            "anomalies_detected": 0,
            "details": []
        }

    df = pd.DataFrame(traffic_list)
    
    anomalies = []
    
    # 1. High Byte Transfer
    # Threshold: e.g., > 100MB (100 * 1024 * 1024)
    HIGH_BYTE_THRESHOLD = 100 * 1024 * 1024
    if 'bytes_transferred' in df.columns:
        high_byte_events = df[df['bytes_transferred'] > HIGH_BYTE_THRESHOLD]
        for _, row in high_byte_events.iterrows():
            anomalies.append({
                "type": "High Data Transfer",
                "source": row.get('source_ip', 'Unknown'),
                "destination": row.get('destination_ip', 'Unknown'),
                "value": f"{row['bytes_transferred'] / (1024*1024):.2f} MB",
                "id": row.get('id')
            })

    # 2. Suspicious Ports - Port Scanning Detection
    # Multiple distinct destination ports from same source IP
    port_scan_threshold = 10
    if 'source_ip' in df.columns and 'port' in df.columns:
        ports_per_ip = df.groupby('source_ip')['port'].nunique()
        scanners = ports_per_ip[ports_per_ip > port_scan_threshold]
        for ip, count in scanners.items():
            anomalies.append({
                "type": "Potential Port Scan",
                "source": ip,
                "destination": "Multiple",
                "value": f"{count} unique ports",
                "id": None
            })

    # 3. DDoS Potential (High packet count)
    PACKET_THRESHOLD = 10000
    if 'packet_count' in df.columns:
        high_packet_events = df[df['packet_count'] > PACKET_THRESHOLD]
        for _, row in high_packet_events.iterrows():
             anomalies.append({
                "type": "High Packet Volume (DDoS Risk)",
                "source": row.get('source_ip', 'Unknown'),
                "destination": row.get('destination_ip', 'Unknown'),
                "value": f"{row['packet_count']} packets",
                "id": row.get('id')
            })

    total_events = len(df)
    anomaly_count = len(anomalies)
    
    # Simple score calculation
    anomaly_score = (anomaly_count / total_events * 100) if total_events > 0 else 0.0
    
    summary = f"Analyzed {total_events} traffic events. Detected {anomaly_count} anomalies."

    return {
        "summary": summary,
        "anomaly_score": round(min(100.0, anomaly_score), 2),
        "anomalies_detected": anomaly_count,
        "details": anomalies
    }
