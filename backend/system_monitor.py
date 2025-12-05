import psutil
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import models

_last_metrics = None
_last_metrics_time = 0
_CACHE_DURATION = 1  # seconds

def get_system_metrics():
    global _last_metrics, _last_metrics_time
    
    current_time = time.time()
    if _last_metrics and (current_time - _last_metrics_time) < _CACHE_DURATION:
        return _last_metrics

    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "cpu": {
            "usage_percent": cpu_usage,
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        },
        "disk": {
            "total": disk.total,
            "free": disk.free,
            "percent": disk.percent,
            "used": disk.used
        }
    }
    
    _last_metrics = metrics
    _last_metrics_time = current_time
    return metrics

def save_metric(db: Session):
    metrics = get_system_metrics()
    
    db_metric = models.SystemMetric(
        timestamp=datetime.now(),
        cpu_usage=metrics["cpu"]["usage_percent"],
        memory_total=metrics["memory"]["total"],
        memory_used=metrics["memory"]["used"],
        memory_percent=metrics["memory"]["percent"],
        disk_total=metrics["disk"]["total"],
        disk_used=metrics["disk"]["used"],
        disk_percent=metrics["disk"]["percent"]
    )
    db.add(db_metric)
    db.commit()
    
    # Cleanup old metrics (> 24 hours)
    cutoff = datetime.now() - timedelta(hours=24)
    db.query(models.SystemMetric).filter(models.SystemMetric.timestamp < cutoff).delete()
    db.commit()

def get_history(db: Session):
    cutoff = datetime.now() - timedelta(hours=24)
    metrics = db.query(models.SystemMetric).filter(models.SystemMetric.timestamp >= cutoff).order_by(models.SystemMetric.timestamp).all()
    
    result = []
    for m in metrics:
        result.append({
            "timestamp": m.timestamp.isoformat(),
            "cpu": {"usage_percent": m.cpu_usage},
            "memory": {
                "total": m.memory_total,
                "available": m.memory_total - m.memory_used,
                "percent": m.memory_percent,
                "used": m.memory_used
            },
            "disk": {
                "total": m.disk_total,
                "free": m.disk_total - m.disk_used,
                "percent": m.disk_percent,
                "used": m.disk_used
            }
        })
    return result
