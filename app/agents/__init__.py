"""
AI Agents for CRAEFTO Automation System
"""

from .research_agent import (
    ResearchAgent,
    research_trending_topics,
    analyze_competitor_content,
    generate_content_ideas_from_trends
)

from .content_generator import (
    ContentGenerator,
    generate_blog_content,
    generate_social_content,
    generate_email_content
)

from .visual_generator import (
    VisualGenerator,
    generate_blog_hero_image,
    generate_social_graphic,
    generate_og_image,
    create_email_banner
)

from .publisher import (
    Publisher,
    publish_twitter_thread,
    publish_linkedin_post,
    send_email_broadcast,
    cross_post_content
)

from .intelligence import (
    BusinessIntelligence,
    analyze_content_performance,
    optimize_strategy,
    track_competitors,
    generate_daily_report,
    predict_content_virality
)

__all__ = [
    'ResearchAgent',
    'research_trending_topics',
    'analyze_competitor_content', 
    'generate_content_ideas_from_trends',
    'ContentGenerator',
    'generate_blog_content',
    'generate_social_content',
    'generate_email_content',
    'VisualGenerator',
    'generate_blog_hero_image',
    'generate_social_graphic',
    'generate_og_image',
    'create_email_banner',
    'Publisher',
    'publish_twitter_thread',
    'publish_linkedin_post',
    'send_email_broadcast',
    'cross_post_content',
    'BusinessIntelligence',
    'analyze_content_performance',
    'optimize_strategy',
    'track_competitors',
    'generate_daily_report',
    'predict_content_virality'
]
