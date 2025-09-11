"""
CRAEFTO Monitoring System
Comprehensive monitoring, logging, health checks, and alerting for the automation platform
"""
import asyncio
import logging
import time
import json
import smtplib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import psutil
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

class AlertType(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class OperationStatus(Enum):
    """Operation status types"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    RETRY = "retry"

@dataclass
class OperationLog:
    """Operation log entry"""
    timestamp: datetime
    operation_type: str
    status: OperationStatus
    duration_ms: float
    details: Dict[str, Any]
    error: Optional[str] = None
    retry_count: int = 0
    cost_usd: float = 0.0

@dataclass
class HealthMetric:
    """Health metric data"""
    name: str
    value: float
    status: str
    threshold: float
    timestamp: datetime

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")
        
        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        return (datetime.utcnow() - self.last_failure_time).seconds > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class CraeftoMonitor:
    """Comprehensive monitoring system for CRAEFTO automation platform"""
    
    def __init__(self):
        self.error_threshold = 5
        self.alert_email = "team@craefto.com"
        self.operation_logs = deque(maxlen=10000)  # Keep last 10k operations
        self.circuit_breakers = {}
        self.health_metrics = {}
        self.api_costs = defaultdict(float)
        self.performance_cache = {}
        self.alert_cooldown = {}  # Prevent spam alerts
        
        # API fallback configurations
        self.api_fallbacks = {
            "openai": ["anthropic", "cached_content"],
            "anthropic": ["openai", "cached_content"],
            "replicate": ["pillow_fallback"],
            "twitter": ["manual_queue"],
            "linkedin": ["manual_queue"],
            "supabase": ["local_sqlite", "file_storage"]
        }
        
        # Cost tracking per API
        self.api_cost_rates = {
            "openai_gpt4": 0.03,  # per 1k tokens
            "anthropic_claude": 0.008,  # per 1k tokens
            "replicate": 0.05,  # per image
            "twitter_api": 0.001,  # per request
            "linkedin_api": 0.001,  # per request
        }
        
        logger.info("🔍 CRAEFTO Monitor initialized")
    
    async def log_operation(
        self, 
        operation_type: str, 
        status: OperationStatus, 
        details: Dict[str, Any],
        duration_ms: float = 0,
        error: str = None,
        retry_count: int = 0,
        cost_usd: float = 0.0
    ):
        """
        Log every operation with comprehensive details
        
        Args:
            operation_type: Type of operation (e.g., 'content_generation', 'api_call')
            status: Success/failure/partial status
            details: Operation-specific details
            duration_ms: Operation duration in milliseconds
            error: Error message if failed
            retry_count: Number of retries attempted
            cost_usd: Cost in USD for the operation
        """
        try:
            log_entry = OperationLog(
                timestamp=datetime.utcnow(),
                operation_type=operation_type,
                status=status,
                duration_ms=duration_ms,
                details=details,
                error=error,
                retry_count=retry_count,
                cost_usd=cost_usd
            )
            
            self.operation_logs.append(log_entry)
            
            # Update API costs
            if cost_usd > 0 and 'api_name' in details:
                self.api_costs[details['api_name']] += cost_usd
            
            # Log to standard logger
            log_level = logging.ERROR if status == OperationStatus.FAILURE else logging.INFO
            logger.log(
                log_level,
                f"📊 {operation_type}: {status.value} ({duration_ms:.2f}ms) - {details.get('description', 'No description')}"
            )
            
            # Check for alert conditions
            if status == OperationStatus.FAILURE:
                await self._check_failure_alerts(operation_type, error)
            
        except Exception as e:
            logger.error(f"❌ Failed to log operation: {str(e)}")
    
    async def handle_api_failure(
        self, 
        api_name: str, 
        error: Exception, 
        retry_count: int = 3,
        operation_details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Smart retry logic with fallbacks and exponential backoff
        
        Args:
            api_name: Name of the failing API
            error: The exception that occurred
            retry_count: Maximum number of retries
            operation_details: Details about the operation for fallback
            
        Returns:
            Result dictionary with success status and data/fallback info
        """
        try:
            logger.warning(f"⚠️ API failure detected: {api_name} - {str(error)}")
            
            # Log initial failure
            await self.log_operation(
                operation_type=f"api_failure_{api_name}",
                status=OperationStatus.FAILURE,
                details={
                    "api_name": api_name,
                    "error": str(error),
                    "operation_details": operation_details or {}
                },
                error=str(error)
            )
            
            # Get or create circuit breaker for this API
            if api_name not in self.circuit_breakers:
                self.circuit_breakers[api_name] = CircuitBreaker()
            
            circuit_breaker = self.circuit_breakers[api_name]
            
            # Attempt retries with exponential backoff
            for attempt in range(retry_count):
                try:
                    if circuit_breaker.state == "OPEN":
                        logger.warning(f"🚫 Circuit breaker OPEN for {api_name}, skipping retry")
                        break
                    
                    # Exponential backoff: 2^attempt seconds + jitter
                    wait_time = (2 ** attempt) + (time.time() % 1)
                    logger.info(f"🔄 Retrying {api_name} in {wait_time:.2f}s (attempt {attempt + 1}/{retry_count})")
                    
                    await asyncio.sleep(wait_time)
                    
                    # This would be where you retry the actual API call
                    # For now, we'll simulate a retry attempt
                    retry_result = await self._simulate_api_retry(api_name, operation_details)
                    
                    if retry_result.get("success"):
                        await self.log_operation(
                            operation_type=f"api_retry_success_{api_name}",
                            status=OperationStatus.SUCCESS,
                            details={
                                "api_name": api_name,
                                "retry_attempt": attempt + 1,
                                "result": retry_result
                            },
                            retry_count=attempt + 1
                        )
                        circuit_breaker._on_success()
                        return retry_result
                    
                except Exception as retry_error:
                    logger.error(f"❌ Retry {attempt + 1} failed for {api_name}: {str(retry_error)}")
                    circuit_breaker._on_failure()
                    continue
            
            # All retries failed, try fallbacks
            logger.warning(f"🔄 All retries failed for {api_name}, attempting fallbacks")
            fallback_result = await self._try_fallbacks(api_name, operation_details)
            
            if fallback_result.get("success"):
                return fallback_result
            
            # All fallbacks failed, send alert
            await self.send_alert(
                AlertType.CRITICAL,
                f"API {api_name} completely failed after {retry_count} retries and all fallbacks"
            )
            
            return {
                "success": False,
                "error": f"All retries and fallbacks failed for {api_name}",
                "fallback_attempted": True
            }
            
        except Exception as e:
            logger.error(f"❌ Error in handle_api_failure: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _simulate_api_retry(self, api_name: str, operation_details: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate API retry - replace with actual API calls"""
        # This is a placeholder - in real implementation, you'd make the actual API call
        import random
        success_rate = 0.3  # 30% chance of success on retry
        
        if random.random() < success_rate:
            return {
                "success": True,
                "data": f"Retry successful for {api_name}",
                "method": "retry"
            }
        else:
            raise Exception(f"Simulated retry failure for {api_name}")
    
    async def _try_fallbacks(self, api_name: str, operation_details: Dict[str, Any]) -> Dict[str, Any]:
        """Try fallback APIs in order of preference"""
        fallbacks = self.api_fallbacks.get(api_name, [])
        
        for fallback in fallbacks:
            try:
                logger.info(f"🔄 Trying fallback: {fallback} for {api_name}")
                
                if fallback == "cached_content":
                    # Try to get cached content
                    cached_result = await self._get_cached_content(operation_details)
                    if cached_result:
                        await self.log_operation(
                            operation_type=f"fallback_cache_{api_name}",
                            status=OperationStatus.SUCCESS,
                            details={"fallback_used": "cached_content", "original_api": api_name}
                        )
                        return {"success": True, "data": cached_result, "method": "cached"}
                
                elif fallback == "manual_queue":
                    # Queue for manual processing
                    await self._queue_for_manual_processing(api_name, operation_details)
                    return {
                        "success": True, 
                        "data": "Queued for manual processing", 
                        "method": "manual_queue"
                    }
                
                elif fallback == "pillow_fallback":
                    # Use Pillow for image generation
                    result = await self._pillow_image_fallback(operation_details)
                    if result:
                        return {"success": True, "data": result, "method": "pillow_fallback"}
                
                else:
                    # Try alternative API
                    alt_result = await self._try_alternative_api(fallback, operation_details)
                    if alt_result.get("success"):
                        return alt_result
                
            except Exception as fallback_error:
                logger.error(f"❌ Fallback {fallback} failed: {str(fallback_error)}")
                continue
        
        return {"success": False, "error": "All fallbacks failed"}
    
    async def _get_cached_content(self, operation_details: Dict[str, Any]) -> Optional[str]:
        """Get cached content if available"""
        # Implement cache lookup logic
        cache_key = operation_details.get("cache_key") or operation_details.get("topic", "default")
        
        # This would connect to your cache (Redis, memory, etc.)
        # For now, return mock cached content
        if cache_key in self.performance_cache:
            logger.info(f"✅ Found cached content for: {cache_key}")
            return self.performance_cache[cache_key]
        
        return None
    
    async def _queue_for_manual_processing(self, api_name: str, operation_details: Dict[str, Any]):
        """Queue operation for manual processing"""
        # This would add to a manual processing queue
        logger.info(f"📝 Queued for manual processing: {api_name}")
        # In real implementation, save to database or queue system
        pass
    
    async def _pillow_image_fallback(self, operation_details: Dict[str, Any]) -> Optional[str]:
        """Generate fallback image using Pillow"""
        try:
            # This would use your existing Pillow image generation
            logger.info("🎨 Generating fallback image with Pillow")
            return "pillow_generated_image_placeholder"
        except Exception as e:
            logger.error(f"❌ Pillow fallback failed: {str(e)}")
            return None
    
    async def _try_alternative_api(self, alt_api: str, operation_details: Dict[str, Any]) -> Dict[str, Any]:
        """Try alternative API"""
        try:
            # This would make a call to the alternative API
            logger.info(f"🔄 Trying alternative API: {alt_api}")
            # Simulate alternative API call
            return {"success": True, "data": f"Alternative API {alt_api} result", "method": alt_api}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive system health monitoring
        
        Returns:
            Health report with scores and alerts
        """
        try:
            health_report = {
                "overall_health": "healthy",
                "health_score": 100,
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {},
                "alerts": []
            }
            
            # API availability checks
            api_health = await self._check_api_availability()
            health_report["checks"]["api_availability"] = api_health
            
            # Database connection check
            db_health = await self._check_database_connection()
            health_report["checks"]["database"] = db_health
            
            # Queue depth check
            queue_health = await self._check_queue_depth()
            health_report["checks"]["queue"] = queue_health
            
            # Memory usage check
            memory_health = await self._check_memory_usage()
            health_report["checks"]["memory"] = memory_health
            
            # Error rate check
            error_health = await self._check_error_rate()
            health_report["checks"]["error_rate"] = error_health
            
            # Circuit breaker status
            circuit_health = await self._check_circuit_breakers()
            health_report["checks"]["circuit_breakers"] = circuit_health
            
            # Calculate overall health score
            health_scores = [
                api_health.get("score", 0),
                db_health.get("score", 0),
                queue_health.get("score", 0),
                memory_health.get("score", 0),
                error_health.get("score", 0),
                circuit_health.get("score", 0)
            ]
            
            overall_score = sum(health_scores) / len(health_scores)
            health_report["health_score"] = round(overall_score, 2)
            
            # Determine overall health status
            if overall_score >= 90:
                health_report["overall_health"] = "healthy"
            elif overall_score >= 70:
                health_report["overall_health"] = "warning"
            else:
                health_report["overall_health"] = "critical"
            
            # Collect alerts from all checks
            for check_name, check_result in health_report["checks"].items():
                if check_result.get("alerts"):
                    health_report["alerts"].extend(check_result["alerts"])
            
            logger.info(f"🏥 Health check completed: {health_report['overall_health']} ({overall_score:.1f}%)")
            
            return health_report
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return {
                "overall_health": "critical",
                "health_score": 0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _check_api_availability(self) -> Dict[str, Any]:
        """Check availability of external APIs"""
        api_results = {}
        api_endpoints = {
            "openai": "https://api.openai.com/v1/models",
            "anthropic": "https://api.anthropic.com/v1/messages",
            # Add other API endpoints
        }
        
        available_count = 0
        total_count = len(api_endpoints)
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for api_name, endpoint in api_endpoints.items():
                try:
                    async with session.get(endpoint) as response:
                        if response.status < 500:  # Not a server error
                            api_results[api_name] = "available"
                            available_count += 1
                        else:
                            api_results[api_name] = f"error_{response.status}"
                except Exception as e:
                    api_results[api_name] = f"unreachable_{str(e)[:50]}"
        
        availability_score = (available_count / total_count) * 100
        
        return {
            "score": availability_score,
            "status": "healthy" if availability_score > 80 else "warning" if availability_score > 50 else "critical",
            "details": api_results,
            "available": available_count,
            "total": total_count,
            "alerts": [] if availability_score > 80 else [f"API availability low: {availability_score:.1f}%"]
        }
    
    async def _check_database_connection(self) -> Dict[str, Any]:
        """Check database connection health"""
        try:
            # This would check your actual database connection
            # For now, we'll simulate a check
            from app.utils.database import get_database
            
            db = get_database()
            if db:
                # Simulate a simple query
                connection_healthy = True
                response_time_ms = 50  # Mock response time
            else:
                connection_healthy = False
                response_time_ms = 0
            
            score = 100 if connection_healthy else 0
            status = "healthy" if connection_healthy else "critical"
            
            return {
                "score": score,
                "status": status,
                "connected": connection_healthy,
                "response_time_ms": response_time_ms,
                "alerts": [] if connection_healthy else ["Database connection failed"]
            }
            
        except Exception as e:
            return {
                "score": 0,
                "status": "critical",
                "connected": False,
                "error": str(e),
                "alerts": [f"Database check failed: {str(e)}"]
            }
    
    async def _check_queue_depth(self) -> Dict[str, Any]:
        """Check processing queue depth"""
        # This would check your actual queue system
        # For now, simulate queue metrics
        queue_depth = len(self.operation_logs)  # Use operation logs as proxy
        max_queue_size = 1000
        
        queue_ratio = queue_depth / max_queue_size
        score = max(0, 100 - (queue_ratio * 100))
        
        status = "healthy" if queue_ratio < 0.7 else "warning" if queue_ratio < 0.9 else "critical"
        
        return {
            "score": score,
            "status": status,
            "queue_depth": queue_depth,
            "max_queue_size": max_queue_size,
            "queue_ratio": queue_ratio,
            "alerts": [] if queue_ratio < 0.8 else [f"Queue depth high: {queue_depth}/{max_queue_size}"]
        }
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check system memory usage"""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            score = max(0, 100 - memory_percent)
            status = "healthy" if memory_percent < 80 else "warning" if memory_percent < 90 else "critical"
            
            return {
                "score": score,
                "status": status,
                "memory_percent": memory_percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "alerts": [] if memory_percent < 85 else [f"High memory usage: {memory_percent:.1f}%"]
            }
            
        except Exception as e:
            return {
                "score": 0,
                "status": "critical",
                "error": str(e),
                "alerts": [f"Memory check failed: {str(e)}"]
            }
    
    async def _check_error_rate(self) -> Dict[str, Any]:
        """Check recent error rate"""
        # Analyze recent operation logs
        recent_cutoff = datetime.utcnow() - timedelta(minutes=15)  # Last 15 minutes
        recent_ops = [log for log in self.operation_logs if log.timestamp > recent_cutoff]
        
        if not recent_ops:
            return {"score": 100, "status": "healthy", "error_rate": 0, "alerts": []}
        
        error_count = sum(1 for log in recent_ops if log.status == OperationStatus.FAILURE)
        error_rate = (error_count / len(recent_ops)) * 100
        
        score = max(0, 100 - (error_rate * 2))  # Penalize errors heavily
        status = "healthy" if error_rate < 5 else "warning" if error_rate < 15 else "critical"
        
        return {
            "score": score,
            "status": status,
            "error_rate": round(error_rate, 2),
            "error_count": error_count,
            "total_operations": len(recent_ops),
            "alerts": [] if error_rate < 10 else [f"High error rate: {error_rate:.1f}%"]
        }
    
    async def _check_circuit_breakers(self) -> Dict[str, Any]:
        """Check circuit breaker status"""
        open_breakers = [name for name, breaker in self.circuit_breakers.items() if breaker.state == "OPEN"]
        half_open_breakers = [name for name, breaker in self.circuit_breakers.items() if breaker.state == "HALF_OPEN"]
        
        total_breakers = len(self.circuit_breakers)
        healthy_breakers = total_breakers - len(open_breakers) - len(half_open_breakers)
        
        if total_breakers == 0:
            score = 100
        else:
            score = (healthy_breakers / total_breakers) * 100
        
        status = "healthy" if not open_breakers else "warning" if len(open_breakers) < 3 else "critical"
        
        alerts = []
        if open_breakers:
            alerts.append(f"Circuit breakers OPEN: {', '.join(open_breakers)}")
        if half_open_breakers:
            alerts.append(f"Circuit breakers HALF_OPEN: {', '.join(half_open_breakers)}")
        
        return {
            "score": score,
            "status": status,
            "open_breakers": open_breakers,
            "half_open_breakers": half_open_breakers,
            "total_breakers": total_breakers,
            "alerts": alerts
        }
    
    async def performance_tracking(self) -> Dict[str, Any]:
        """
        Track comprehensive system performance metrics
        
        Returns:
            Performance report with metrics and recommendations
        """
        try:
            # Analyze recent operations
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)  # Last 24 hours
            recent_ops = [log for log in self.operation_logs if log.timestamp > recent_cutoff]
            
            if not recent_ops:
                return {"message": "No recent operations to analyze"}
            
            # Content generation speed analysis
            content_ops = [log for log in recent_ops if "content" in log.operation_type.lower()]
            avg_content_time = sum(log.duration_ms for log in content_ops) / len(content_ops) if content_ops else 0
            
            # API cost analysis
            total_cost = sum(log.cost_usd for log in recent_ops)
            cost_by_api = defaultdict(float)
            for log in recent_ops:
                if log.cost_usd > 0 and 'api_name' in log.details:
                    cost_by_api[log.details['api_name']] += log.cost_usd
            
            # Success rate analysis
            success_count = sum(1 for log in recent_ops if log.status == OperationStatus.SUCCESS)
            success_rate = (success_count / len(recent_ops)) * 100
            
            # Operation type breakdown
            op_type_counts = defaultdict(int)
            op_type_avg_time = defaultdict(list)
            for log in recent_ops:
                op_type_counts[log.operation_type] += 1
                op_type_avg_time[log.operation_type].append(log.duration_ms)
            
            # Calculate average times
            op_type_performance = {}
            for op_type, times in op_type_avg_time.items():
                op_type_performance[op_type] = {
                    "count": op_type_counts[op_type],
                    "avg_time_ms": sum(times) / len(times),
                    "max_time_ms": max(times),
                    "min_time_ms": min(times)
                }
            
            # Identify bottlenecks
            bottlenecks = []
            for op_type, perf in op_type_performance.items():
                if perf["avg_time_ms"] > 5000:  # Operations taking >5 seconds
                    bottlenecks.append({
                        "operation": op_type,
                        "avg_time_ms": perf["avg_time_ms"],
                        "recommendation": f"Consider optimizing {op_type} - avg time {perf['avg_time_ms']:.0f}ms"
                    })
            
            # Cost optimization opportunities
            cost_optimizations = []
            for api, cost in cost_by_api.items():
                if cost > 10:  # APIs costing more than $10/day
                    cost_optimizations.append({
                        "api": api,
                        "daily_cost": cost,
                        "recommendation": f"High cost API: {api} (${cost:.2f}/day) - consider caching or alternatives"
                    })
            
            performance_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "period_hours": 24,
                "total_operations": len(recent_ops),
                "success_rate": round(success_rate, 2),
                "content_generation": {
                    "operations": len(content_ops),
                    "avg_time_ms": round(avg_content_time, 2),
                    "status": "good" if avg_content_time < 3000 else "slow"
                },
                "api_costs": {
                    "total_daily_cost": round(total_cost, 4),
                    "cost_by_api": dict(cost_by_api),
                    "monthly_projection": round(total_cost * 30, 2)
                },
                "operation_performance": op_type_performance,
                "bottlenecks": bottlenecks,
                "cost_optimizations": cost_optimizations,
                "recommendations": self._generate_performance_recommendations(
                    success_rate, avg_content_time, total_cost, bottlenecks
                )
            }
            
            logger.info(f"📈 Performance tracking completed: {len(recent_ops)} operations analyzed")
            
            return performance_report
            
        except Exception as e:
            logger.error(f"❌ Performance tracking failed: {str(e)}")
            return {"error": str(e)}
    
    def _generate_performance_recommendations(
        self, 
        success_rate: float, 
        avg_content_time: float, 
        total_cost: float, 
        bottlenecks: List[Dict]
    ) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if success_rate < 95:
            recommendations.append(f"Improve error handling - success rate is {success_rate:.1f}%")
        
        if avg_content_time > 3000:
            recommendations.append(f"Optimize content generation - avg time {avg_content_time:.0f}ms")
        
        if total_cost > 50:
            recommendations.append(f"Review API costs - daily spend ${total_cost:.2f}")
        
        if bottlenecks:
            recommendations.append(f"Address {len(bottlenecks)} performance bottlenecks")
        
        if not recommendations:
            recommendations.append("System performance is optimal")
        
        return recommendations
    
    async def send_alert(self, alert_type: AlertType, message: str, details: Dict[str, Any] = None):
        """
        Multi-channel alert system
        
        Args:
            alert_type: Severity level of alert
            message: Alert message
            details: Additional alert details
        """
        try:
            # Check cooldown to prevent spam
            alert_key = f"{alert_type.value}_{message[:50]}"
            last_sent = self.alert_cooldown.get(alert_key)
            
            cooldown_minutes = 60 if alert_type == AlertType.CRITICAL else 180
            if last_sent and (datetime.utcnow() - last_sent).seconds < cooldown_minutes * 60:
                logger.debug(f"🔇 Alert in cooldown: {alert_key}")
                return
            
            self.alert_cooldown[alert_key] = datetime.utcnow()
            
            alert_data = {
                "type": alert_type.value,
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
                "system": "CRAEFTO Automation"
            }
            
            # Log the alert
            logger.warning(f"🚨 ALERT [{alert_type.value.upper()}]: {message}")
            
            # Send email for critical alerts
            if alert_type == AlertType.CRITICAL:
                await self._send_email_alert(alert_data)
            
            # Send Slack notification for warnings and critical
            if alert_type in [AlertType.CRITICAL, AlertType.WARNING]:
                await self._send_slack_alert(alert_data)
            
            # Always log to dashboard/monitoring system
            await self._log_dashboard_alert(alert_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to send alert: {str(e)}")
    
    async def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send email alert"""
        try:
            # This would use your email service (SMTP, SendGrid, etc.)
            # For now, we'll log what would be sent
            
            subject = f"🚨 CRAEFTO Alert: {alert_data['type'].upper()}"
            body = f"""
            Alert Type: {alert_data['type']}
            Message: {alert_data['message']}
            Timestamp: {alert_data['timestamp']}
            System: {alert_data['system']}
            
            Details:
            {json.dumps(alert_data['details'], indent=2)}
            """
            
            logger.info(f"📧 Email alert would be sent to {self.alert_email}")
            logger.info(f"Subject: {subject}")
            
            # Uncomment and configure for actual email sending:
            # await self._actual_send_email(self.alert_email, subject, body)
            
        except Exception as e:
            logger.error(f"❌ Failed to send email alert: {str(e)}")
    
    async def _send_slack_alert(self, alert_data: Dict[str, Any]):
        """Send Slack alert"""
        try:
            # This would use Slack webhook or API
            # For now, we'll log what would be sent
            
            slack_message = {
                "text": f"🚨 CRAEFTO Alert: {alert_data['message']}",
                "attachments": [
                    {
                        "color": "danger" if alert_data['type'] == "critical" else "warning",
                        "fields": [
                            {"title": "Type", "value": alert_data['type'], "short": True},
                            {"title": "Time", "value": alert_data['timestamp'], "short": True}
                        ]
                    }
                ]
            }
            
            logger.info(f"💬 Slack alert would be sent: {slack_message['text']}")
            
            # Uncomment and configure for actual Slack sending:
            # await self._actual_send_slack(slack_message)
            
        except Exception as e:
            logger.error(f"❌ Failed to send Slack alert: {str(e)}")
    
    async def _log_dashboard_alert(self, alert_data: Dict[str, Any]):
        """Log alert to dashboard/monitoring system"""
        try:
            # This would save to your monitoring dashboard
            logger.info(f"📊 Dashboard alert logged: {alert_data['type']} - {alert_data['message']}")
            
            # Save to operation logs for tracking
            await self.log_operation(
                operation_type="system_alert",
                status=OperationStatus.SUCCESS,
                details=alert_data
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to log dashboard alert: {str(e)}")
    
    async def _check_failure_alerts(self, operation_type: str, error: str):
        """Check if we should send failure alerts"""
        # Count recent failures for this operation type
        recent_cutoff = datetime.utcnow() - timedelta(minutes=10)
        recent_failures = [
            log for log in self.operation_logs 
            if log.timestamp > recent_cutoff 
            and log.operation_type == operation_type 
            and log.status == OperationStatus.FAILURE
        ]
        
        if len(recent_failures) >= self.error_threshold:
            await self.send_alert(
                AlertType.WARNING,
                f"High failure rate for {operation_type}: {len(recent_failures)} failures in 10 minutes"
            )
    
    def get_operation_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get operation statistics for the specified time period"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_ops = [log for log in self.operation_logs if log.timestamp > cutoff]
        
        if not recent_ops:
            return {"message": "No operations in specified time period"}
        
        stats = {
            "total_operations": len(recent_ops),
            "success_rate": (sum(1 for log in recent_ops if log.status == OperationStatus.SUCCESS) / len(recent_ops)) * 100,
            "avg_duration_ms": sum(log.duration_ms for log in recent_ops) / len(recent_ops),
            "total_cost_usd": sum(log.cost_usd for log in recent_ops),
            "operation_types": {},
            "error_summary": {}
        }
        
        # Operation type breakdown
        for log in recent_ops:
            if log.operation_type not in stats["operation_types"]:
                stats["operation_types"][log.operation_type] = {"count": 0, "avg_time": 0, "success_rate": 0}
            
            stats["operation_types"][log.operation_type]["count"] += 1
        
        # Calculate averages and success rates for each operation type
        for op_type in stats["operation_types"]:
            type_ops = [log for log in recent_ops if log.operation_type == op_type]
            stats["operation_types"][op_type]["avg_time"] = sum(log.duration_ms for log in type_ops) / len(type_ops)
            stats["operation_types"][op_type]["success_rate"] = (sum(1 for log in type_ops if log.status == OperationStatus.SUCCESS) / len(type_ops)) * 100
        
        return stats

# Decorator for automatic operation logging
def monitor_operation(operation_type: str, cost_usd: float = 0.0):
    """
    Decorator to automatically log operations
    
    Usage:
        @monitor_operation("content_generation", cost_usd=0.05)
        async def generate_content():
            # Your function code
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            monitor = CraeftoMonitor()  # In production, use a singleton instance
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                await monitor.log_operation(
                    operation_type=operation_type,
                    status=OperationStatus.SUCCESS,
                    details={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                        "result_type": type(result).__name__
                    },
                    duration_ms=duration_ms,
                    cost_usd=cost_usd
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                await monitor.log_operation(
                    operation_type=operation_type,
                    status=OperationStatus.FAILURE,
                    details={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    },
                    duration_ms=duration_ms,
                    error=str(e),
                    cost_usd=cost_usd
                )
                
                raise e
        
        return wrapper
    return decorator

# Global monitor instance (use singleton pattern in production)
global_monitor = CraeftoMonitor()
