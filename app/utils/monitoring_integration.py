"""
CRAEFTO Monitoring Integration Examples
Shows how to integrate the monitoring system with existing agents and API endpoints
"""
import asyncio
from typing import Dict, Any

from app.utils.monitoring import (
    CraeftoMonitor, 
    monitor_operation, 
    OperationStatus, 
    AlertType,
    global_monitor
)

# Example: Integrating with ResearchAgent
class MonitoredResearchAgent:
    """Example of how to integrate monitoring with ResearchAgent"""
    
    def __init__(self):
        self.monitor = global_monitor
        self.sources = ["reddit", "producthunt", "twitter", "google_trends"]
    
    @monitor_operation("research_trending_topics", cost_usd=0.02)
    async def find_trending_topics(self) -> Dict[str, Any]:
        """Find trending topics with automatic monitoring"""
        try:
            # Simulate the actual research operation
            trending_data = await self._perform_research()
            
            # Log additional details
            await self.monitor.log_operation(
                operation_type="research_sources_scraped",
                status=OperationStatus.SUCCESS,
                details={
                    "sources_used": self.sources,
                    "topics_found": len(trending_data),
                    "cache_hit": False
                },
                duration_ms=1500
            )
            
            return trending_data
            
        except Exception as e:
            # Handle API failure with smart retry
            retry_result = await self.monitor.handle_api_failure(
                api_name="research_apis",
                error=e,
                retry_count=3,
                operation_details={"operation": "trending_research", "sources": self.sources}
            )
            
            if retry_result.get("success"):
                return retry_result["data"]
            else:
                raise e
    
    async def _perform_research(self):
        """Simulate research operation"""
        # This would be your actual research logic
        import random
        if random.random() < 0.1:  # 10% chance of failure
            raise Exception("Research API temporarily unavailable")
        
        return [
            {"topic": "SaaS Analytics", "relevance_score": 95},
            {"topic": "AI Automation", "relevance_score": 87}
        ]

# Example: Integrating with ContentGenerator
class MonitoredContentGenerator:
    """Example of how to integrate monitoring with ContentGenerator"""
    
    def __init__(self):
        self.monitor = global_monitor
    
    async def generate_blog_post(self, topic: str, research_data: Dict = None) -> Dict[str, Any]:
        """Generate blog post with comprehensive monitoring"""
        operation_start = asyncio.get_event_loop().time()
        
        try:
            # Log operation start
            await self.monitor.log_operation(
                operation_type="content_generation_start",
                status=OperationStatus.SUCCESS,
                details={
                    "content_type": "blog_post",
                    "topic": topic,
                    "has_research_data": research_data is not None
                }
            )
            
            # Try OpenAI first
            try:
                result = await self._generate_with_openai(topic, research_data)
                cost = 0.15  # Estimated cost for GPT-4
                
                await self.monitor.log_operation(
                    operation_type="openai_blog_generation",
                    status=OperationStatus.SUCCESS,
                    details={
                        "model": "gpt-4",
                        "topic": topic,
                        "word_count": len(result.get("content", "").split())
                    },
                    duration_ms=(asyncio.get_event_loop().time() - operation_start) * 1000,
                    cost_usd=cost
                )
                
                return result
                
            except Exception as openai_error:
                # Handle OpenAI failure with fallback to Anthropic
                retry_result = await self.monitor.handle_api_failure(
                    api_name="openai",
                    error=openai_error,
                    retry_count=2,
                    operation_details={
                        "content_type": "blog_post",
                        "topic": topic,
                        "fallback_available": True
                    }
                )
                
                if retry_result.get("success"):
                    return retry_result["data"]
                
                # Try Anthropic fallback
                logger.info("🔄 Falling back to Anthropic for blog generation")
                result = await self._generate_with_anthropic(topic, research_data)
                cost = 0.08  # Estimated cost for Claude
                
                await self.monitor.log_operation(
                    operation_type="anthropic_blog_generation",
                    status=OperationStatus.SUCCESS,
                    details={
                        "model": "claude-3",
                        "topic": topic,
                        "fallback_used": True,
                        "original_error": str(openai_error)
                    },
                    duration_ms=(asyncio.get_event_loop().time() - operation_start) * 1000,
                    cost_usd=cost
                )
                
                return result
                
        except Exception as e:
            # Log final failure
            await self.monitor.log_operation(
                operation_type="content_generation_failure",
                status=OperationStatus.FAILURE,
                details={
                    "topic": topic,
                    "error_type": type(e).__name__
                },
                duration_ms=(asyncio.get_event_loop().time() - operation_start) * 1000,
                error=str(e)
            )
            
            # Send alert for content generation failure
            await self.monitor.send_alert(
                AlertType.WARNING,
                f"Content generation failed for topic: {topic}",
                details={"error": str(e), "topic": topic}
            )
            
            raise e
    
    async def _generate_with_openai(self, topic: str, research_data: Dict = None):
        """Simulate OpenAI content generation"""
        import random
        if random.random() < 0.15:  # 15% chance of failure
            raise Exception("OpenAI API rate limit exceeded")
        
        return {
            "content": f"Generated blog post about {topic} using OpenAI...",
            "meta_description": f"Learn about {topic} in this comprehensive guide",
            "word_count": 1200
        }
    
    async def _generate_with_anthropic(self, topic: str, research_data: Dict = None):
        """Simulate Anthropic content generation"""
        import random
        if random.random() < 0.05:  # 5% chance of failure
            raise Exception("Anthropic API temporarily unavailable")
        
        return {
            "content": f"Generated blog post about {topic} using Anthropic Claude...",
            "meta_description": f"Discover {topic} insights and best practices",
            "word_count": 1100
        }

