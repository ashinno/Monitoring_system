import csv
import json
import io
import zipfile
from fpdf import FPDF
from datetime import datetime
from fastapi.responses import StreamingResponse, Response

def export_logs(logs, format="csv", compress=False):
    content = None
    media_type = ""
    filename = ""

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Timestamp", "User", "Activity", "Risk Level", "Description", "IP", "Details"])
        for log in logs:
            writer.writerow([
                log.id, 
                log.timestamp, 
                log.user, 
                log.activity_type, 
                log.risk_level, 
                log.description, 
                log.ip_address,
                log.details
            ])
        output.seek(0)
        content = output.getvalue().encode('utf-8')
        media_type = "text/csv"
        filename = "logs.csv"
    
    elif format == "json":
        data = []
        for log in logs:
            d = {
                "id": log.id,
                "timestamp": log.timestamp,
                "user": log.user,
                "activity_type": log.activity_type,
                "risk_level": log.risk_level,
                "description": log.description,
                "details": log.details,
                "ip_address": log.ip_address,
                "location": log.location
            }
            data.append(d)
        content = json.dumps(data, default=str).encode('utf-8')
        media_type = "application/json"
        filename = "logs.json"

    elif format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Security Incident Report", 0, 1, 'C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 10, f"Generated on: {datetime.now().isoformat()}", 0, 1, 'C')
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 10)
        # Simple table header
        pdf.cell(40, 7, "Timestamp", 1)
        pdf.cell(30, 7, "Level", 1)
        pdf.cell(40, 7, "User", 1)
        pdf.cell(80, 7, "Description", 1)
        pdf.ln()
        
        pdf.set_font("Arial", '', 8)
        for log in logs:
            # Truncate content to fit
            ts = log.timestamp[:19]
            risk = log.risk_level
            user = log.user[:20]
            desc = log.description[:50]
            
            pdf.cell(40, 6, ts, 1)
            pdf.cell(30, 6, risk, 1)
            pdf.cell(40, 6, user, 1)
            pdf.cell(80, 6, desc, 1)
            pdf.ln()
            
        content = pdf.output(dest='S').encode('latin-1')
        media_type = "application/pdf"
        filename = "logs.pdf"
    else:
        return {"error": "Invalid format"}

    if compress:
        zip_output = io.BytesIO()
        with zipfile.ZipFile(zip_output, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(filename, content)
        zip_output.seek(0)
        return StreamingResponse(iter([zip_output.getvalue()]), media_type="application/zip", headers={"Content-Disposition": "attachment; filename=logs.zip"})

    return Response(content=content, media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})
