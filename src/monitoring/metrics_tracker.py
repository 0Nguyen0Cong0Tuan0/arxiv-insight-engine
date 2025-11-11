# src/monitoring/metrics_tracker.py
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
from pathlib import Path
from threading import Lock
import time
from functools import wraps

@dataclass
class MetricRecord:
    """Single metric record"""
    timestamp: str
    operation: str  # retrieve, qa, summarize, compare, analyze, fact_check, tts, stt
    latency: float
    success: bool
    tokens_used: int = 0
    cost_estimate: float = 0.0
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return asdict(self)

class MetricsTracker:
    """Tracks metrics for the entire RAG pipeline"""
    _instance = None
    _lock = Lock()
    
    # Cost estimates (USD per 1K tokens) - assumed rates
    COST_RATES = {
        "llm": 0.0002,  # Hugging Face Inference API estimate
        "embedding": 0.00001,
        "whisper": 0.006,  # per minute
        "tts": 0.000001  # per character
    }
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.metrics: List[MetricRecord] = []
        self.metrics_file = Path("data/metrics_log.jsonl")
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_metrics()
    
    def _load_metrics(self):
        """Load existing metrics from file"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    for line in f:
                        record = json.loads(line)
                        self.metrics.append(MetricRecord(**record))
            except Exception as e:
                print(f"Error loading metrics: {e}")
    
    def _save_metric(self, metric: MetricRecord):
        """Append metric to file"""
        try:
            with open(self.metrics_file, 'a') as f:
                f.write(json.dumps(metric.to_dict()) + '\n')
        except Exception as e:
            print(f"Error saving metric: {e}")
    
    def track_operation(
        self,
        operation: str,
        tokens_used: int = 0,
        metadata: Optional[Dict] = None
    ):
        """Decorator to track operation metrics"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_msg = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error_msg = str(e)
                    raise
                finally:
                    latency = time.time() - start_time
                    
                    # Estimate cost based on operation
                    cost = self._estimate_cost(operation, tokens_used, latency)
                    
                    # Create metric record
                    metric = MetricRecord(
                        timestamp=datetime.now().isoformat(),
                        operation=operation,
                        latency=latency,
                        success=success,
                        tokens_used=tokens_used,
                        cost_estimate=cost,
                        metadata={
                            **(metadata or {}),
                            "error": error_msg if not success else None
                        }
                    )
                    
                    # Store metric
                    with self._lock:
                        self.metrics.append(metric)
                        self._save_metric(metric)
            
            return wrapper
        return decorator
    
    def record_operation(
        self,
        operation: str,
        latency: float,
        success: bool = True,
        tokens_used: int = 0,
        metadata: Optional[Dict] = None
    ):
        """Manually record an operation metric"""
        cost = self._estimate_cost(operation, tokens_used, latency)
        
        metric = MetricRecord(
            timestamp=datetime.now().isoformat(),
            operation=operation,
            latency=latency,
            success=success,
            tokens_used=tokens_used,
            cost_estimate=cost,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.metrics.append(metric)
            self._save_metric(metric)
    
    def _estimate_cost(self, operation: str, tokens: int, latency: float) -> float:
        """Estimate cost based on operation type"""
        if operation in ["simple_qa", "summarize", "compare", "analyze", "fact_check"]:
            return (tokens / 1000) * self.COST_RATES["llm"]
        elif operation == "retrieve":
            return (tokens / 1000) * self.COST_RATES["embedding"]
        elif operation == "stt":  # Speech-to-text
            minutes = latency / 60
            return minutes * self.COST_RATES["whisper"]
        elif operation == "tts":  # Text-to-speech
            return tokens * self.COST_RATES["tts"]
        return 0.0
    
    def get_summary_stats(self, hours: int = 24) -> Dict:
        """Get summary statistics for the last N hours"""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        recent_metrics = [
            m for m in self.metrics
            if datetime.fromisoformat(m.timestamp).timestamp() > cutoff
        ]
        
        if not recent_metrics:
            return {
                "total_operations": 0,
                "success_rate": 0.0,
                "avg_latency": 0.0,
                "total_cost": 0.0,
                "operations_breakdown": {}
            }
        
        # Calculate stats
        total = len(recent_metrics)
        successful = sum(1 for m in recent_metrics if m.success)
        total_latency = sum(m.latency for m in recent_metrics)
        total_cost = sum(m.cost_estimate for m in recent_metrics)
        
        # Operation breakdown
        operations = {}
        for metric in recent_metrics:
            if metric.operation not in operations:
                operations[metric.operation] = {
                    "count": 0,
                    "avg_latency": 0.0,
                    "total_cost": 0.0,
                    "success_rate": 0.0
                }
            
            op_stats = operations[metric.operation]
            op_stats["count"] += 1
            op_stats["avg_latency"] += metric.latency
            op_stats["total_cost"] += metric.cost_estimate
            if metric.success:
                op_stats["success_rate"] += 1
        
        # Calculate averages
        for op_stats in operations.values():
            count = op_stats["count"]
            op_stats["avg_latency"] /= count
            op_stats["success_rate"] = (op_stats["success_rate"] / count) * 100
        
        return {
            "total_operations": total,
            "success_rate": (successful / total) * 100,
            "avg_latency": total_latency / total,
            "total_cost": total_cost,
            "operations_breakdown": operations,
            "time_window_hours": hours
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Get recent error records"""
        errors = [
            {
                "timestamp": m.timestamp,
                "operation": m.operation,
                "error": m.metadata.get("error"),
                "latency": m.latency
            }
            for m in reversed(self.metrics)
            if not m.success
        ]
        return errors[:limit]
    
    def export_metrics(self, output_path: str = "metrics_export.json"):
        """Export all metrics to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(
                [m.to_dict() for m in self.metrics],
                f,
                indent=2
            )
        print(f"Metrics exported to {output_path}")

# Global instance
metrics_tracker = MetricsTracker()


# Integration wrapper for agent nodes
def track_node_execution(node_name: str):
    """Decorator for tracking agent node execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(state):
            start_time = time.time()
            success = True
            
            try:
                result = func(state)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                latency = time.time() - start_time
                
                # Estimate tokens (rough approximation)
                tokens = len(str(state.get("query", ""))) // 4
                if "retrieved_chunks" in state:
                    tokens += sum(len(c.page_content) // 4 for c in state["retrieved_chunks"][:5])
                
                metrics_tracker.record_operation(
                    operation=node_name,
                    latency=latency,
                    success=success,
                    tokens_used=tokens,
                    metadata={
                        "query": state.get("query", ""),
                        "route": state.get("route", "unknown")
                    }
                )
        
        return wrapper
    return decorator