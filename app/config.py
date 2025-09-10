"""
Configuration settings for CRAEFTO automation system
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Dict, Any
import logging


class Settings(BaseSettings):
    """Application settings loaded from environment variables using Pydantic"""
    
    # Core AI API Keys
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for content generation",
        env="OPENAI_API_KEY"
    )
    
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic Claude API key for content generation",
        env="ANTHROPIC_API_KEY"
    )
    
    # Visual Generation
    midjourney_webhook: str = Field(
        default="",
        description="Discord bot or proxy webhook URL for Midjourney image generation",
        env="MIDJOURNEY_WEBHOOK"
    )
    
    # Twitter/X API Configuration
    twitter_api_key: str = Field(
        default="",
        description="Twitter API Key (Consumer Key)",
        env="TWITTER_API_KEY"
    )
    
    twitter_api_secret: str = Field(
        default="",
        description="Twitter API Secret (Consumer Secret)",
        env="TWITTER_API_SECRET"
    )
    
    twitter_access_token: str = Field(
        default="",
        description="Twitter Access Token",
        env="TWITTER_ACCESS_TOKEN"
    )
    
    twitter_access_secret: str = Field(
        default="",
        description="Twitter Access Token Secret",
        env="TWITTER_ACCESS_SECRET"
    )
    
    # Database Configuration
    supabase_url: str = Field(
        default="",
        description="Supabase project URL",
        env="SUPABASE_URL"
    )
    
    supabase_key: str = Field(
        default="",
        description="Supabase API key (anon/service_role)",
        env="SUPABASE_KEY"
    )
    
    # Email Marketing
    convertkit_api_key: str = Field(
        default="",
        description="ConvertKit API key for email campaigns",
        env="CONVERTKIT_API_KEY"
    )
    
    # Integration Automation
    make_webhook_url: str = Field(
        default="",
        description="Make.com webhook URL for workflow integrations",
        env="MAKE_WEBHOOK_URL"
    )
    
    # Additional Social Media APIs (Optional)
    linkedin_client_id: str = Field(
        default="",
        description="LinkedIn OAuth Client ID",
        env="LINKEDIN_CLIENT_ID"
    )
    
    linkedin_client_secret: str = Field(
        default="",
        description="LinkedIn OAuth Client Secret",
        env="LINKEDIN_CLIENT_SECRET"
    )
    
    linkedin_access_token: str = Field(
        default="",
        description="LinkedIn Access Token",
        env="LINKEDIN_ACCESS_TOKEN"
    )
    
    # Alternative Email Services
    mailchimp_api_key: str = Field(
        default="",
        description="Mailchimp API key (alternative to ConvertKit)",
        env="MAILCHIMP_API_KEY"
    )
    
    mailchimp_server_prefix: str = Field(
        default="",
        description="Mailchimp server prefix (e.g., us1, us2)",
        env="MAILCHIMP_SERVER_PREFIX"
    )
    
    # SMTP Configuration (Fallback)
    smtp_server: str = Field(
        default="smtp.gmail.com",
        description="SMTP server for direct email sending",
        env="SMTP_SERVER"
    )
    
    smtp_port: int = Field(
        default=587,
        description="SMTP server port",
        env="SMTP_PORT"
    )
    
    email_address: str = Field(
        default="",
        description="Email address for SMTP authentication",
        env="EMAIL_ADDRESS"
    )
    
    email_password: str = Field(
        default="",
        description="Email password or app password for SMTP",
        env="EMAIL_PASSWORD"
    )
    
    # System Configuration
    environment: str = Field(
        default="development",
        description="Application environment (development/staging/production)",
        env="ENVIRONMENT"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG/INFO/WARNING/ERROR)",
        env="LOG_LEVEL"
    )
    
    automation_schedule_hours: int = Field(
        default=4,
        description="Hours between automated content generation cycles",
        env="AUTOMATION_SCHEDULE_HOURS"
    )
    
    max_content_generation_retries: int = Field(
        default=3,
        description="Maximum retries for content generation failures",
        env="MAX_CONTENT_GENERATION_RETRIES"
    )
    
    # =============================================================================
    # RATE LIMITING & FAULT TOLERANCE CONFIGURATION
    # =============================================================================
    
    # Global Rate Limiting (Fallback defaults)
    rate_limit_per_minute: int = Field(
        default=60,
        description="Global API rate limit per minute (fallback)",
        env="RATE_LIMIT_PER_MINUTE"
    )
    
    rate_limit_per_hour: int = Field(
        default=1000,
        description="Global API rate limit per hour (fallback)",
        env="RATE_LIMIT_PER_HOUR"
    )
    
    # Service-Specific Rate Limits (calls per minute)
    openai_rate_limit: int = Field(
        default=20,
        description="OpenAI API calls per minute",
        env="OPENAI_RATE_LIMIT"
    )
    
    anthropic_rate_limit: int = Field(
        default=15,
        description="Anthropic API calls per minute",
        env="ANTHROPIC_RATE_LIMIT"
    )
    
    twitter_rate_limit: int = Field(
        default=300,
        description="Twitter API calls per minute (per 15-min window)",
        env="TWITTER_RATE_LIMIT"
    )
    
    linkedin_rate_limit: int = Field(
        default=100,
        description="LinkedIn API calls per minute",
        env="LINKEDIN_RATE_LIMIT"
    )
    
    supabase_rate_limit: int = Field(
        default=100,
        description="Supabase API calls per minute",
        env="SUPABASE_RATE_LIMIT"
    )
    
    convertkit_rate_limit: int = Field(
        default=120,
        description="ConvertKit API calls per minute",
        env="CONVERTKIT_RATE_LIMIT"
    )
    
    midjourney_rate_limit: int = Field(
        default=5,
        description="Midjourney API calls per minute",
        env="MIDJOURNEY_RATE_LIMIT"
    )
    
    make_webhook_rate_limit: int = Field(
        default=60,
        description="Make.com webhook calls per minute",
        env="MAKE_WEBHOOK_RATE_LIMIT"
    )
    
    # Retry Logic Configuration
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
        env="MAX_RETRIES"
    )
    
    base_retry_delay: float = Field(
        default=1.0,
        description="Base delay for exponential backoff (seconds)",
        env="BASE_RETRY_DELAY"
    )
    
    max_retry_delay: float = Field(
        default=60.0,
        description="Maximum retry delay (seconds)",
        env="MAX_RETRY_DELAY"
    )
    
    exponential_base: float = Field(
        default=2.0,
        description="Exponential backoff multiplier",
        env="EXPONENTIAL_BASE"
    )
    
    jitter_enabled: bool = Field(
        default=True,
        description="Enable jitter in retry delays",
        env="JITTER_ENABLED"
    )
    
    # Queue System Configuration
    queue_max_size: int = Field(
        default=1000,
        description="Maximum queue size for requests",
        env="QUEUE_MAX_SIZE"
    )
    
    queue_timeout: float = Field(
        default=300.0,
        description="Queue timeout in seconds",
        env="QUEUE_TIMEOUT"
    )
    
    queue_batch_size: int = Field(
        default=10,
        description="Number of requests to process in batch",
        env="QUEUE_BATCH_SIZE"
    )
    
    queue_processing_interval: float = Field(
        default=1.0,
        description="Interval between queue processing cycles (seconds)",
        env="QUEUE_PROCESSING_INTERVAL"
    )
    
    # Circuit Breaker Configuration
    circuit_breaker_failure_threshold: int = Field(
        default=5,
        description="Number of failures before opening circuit",
        env="CIRCUIT_BREAKER_FAILURE_THRESHOLD"
    )
    
    circuit_breaker_recovery_timeout: float = Field(
        default=60.0,
        description="Circuit breaker recovery timeout (seconds)",
        env="CIRCUIT_BREAKER_RECOVERY_TIMEOUT"
    )
    
    circuit_breaker_expected_exception: str = Field(
        default="requests.exceptions.RequestException",
        description="Exception type that triggers circuit breaker",
        env="CIRCUIT_BREAKER_EXPECTED_EXCEPTION"
    )
    
    # Content Generation Settings
    content_types: List[str] = Field(
        default=["twitter", "linkedin", "blog", "email"],
        description="Supported content types for generation"
    )
    
    max_content_length: Dict[str, int] = Field(
        default={
            "twitter": 280,
            "linkedin": 3000,
            "blog": 5000,
            "email": 2000
        },
        description="Maximum content length by type"
    )
    
    # Trend Research Sources
    trend_sources: List[str] = Field(
        default=[
            "https://trends.google.com/trends/trendingsearches/daily/rss",
            "https://www.reddit.com/r/trending.json",
            "https://newsapi.org/v2/top-headlines"
        ],
        description="Data sources for trend research"
    )
    
    # =============================================================================
    # CRAEFTO BRAND CONSTANTS
    # =============================================================================
    
    # Brand Voice & Tone
    brand_voice: str = Field(
        default="Premium, crafted, SaaS-focused, practical, speed-oriented, film noise, viby",
        description="Craefto brand voice and tone characteristics",
        env="BRAND_VOICE"
    )
    
    # Brand Colors (Hex codes) - Minimal Black & White Palette
    primary_colors: List[str] = Field(
        default=[
            "#010101",  # near-black (background base)
            "#151615",  # deep charcoal (text & accents)  
            "#333433",  # dark gray (UI elements)
            "#535955",  # muted dark gray-green (background swirls)
            "#69736c",  # desaturated green-gray (secondary accents)
            "#ededed"   # light gray / off-white (text & highlights)
        ],
        description="Craefto minimal black & white color palette with subtle green-gray accents"
    )
    
    # Target Audience Segments
    target_audience: List[str] = Field(
        default=["SaaS founders", "Product marketers", "Growth teams", "Solopreneurs"],
        description="Craefto target audience segments"
    )
    
    # Content Pillars & Topics
    content_pillars: List[str] = Field(
        default=[
            "Framer tutorials",
            "SaaS design patterns", 
            "CRO tips",
            "Template showcases",
            "Web Design trends",
            "Award winning designs"
        ],
        description="Craefto content pillars and main topics"
    )
    
    # Typography & Visual Identity
    primary_font: str = Field(
        default="Space Mono",
        description="Primary font for body text and UI elements"
    )
    
    logo_font: str = Field(
        default="Source Serif 4 Bold",
        description="Font used for the Craefto logo"
    )
    
    logo_symbol: str = Field(
        default="æ",
        description="Text-based logo symbol for Craefto brand"
    )
    
    design_style: str = Field(
        default="Minimal black and white with subtle green-gray accents, film grain textures, geometric shapes, and calligraphy-inspired typography",
        description="Overall design aesthetic and style approach"
    )
    
    # Visual Style Elements
    visual_elements: List[str] = Field(
        default=[
            "Film grain textures",
            "Geometric shapes",
            "Typography focus", 
            "Calligraphy inspiration",
            "Minimal compositions",
            "High contrast",
            "Clean lines",
            "Subtle textures"
        ],
        description="Key visual elements that define Craefto's aesthetic"
    )
    
    design_inspirations: List[str] = Field(
        default=[
            "Film photography grain",
            "Bauhaus geometric principles", 
            "Modern calligraphy",
            "Swiss typography",
            "Brutalist design",
            "Japanese minimalism",
            "Scandinavian design"
        ],
        description="Design movements and styles that inspire Craefto's visual identity"
    )
    
    # Security & Performance
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Secret key for JWT tokens and encryption",
        env="SECRET_KEY"
    )
    
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
        env="CORS_ORIGINS"
    )
    
    max_workers: int = Field(
        default=4,
        description="Maximum number of background workers",
        env="MAX_WORKERS"
    )
    
    # Validation
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'staging', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(f'environment must be one of {valid_envs}')
        return v.lower()
    
    @validator('automation_schedule_hours')
    def validate_schedule_hours(cls, v):
        if v < 1 or v > 24:
            raise ValueError('automation_schedule_hours must be between 1 and 24')
        return v
    
    @validator('cors_origins', pre=True)
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('max_retries')
    def validate_max_retries(cls, v):
        if v < 0 or v > 10:
            raise ValueError('max_retries must be between 0 and 10')
        return v
    
    @validator('base_retry_delay', 'max_retry_delay')
    def validate_retry_delays(cls, v):
        if v < 0.1 or v > 300:
            raise ValueError('retry delays must be between 0.1 and 300 seconds')
        return v
    
    @validator('exponential_base')
    def validate_exponential_base(cls, v):
        if v < 1.1 or v > 10:
            raise ValueError('exponential_base must be between 1.1 and 10')
        return v
    
    @validator('queue_max_size')
    def validate_queue_max_size(cls, v):
        if v < 10 or v > 10000:
            raise ValueError('queue_max_size must be between 10 and 10000')
        return v
    
    @validator('circuit_breaker_failure_threshold')
    def validate_circuit_breaker_threshold(cls, v):
        if v < 1 or v > 100:
            raise ValueError('circuit_breaker_failure_threshold must be between 1 and 100')
        return v
    
    # Helper methods
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    def get_twitter_config(self) -> Dict[str, str]:
        """Get Twitter API configuration as dictionary"""
        return {
            "api_key": self.twitter_api_key,
            "api_secret": self.twitter_api_secret,
            "access_token": self.twitter_access_token,
            "access_secret": self.twitter_access_secret
        }
    
    def get_supabase_config(self) -> Dict[str, str]:
        """Get Supabase configuration as dictionary"""
        return {
            "url": self.supabase_url,
            "key": self.supabase_key
        }
    
    def get_linkedin_config(self) -> Dict[str, str]:
        """Get LinkedIn API configuration as dictionary"""
        return {
            "client_id": self.linkedin_client_id,
            "client_secret": self.linkedin_client_secret,
            "access_token": self.linkedin_access_token
        }
    
    def has_required_api_keys(self) -> Dict[str, bool]:
        """Check which API keys are configured"""
        return {
            "openai": bool(self.openai_api_key),
            "anthropic": bool(self.anthropic_api_key),
            "twitter": all([
                self.twitter_api_key,
                self.twitter_api_secret,
                self.twitter_access_token,
                self.twitter_access_secret
            ]),
            "supabase": bool(self.supabase_url and self.supabase_key),
            "convertkit": bool(self.convertkit_api_key),
            "midjourney": bool(self.midjourney_webhook),
            "make": bool(self.make_webhook_url)
        }
    
    # =============================================================================
    # BRAND HELPER METHODS
    # =============================================================================
    
    def get_brand_config(self) -> Dict[str, Any]:
        """Get complete Craefto brand configuration"""
        return {
            "voice": self.brand_voice,
            "colors": {
                "palette": self.primary_colors,
                "near_black": self.primary_colors[0],        # #010101 - background base
                "deep_charcoal": self.primary_colors[1],     # #151615 - text & accents
                "dark_gray": self.primary_colors[2],         # #333433 - UI elements
                "muted_gray_green": self.primary_colors[3],  # #535955 - background swirls
                "desaturated_green": self.primary_colors[4], # #69736c - secondary accents
                "light_gray": self.primary_colors[5]         # #ededed - text & highlights
            },
            "typography": {
                "primary_font": self.primary_font,
                "logo_font": self.logo_font,
                "logo_symbol": self.logo_symbol
            },
            "design_style": self.design_style,
            "visual_elements": self.visual_elements,
            "design_inspirations": self.design_inspirations,
            "audience": self.target_audience,
            "content_pillars": self.content_pillars
        }
    
    def get_brand_voice_keywords(self) -> List[str]:
        """Extract brand voice keywords as list"""
        return [keyword.strip() for keyword in self.brand_voice.split(",")]
    
    def get_random_content_pillar(self) -> str:
        """Get a random content pillar for content generation"""
        import random
        return random.choice(self.content_pillars)
    
    def get_random_target_audience(self) -> str:
        """Get a random target audience segment"""
        import random
        return random.choice(self.target_audience)
    
    def get_content_prompt_context(self) -> str:
        """Get brand context for AI content generation prompts"""
        voice_keywords = ", ".join(self.get_brand_voice_keywords())
        audience = ", ".join(self.target_audience)
        pillars = ", ".join(self.content_pillars)
        visual_elements = ", ".join(self.visual_elements)
        inspirations = ", ".join(self.design_inspirations)
        
        return f"""
