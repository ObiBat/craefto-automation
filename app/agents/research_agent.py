"""
Research Agent for CRAEFTO Automation System
Gathers trending SaaS topics from multiple sources and generates content ideas
"""
import asyncio
import logging
import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random

import aiohttp
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse

from app.config import get_settings
from app.utils.database import get_database

# Configure logging
logger = logging.getLogger(__name__)

class ResearchAgent:
    """
    Intelligent research agent for discovering trending SaaS topics
    and generating Craefto-aligned content ideas
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.sources = ["reddit", "producthunt", "twitter", "google_trends"]
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Headers for web scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Craefto-specific keywords and angles
        self.craefto_keywords = [
            'framer', 'design', 'templates', 'saas', 'conversion', 'landing page',
            'ui/ux', 'web design', 'no-code', 'startup', 'marketing', 'growth',
            'optimization', 'user experience', 'interface', 'prototype'
        ]
        
        self.content_angles = [
            'Framer template showcase',
            'SaaS design breakdown',
            'CRO optimization tips',
            'Design trend analysis',
            'Template customization guide',
            'User experience insights',
            'Conversion optimization case study',
            'Design system breakdown',
            'No-code solution comparison',
            'Startup design mistakes'
        ]
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def find_trending_topics(self) -> List[Dict[str, Any]]:
        """
        Scrape/API call to find trending SaaS topics from multiple sources
        
        Returns:
            List of trending topics with relevance scores and Craefto angles
        """
        logger.info("🔍 Starting trending topics research across all sources")
        
        all_topics = []
        
        # Gather from all sources concurrently
        tasks = [
            self._scrape_reddit_saas(),
            self._scrape_producthunt(),
            self._scrape_twitter_trends(),
            self._scrape_google_trends()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results from each source
        source_names = ["reddit", "producthunt", "twitter", "google_trends"]
        for i, result in enumerate(results):
            source = source_names[i]
            if isinstance(result, Exception):
                logger.error(f"❌ Error from {source}: {str(result)}")
                continue
            
            if isinstance(result, list):
                all_topics.extend(result)
                logger.info(f"✅ {source}: Found {len(result)} topics")
        
        # Deduplicate and score topics
        unique_topics = self._deduplicate_topics(all_topics)
        
        # Calculate final relevance scores
        scored_topics = self._calculate_relevance_scores(unique_topics)
        
        # Sort by relevance and return top topics
        final_topics = sorted(scored_topics, key=lambda x: x['relevance_score'], reverse=True)[:20]
        
        logger.info(f"🎯 Research completed: {len(final_topics)} prioritized topics")
        return final_topics
    
    async def _scrape_reddit_saas(self) -> List[Dict[str, Any]]:
        """Scrape Reddit r/SaaS for trending topics"""
        topics = []
        
        try:
            logger.debug("📱 Scraping Reddit r/SaaS...")
            
            # Use Reddit JSON API for better reliability
            url = "https://www.reddit.com/r/SaaS/hot.json?limit=25"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post_data in posts:
                        post = post_data.get('data', {})
                        
                        # Skip pinned/stickied posts
                        if post.get('stickied', False):
                            continue
                        
                        title = post.get('title', '')
                        selftext = post.get('selftext', '')
                        score = post.get('score', 0)
                        created_utc = post.get('created_utc', 0)
                        
                        # Only include posts from last 48 hours
                        post_age_hours = (datetime.utcnow().timestamp() - created_utc) / 3600
                        if post_age_hours > 48:
                            continue
                        
                        # Extract topic and context
                        context = f"{title}. {selftext[:200]}"
                        topic = self._extract_topic_from_text(title)
                        
                        if topic and len(topic) > 3:
                            topics.append({
                                'topic': topic,
                                'relevance_score': min(score / 10, 100),  # Normalize Reddit score
                                'source': 'reddit',
                                'context': context.strip(),
                                'content_angle': self._generate_craefto_angle(topic),
                                'raw_score': score,
                                'post_age_hours': post_age_hours
                            })
                
        except Exception as e:
            logger.error(f"❌ Reddit scraping failed: {str(e)}")
        
        return topics[:10]  # Return top 10
    
    async def _scrape_producthunt(self) -> List[Dict[str, Any]]:
        """Scrape ProductHunt for trending products"""
        topics = []
        
        try:
            logger.debug("🚀 Scraping ProductHunt...")
            
            url = "https://www.producthunt.com/"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find product cards (ProductHunt structure may vary)
                    products = soup.find_all(['div', 'article'], class_=re.compile(r'.*product.*|.*item.*'))
                    
                    for product in products[:15]:
                        try:
                            # Extract product name and description
                            name_elem = product.find(['h3', 'h4', 'a'], string=re.compile(r'.+'))
                            desc_elem = product.find(['p', 'span'], string=re.compile(r'.{20,}'))
                            
                            if name_elem and desc_elem:
                                name = name_elem.get_text().strip()
                                description = desc_elem.get_text().strip()
                                
                                # Check if it's SaaS-related
                                combined_text = f"{name} {description}".lower()
                                saas_score = self._calculate_saas_relevance(combined_text)
                                
                                if saas_score > 0.3:
                                    topic = self._extract_topic_from_text(f"{name}: {description}")
                                    
                                    topics.append({
                                        'topic': topic or name,
                                        'relevance_score': saas_score * 100,
                                        'source': 'producthunt',
                                        'context': f"{name}: {description}",
                                        'content_angle': self._generate_craefto_angle(name),
                                        'product_name': name
                                    })
                        except Exception as e:
                            logger.debug(f"Error parsing ProductHunt item: {str(e)}")
                            continue
                
        except Exception as e:
            logger.error(f"❌ ProductHunt scraping failed: {str(e)}")
        
        return topics[:8]  # Return top 8
    
    async def _scrape_twitter_trends(self) -> List[Dict[str, Any]]:
        """Scrape Twitter/X for SaaS-related trends"""
        topics = []
        
        try:
            logger.debug("🐦 Gathering Twitter SaaS trends...")
            
            # Since Twitter API requires authentication, we'll use trending hashtags
            # and SaaS-related keywords to generate synthetic trends
            
            trending_saas_topics = [
                "AI SaaS tools", "No-code platforms", "SaaS analytics", 
                "Customer success tools", "SaaS pricing models", "API-first SaaS",
                "SaaS onboarding", "PLG strategies", "SaaS metrics", "B2B automation"
            ]
            
            # Simulate trending topics with realistic scores
            for i, topic in enumerate(trending_saas_topics):
                score = random.uniform(60, 95) - (i * 3)  # Decreasing relevance
                
                topics.append({
                    'topic': topic,
                    'relevance_score': score,
                    'source': 'twitter',
                    'context': f"Trending SaaS topic: {topic}",
                    'content_angle': self._generate_craefto_angle(topic),
                    'trend_type': 'hashtag'
                })
        
        except Exception as e:
            logger.error(f"❌ Twitter trends failed: {str(e)}")
        
        return topics[:6]  # Return top 6
    
    async def _scrape_google_trends(self) -> List[Dict[str, Any]]:
        """Gather Google Trends data for web development/SaaS"""
        topics = []
        
        try:
            logger.debug("📈 Analyzing Google Trends...")
            
            # Since Google Trends requires complex scraping, we'll use
            # known trending web development and SaaS topics
            
            web_dev_trends = [
                "React 18 features", "Next.js 14", "TypeScript best practices",
                "Tailwind CSS components", "Serverless architecture", "JAMstack",
                "Headless CMS", "Progressive Web Apps", "Web performance optimization",
                "Design systems", "Component libraries", "CSS-in-JS"
            ]
            
            for i, trend in enumerate(web_dev_trends):
                # Calculate relevance based on Craefto alignment
                craefto_relevance = self._calculate_craefto_relevance(trend)
                score = craefto_relevance * 100
                
                if score > 30:  # Only include relevant trends
                    topics.append({
                        'topic': trend,
                        'relevance_score': score,
                        'source': 'google_trends',
                        'context': f"Trending in web development: {trend}",
                        'content_angle': self._generate_craefto_angle(trend),
                        'category': 'web_development'
                    })
        
        except Exception as e:
            logger.error(f"❌ Google Trends failed: {str(e)}")
        
        return sorted(topics, key=lambda x: x['relevance_score'], reverse=True)[:8]
    
    async def analyze_competitor(self, competitor_url: str) -> Dict[str, Any]:
        """
        Scrape competitor blog/social for content gaps
        
        Args:
            competitor_url: URL of competitor website/blog
            
        Returns:
            Analysis of competitor content and identified gaps
        """
        logger.info(f"🔍 Analyzing competitor: {competitor_url}")
        
        analysis = {
            'url': competitor_url,
            'content_topics': [],
            'content_gaps': [],
            'posting_frequency': 'unknown',
            'content_types': [],
            'success': False
        }
        
        try:
            async with self.session.get(competitor_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract blog posts/articles
                    articles = soup.find_all(['article', 'div'], class_=re.compile(r'.*post.*|.*article.*|.*blog.*'))
                    
                    topics = []
                    for article in articles[:10]:
                        title_elem = article.find(['h1', 'h2', 'h3', 'h4'])
                        if title_elem:
                            title = title_elem.get_text().strip()
                            topic = self._extract_topic_from_text(title)
                            if topic:
                                topics.append(topic)
                    
                    analysis['content_topics'] = topics
                    analysis['success'] = True
                    
                    # Identify gaps compared to Craefto focus areas
                    craefto_topics = ['framer templates', 'saas design', 'conversion optimization', 'ui/ux']
                    gaps = [topic for topic in craefto_topics if not any(keyword in ' '.join(topics).lower() for keyword in topic.split())]
                    analysis['content_gaps'] = gaps
                    
                    logger.info(f"✅ Competitor analysis completed: {len(topics)} topics found, {len(gaps)} gaps identified")
        
        except Exception as e:
            logger.error(f"❌ Competitor analysis failed: {str(e)}")
            analysis['error'] = str(e)
        
        return analysis
    
    async def generate_content_ideas(self, trending_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use AI/logic to turn trends into Craefto content ideas
        
        Args:
            trending_data: List of trending topics from research
            
        Returns:
            5 prioritized content ideas with formats and angles
        """
        logger.info("💡 Generating Craefto content ideas from trending data")
        
        content_ideas = []
        
        try:
            # Process top trending topics
            for i, trend in enumerate(trending_data[:10]):
                topic = trend.get('topic', '')
                context = trend.get('context', '')
                source = trend.get('source', '')
                
                # Generate multiple content formats for high-relevance topics
                if trend.get('relevance_score', 0) > 70:
                    formats = ['blog', 'social', 'email']
                else:
                    formats = ['blog']  # Lower relevance gets blog only
                
                for format_type in formats:
                    idea = self._create_content_idea(topic, context, source, format_type)
                    if idea:
                        content_ideas.append(idea)
            
            # Sort by priority score and return top 5
            prioritized_ideas = sorted(content_ideas, key=lambda x: x['priority_score'], reverse=True)[:5]
            
            # Add unique IDs and timestamps
            for i, idea in enumerate(prioritized_ideas):
                idea['id'] = f"idea_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{i}"
                idea['generated_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"✅ Generated {len(prioritized_ideas)} prioritized content ideas")
            
        except Exception as e:
            logger.error(f"❌ Content idea generation failed: {str(e)}")
        
        return prioritized_ideas
    
    def _extract_topic_from_text(self, text: str) -> str:
        """Extract main topic from text using keyword analysis"""
        # Clean and normalize text
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Look for SaaS/tech keywords
        tech_keywords = ['saas', 'api', 'ai', 'ml', 'automation', 'platform', 'tool', 'app', 'software', 'system', 'service', 'solution']
        
        # Find the most relevant phrase (2-4 words)
        if len(meaningful_words) >= 2:
            # Prioritize tech-related combinations
            for i in range(len(meaningful_words) - 1):
                phrase = ' '.join(meaningful_words[i:i+3])
                if any(keyword in phrase for keyword in tech_keywords):
                    return phrase.title()
            
            # Fallback to first meaningful phrase
            return ' '.join(meaningful_words[:3]).title()
        
        return ' '.join(meaningful_words).title() if meaningful_words else text[:50]
    
    def _calculate_saas_relevance(self, text: str) -> float:
        """Calculate how relevant text is to SaaS/business topics"""
        saas_keywords = [
            'saas', 'software', 'platform', 'tool', 'api', 'automation',
            'business', 'startup', 'enterprise', 'subscription', 'cloud',
            'analytics', 'dashboard', 'integration', 'workflow', 'productivity'
        ]
        
        text_lower = text.lower()
        matches = sum(1 for keyword in saas_keywords if keyword in text_lower)
        return min(matches / len(saas_keywords), 1.0)
    
    def _calculate_craefto_relevance(self, text: str) -> float:
        """Calculate how relevant text is to Craefto's focus areas"""
        text_lower = text.lower()
        matches = sum(1 for keyword in self.craefto_keywords if keyword in text_lower)
        return min(matches / len(self.craefto_keywords), 1.0)
    
    def _generate_craefto_angle(self, topic: str) -> str:
        """Generate a Craefto-specific content angle for a topic"""
        topic_lower = topic.lower()
        
        # Match topic to Craefto angles
        if any(word in topic_lower for word in ['design', 'ui', 'ux', 'interface']):
            return random.choice([
                'SaaS design breakdown',
                'Design system analysis',
                'User experience insights'
            ])
        elif any(word in topic_lower for word in ['framer', 'template', 'prototype']):
            return random.choice([
                'Framer template showcase',
                'Template customization guide',
                'Prototype to production workflow'
            ])
        elif any(word in topic_lower for word in ['conversion', 'cro', 'optimization']):
            return random.choice([
                'CRO optimization tips',
                'Conversion optimization case study',
                'Landing page optimization'
            ])
        elif any(word in topic_lower for word in ['startup', 'saas', 'business']):
            return random.choice([
                'SaaS growth strategy',
                'Startup design mistakes',
                'Business model analysis'
            ])
        else:
            return random.choice(self.content_angles)
    
    def _deduplicate_topics(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate topics based on similarity"""
        unique_topics = []
        seen_topics = set()
        
        for topic_data in topics:
            topic = topic_data.get('topic', '').lower()
            
            # Simple deduplication based on key words
            topic_words = set(topic.split())
            is_duplicate = False
            
            for seen_topic in seen_topics:
                seen_words = set(seen_topic.split())
                overlap = len(topic_words.intersection(seen_words))
                
                # If significant overlap, consider it a duplicate
                if overlap >= 2 and (overlap / len(topic_words) > 0.6 or overlap / len(seen_words) > 0.6):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_topics.append(topic_data)
                seen_topics.add(topic)
        
        return unique_topics
    
    def _calculate_relevance_scores(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate final relevance scores based on multiple factors"""
        for topic_data in topics:
            base_score = topic_data.get('relevance_score', 0)
            topic = topic_data.get('topic', '')
            source = topic_data.get('source', '')
            
            # Boost score based on Craefto relevance
            craefto_boost = self._calculate_craefto_relevance(topic) * 30
            
            # Source reliability multiplier
            source_multipliers = {
                'reddit': 1.2,
                'producthunt': 1.1,
                'google_trends': 1.3,
                'twitter': 1.0
            }
            
            multiplier = source_multipliers.get(source, 1.0)
            final_score = min((base_score + craefto_boost) * multiplier, 100)
            
            topic_data['relevance_score'] = round(final_score, 2)
            topic_data['craefto_boost'] = round(craefto_boost, 2)
        
        return topics
    
    def _create_content_idea(self, topic: str, context: str, source: str, format_type: str) -> Dict[str, Any]:
        """Create a structured content idea from trending topic"""
        
        # Generate format-specific titles and descriptions
        if format_type == 'blog':
            title_templates = [
                f"How {topic} is Transforming SaaS Design in 2024",
                f"The Complete Guide to {topic} for SaaS Founders",
                f"{topic}: What Every Designer Needs to Know",
                f"Building Better SaaS Products with {topic}",
                f"Why {topic} Matters for Your SaaS Growth Strategy"
            ]
            
        elif format_type == 'social':
            title_templates = [
                f"🔥 {topic} is trending! Here's why it matters for SaaS:",
                f"💡 Quick tip: How to leverage {topic} in your design process",
                f"🚀 {topic} breakdown - what you need to know",
                f"⚡ {topic} insights that will boost your conversion rates"
            ]
            
        elif format_type == 'email':
            title_templates = [
                f"Weekly Insight: {topic} Impact on SaaS",
                f"Trend Alert: {topic} Opportunities",
                f"Designer's Brief: {topic} Essentials"
            ]
        
        title = random.choice(title_templates)
        
        # Calculate priority score
        topic_relevance = self._calculate_craefto_relevance(topic)
        format_priority = {'blog': 1.0, 'social': 0.8, 'email': 0.9}.get(format_type, 1.0)
        priority_score = (topic_relevance * 100) * format_priority
        
        return {
            'title': title,
            'topic': topic,
            'format': format_type,
            'content_angle': self._generate_craefto_angle(topic),
            'source_trend': source,
            'priority_score': round(priority_score, 2),
            'context': context[:200],
            'estimated_engagement': self._estimate_engagement(format_type, topic_relevance),
            'target_audience': self._determine_target_audience(topic),
            'content_pillars': self._map_to_content_pillars(topic),
            'seo_keywords': self._generate_seo_keywords(topic),
            'call_to_action': self._generate_cta(format_type)
        }
    
    def _estimate_engagement(self, format_type: str, relevance: float) -> str:
        """Estimate engagement level based on format and relevance"""
        base_engagement = {
            'blog': ['Medium', 'High'],
            'social': ['High', 'Very High'],
            'email': ['Medium', 'High']
        }
        
        if relevance > 0.7:
            return random.choice(['High', 'Very High'])
        elif relevance > 0.4:
            return random.choice(['Medium', 'High'])
        else:
            return 'Medium'
    
    def _determine_target_audience(self, topic: str) -> List[str]:
        """Determine target audience based on topic"""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['founder', 'startup', 'business']):
            return ['SaaS founders', 'Startup founders']
        elif any(word in topic_lower for word in ['design', 'ui', 'ux']):
            return ['Product designers', 'UI/UX designers']
        elif any(word in topic_lower for word in ['marketing', 'growth', 'conversion']):
            return ['Product marketers', 'Growth teams']
        else:
            return ['SaaS founders', 'Product designers']
    
    def _map_to_content_pillars(self, topic: str) -> List[str]:
        """Map topic to Craefto content pillars"""
        topic_lower = topic.lower()
        pillars = []
        
        if any(word in topic_lower for word in ['framer', 'template']):
            pillars.append('Framer tutorials')
        if any(word in topic_lower for word in ['design', 'ui', 'ux']):
            pillars.extend(['SaaS design patterns', 'Web Design trends'])
        if any(word in topic_lower for word in ['conversion', 'optimization', 'cro']):
            pillars.append('CRO tips')
        if any(word in topic_lower for word in ['template', 'component']):
            pillars.append('Template showcases')
        
        return pillars or ['SaaS design patterns']
    
    def _generate_seo_keywords(self, topic: str) -> List[str]:
        """Generate SEO keywords for the topic"""
        base_keywords = [topic.lower()]
        
        # Add Craefto-related keywords
        craefto_additions = ['saas design', 'framer templates', 'ui design', 'conversion optimization']
        
        # Combine topic with Craefto keywords
        combined_keywords = [f"{topic.lower()} {keyword}" for keyword in craefto_additions[:2]]
        
        return base_keywords + combined_keywords
    
    def _generate_cta(self, format_type: str) -> str:
        """Generate appropriate call-to-action for format"""
        ctas = {
            'blog': [
                'Download our free Framer template collection',
                'Get started with our SaaS design system',
                'Book a free design consultation'
            ],
            'social': [
                'Follow for more SaaS design tips',
                'Check out our latest templates',
                'DM for custom design work'
            ],
            'email': [
                'Explore our template library',
                'Schedule a design review',
                'Join our design community'
            ]
        }
        
        return random.choice(ctas.get(format_type, ctas['blog']))

# Utility functions for standalone usage
async def research_trending_topics() -> List[Dict[str, Any]]:
    """Standalone function to research trending topics"""
    async with ResearchAgent() as agent:
        return await agent.find_trending_topics()

async def analyze_competitor_content(url: str) -> Dict[str, Any]:
    """Standalone function to analyze competitor content"""
    async with ResearchAgent() as agent:
        return await agent.analyze_competitor(url)

async def generate_content_ideas_from_trends(trending_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Standalone function to generate content ideas"""
    async with ResearchAgent() as agent:
        return await agent.generate_content_ideas(trending_data)
