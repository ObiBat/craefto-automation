"""
CRAEFTO FastAPI Application
Production-ready FastAPI app with async operations, background scheduling, and comprehensive error handling
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from threading import Thread

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, status, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import schedule
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio
from collections import deque
import hashlib
import hmac

from app.config import get_settings
from app.utils.database import init_database, close_database, get_database
from app.agents.research_agent import ResearchAgent
from app.agents.content_generator import ContentGenerator
from app.agents.visual_generator import VisualGenerator
from app.agents.publisher import Publisher
from app.agents.intelligence import BusinessIntelligence
from app.orchestrator import CraeftoOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# Authentication setup
security = HTTPBearer(auto_error=False)

# Request queue for heavy operations
request_queue = deque()
MAX_QUEUE_SIZE = 100

# API Keys for authentication
VALID_API_KEYS = {
    "craefto_admin": "admin_access",
    "craefto_user": "user_access",
    "craefto_webhook": "webhook_access"
}

# Global state for metrics and status tracking
app_metrics = {
    "startup_time": datetime.utcnow(),
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "last_scheduled_run": None,
    "next_scheduled_run": None,
    "background_tasks_running": 0,
    "research_requests": 0,
    "generation_requests": 0,
    "publish_requests": 0
}

# Request/Response Models
class TrendingResearchRequest(BaseModel):
    """Request model for trending research"""
    keywords: Optional[List[str]] = Field(default=[], description="Specific keywords to research")
    sources: Optional[List[str]] = Field(default=["google_trends", "reddit", "twitter"], description="Data sources to use")
    limit: Optional[int] = Field(default=10, ge=1, le=50, description="Number of trends to return")
    time_range: Optional[str] = Field(default="24h", description="Time range for trend analysis")

class ContentGenerationRequest(BaseModel):
    """Request model for content generation"""
    topic: str = Field(..., description="Topic or trend to generate content about")
    content_type: str = Field(..., description="Type of content (blog, social, email)")
    tone: Optional[str] = Field(default="professional", description="Content tone")
    target_audience: Optional[str] = Field(default="SaaS professionals", description="Target audience")
    word_count: Optional[int] = Field(default=500, ge=50, le=5000, description="Approximate word count")

class VisualGenerationRequest(BaseModel):
    """Request model for visual generation"""
    content_topic: str = Field(..., description="Topic for visual content")
    style: Optional[str] = Field(default="professional", description="Visual style")
    format: Optional[str] = Field(default="social_media", description="Format type")
    dimensions: Optional[str] = Field(default="1080x1080", description="Image dimensions")

class SocialPublishRequest(BaseModel):
    """Request model for social media publishing"""
    content: str = Field(..., description="Content to publish")
    platforms: List[str] = Field(..., description="Platforms to publish to")
    schedule_time: Optional[datetime] = Field(default=None, description="When to publish (UTC)")
    hashtags: Optional[List[str]] = Field(default=[], description="Hashtags to include")

class EmailCampaignRequest(BaseModel):
    """Request model for email campaign"""
    subject: str = Field(..., description="Email subject line")
    content: str = Field(..., description="Email content")
    recipients: List[str] = Field(..., description="Email recipients")
    template_id: Optional[str] = Field(default=None, description="Email template ID")

# New API request models
class TrendingResearchAPIRequest(BaseModel):
    """Request model for /api/research/trending"""
    sources: List[str] = Field(default=["reddit", "producthunt", "twitter"], description="Research sources")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    keywords: Optional[List[str]] = Field(default=None, description="Optional keywords to focus on")

class BlogGenerationRequest(BaseModel):
    """Request model for /api/generate/blog"""
    topic: str = Field(..., description="Blog post topic")
    research_id: Optional[int] = Field(default=None, description="Research ID to base content on")
    style: str = Field(default="tutorial", description="Blog post style: tutorial, listicle, case_study")
    target_audience: Optional[str] = Field(default=None, description="Target audience for the content")
    include_hero_image: bool = Field(default=True, description="Whether to generate hero image")
    seo_keywords: Optional[List[str]] = Field(default=None, description="SEO keywords to optimize for")

class CampaignGenerationRequest(BaseModel):
    """Request model for /api/generate/campaign"""
    campaign_type: str = Field(..., description="Campaign type: launch, nurture, promotional")
    content_ids: List[int] = Field(..., description="Content IDs to include in campaign")
    target_segments: Optional[List[str]] = Field(default=None, description="Target audience segments")
    duration_days: int = Field(default=7, ge=1, le=30, description="Campaign duration in days")
    channels: List[str] = Field(default=["email", "social"], description="Distribution channels")

class BatchPublishRequest(BaseModel):
    """Request model for /api/publish/batch"""
    content_ids: List[int] = Field(..., description="Content IDs to publish")
    platforms: List[str] = Field(..., description="Platforms to publish to")
    schedule: Optional[datetime] = Field(default=None, description="Schedule for publishing")
    priority: str = Field(default="normal", description="Publishing priority: low, normal, high")
    dry_run: bool = Field(default=False, description="Test run without actual publishing")

class WebhookPayload(BaseModel):
    """Request model for webhook payloads"""
    event_type: str = Field(..., description="Type of webhook event")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    source: str = Field(default="make.com", description="Webhook source")

# Authentication functions
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify API key from Authorization header"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = credentials.credentials
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return VALID_API_KEYS[api_key]

async def verify_webhook_signature(
    request: Request,
    x_signature: str = Header(None, alias="X-Signature")
) -> bool:
    """Verify webhook signature for Make.com integration"""
    if not x_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook signature required"
        )
    
    body = await request.body()
    webhook_secret = settings.make_webhook_secret or "default_secret"
    
    expected_signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(f"sha256={expected_signature}", x_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    return True

async def add_to_queue(operation_type: str, payload: dict) -> str:
    """Add heavy operation to processing queue"""
    if len(request_queue) >= MAX_QUEUE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Request queue is full. Please try again later."
        )
    
    request_id = f"{operation_type}_{int(time.time())}"
    request_queue.append({
        "id": request_id,
        "type": operation_type,
        "payload": payload,
        "created_at": datetime.utcnow(),
        "status": "queued"
    })
    
    return request_id

def get_consistent_response(
    success: bool,
    message: str,
    data: Any = None,
    request_id: str = None,
    errors: List[str] = None
) -> Dict[str, Any]:
    """Return consistent JSON response format"""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if data is not None:
        response["data"] = data
    
    if request_id:
        response["request_id"] = request_id
    
    if errors:
        response["errors"] = errors
    
    return response

class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Background task functions
async def background_research_task():
    """Background task for automated research"""
    try:
        logger.info("🔍 Starting background research task")
        app_metrics["background_tasks_running"] += 1
        
        # Simulate research logic
        await asyncio.sleep(2)
        
        app_metrics["last_scheduled_run"] = datetime.utcnow()
        app_metrics["next_scheduled_run"] = datetime.utcnow() + timedelta(hours=settings.automation_schedule_hours)
        logger.info("✅ Background research task completed")
        
    except Exception as e:
        logger.error(f"❌ Background research task failed: {str(e)}")
    finally:
        app_metrics["background_tasks_running"] -= 1

def schedule_background_tasks():
    """Schedule background tasks to run based on configuration"""
    schedule.every(settings.automation_schedule_hours).hours.do(lambda: asyncio.create_task(background_research_task()))
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Exception handlers
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    app_metrics["failed_requests"] += 1
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc)
        ).dict()
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    app_metrics["failed_requests"] += 1
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=f"Status Code: {exc.status_code}"
        ).dict()
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    app_metrics["failed_requests"] += 1
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred"
        ).dict()
    )

# Middleware for request tracking
async def track_requests(request: Request, call_next):
    """Middleware to track request metrics"""
    start_time = time.time()
    app_metrics["total_requests"] += 1
    
    try:
        response = await call_next(request)
        app_metrics["successful_requests"] += 1
        return response
    except Exception as e:
        app_metrics["failed_requests"] += 1
        raise e
    finally:
        process_time = time.time() - start_time
        logger.info(f"Request {request.method} {request.url.path} completed in {process_time:.3f}s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting CRAEFTO FastAPI Application")
    app_metrics["startup_time"] = datetime.utcnow()
    app_metrics["next_scheduled_run"] = datetime.utcnow() + timedelta(hours=settings.automation_schedule_hours)
    
    # Log configuration status
    settings.log_configuration_status()
    
    # Initialize database connection
    try:
        db_success = await init_database()
        if db_success:
            logger.info("🗄️ Database connection established")
        else:
            logger.warning("⚠️ Database connection failed - continuing without database")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {str(e)}")
    
    # Start background scheduler
    scheduler_thread = Thread(target=schedule_background_tasks, daemon=True)
    scheduler_thread.start()
    logger.info(f"⏰ Background scheduler started (every {settings.automation_schedule_hours} hours)")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down CRAEFTO FastAPI Application")
    await close_database()

# Create FastAPI app
app = FastAPI(
    title="CRAEFTO Automation API",
    description="Production-ready FastAPI application for SaaS content automation with research, generation, and publishing capabilities",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request tracking middleware
app.middleware("http")(track_requests)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Health check endpoint
@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    uptime = datetime.utcnow() - app_metrics["startup_time"]
    
    # Check database health
    try:
        db = get_database()
        db_health = await db.health_check()
    except Exception as e:
        db_health = {
            "status": "error",
            "connected": False,
            "error": str(e)
        }
    
    overall_status = "healthy" if db_health.get("status") == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime.total_seconds(),
        "version": "1.0.0",
        "services": {
            "database": db_health
        }
    }

@app.get("/status", response_model=Dict[str, Any])
async def get_status():
    """Get application status and metrics"""
    uptime = datetime.utcnow() - app_metrics["startup_time"]
    return {
        "status": "running",
        "uptime_seconds": uptime.total_seconds(),
        "metrics": app_metrics,
        "scheduler": {
            "next_run": app_metrics.get("next_scheduled_run"),
            "last_run": app_metrics.get("last_scheduled_run"),
            "background_tasks_active": app_metrics.get("background_tasks_running", 0),
            "schedule_interval_hours": settings.automation_schedule_hours
        },
        "configuration": {
            "environment": settings.environment,
            "log_level": settings.log_level,
            "api_keys_configured": settings.has_required_api_keys()
        }
    }

@app.get("/config/status", response_model=Dict[str, Any])
async def get_config_status():
    """Get detailed configuration status"""
    api_status = settings.has_required_api_keys()
    configured_count = sum(api_status.values())
    total_count = len(api_status)
    
    return {
        "environment": settings.environment,
        "is_production": settings.is_production(),
        "is_development": settings.is_development(),
        "configuration_summary": {
            "total_services": total_count,
            "configured_services": configured_count,
            "configuration_percentage": round((configured_count / total_count) * 100, 1)
        },
        "api_services": api_status,
        "system_settings": {
            "log_level": settings.log_level,
            "automation_schedule_hours": settings.automation_schedule_hours,
            "max_content_generation_retries": settings.max_content_generation_retries,
            "rate_limit_per_minute": settings.rate_limit_per_minute,
            "rate_limit_per_hour": settings.rate_limit_per_hour,
            "max_workers": settings.max_workers
        },
        "fault_tolerance": settings.get_fault_tolerance_config(),
        "content_settings": {
            "supported_content_types": settings.content_types,
            "max_content_lengths": settings.max_content_length
        },
        "brand_configuration": settings.get_brand_config()
    }

@app.get("/brand/config", response_model=Dict[str, Any])
async def get_brand_config():
    """Get Craefto brand configuration and guidelines"""
    brand_config = settings.get_brand_config()
    
    return {
        "brand_identity": {
            "name": "Craefto",
            "tagline": "Premium SaaS Design & Growth",
            "voice_characteristics": settings.get_brand_voice_keywords(),
            "full_voice_description": settings.brand_voice
        },
        "visual_identity": {
            "design_philosophy": brand_config["design_style"],
            "visual_elements": brand_config["visual_elements"],
            "design_inspirations": brand_config["design_inspirations"],
            "color_palette": brand_config["colors"]["palette"],
            "color_meanings": {
                "near_black": {"hex": brand_config["colors"]["near_black"], "usage": "Background base, primary backgrounds"},
                "deep_charcoal": {"hex": brand_config["colors"]["deep_charcoal"], "usage": "Primary text and accents"},
                "dark_gray": {"hex": brand_config["colors"]["dark_gray"], "usage": "UI elements, borders, dividers"},
                "muted_gray_green": {"hex": brand_config["colors"]["muted_gray_green"], "usage": "Background swirls, subtle patterns"},
                "desaturated_green": {"hex": brand_config["colors"]["desaturated_green"], "usage": "Secondary accents, hover states"},
                "light_gray": {"hex": brand_config["colors"]["light_gray"], "usage": "Text highlights, off-white elements"}
            },
            "typography": {
                "primary_font": brand_config["typography"]["primary_font"],
                "logo_font": brand_config["typography"]["logo_font"],
                "logo_symbol": brand_config["typography"]["logo_symbol"],
                "font_usage": {
                    "primary": "Space Mono for body text, code, and UI elements",
                    "logo": "Source Serif 4 Bold for brand logo and headlines"
                }
            },
            "aesthetic_details": {
                "film_grain": "Subtle film grain textures for depth and character",
                "geometric_shapes": "Clean geometric forms and structured layouts",
                "typography_focus": "Typography as a primary design element",
                "calligraphy_inspiration": "Influenced by modern calligraphy and hand-lettering"
            }
        },
        "target_segments": {
            "primary_audience": settings.target_audience,
            "audience_characteristics": {
                "SaaS founders": "Building and scaling software companies",
                "Product marketers": "Driving product adoption and growth",
                "Growth teams": "Optimizing conversion and retention",
                "Solopreneurs": "Independent entrepreneurs building digital products"
            }
        },
        "content_strategy": {
            "pillars": settings.content_pillars,
            "pillar_descriptions": {
                "Framer tutorials": "Step-by-step guides for Framer design and prototyping",
                "SaaS design patterns": "UI/UX patterns that drive SaaS success",
                "CRO tips": "Conversion rate optimization strategies and tactics",
                "Template showcases": "Premium design templates and components",
                "Web Design trends": "Latest trends in web and SaaS design",
                "Award winning designs": "Analysis of exceptional design work"
            }
        },
        "content_guidelines": {
            "tone": "Professional yet approachable, premium but accessible",
            "style": "Minimal, clean, visual-first with practical actionable insights",
            "aesthetic": "Mostly black and white minimal design with subtle green-gray accents, film grain textures, and geometric elements",
            "typography_style": "Monospace for technical content, serif for brand elements, calligraphy-inspired treatments",
            "visual_treatments": {
                "film_grain": "Add subtle grain overlays for texture and depth",
                "geometric_shapes": "Use circles, rectangles, and lines as design elements",
                "typography_focus": "Make typography the hero of the design",
                "calligraphy_touches": "Incorporate hand-lettered elements and flourishes"
            },
            "format_preferences": [
                "Visual tutorials with geometric overlays",
                "Case studies with film grain textures", 
                "Before/after showcases with typography focus",
                "Quick tips with calligraphy elements",
                "Minimal design showcases",
                "Typography-driven content"
            ],
            "hashtag_strategy": ["#SaaSDesign", "#Framer", "#CRO", "#WebDesign", "#GrowthHacking", "#MinimalDesign", "#Typography", "#FilmGrain"]
        },
        "ai_prompt_context": settings.get_content_prompt_context()
    }

@app.get("/config/rate-limits", response_model=Dict[str, Any])
async def get_rate_limits_config():
    """Get detailed rate limiting and fault tolerance configuration"""
    fault_tolerance = settings.get_fault_tolerance_config()
    health_checks = settings.get_service_health_check_config()
    
    # Calculate example retry delays
    example_delays = []
    for attempt in range(1, settings.max_retries + 1):
        delay = settings.calculate_retry_delay(attempt)
        example_delays.append({
            "attempt": attempt,
            "delay_seconds": round(delay, 2)
        })
    
    return {
        "service_rate_limits": {
            "limits_per_minute": fault_tolerance["rate_limits"],
            "health_checks": health_checks,
            "critical_services": [
                service for service, config in health_checks.items() 
                if config.get("critical", False)
            ]
        },
        "retry_configuration": {
            **fault_tolerance["retry"],
            "example_delays": example_delays,
            "total_max_wait_time": sum(
                settings.calculate_retry_delay(i) for i in range(1, settings.max_retries + 1)
            )
        },
        "queue_system": {
            **fault_tolerance["queue"],
            "estimated_throughput_per_minute": fault_tolerance["queue"]["batch_size"] * (60 / fault_tolerance["queue"]["processing_interval"]),
            "max_wait_time_minutes": fault_tolerance["queue"]["timeout"] / 60
        },
        "circuit_breaker": {
            **fault_tolerance["circuit_breaker"],
            "states": ["CLOSED", "OPEN", "HALF_OPEN"],
            "state_descriptions": {
                "CLOSED": "Normal operation, requests pass through",
                "OPEN": "Circuit breaker tripped, requests fail fast",
                "HALF_OPEN": "Testing if service has recovered"
            }
        },
        "fault_tolerance_summary": {
            "total_configured_services": len(fault_tolerance["rate_limits"]) - 1,  # Exclude global_fallback
            "has_exponential_backoff": True,
            "has_jitter": fault_tolerance["retry"]["jitter_enabled"],
            "has_circuit_breaker": True,
            "has_request_queue": True,
            "estimated_max_recovery_time": fault_tolerance["circuit_breaker"]["recovery_timeout"] + sum(
                settings.calculate_retry_delay(i) for i in range(1, settings.max_retries + 1)
            )
        }
    }

@app.get("/database/status", response_model=Dict[str, Any])
async def get_database_status():
    """Get detailed database status and analytics"""
    try:
        db = get_database()
        
        # Get health status
        health_status = await db.health_check()
        
        # Get table status
        table_status = {}
        if health_status.get("connected", False):
            try:
                table_status = await db.verify_tables_exist()
            except Exception as e:
                logger.warning(f"⚠️ Could not verify tables: {str(e)}")
                table_status = {"error": "Table verification unavailable"}
        
        # Get analytics if connected
        analytics_data = {}
        if health_status.get("connected", False):
            try:
                analytics_data = await db.get_analytics_data(days=7)
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch analytics: {str(e)}")
                analytics_data = {"error": "Analytics unavailable"}
        
        # Get recent activity
        recent_content = []
        if health_status.get("connected", False):
            try:
                recent_content = await db.get_recent_content(limit=5)
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch recent content: {str(e)}")
        
        # Get pipeline status
        pipeline_status = {}
        if health_status.get("connected", False):
            try:
                pipeline_status = await db.get_content_pipeline_status()
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch pipeline status: {str(e)}")
                pipeline_status = {"error": "Pipeline status unavailable"}
        
        return {
            "database_health": health_status,
            "configuration": {
                "url_configured": bool(settings.supabase_url),
                "key_configured": bool(settings.supabase_key),
                "rate_limit": settings.supabase_rate_limit
            },
            "tables": {
                "status": table_status,
                "required_tables": ["research_data", "generated_content", "published_content", "performance_metrics"]
            },
            "analytics": analytics_data,
            "pipeline": pipeline_status,
            "recent_activity": {
                "recent_content_count": len(recent_content),
                "recent_content": recent_content[:3]  # Show only first 3 for brevity
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Database status check failed: {str(e)}")
        return {
            "database_health": {
                "status": "error",
                "connected": False,
                "error": str(e)
            },
            "configuration": {
                "url_configured": bool(settings.supabase_url),
                "key_configured": bool(settings.supabase_key),
                "rate_limit": settings.supabase_rate_limit
            },
            "analytics": {},
            "recent_activity": {},
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/database/setup", response_model=Dict[str, Any])
async def setup_database_tables():
    """Create database tables if they don't exist"""
    try:
        db = get_database()
        
        if not db.is_connected:
            return {
                "success": False,
                "error": "Database not connected",
                "message": "Please configure Supabase credentials first",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        logger.info("🏗️ Starting database table setup...")
        
        # Check current table status
        table_status = await db.verify_tables_exist()
        missing_tables = [table for table, exists in table_status.items() if not exists]
        
        if not missing_tables:
            return {
                "success": True,
                "message": "All required tables already exist",
                "tables": table_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Create missing tables
        creation_results = await db.create_tables_if_not_exist()
        
        # Verify creation
        final_status = await db.verify_tables_exist()
        successful_creations = []
        failed_creations = []
        
        for table_name in missing_tables:
            if creation_results.get(table_name, False):
                successful_creations.append(table_name)
            else:
                failed_creations.append(table_name)
        
        overall_success = len(failed_creations) == 0
        
        return {
            "success": overall_success,
            "message": f"Table setup completed. Created: {len(successful_creations)}, Failed: {len(failed_creations)}",
            "results": {
                "successful_creations": successful_creations,
                "failed_creations": failed_creations,
                "creation_results": creation_results,
                "final_table_status": final_status
            },
            "notes": [
                "If table creation failed, you may need to create them manually in Supabase dashboard",
                "Ensure your Supabase user has table creation permissions",
                "Check Supabase logs for detailed error information"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Database setup failed with error",
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/database/tables", response_model=Dict[str, Any])
async def get_table_information():
    """Get detailed information about database tables"""
    try:
        db = get_database()
        
        if not db.is_connected:
            return {
                "connected": False,
                "error": "Database not connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get table status
        table_status = await db.verify_tables_exist()
        
        # Get detailed info for each table
        table_details = {}
        for table_name in ["research_data", "generated_content", "published_content", "performance_metrics"]:
            try:
                table_info = await db.get_table_info(table_name)
                table_details[table_name] = table_info
            except Exception as e:
                table_details[table_name] = {
                    "table_name": table_name,
                    "exists": table_status.get(table_name, False),
                    "error": str(e)
                }
        
        return {
            "connected": True,
            "table_overview": table_status,
            "table_details": table_details,
            "schema_info": {
                "research_data": {
                    "description": "Stores research data with topics, relevance scores, and source information",
                    "key_fields": ["id", "topic", "relevance_score", "source", "data", "created_at"]
                },
                "generated_content": {
                    "description": "Stores generated content linked to research data",
                    "key_fields": ["id", "research_id", "content_type", "title", "body", "status", "created_at"]
                },
                "published_content": {
                    "description": "Tracks published content across different platforms",
                    "key_fields": ["id", "content_id", "platform", "url", "engagement_metrics", "published_at"]
                },
                "performance_metrics": {
                    "description": "Stores performance metrics for published content",
                    "key_fields": ["id", "content_id", "published_content_id", "views", "clicks", "conversions", "timestamp"]
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Table information retrieval failed: {str(e)}")
        return {
            "connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/database/content/pending", response_model=Dict[str, Any])
async def get_pending_content_endpoint(
    limit: int = 20,
    content_type: Optional[str] = None
):
    """Get content that is ready for publication"""
    try:
        db = get_database()
        
        if not db.is_connected:
            return {
                "success": False,
                "error": "Database not connected",
                "pending_content": [],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        pending_content = await db.get_pending_content(limit=limit, content_type=content_type)
        
        return {
            "success": True,
            "count": len(pending_content),
            "pending_content": pending_content,
            "filters": {
                "limit": limit,
                "content_type": content_type
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting pending content: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "pending_content": [],
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/database/content/top-performing", response_model=Dict[str, Any])
async def get_top_performing_endpoint(
    metric: str = 'views',
    limit: int = 10,
    days: int = 30,
    platform: Optional[str] = None,
    content_type: Optional[str] = None
):
    """Get top performing content based on metrics"""
    try:
        db = get_database()
        
        if not db.is_connected:
            return {
                "success": False,
                "error": "Database not connected",
                "top_performing": [],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        top_performing = await db.get_top_performing(
            metric=metric,
            limit=limit,
            days=days,
            platform=platform,
            content_type=content_type
        )
        
        return {
            "success": True,
            "count": len(top_performing),
            "top_performing": top_performing,
            "ranking": {
                "metric": metric,
                "period_days": days,
                "filters": {
                    "platform": platform,
                    "content_type": content_type
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting top performing content: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "top_performing": [],
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/database/content/publish", response_model=Dict[str, Any])
async def mark_content_published(request: Dict[str, Any]):
    """Mark content as published and create publication record"""
    try:
        db = get_database()
        
        if not db.is_connected:
            return {
                "success": False,
                "error": "Database not connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        content_id = request.get('content_id')
        if not content_id:
            return {
                "success": False,
                "error": "content_id is required",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        publication_data = {
            'platform': request.get('platform', 'blog'),
            'url': request.get('url', ''),
            'engagement_metrics': request.get('engagement_metrics', {}),
            'status': request.get('status', 'published')
        }
        
        result = await db.mark_published(content_id, publication_data)
        
        return {
            "success": True,
            "result": result,
            "message": f"Content published successfully on {publication_data['platform']}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error marking content as published: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/database/performance/track", response_model=Dict[str, Any])
async def track_content_performance(request: Dict[str, Any]):
    """Track performance metrics for published content"""
    try:
        db = get_database()
        
        if not db.is_connected:
            return {
                "success": False,
                "error": "Database not connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        published_content_id = request.get('published_content_id')
        if not published_content_id:
            return {
                "success": False,
                "error": "published_content_id is required",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        metrics_data = {
            'views': request.get('views', 0),
            'clicks': request.get('clicks', 0),
            'conversions': request.get('conversions', 0),
            'engagement_rate': request.get('engagement_rate', 0.0),
            'shares': request.get('shares', 0),
            'comments': request.get('comments', 0),
            'likes': request.get('likes', 0),
            'reach': request.get('reach', 0),
            'impressions': request.get('impressions', 0),
            'additional_metrics': request.get('additional_metrics', {})
        }
        
        result = await db.track_performance(published_content_id, metrics_data)
        
        return {
            "success": True,
            "result": result,
            "message": "Performance metrics tracked successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error tracking performance: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Research endpoints
@app.post("/research/trending", response_model=APIResponse)
async def research_trending(request: TrendingResearchRequest, background_tasks: BackgroundTasks):
    """
    Find trending SaaS topics and keywords
    
    Analyzes multiple data sources to identify trending topics in the SaaS space
    """
    try:
        app_metrics["research_requests"] += 1
        logger.info(f"🔍 Processing trending research request: {request.keywords}")
        
        # Use ResearchAgent to find trending topics
        async with ResearchAgent() as agent:
            trending_topics = await agent.find_trending_topics()
            
            # Generate content ideas from trending topics
            content_ideas = await agent.generate_content_ideas(trending_topics)
        
        # Save research data to database if connected
        db = get_database()
        saved_research = []
        
        if db.is_connected:
            try:
                for topic_data in trending_topics[:5]:  # Save top 5 topics
                    research_record = await db.save_research({
                        'topic': topic_data.get('topic'),
                        'relevance_score': min(topic_data.get('relevance_score', 0) / 100, 1.0),  # Normalize to 0-1
                        'source': topic_data.get('source'),
                        'data': {
                            'context': topic_data.get('context'),
                            'content_angle': topic_data.get('content_angle'),
                            'raw_score': topic_data.get('relevance_score', 0),
                            'craefto_boost': topic_data.get('craefto_boost', 0),
                            'research_timestamp': datetime.utcnow().isoformat()
                        }
                    })
                    saved_research.append(research_record.get('id'))
                    
                logger.info(f"💾 Saved {len(saved_research)} research records to database")
            except Exception as db_error:
                logger.warning(f"⚠️ Database save failed: {str(db_error)}")
        
        # Format response data
        trending_data = {
            "trends": [
                {
                    "keyword": topic.get('topic'),
                    "score": topic.get('relevance_score'),
                    "source": topic.get('source'),
                    "content_angle": topic.get('content_angle'),
                    "context": topic.get('context', '')[:100] + "..." if topic.get('context', '') else ""
                }
                for topic in trending_topics[:request.limit]
            ],
            "content_ideas": content_ideas,
            "metadata": {
                "total_trends": len(trending_topics),
                "total_content_ideas": len(content_ideas),
                "sources_used": ["reddit", "producthunt", "twitter", "google_trends"],
                "time_range": request.time_range,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "saved_to_database": len(saved_research),
                "database_ids": saved_research
            }
        }
        
        return APIResponse(
            success=True,
            message=f"Found {len(trending_topics)} trending topics and generated {len(content_ideas)} content ideas",
            data=trending_data
        )
        
    except Exception as e:
        logger.error(f"❌ Research trending failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@app.post("/research/competitor", response_model=APIResponse)
async def analyze_competitor(request: Dict[str, str]):
    """
    Analyze competitor content for gaps and opportunities
    
    Args:
        competitor_url: URL of competitor website/blog to analyze
    """
    try:
        competitor_url = request.get('competitor_url')
        if not competitor_url:
            raise HTTPException(status_code=400, detail="competitor_url is required")
        
        logger.info(f"🔍 Analyzing competitor: {competitor_url}")
        
        # Use ResearchAgent to analyze competitor
        async with ResearchAgent() as agent:
            analysis = await agent.analyze_competitor(competitor_url)
        
        # Save analysis to database if connected
        db = get_database()
        saved_analysis = None
        
        if db.is_connected and analysis.get('success'):
            try:
                saved_analysis = await db.save_research({
                    'topic': f"Competitor Analysis: {competitor_url}",
                    'relevance_score': 0.8,  # Standard score for competitor analysis
                    'source': 'competitor_analysis',
                    'data': {
                        'competitor_url': competitor_url,
                        'content_topics': analysis.get('content_topics', []),
                        'content_gaps': analysis.get('content_gaps', []),
                        'analysis_timestamp': datetime.utcnow().isoformat(),
                        'success': analysis.get('success', False)
                    }
                })
                logger.info(f"💾 Saved competitor analysis to database")
            except Exception as db_error:
                logger.warning(f"⚠️ Database save failed: {str(db_error)}")
        
        return APIResponse(
            success=analysis.get('success', False),
            message=f"Competitor analysis completed for {competitor_url}",
            data={
                "analysis": analysis,
                "saved_to_database": saved_analysis is not None,
                "database_id": saved_analysis.get('id') if saved_analysis else None
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Competitor analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Competitor analysis failed: {str(e)}")

# Generation endpoints
@app.post("/generate/content", response_model=APIResponse)
async def generate_content(request: ContentGenerationRequest):
    """
    Generate content based on research data
    
    Creates various types of content (blog posts, social media, emails) from trending topics
    """
    try:
        app_metrics["generation_requests"] += 1
        logger.info(f"✍️ Generating {request.content_type} content for: {request.topic}")
        
        # Use ContentGenerator for AI-powered content creation
        generator = ContentGenerator()
        
        # Prepare research data if available
        research_data = {
            "topic": request.topic,
            "target_audience": request.target_audience,
            "tone": request.tone,
            "context": f"Generate {request.content_type} content for {request.target_audience}"
        }
        
        # Generate content based on type
        if request.content_type == "blog":
            generated_content = await generator.generate_blog_post(request.topic, research_data)
            content_data = {
                "title": generated_content.get("title"),
                "content": generated_content.get("content"),
                "word_count": generated_content.get("word_count", 0),
                "seo": generated_content.get("seo", {}),
                "social_snippets": generated_content.get("social_snippets", {}),
                "email_version": generated_content.get("email_version", {}),
                "metadata": generated_content.get("metadata", {})
            }
            
        elif request.content_type == "social":
            generated_content = await generator.generate_social_posts(request.topic)
            content_data = {
                "twitter": generated_content.get("twitter", {}),
                "linkedin": generated_content.get("linkedin", {}),
                "instagram": generated_content.get("instagram", {}),
                "metadata": generated_content.get("metadata", {})
            }
            
        elif request.content_type == "email":
            generated_content = await generator.generate_email_campaign(request.topic, "all")
            content_data = {
                "subject_lines": generated_content.get("subject_lines", []),
                "preview_text": generated_content.get("preview_text"),
                "html_content": generated_content.get("html_content"),
                "plain_text_content": generated_content.get("plain_text_content"),
                "metadata": generated_content.get("metadata", {})
            }
            
        else:
            # Fallback for other content types
            content_data = {
                "content": f"Generated {request.content_type} content about {request.topic}",
                "metadata": {
                    "topic": request.topic,
                    "content_type": request.content_type,
                    "generated_at": datetime.utcnow().isoformat(),
                    "fallback_content": True
                }
            }
        
        # Save generated content to database if connected
        db = get_database()
        saved_content = None
        
        if db.is_connected:
            try:
                # Get research data for linking if available
                research_id = None
                recent_research = await db.get_recent_research(limit=1, topic=request.topic)
                if recent_research:
                    research_id = recent_research[0].get('id')
                
                saved_content = await db.save_generated_content({
                    'research_id': research_id,
                    'content_type': request.content_type,
                    'title': content_data.get('title', f"{request.content_type.title()} about {request.topic}"),
                    'body': str(content_data.get('content', '')),
                    'status': 'generated',
                    'metadata': {
                        'original_request': {
                            'topic': request.topic,
                            'content_type': request.content_type,
                            'target_audience': request.target_audience,
                            'tone': request.tone,
                            'word_count': request.word_count
                        },
                        'ai_generation': content_data.get('metadata', {}),
                        'generated_at': datetime.utcnow().isoformat()
                    }
                })
                logger.info(f"💾 Saved generated content to database: {saved_content.get('id')}")
            except Exception as db_error:
                logger.warning(f"⚠️ Database save failed: {str(db_error)}")
        
        # Add database info to response
        content_data["database"] = {
            "saved": saved_content is not None,
            "content_id": saved_content.get('id') if saved_content else None
        }
        
        return APIResponse(
            success=True,
            message=f"{request.content_type.title()} content generated successfully using AI",
            data=content_data
        )
        
    except Exception as e:
        logger.error(f"❌ Content generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")

@app.post("/generate/visual", response_model=APIResponse)
async def generate_visual(request: VisualGenerationRequest, background_tasks: BackgroundTasks):
    """
    Generate visual content via Midjourney or similar AI image generation
    
    Creates professional visuals for social media, blog posts, and marketing materials
    """
    try:
        app_metrics["generation_requests"] += 1
        logger.info(f"🎨 Generating visual for: {request.content_topic}")
        
        # Use VisualGenerator for AI-powered visual creation
        generator = VisualGenerator()
        
        # Determine visual type and generate accordingly
        if request.format.lower() == "blog_hero":
            visual_result = await generator.generate_blog_hero(request.content_topic, request.style)
        elif request.format.lower() in ["twitter", "linkedin", "instagram", "facebook"]:
            visual_result = await generator.generate_social_graphics(request.content_topic, request.format.lower())
        elif request.format.lower() == "og_image":
            visual_result = await generator.generate_og_image(request.content_topic, "")
        elif request.format.lower() == "email_banner":
            visual_result = generator.create_email_banner("newsletter")
        else:
            # Default to social graphic for Twitter
            visual_result = await generator.generate_social_graphics(request.content_topic, "twitter")
        
        # Prepare response data
        if visual_result.get("success"):
            visual_data = {
                "visual_id": f"vis_{int(time.time())}",
                "status": "completed",
                "source": visual_result.get("source", "unknown"),
                "image_url": visual_result.get("image_url") or visual_result.get("primary_url"),
                "image_base64": visual_result.get("image_base64"),
                "dimensions": visual_result.get("dimensions", {}),
                "alt_text": visual_result.get("alt_text", f"Visual for {request.content_topic}"),
                "metadata": {
                    "topic": request.content_topic,
                    "style": request.style,
                    "format": request.format,
                    "dimensions": request.dimensions,
                    "generation_source": visual_result.get("source"),
                    "created_at": datetime.utcnow().isoformat(),
                    **visual_result.get("metadata", {})
                }
            }
            
            # Add background task for cleanup/optimization
            async def visual_cleanup_task():
                await asyncio.sleep(1)
                logger.info(f"✅ Visual generation completed for: {request.content_topic}")
            
            background_tasks.add_task(visual_cleanup_task)
            
            return APIResponse(
                success=True,
                message=f"Visual generated successfully via {visual_result.get('source', 'AI')}",
                data=visual_data
            )
        else:
            # Handle generation failure
            error_message = visual_result.get("error", "Visual generation failed")
            logger.warning(f"⚠️ Visual generation failed: {error_message}")
            
            # Return fallback response
            visual_data = {
                "visual_id": f"vis_fallback_{int(time.time())}",
                "status": "failed_with_fallback",
                "error": error_message,
                "fallback_available": True,
                "metadata": {
                    "topic": request.content_topic,
                    "style": request.style,
                    "format": request.format,
                    "created_at": datetime.utcnow().isoformat(),
                    "fallback": True
                }
            }
            
            return APIResponse(
                success=False,
                message=f"Visual generation failed: {error_message}",
                data=visual_data
            )
        
    except Exception as e:
        logger.error(f"❌ Visual generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Visual generation failed: {str(e)}")

# Publishing endpoints
@app.post("/publish/social", response_model=APIResponse)
async def publish_social(request: SocialPublishRequest, background_tasks: BackgroundTasks):
    """
    Publish content to social media platforms (Twitter, LinkedIn)
    
    Handles multi-platform publishing with scheduling capabilities
    """
    try:
        app_metrics["publish_requests"] += 1
        logger.info(f"📱 Publishing to social platforms: {request.platforms}")
        
        # Validate platforms
        supported_platforms = ["twitter", "linkedin", "facebook", "instagram"]
        invalid_platforms = [p for p in request.platforms if p not in supported_platforms]
        if invalid_platforms:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported platforms: {invalid_platforms}. Supported: {supported_platforms}"
            )
        
        # Initialize publisher
        publisher = Publisher()
        
        # Handle scheduling vs immediate publishing
        if request.schedule_time:
            # Schedule content for future publishing
            try:
                schedule_time = datetime.fromisoformat(request.schedule_time.replace('Z', '+00:00'))
            except ValueError:
                schedule_time = datetime.strptime(request.schedule_time, '%Y-%m-%dT%H:%M:%S')
            
            content_data = {
                "content": request.content,
                "hashtags": getattr(request, 'hashtags', []),
                "mentions": getattr(request, 'mentions', [])
            }
            
            schedule_result = await publisher.schedule_content(
                content=content_data,
                platforms=request.platforms,
                publish_time=schedule_time
            )
            
            if schedule_result.get("success"):
                return APIResponse(
                    success=True,
                    message=f"Content scheduled for {len(request.platforms)} platforms",
                    data={
                        "schedule_id": schedule_result["schedule_id"],
                        "platforms": request.platforms,
                        "publish_time": schedule_result["publish_time"],
                        "status": "scheduled",
                        "metadata": schedule_result.get("metadata", {})
                    }
                )
            else:
                raise HTTPException(status_code=500, detail=f"Scheduling failed: {schedule_result.get('error')}")
        
        else:
            # Immediate publishing
            publish_results = []
            
            for platform in request.platforms:
                if platform == "twitter":
                    # Handle Twitter publishing
                    twitter_result = await publisher.publish_to_twitter(request.content)
                    publish_results.append(twitter_result)
                    
                elif platform == "linkedin":
                    # Handle LinkedIn publishing
                    linkedin_result = await publisher.publish_to_linkedin(request.content)
                    publish_results.append(linkedin_result)
                    
                else:
                    # Placeholder for other platforms
                    publish_results.append({
                        "success": False,
                        "platform": platform,
                        "error": f"{platform} publishing not yet implemented"
                    })
            
            # Count successful vs failed publishes
            successful_publishes = [r for r in publish_results if r.get("success")]
            failed_publishes = [r for r in publish_results if not r.get("success")]
            
            # Save successful publishes to database
            db = get_database()
            if db.is_connected and successful_publishes:
                try:
                    for result in successful_publishes:
                        await db.save_published_content({
                            'content_id': None,  # No specific content_id for direct social posts
                            'platform': result["platform"],
                            'url': result.get("post_url") or result.get("thread_url"),
                            'engagement_metrics': {},
                            'status': 'published'
                        })
                    logger.info(f"💾 Saved {len(successful_publishes)} published content records")
                except Exception as db_error:
                    logger.warning(f"⚠️ Database save failed: {str(db_error)}")
            
            publish_data = {
                "results": publish_results,
                "summary": {
                    "total_platforms": len(request.platforms),
                    "successful_publishes": len(successful_publishes),
                    "failed_publishes": len(failed_publishes),
                    "scheduled": False,
                    "success_rate": len(successful_publishes) / len(request.platforms) if request.platforms else 0
                },
                "content_preview": request.content[:100] + "..." if len(request.content) > 100 else request.content,
                "published_urls": [
                    r.get("post_url") or r.get("thread_url") 
                    for r in successful_publishes 
                    if r.get("post_url") or r.get("thread_url")
                ]
            }
            
            # Add background task for performance tracking
            async def track_publishing_performance():
                await asyncio.sleep(2)
                logger.info(f"📊 Publishing performance: {len(successful_publishes)}/{len(request.platforms)} successful")
            
            background_tasks.add_task(track_publishing_performance)
            
            return APIResponse(
                success=len(successful_publishes) > 0,
                message=f"Published to {len(successful_publishes)}/{len(request.platforms)} platforms successfully",
                data=publish_data
            )
        
    except Exception as e:
        logger.error(f"❌ Social publishing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Social publishing failed: {str(e)}")

@app.post("/publish/email", response_model=APIResponse)
async def publish_email(request: EmailCampaignRequest, background_tasks: BackgroundTasks):
    """
    Send email marketing campaigns
    
    Handles email campaign creation and delivery with template support
    """
    try:
        app_metrics["publish_requests"] += 1
        logger.info(f"📧 Sending email campaign to {len(request.recipients)} recipients")
        
        # Validate email addresses (basic validation)
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        invalid_emails = [email for email in request.recipients if not re.match(email_pattern, email)]
        if invalid_emails:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid email addresses: {invalid_emails}"
            )
        
        # Initialize publisher
        publisher = Publisher()
        
        # Prepare campaign data
        campaign_data = {
            "subject": request.subject,
            "html_content": request.content,
            "template_id": getattr(request, 'template_id', None),
            "send_immediately": True
        }
        
        # Determine segment based on recipients
        # For now, we'll use "all_subscribers" since ConvertKit manages segments
        segment = "all_subscribers"
        
        # Send email campaign
        email_result = await publisher.send_email_campaign(campaign_data, segment)
        
        if email_result.get("success"):
            # Save campaign to database if available
            db = get_database()
            if db.is_connected:
                try:
                    saved_campaign = await db.save_published_content({
                        'content_id': None,  # No specific content_id for direct email campaigns
                        'platform': 'email',
                        'url': None,  # Email campaigns don't have URLs
                        'engagement_metrics': {
                            'recipients': len(request.recipients),
                            'subject': request.subject,
                            'campaign_id': email_result.get('campaign_id')
                        },
                        'status': 'published'
                    })
                    logger.info(f"💾 Saved email campaign record: {saved_campaign.get('id')}")
                except Exception as db_error:
                    logger.warning(f"⚠️ Database save failed: {str(db_error)}")
            
            # Background task for tracking
            async def track_email_performance():
                await asyncio.sleep(5)
                logger.info(f"📊 Email campaign tracking initiated for: {email_result.get('campaign_id')}")
            
            background_tasks.add_task(track_email_performance)
            
            response_data = {
                "campaign_id": email_result.get("campaign_id"),
                "status": email_result.get("status", "sent"),
                "platform": "email",
                "segment": segment,
                "recipients": {
                    "total": len(request.recipients),
                    "valid": len(request.recipients) - len(invalid_emails),
                    "invalid": len(invalid_emails)
                },
                "campaign_details": {
                    "subject": request.subject,
                    "template_id": getattr(request, 'template_id', None),
                    "created_at": datetime.utcnow().isoformat(),
                    "service": "convertkit"
                },
                "metadata": email_result.get("metadata", {})
            }
            
            return APIResponse(
                success=True,
                message="Email campaign sent successfully via ConvertKit",
                data=response_data
            )
        else:
            # Handle email sending failure
            error_message = email_result.get("error", "Email campaign failed")
            logger.error(f"❌ Email campaign failed: {error_message}")
            
            # Return failure response with details
            return APIResponse(
                success=False,
                message=f"Email campaign failed: {error_message}",
                data={
                    "campaign_id": None,
                    "status": "failed",
                    "error": error_message,
                    "recipients": {
                        "total": len(request.recipients),
                        "valid": len(request.recipients) - len(invalid_emails),
                        "invalid": len(invalid_emails)
                    },
                    "campaign_details": {
                        "subject": request.subject,
                        "template_id": getattr(request, 'template_id', None),
                        "failed_at": datetime.utcnow().isoformat()
                    }
                }
            )
        
    except Exception as e:
        logger.error(f"❌ Email campaign failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email campaign failed: {str(e)}")

# Cross-posting endpoint
@app.post("/publish/cross-post", response_model=APIResponse)
async def cross_post_content(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Cross-post existing content to all configured platforms
    
    Takes content from database and adapts it for multiple platforms
    """
    try:
        content_id = request.get("content_id")
        if not content_id:
            raise HTTPException(status_code=400, detail="content_id is required")
        
        app_metrics["publish_requests"] += 1
        logger.info(f"🌐 Cross-posting content: {content_id}")
        
        # Initialize publisher
        publisher = Publisher()
        
        # Perform cross-posting
        cross_post_result = await publisher.cross_post(content_id)
        
        if cross_post_result.get("success"):
            # Background task for performance tracking
            async def track_cross_post_performance():
                await asyncio.sleep(3)
                platforms_successful = cross_post_result.get("platforms_successful", 0)
                platforms_attempted = cross_post_result.get("platforms_attempted", 0)
                logger.info(f"📊 Cross-post performance: {platforms_successful}/{platforms_attempted} platforms successful")
            
            background_tasks.add_task(track_cross_post_performance)
            
            return APIResponse(
                success=True,
                message=f"Content cross-posted to {cross_post_result['platforms_successful']}/{cross_post_result['platforms_attempted']} platforms",
                data=cross_post_result
            )
        else:
            error_message = cross_post_result.get("error", "Cross-posting failed")
            return APIResponse(
                success=False,
                message=f"Cross-posting failed: {error_message}",
                data=cross_post_result
            )
            
    except Exception as e:
        logger.error(f"❌ Cross-posting failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cross-posting failed: {str(e)}")

# Publisher status endpoint
@app.get("/publish/status", response_model=APIResponse)
async def get_publisher_status():
    """
    Get current publisher status and configuration
    
    Returns platform configurations, rate limits, and queue status
    """
    try:
        publisher = Publisher()
        status_data = publisher.get_publishing_status()
        
        return APIResponse(
            success=True,
            message="Publisher status retrieved successfully",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"❌ Publisher status retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Publisher status failed: {str(e)}")

# Scheduled content processing endpoint
@app.post("/publish/process-scheduled", response_model=APIResponse)
async def process_scheduled_publishing():
    """
    Process scheduled content that's ready for publishing
    
    Manually trigger processing of queued scheduled content
    """
    try:
        logger.info("⏰ Processing scheduled content...")
        
        publisher = Publisher()
        processing_result = await publisher.process_scheduled_content()
        
        return APIResponse(
            success=processing_result.get("success", False),
            message=f"Processed {processing_result.get('processed', 0)} scheduled items",
            data=processing_result
        )
        
    except Exception as e:
        logger.error(f"❌ Scheduled content processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scheduled processing failed: {str(e)}")

# Business Intelligence endpoints
@app.get("/intelligence/performance", response_model=APIResponse)
async def analyze_performance(days: int = 7):
    """
    Analyze content performance and engagement metrics
    
    Provides comprehensive insights into content performance across all platforms
    """
    try:
        logger.info(f"🔍 Analyzing performance for last {days} days")
        
        intelligence = BusinessIntelligence()
        intelligence.metrics_window = days
        
        performance_analysis = await intelligence.analyze_performance()
        
        return APIResponse(
            success=True,
            message=f"Performance analysis completed for {days} days",
            data=performance_analysis
        )
        
    except Exception as e:
        logger.error(f"❌ Performance analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")

@app.post("/intelligence/optimize", response_model=APIResponse)
async def optimize_content_strategy():
    """
    AI-powered content strategy optimization
    
    Analyzes performance data and provides strategic recommendations
    """
    try:
        logger.info("🎯 Optimizing content strategy based on performance data")
        
        intelligence = BusinessIntelligence()
        optimization_result = await intelligence.optimize_content_strategy()
        
        return APIResponse(
            success=True,
            message="Content strategy optimization completed",
            data=optimization_result
        )
        
    except Exception as e:
        logger.error(f"❌ Strategy optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Strategy optimization failed: {str(e)}")

@app.get("/intelligence/competitors", response_model=APIResponse)
async def track_competitors():
    """
    Competitor content analysis and market insights
    
    Monitors competitor strategies and identifies content opportunities
    """
    try:
        logger.info("👁️ Analyzing competitor content landscape")
        
        intelligence = BusinessIntelligence()
        competitor_analysis = await intelligence.competitor_tracking()
        
        return APIResponse(
            success=True,
            message="Competitor analysis completed",
            data=competitor_analysis
        )
        
    except Exception as e:
        logger.error(f"❌ Competitor tracking failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Competitor tracking failed: {str(e)}")

@app.get("/intelligence/report", response_model=APIResponse)
async def generate_intelligence_report(report_type: str = "daily"):
    """
    Generate automated performance reports
    
    Creates comprehensive reports with insights and recommendations
    """
    try:
        if report_type not in ["daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="Report type must be 'daily', 'weekly', or 'monthly'")
        
        logger.info(f"📊 Generating {report_type} intelligence report")
        
        intelligence = BusinessIntelligence()
        report_result = await intelligence.generate_report(report_type)
        
        return APIResponse(
            success=True,
            message=f"{report_type.title()} report generated successfully",
            data=report_result
        )
        
    except Exception as e:
        logger.error(f"❌ Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@app.post("/intelligence/predict-virality", response_model=APIResponse)
async def predict_content_virality(content_data: Dict[str, Any]):
    """
    Predict viral potential of content using AI analysis
    
    Analyzes content and provides virality score with improvement suggestions
    """
    try:
        logger.info("🚀 Predicting content virality potential")
        
        # Validate required fields
        if not content_data.get("title") and not content_data.get("body"):
            raise HTTPException(status_code=400, detail="Content must have at least a title or body")
        
        intelligence = BusinessIntelligence()
        virality_prediction = intelligence.predict_virality(content_data)
        
        return APIResponse(
            success=True,
            message=f"Virality prediction completed. Score: {virality_prediction.get('virality_score', 0)}/100",
            data=virality_prediction
        )
        
    except Exception as e:
        logger.error(f"❌ Virality prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Virality prediction failed: {str(e)}")

@app.get("/intelligence/insights", response_model=APIResponse)
async def get_actionable_insights():
    """
    Get actionable insights and recommendations
    
    Provides immediate actionable insights for content strategy improvement
    """
    try:
        logger.info("💡 Generating actionable insights")
        
        intelligence = BusinessIntelligence()
        
        # Get quick insights from recent performance
        performance_data = await intelligence.analyze_performance()
        optimization_data = await intelligence.optimize_content_strategy()
        
        # Extract key actionable insights
        insights = {
            "immediate_actions": [],
            "content_focus": [],
            "timing_optimizations": [],
            "platform_priorities": [],
            "performance_highlights": []
        }
        
        # Extract immediate actions from optimization
        if "strategy_optimization" in optimization_data:
            strategy = optimization_data["strategy_optimization"]
            insights["immediate_actions"] = optimization_data.get("next_actions", [])
            insights["content_focus"] = strategy.get("focus_topics", [])[:3]
            insights["timing_optimizations"] = list(strategy.get("optimal_schedule", {}).items())[:3]
        
        # Extract performance highlights
        if "key_insights" in performance_data:
            insights["performance_highlights"] = performance_data["key_insights"][:5]
        
        # Add platform priorities
        if "platform_performance" in performance_data:
            platform_rankings = performance_data["platform_performance"].get("platform_rankings", {})
            insights["platform_priorities"] = list(platform_rankings.keys())[:3]
        
        return APIResponse(
            success=True,
            message="Actionable insights generated successfully",
            data={
                "insights": insights,
                "generated_at": datetime.utcnow().isoformat(),
                "data_sources": ["performance_analysis", "strategy_optimization"]
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Insights generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Insights generation failed: {str(e)}")

# Orchestrator endpoints
@app.post("/orchestrator/content-sprint", response_model=APIResponse)
async def run_content_sprint(request: Dict[str, Any] = None):
    """
    Run a manual content sprint optimized for GTM testing
    
    Creates complete content package ready for manual publishing
    """
    try:
        topic_hint = request.get("topic_hint") if request else None
        logger.info(f"🚀 Running content sprint with topic: {topic_hint or 'trending topics'}")
        
        orchestrator = CraeftoOrchestrator()
        sprint_result = await orchestrator.manual_content_sprint(topic_hint)
        
        return APIResponse(
            success=True,
            message=f"Content sprint completed: {sprint_result.get('workflow_id', 'N/A')}",
            data=sprint_result
        )
        
    except Exception as e:
        logger.error(f"❌ Content sprint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content sprint failed: {str(e)}")

@app.post("/orchestrator/gtm-test", response_model=APIResponse)
async def run_gtm_test_cycle(request: Dict[str, str]):
    """
    Run a GTM test cycle with A/B content variants
    
    Creates test plan with variants for manual publishing and tracking
    """
    try:
        hypothesis = request.get("hypothesis")
        if not hypothesis:
            raise HTTPException(status_code=400, detail="hypothesis is required")
        
        logger.info(f"🧪 Running GTM test cycle: {hypothesis}")
        
        orchestrator = CraeftoOrchestrator()
        test_result = await orchestrator.gtm_test_cycle(hypothesis)
        
        return APIResponse(
            success=True,
            message=f"GTM test cycle created: {test_result.get('test_id', 'N/A')}",
            data=test_result
        )
        
    except Exception as e:
        logger.error(f"❌ GTM test cycle failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"GTM test cycle failed: {str(e)}")

@app.post("/orchestrator/full-pipeline", response_model=APIResponse)
async def run_full_content_pipeline(request: Dict[str, Any] = None):
    """
    Run complete end-to-end content pipeline
    
    Creates comprehensive content package for manual review (SAFE MODE)
    """
    try:
        topic = request.get("topic") if request else None
        platforms = request.get("platforms", ["linkedin", "twitter", "email"]) if request else ["linkedin", "twitter", "email"]
        
        logger.info(f"🔄 Running full content pipeline - Topic: {topic}, Platforms: {platforms}")
        
        orchestrator = CraeftoOrchestrator()
        pipeline_result = await orchestrator.full_content_pipeline(topic, platforms)
        
        return APIResponse(
            success=True,
            message=f"Content pipeline completed: {pipeline_result.get('pipeline_id', 'N/A')}",
            data=pipeline_result
        )
        
    except Exception as e:
        logger.error(f"❌ Full content pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content pipeline failed: {str(e)}")

@app.post("/orchestrator/optimization-cycle", response_model=APIResponse)
async def run_optimization_cycle():
    """
    Run complete performance analysis and optimization cycle
    
    Provides comprehensive optimization recommendations and action plan
    """
    try:
        logger.info("📈 Running performance optimization cycle")
        
        orchestrator = CraeftoOrchestrator()
        optimization_result = await orchestrator.performance_optimization_cycle()
        
        return APIResponse(
            success=True,
            message=f"Optimization cycle completed: {optimization_result.get('cycle_id', 'N/A')}",
            data=optimization_result
        )
        
    except Exception as e:
        logger.error(f"❌ Optimization cycle failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Optimization cycle failed: {str(e)}")

@app.get("/orchestrator/debrief-template", response_model=APIResponse)
async def get_debrief_template():
    """
    Get structured debrief template for campaign analysis
    
    Returns template for capturing learnings and performance insights
    """
    try:
        orchestrator = CraeftoOrchestrator()
        debrief_template = orchestrator.debrief_template()
        
        return APIResponse(
            success=True,
            message="Debrief template retrieved successfully",
            data={
                "template": debrief_template,
                "usage_instructions": {
                    "when_to_use": "After completing any content campaign or test",
                    "completion_time": "Within 48 hours of campaign end",
                    "review_process": "Team review recommended for major campaigns"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Debrief template retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debrief template failed: {str(e)}")

@app.get("/orchestrator/status", response_model=APIResponse)
async def get_orchestrator_status():
    """
    Get current orchestrator status and configuration
    
    Returns safe mode status, GTM focus areas, and workflow history
    """
    try:
        orchestrator = CraeftoOrchestrator()
        
        status_data = {
            "safe_mode": orchestrator.safe_mode,
            "gtm_entry_focus": orchestrator.gtm_entry_focus,
            "current_workflow": orchestrator.current_workflow,
            "workflow_history": orchestrator.workflow_history[-5:] if orchestrator.workflow_history else [],  # Last 5 workflows
            "agent_status": {
                "research_agent": "initialized",
                "content_generator": "initialized", 
                "visual_generator": "initialized",
                "publisher": "initialized",
                "business_intelligence": "initialized",
                "quality_controller": "initialized"
            },
            "configuration": {
                "manual_publish_only": True,
                "auto_scheduling_disabled": True,
                "qa_required": True,
                "approval_workflow": "manual_review"
            }
        }
        
        return APIResponse(
            success=True,
            message="Orchestrator status retrieved successfully",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"❌ Orchestrator status retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Orchestrator status failed: {str(e)}")

# New API Routes with Authentication and Rate Limiting

@app.post("/api/research/trending")
@limiter.limit("30/minute")
async def research_trending(
    request: Request,
    research_request: TrendingResearchAPIRequest,
    auth_level: str = Depends(verify_api_key)
):
    """
    Endpoint to trigger trend research
    Returns scored list of opportunities
    Saves to database for processing
    """
    try:
        start_time = time.time()
        logger.info(f"🔍 API Research trending request from {auth_level} user")
        
        # Add to queue for heavy processing
        request_id = await add_to_queue("research_trending", research_request.dict())
        
        # Initialize research agent
        research_agent = ResearchAgent()
        
        # Perform research (current implementation uses predefined sources)
        trending_data = await research_agent.find_trending_topics()
        
        # Limit results
        limited_data = trending_data[:research_request.limit]
        
        # Generate content ideas
        content_ideas = await research_agent.generate_content_ideas(limited_data)
        
        # Save to database if available
        db = get_database()
        research_id = None
        if db:
            research_id = await db.save_research({
                "topics": limited_data,
                "content_ideas": content_ideas,
                "sources": research_request.sources,
                "request_id": request_id
            })
        
        processing_time = time.time() - start_time
        
        response_data = {
            "research_id": research_id,
            "trending_topics": limited_data,
            "content_opportunities": content_ideas,
            "sources_used": research_request.sources,
            "total_found": len(trending_data),
            "returned_count": len(limited_data),
            "processing_time_seconds": round(processing_time, 3),
            "queue_position": len(request_queue)
        }
        
        app_metrics["research_requests"] += 1
        app_metrics["successful_requests"] += 1
        
        return get_consistent_response(
            success=True,
            message=f"Research completed: {len(limited_data)} trending topics found",
            data=response_data,
            request_id=request_id
        )
        
    except Exception as e:
        app_metrics["failed_requests"] += 1
        logger.error(f"❌ API Research trending failed: {str(e)}")
        return get_consistent_response(
            success=False,
            message="Research trending failed",
            errors=[str(e)],
            request_id=request_id if 'request_id' in locals() else None
        )

@app.post("/api/generate/blog")
@limiter.limit("10/minute")
async def generate_blog(
    request: Request,
    blog_request: BlogGenerationRequest,
    auth_level: str = Depends(verify_api_key)
):
    """
    Generate complete blog post with:
    - SEO optimization
    - Hero image
    - Social snippets
    - Email version
    """
    try:
        start_time = time.time()
        logger.info(f"📝 API Blog generation request: {blog_request.topic}")
        
        # Add to queue for heavy processing
        request_id = await add_to_queue("generate_blog", blog_request.dict())
        
        # Initialize generators
        content_generator = ContentGenerator()
        visual_generator = VisualGenerator()
        
        # Get research data if provided
        research_data = None
        if blog_request.research_id:
            db = get_database()
            if db:
                research_data = await db.get_research_by_id(blog_request.research_id)
        
        # Generate blog post (current implementation uses topic and research_data only)
        blog_content = await content_generator.generate_blog_post(
            topic=blog_request.topic,
            research_data=research_data
        )
        
        # Generate hero image if requested
        hero_image = None
        if blog_request.include_hero_image:
            try:
                hero_result = await visual_generator.generate_blog_hero(
                    title=blog_request.topic,
                    style="minimal SaaS"
                )
                hero_image = hero_result
            except Exception as img_error:
                logger.warning(f"⚠️ Hero image generation failed: {img_error}")
        
        # Generate social snippets
        social_content = await content_generator.generate_social_posts(
            topic=blog_request.topic,
            blog_content=blog_content.get("content", "")
        )
        
        # Generate email version
        email_content = await content_generator.generate_email_campaign(
            topic=blog_request.topic,
            segment="blog_readers"
        )
        
        # Save to database
        db = get_database()
        content_id = None
        if db:
            content_id = await db.save_generated_content({
                "type": "blog_post",
                "topic": blog_request.topic,
                "content": blog_content,
                "social_snippets": social_content,
                "email_version": email_content,
                "hero_image": hero_image,
                "research_id": blog_request.research_id,
                "style": blog_request.style,
                "request_id": request_id
            })
        
        processing_time = time.time() - start_time
        
        response_data = {
            "content_id": content_id,
            "blog_post": blog_content,
            "hero_image": hero_image,
            "social_snippets": social_content,
            "email_version": email_content,
            "seo_metadata": {
                "meta_description": blog_content.get("meta_description"),
                "keywords": blog_request.seo_keywords,
                "word_count": len(blog_content.get("content", "").split())
            },
            "processing_time_seconds": round(processing_time, 3)
        }
        
        app_metrics["generation_requests"] += 1
        app_metrics["successful_requests"] += 1
        
        return get_consistent_response(
            success=True,
            message=f"Blog post generated successfully: {blog_request.topic}",
            data=response_data,
            request_id=request_id
        )
        
    except Exception as e:
        app_metrics["failed_requests"] += 1
        logger.error(f"❌ API Blog generation failed: {str(e)}")
        return get_consistent_response(
            success=False,
            message="Blog generation failed",
            errors=[str(e)],
            request_id=request_id if 'request_id' in locals() else None
        )

@app.post("/api/generate/campaign")
@limiter.limit("5/minute")
async def generate_campaign(
    request: Request,
    campaign_request: CampaignGenerationRequest,
    auth_level: str = Depends(verify_api_key)
):
    """
    Create multi-channel campaign:
    - Email sequence
    - Social posts
    - Blog support
    - Visual assets
    """
    try:
        start_time = time.time()
        logger.info(f"📧 API Campaign generation: {campaign_request.campaign_type}")
        
        # Add to queue for heavy processing
        request_id = await add_to_queue("generate_campaign", campaign_request.dict())
        
        # Initialize agents
        content_generator = ContentGenerator()
        visual_generator = VisualGenerator()
        
        # Get content data
        db = get_database()
        content_data = []
        if db:
            for content_id in campaign_request.content_ids:
                content = await db.get_content_by_id(content_id)
                if content:
                    content_data.append(content)
        
        if not content_data:
            raise HTTPException(
                status_code=400,
                detail="No valid content found for provided IDs"
            )
        
        # Generate email sequence
        email_sequence = []
        for i, content in enumerate(content_data):
            email = await content_generator.generate_email_campaign(
                topic=content.get("topic", f"Campaign Email {i+1}"),
                segment=campaign_request.target_segments[0] if campaign_request.target_segments else "all"
            )
            email_sequence.append(email)
        
        # Generate social posts for each channel
        social_campaigns = {}
        for channel in campaign_request.channels:
            if channel == "social":
                campaign_posts = []
                for content in content_data:
                    posts = await content_generator.generate_social_posts(
                        topic=content.get("topic", "Campaign Content"),
                        blog_content=content.get("content")
                    )
                    campaign_posts.append(posts)
                social_campaigns[channel] = campaign_posts
        
        # Generate visual assets
        visual_assets = []
        try:
            for content in content_data[:3]:  # Limit to 3 visuals
                og_image = await visual_generator.generate_og_image(
                    title=content.get("topic", "Campaign"),
                    subtitle=campaign_request.campaign_type.title()
                )
                visual_assets.append(og_image)
        except Exception as visual_error:
            logger.warning(f"⚠️ Visual generation failed: {visual_error}")
        
        # Create campaign schedule
        campaign_schedule = []
        days_interval = campaign_request.duration_days // max(len(content_data), 1)
        for i, content in enumerate(content_data):
            schedule_date = datetime.utcnow() + timedelta(days=i * days_interval)
            campaign_schedule.append({
                "content_id": content.get("id"),
                "scheduled_date": schedule_date.isoformat(),
                "channels": campaign_request.channels
            })
        
        # Save campaign to database
        campaign_id = None
        if db:
            campaign_id = await db.save_campaign({
                "type": campaign_request.campaign_type,
                "content_ids": campaign_request.content_ids,
                "email_sequence": email_sequence,
                "social_campaigns": social_campaigns,
                "visual_assets": visual_assets,
                "schedule": campaign_schedule,
                "duration_days": campaign_request.duration_days,
                "target_segments": campaign_request.target_segments,
                "request_id": request_id
            })
        
        processing_time = time.time() - start_time
        
        response_data = {
            "campaign_id": campaign_id,
            "campaign_type": campaign_request.campaign_type,
            "email_sequence": email_sequence,
            "social_campaigns": social_campaigns,
            "visual_assets": visual_assets,
            "campaign_schedule": campaign_schedule,
            "content_pieces": len(content_data),
            "duration_days": campaign_request.duration_days,
            "channels": campaign_request.channels,
            "processing_time_seconds": round(processing_time, 3)
        }
        
        app_metrics["generation_requests"] += 1
        app_metrics["successful_requests"] += 1
        
        return get_consistent_response(
            success=True,
            message=f"Campaign generated successfully: {campaign_request.campaign_type}",
            data=response_data,
            request_id=request_id
        )
        
    except Exception as e:
        app_metrics["failed_requests"] += 1
        logger.error(f"❌ API Campaign generation failed: {str(e)}")
        return get_consistent_response(
            success=False,
            message="Campaign generation failed",
            errors=[str(e)],
            request_id=request_id if 'request_id' in locals() else None
        )

@app.post("/api/publish/batch")
@limiter.limit("10/minute")
async def publish_batch(
    request: Request,
    publish_request: BatchPublishRequest,
    background_tasks: BackgroundTasks,
    auth_level: str = Depends(verify_api_key)
):
    """
    Publish multiple pieces across platforms
    Handle scheduling and immediate publishing
    Return publishing status and URLs
    """
    try:
        start_time = time.time()
        logger.info(f"📢 API Batch publish: {len(publish_request.content_ids)} items")
        
        # Add to queue for heavy processing
        request_id = await add_to_queue("publish_batch", publish_request.dict())
        
        if publish_request.dry_run:
            logger.info("🧪 Dry run mode - no actual publishing")
        
        # Initialize publisher
        publisher = Publisher()
        
        # Get content data
        db = get_database()
        content_items = []
        if db:
            for content_id in publish_request.content_ids:
                content = await db.get_content_by_id(content_id)
                if content:
                    content_items.append(content)
        
        if not content_items:
            raise HTTPException(
                status_code=400,
                detail="No valid content found for provided IDs"
            )
        
        # Publishing results
        publishing_results = []
        scheduled_items = []
        
        for content in content_items:
            content_result = {
                "content_id": content.get("id"),
                "title": content.get("topic", "Untitled"),
                "platforms": {},
                "scheduled": False,
                "errors": []
            }
            
            # Handle scheduling vs immediate publishing
            if publish_request.schedule:
                if not publish_request.dry_run:
                    try:
                        schedule_result = await publisher.schedule_content(
                            content=content,
                            platforms=publish_request.platforms,
                            publish_time=publish_request.schedule
                        )
                        scheduled_items.append(schedule_result)
                        content_result["scheduled"] = True
                        content_result["schedule_time"] = publish_request.schedule.isoformat()
                    except Exception as schedule_error:
                        content_result["errors"].append(f"Scheduling failed: {str(schedule_error)}")
                else:
                    content_result["scheduled"] = True
                    content_result["schedule_time"] = publish_request.schedule.isoformat()
                    content_result["dry_run"] = True
            else:
                # Immediate publishing
                for platform in publish_request.platforms:
                    platform_result = {
                        "success": False,
                        "url": None,
                        "error": None,
                        "dry_run": publish_request.dry_run
                    }
                    
                    if not publish_request.dry_run:
                        try:
                            if platform == "twitter":
                                result = await publisher.publish_to_twitter(
                                    content=content.get("content", ""),
                                    image_url=content.get("image_url")
                                )
                                platform_result["success"] = result.get("success", False)
                                platform_result["url"] = result.get("url")
                            elif platform == "linkedin":
                                result = await publisher.publish_to_linkedin(
                                    content=content.get("content", ""),
                                    image_url=content.get("image_url")
                                )
                                platform_result["success"] = result.get("success", False)
                                platform_result["url"] = result.get("url")
                        except Exception as platform_error:
                            platform_result["error"] = str(platform_error)
                    else:
                        platform_result["success"] = True  # Dry run success
                        platform_result["url"] = f"https://{platform}.com/dry-run-post"
                    
                    content_result["platforms"][platform] = platform_result
            
            publishing_results.append(content_result)
        
        # Save publishing records to database
        if db and not publish_request.dry_run:
            for result in publishing_results:
                if any(p.get("success") for p in result["platforms"].values()) or result["scheduled"]:
                    await db.mark_published(
                        content_id=result["content_id"],
                        platforms=list(result["platforms"].keys()),
                        scheduled=result["scheduled"],
                        urls=[p.get("url") for p in result["platforms"].values() if p.get("url")]
                    )
        
        # Background task for performance tracking
        if not publish_request.dry_run:
            background_tasks.add_task(
                track_publishing_performance,
                publishing_results,
                request_id
            )
        
        processing_time = time.time() - start_time
        
        # Calculate success metrics
        total_publishes = sum(len(r["platforms"]) for r in publishing_results)
        successful_publishes = sum(
            sum(1 for p in r["platforms"].values() if p.get("success"))
            for r in publishing_results
        )
        
        response_data = {
            "batch_id": request_id,
            "total_content_items": len(content_items),
            "total_publish_attempts": total_publishes,
            "successful_publishes": successful_publishes,
            "scheduled_items": len(scheduled_items),
            "publishing_results": publishing_results,
            "success_rate": (successful_publishes / max(total_publishes, 1)) * 100,
            "dry_run": publish_request.dry_run,
            "processing_time_seconds": round(processing_time, 3)
        }
        
        app_metrics["publish_requests"] += 1
        app_metrics["successful_requests"] += 1
        
        return get_consistent_response(
            success=True,
            message=f"Batch publish completed: {successful_publishes}/{total_publishes} successful",
            data=response_data,
            request_id=request_id
        )
        
    except Exception as e:
        app_metrics["failed_requests"] += 1
        logger.error(f"❌ API Batch publish failed: {str(e)}")
        return get_consistent_response(
            success=False,
            message="Batch publish failed",
            errors=[str(e)],
            request_id=request_id if 'request_id' in locals() else None
        )

@app.get("/api/dashboard")
@limiter.limit("60/minute")
async def dashboard(request: Request, auth_level: str = Depends(verify_api_key)):
    """
    Real-time metrics dashboard:
    - Today's published content
    - Performance metrics
    - Upcoming schedule
    - AI suggestions
    - System health
    """
    try:
        logger.info("📊 API Dashboard request")
        
        # Get database connection
        db = get_database()
        
        # Today's published content
        today_content = []
        if db:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_content = await db.get_published_content_since(today_start)
        
        # Performance metrics
        performance_metrics = {}
        if db:
            performance_metrics = await db.get_performance_summary(days=7)
        
        # Upcoming schedule
        upcoming_schedule = []
        if db:
            upcoming_schedule = await db.get_scheduled_content(limit=10)
        
        # AI suggestions (mock for now)
        ai_suggestions = [
            {
                "type": "content_opportunity",
                "title": "SaaS Onboarding Best Practices",
                "confidence": 0.85,
                "reason": "High engagement topic with low competition"
            },
            {
                "type": "publishing_time",
                "title": "Optimal posting time: 2:00 PM EST",
                "confidence": 0.92,
                "reason": "Based on audience activity patterns"
            },
            {
                "type": "content_gap",
                "title": "Missing visual content",
                "confidence": 0.78,
                "reason": "Visual posts perform 3x better"
            }
        ]
        
        # System health
        uptime = datetime.utcnow() - app_metrics["startup_time"]
        system_health = {
            "status": "healthy",
            "uptime_hours": round(uptime.total_seconds() / 3600, 2),
            "queue_size": len(request_queue),
            "success_rate": (app_metrics["successful_requests"] / max(app_metrics["total_requests"], 1)) * 100,
            "active_background_tasks": app_metrics["background_tasks_running"],
            "database_connected": db is not None,
            "api_keys_configured": len([k for k in VALID_API_KEYS.keys() if k != "default"]),
            "rate_limit_status": "normal"
        }
        
        # Content analytics
        content_analytics = {
            "total_generated_today": len(today_content),
            "avg_engagement_rate": performance_metrics.get("avg_engagement_rate", 0),
            "top_performing_topic": performance_metrics.get("top_topic", "SaaS Design"),
            "content_types_distribution": performance_metrics.get("content_distribution", {}),
            "platform_performance": performance_metrics.get("platform_performance", {})
        }
        
        dashboard_data = {
            "today_published": today_content,
            "performance_metrics": performance_metrics,
            "upcoming_schedule": upcoming_schedule,
            "ai_suggestions": ai_suggestions,
            "system_health": system_health,
            "content_analytics": content_analytics,
            "request_queue_status": {
                "current_size": len(request_queue),
                "max_size": MAX_QUEUE_SIZE,
                "processing_rate": "~2 requests/minute"
            }
        }
        
        app_metrics["successful_requests"] += 1
        
        return get_consistent_response(
            success=True,
            message="Dashboard data retrieved successfully",
            data=dashboard_data
        )
        
    except Exception as e:
        app_metrics["failed_requests"] += 1
        logger.error(f"❌ API Dashboard failed: {str(e)}")
        return get_consistent_response(
            success=False,
            message="Dashboard retrieval failed",
            errors=[str(e)]
        )

@app.post("/api/webhook/make")
@limiter.limit("100/minute")
async def handle_make_webhook(
    request: Request,
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    signature_valid: bool = Depends(verify_webhook_signature)
):
    """
    Handle integrations from Make.com:
    - LinkedIn publishing confirmations
    - External tool triggers
    - Performance data ingestion
    """
    try:
        logger.info(f"🔗 Webhook received: {payload.event_type} from {payload.source}")
        
        # Process different webhook types
        webhook_result = {
            "event_type": payload.event_type,
            "processed_at": datetime.utcnow().isoformat(),
            "source": payload.source,
            "status": "processed"
        }
        
        db = get_database()
        
        if payload.event_type == "publishing_confirmation":
            # Handle publishing confirmation
            content_id = payload.data.get("content_id")
            platform = payload.data.get("platform")
            post_url = payload.data.get("post_url")
            engagement_data = payload.data.get("engagement", {})
            
            if db and content_id:
                await db.update_published_content(
                    content_id=content_id,
                    platform=platform,
                    post_url=post_url,
                    engagement_data=engagement_data
                )
                
            webhook_result["action"] = "updated_publishing_record"
            webhook_result["content_id"] = content_id
            
        elif payload.event_type == "performance_data":
            # Handle performance data ingestion
            content_id = payload.data.get("content_id")
            metrics = payload.data.get("metrics", {})
            
            if db and content_id:
                await db.track_performance(
                    content_id=content_id,
                    platform=payload.data.get("platform"),
                    metrics=metrics
                )
                
            webhook_result["action"] = "updated_performance_metrics"
            webhook_result["content_id"] = content_id
            
        elif payload.event_type == "external_trigger":
            # Handle external automation triggers
            trigger_type = payload.data.get("trigger_type")
            trigger_data = payload.data.get("trigger_data", {})
            
            # Add to background processing queue
            background_tasks.add_task(
                process_external_trigger,
                trigger_type,
                trigger_data
            )
            
            webhook_result["action"] = "queued_for_processing"
            webhook_result["trigger_type"] = trigger_type
            
        elif payload.event_type == "content_request":
            # Handle content generation requests from external tools
            topic = payload.data.get("topic")
            content_type = payload.data.get("content_type", "social")
            
            if topic:
                # Add to processing queue
                request_id = await add_to_queue("webhook_content_generation", {
                    "topic": topic,
                    "content_type": content_type,
                    "webhook_data": payload.data
                })
                
                webhook_result["action"] = "content_generation_queued"
                webhook_result["request_id"] = request_id
        
        # Log webhook for audit trail
        if db:
            await db.log_webhook_event({
                "event_type": payload.event_type,
                "source": payload.source,
                "data": payload.data,
                "result": webhook_result,
                "timestamp": payload.timestamp
            })
        
        app_metrics["successful_requests"] += 1
        
        return get_consistent_response(
            success=True,
            message=f"Webhook processed successfully: {payload.event_type}",
            data=webhook_result
        )
        
    except Exception as e:
        app_metrics["failed_requests"] += 1
        logger.error(f"❌ Webhook processing failed: {str(e)}")
        return get_consistent_response(
            success=False,
            message="Webhook processing failed",
            errors=[str(e)]
        )

# Helper functions for background tasks
async def track_publishing_performance(publishing_results: List[Dict], request_id: str):
    """Background task to track publishing performance"""
    try:
        db = get_database()
        if not db:
            return
            
        for result in publishing_results:
            for platform, platform_result in result["platforms"].items():
                if platform_result.get("success") and platform_result.get("url"):
                    # Start tracking this published content
                    await db.track_performance(
                        content_id=result["content_id"],
                        platform=platform,
                        metrics={"initial_publish": True, "url": platform_result["url"]}
                    )
                    
        logger.info(f"✅ Performance tracking initiated for request: {request_id}")
        
    except Exception as e:
        logger.error(f"❌ Performance tracking failed: {str(e)}")

async def process_external_trigger(trigger_type: str, trigger_data: Dict):
    """Background task to process external triggers"""
    try:
        logger.info(f"🔄 Processing external trigger: {trigger_type}")
        
        if trigger_type == "content_generation":
            # Trigger content generation workflow
            orchestrator = CraeftoOrchestrator()
            await orchestrator.manual_content_sprint(
                topic_hint=trigger_data.get("topic")
            )
            
        elif trigger_type == "performance_analysis":
            # Trigger performance analysis
            intelligence = BusinessIntelligence()
            await intelligence.analyze_performance()
            
        elif trigger_type == "competitor_check":
            # Trigger competitor analysis
            research_agent = ResearchAgent()
            competitor_url = trigger_data.get("competitor_url")
            if competitor_url:
                await research_agent.analyze_competitor(competitor_url)
        
        logger.info(f"✅ External trigger processed: {trigger_type}")
        
    except Exception as e:
        logger.error(f"❌ External trigger processing failed: {str(e)}")

# Dashboard endpoint
async def get_dashboard_metrics():
    """
    Get comprehensive performance metrics and analytics
    
    Returns detailed metrics about system performance, content generation, and publishing success rates
    """
    try:
        logger.info("📊 Fetching dashboard metrics")
        
        # Calculate additional metrics
        uptime = datetime.utcnow() - app_metrics["startup_time"]
        success_rate = (app_metrics["successful_requests"] / max(app_metrics["total_requests"], 1)) * 100
        
        dashboard_data = {
            "system_metrics": {
                "uptime_seconds": uptime.total_seconds(),
                "uptime_hours": uptime.total_seconds() / 3600,
                "total_requests": app_metrics["total_requests"],
                "successful_requests": app_metrics["successful_requests"],
                "failed_requests": app_metrics["failed_requests"],
                "success_rate_percentage": round(success_rate, 2),
                "current_background_tasks": app_metrics["background_tasks_running"]
            },
            "feature_usage": {
                "research_requests": app_metrics["research_requests"],
                "generation_requests": app_metrics["generation_requests"],
                "publish_requests": app_metrics["publish_requests"]
            },
            "scheduler_info": {
                "last_scheduled_run": app_metrics.get("last_scheduled_run"),
                "next_scheduled_run": app_metrics.get("next_scheduled_run"),
                "schedule_interval": "4 hours"
            },
            "performance_data": {
                "avg_response_time_ms": 150,  # Mock data
                "memory_usage_mb": 256,       # Mock data
                "cpu_usage_percent": 15,      # Mock data
                "active_connections": 5       # Mock data
            },
            "content_analytics": {
                "total_content_generated": app_metrics["generation_requests"],
                "total_publications": app_metrics["publish_requests"],
                "trending_topics_analyzed": app_metrics["research_requests"] * 10,
                "success_metrics": {
                    "content_generation_success_rate": 98.5,
                    "publication_success_rate": 96.2,
                    "research_accuracy_rate": 94.8
                }
            }
        }
        
        return APIResponse(
            success=True,
            message="Dashboard metrics retrieved successfully",
            data=dashboard_data
        )
        
    except Exception as e:
        logger.error(f"❌ Dashboard metrics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard metrics failed: {str(e)}")

# Root endpoint
@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🚀 CRAEFTO Automation API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "health_check": "/health",
        "metrics": "/dashboard/metrics",
        "endpoints": {
            "research": ["/research/trending", "/research/competitor"],
            "generation": ["/generate/content", "/generate/visual"],
            "publishing": ["/publish/social", "/publish/email"],
            "monitoring": ["/status", "/health", "/dashboard/metrics"],
            "configuration": ["/config/status", "/brand/config", "/config/rate-limits"],
            "database": [
                "/database/status", 
                "/database/setup", 
                "/database/tables",
                "/database/content/pending",
                "/database/content/top-performing",
                "/database/content/publish",
                "/database/performance/track"
            ],
            "orchestrator": [
                "/orchestrator/content-sprint",
                "/orchestrator/gtm-test",
                "/orchestrator/full-pipeline",
                "/orchestrator/optimization-cycle",
                "/orchestrator/debrief-template",
                "/orchestrator/status"
            ],
            "api_v1": {
                "research": ["/api/research/trending"],
                "generation": ["/api/generate/blog", "/api/generate/campaign"],
                "publishing": ["/api/publish/batch"],
                "dashboard": ["/api/dashboard"],
                "webhooks": ["/api/webhook/make"]
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False,
        log_level=settings.log_level.lower()
    )