# Example: Enhanced API endpoint with monitoring
async def monitored_api_endpoint_example():
    """Example of how to integrate monitoring into API endpoints"""
    from fastapi import HTTPException
    
    monitor = global_monitor
    
    try:
        # Log API request start
        await monitor.log_operation(
            operation_type="api_request_start",
            status=OperationStatus.SUCCESS,
            details={
                "endpoint": "/api/generate/blog",
                "method": "POST"
            }
        )
        
        # Perform operation with monitoring
        content_generator = MonitoredContentGenerator()
        result = await content_generator.generate_blog_post("SaaS Onboarding")
        
        # Log successful API response
        await monitor.log_operation(
            operation_type="api_request_success",
            status=OperationStatus.SUCCESS,
            details={
                "endpoint": "/api/generate/blog",
                "response_size": len(str(result))
            }
        )
        
        return result
        
    except Exception as e:
        # Log API failure
        await monitor.log_operation(
            operation_type="api_request_failure",
            status=OperationStatus.FAILURE,
            details={
                "endpoint": "/api/generate/blog",
                "error_type": type(e).__name__
            },
            error=str(e)
        )
        
        # Send alert for API failures
        await monitor.send_alert(
            AlertType.WARNING,
            f"API endpoint failed: /api/generate/blog",
            details={"error": str(e)}
        )
        
        raise HTTPException(status_code=500, detail=str(e))

# Example: Scheduled health monitoring
async def scheduled_health_check():
    """Example of scheduled health monitoring"""
    monitor = global_monitor
    
    # Perform comprehensive health check
    health_report = await monitor.health_check()
    
    # Check if any critical issues
    if health_report["overall_health"] == "critical":
        await monitor.send_alert(
            AlertType.CRITICAL,
            f"System health critical: {health_report['health_score']}%",
            details=health_report
        )
    elif health_report["overall_health"] == "warning":
        await monitor.send_alert(
            AlertType.WARNING,
            f"System health warning: {health_report['health_score']}%",
            details=health_report
        )
    
    # Log health check results
    await monitor.log_operation(
        operation_type="scheduled_health_check",
        status=OperationStatus.SUCCESS,
        details={
            "health_score": health_report["health_score"],
            "status": health_report["overall_health"],
            "alerts_count": len(health_report.get("alerts", []))
        }
    )
    
    return health_report

# Example: Performance tracking and optimization
async def daily_performance_report():
    """Example of generating daily performance reports"""
    monitor = global_monitor
    
    # Get performance metrics
    performance_report = await monitor.performance_tracking()
    
    # Check for performance issues
    if performance_report.get("bottlenecks"):
        await monitor.send_alert(
            AlertType.WARNING,
            f"Performance bottlenecks detected: {len(performance_report['bottlenecks'])} issues",
            details=performance_report["bottlenecks"]
        )
    
    # Check for high costs
    daily_cost = performance_report.get("api_costs", {}).get("total_daily_cost", 0)
    if daily_cost > 100:  # Alert if daily costs exceed $100
        await monitor.send_alert(
            AlertType.WARNING,
            f"High API costs detected: ${daily_cost:.2f}/day",
            details=performance_report["api_costs"]
        )
    
    return performance_report

# Example usage and testing
async def demo_monitoring_system():
    """Demonstrate the monitoring system capabilities"""
    print("🔍 CRAEFTO Monitoring System Demo")
    print("=" * 50)
    
    monitor = global_monitor
    
    # 1. Test operation logging
    print("\n1. Testing operation logging...")
    await monitor.log_operation(
        operation_type="demo_operation",
        status=OperationStatus.SUCCESS,
        details={"test": "demo", "feature": "logging"},
        duration_ms=250,
        cost_usd=0.01
    )
    
    # 2. Test API failure handling
    print("\n2. Testing API failure handling...")
    try:
        result = await monitor.handle_api_failure(
            api_name="demo_api",
            error=Exception("Simulated API failure"),
            retry_count=2,
            operation_details={"operation": "demo"}
        )
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Failed as expected: {str(e)}")
    
    # 3. Test health check
    print("\n3. Testing health check...")
    health = await monitor.health_check()
    print(f"   Overall health: {health['overall_health']} ({health['health_score']}%)")
    
    # 4. Test performance tracking
    print("\n4. Testing performance tracking...")
    performance = await monitor.performance_tracking()
    print(f"   Operations analyzed: {performance.get('total_operations', 0)}")
    
    # 5. Test alert system
    print("\n5. Testing alert system...")
    await monitor.send_alert(
        AlertType.INFO,
        "Demo alert: Monitoring system is working correctly",
        details={"demo": True, "timestamp": "2025-09-10"}
    )
    
    # 6. Get operation statistics
    print("\n6. Getting operation statistics...")
    stats = monitor.get_operation_stats(hours=1)
    print(f"   Recent operations: {stats.get('total_operations', 0)}")
    
    print("\n✅ Monitoring system demo completed!")

if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_monitoring_system())