Brand Voice: {voice_keywords}
Target Audience: {audience}
Content Focus Areas: {pillars}
Visual Style: {self.design_style}
Visual Elements: {visual_elements}
Design Inspirations: {inspirations}
Color Palette: {", ".join(self.primary_colors)}
Typography: Primary font is {self.primary_font}, Logo uses {self.logo_font}
Logo: Text-based "{self.logo_symbol}" symbol
        """.strip()
    
    def is_brand_relevant_topic(self, topic: str) -> bool:
        """Check if a topic aligns with Craefto brand pillars"""
        topic_lower = topic.lower()
        brand_keywords = [
            "framer", "saas", "design", "cro", "conversion", "template", 
            "web design", "ui", "ux", "landing page", "growth", "marketing",
            "startup", "founder", "product", "trends", "award"
        ]
        return any(keyword in topic_lower for keyword in brand_keywords)
    
    # =============================================================================
    # RATE LIMITING & FAULT TOLERANCE HELPER METHODS
    # =============================================================================
    
    def get_service_rate_limits(self) -> Dict[str, int]:
        """Get all service-specific rate limits"""
        return {
            "openai": self.openai_rate_limit,
            "anthropic": self.anthropic_rate_limit,
            "twitter": self.twitter_rate_limit,
            "linkedin": self.linkedin_rate_limit,
            "supabase": self.supabase_rate_limit,
            "convertkit": self.convertkit_rate_limit,
            "midjourney": self.midjourney_rate_limit,
            "make_webhook": self.make_webhook_rate_limit,
            "global_fallback": self.rate_limit_per_minute
        }
    
    def get_rate_limit_for_service(self, service: str) -> int:
        """Get rate limit for a specific service with fallback"""
        rate_limits = self.get_service_rate_limits()
        return rate_limits.get(service.lower(), self.rate_limit_per_minute)
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration for exponential backoff"""
        return {
            "max_retries": self.max_retries,
            "base_delay": self.base_retry_delay,
            "max_delay": self.max_retry_delay,
            "exponential_base": self.exponential_base,
            "jitter_enabled": self.jitter_enabled
        }
    
    def calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and optional jitter"""
        import random
        import math
        
        if attempt <= 0:
            return 0
        
        # Exponential backoff: base_delay * (exponential_base ^ (attempt - 1))
        delay = self.base_retry_delay * (self.exponential_base ** (attempt - 1))
        
        # Cap at max_retry_delay
        delay = min(delay, self.max_retry_delay)
        
        # Add jitter if enabled (±25% randomness)
        if self.jitter_enabled:
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0.1, delay)  # Ensure minimum delay
        
        return delay
    
    def get_queue_config(self) -> Dict[str, Any]:
        """Get queue system configuration"""
        return {
            "max_size": self.queue_max_size,
            "timeout": self.queue_timeout,
            "batch_size": self.queue_batch_size,
            "processing_interval": self.queue_processing_interval
        }
    
    def get_circuit_breaker_config(self) -> Dict[str, Any]:
        """Get circuit breaker configuration"""
        return {
            "failure_threshold": self.circuit_breaker_failure_threshold,
            "recovery_timeout": self.circuit_breaker_recovery_timeout,
            "expected_exception": self.circuit_breaker_expected_exception
        }
    
    def get_fault_tolerance_config(self) -> Dict[str, Any]:
        """Get complete fault tolerance configuration"""
        return {
            "rate_limits": self.get_service_rate_limits(),
            "retry": self.get_retry_config(),
            "queue": self.get_queue_config(),
            "circuit_breaker": self.get_circuit_breaker_config()
        }
    
    def is_service_rate_limited(self, service: str, current_calls: int) -> bool:
        """Check if service has exceeded rate limit"""
        limit = self.get_rate_limit_for_service(service)
        return current_calls >= limit
    
    def get_service_health_check_config(self) -> Dict[str, Dict[str, Any]]:
        """Get health check configuration for each service"""
        return {
            "openai": {
                "timeout": 30,
                "rate_limit": self.openai_rate_limit,
                "critical": True
            },
            "anthropic": {
                "timeout": 30,
                "rate_limit": self.anthropic_rate_limit,
                "critical": True
            },
            "twitter": {
                "timeout": 15,
                "rate_limit": self.twitter_rate_limit,
                "critical": False
            },
            "linkedin": {
                "timeout": 20,
                "rate_limit": self.linkedin_rate_limit,
                "critical": False
            },
            "supabase": {
                "timeout": 10,
                "rate_limit": self.supabase_rate_limit,
                "critical": True
            },
            "convertkit": {
                "timeout": 15,
                "rate_limit": self.convertkit_rate_limit,
                "critical": False
            },
            "midjourney": {
                "timeout": 60,
                "rate_limit": self.midjourney_rate_limit,
                "critical": False
            },
            "make_webhook": {
                "timeout": 30,
                "rate_limit": self.make_webhook_rate_limit,
                "critical": False
            }
        }
    
    def log_configuration_status(self):
        """Log the configuration status for debugging"""
        logger = logging.getLogger(__name__)
        api_status = self.has_required_api_keys()
        
        logger.info(f"🔧 Configuration loaded for {self.environment} environment")
        logger.info(f"📊 API Keys Status: {sum(api_status.values())}/{len(api_status)} configured")
        
        for service, configured in api_status.items():
            status = "✅" if configured else "❌"
            logger.info(f"  {status} {service.title()}")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True


# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
