"""
Content Generator Agent for CRAEFTO Automation System
Creates high-quality, brand-consistent content across multiple formats using AI
"""
import asyncio
import logging
import json
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import random

try:
    import openai
    from openai import AsyncOpenAI
except ImportError:
    openai = None
    AsyncOpenAI = None

try:
    import anthropic
    from anthropic import AsyncAnthropic
except ImportError:
    anthropic = None
    AsyncAnthropic = None

from app.config import get_settings
from app.utils.database import get_database

# Configure logging
logger = logging.getLogger(__name__)

class ContentGenerator:
    """
    AI-powered content generator for creating Craefto-branded content
    across blog posts, social media, and email campaigns
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize AI clients if API keys are available
        if self.settings.openai_api_key and AsyncOpenAI:
            self.openai_client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        
        if self.settings.anthropic_api_key and AsyncAnthropic:
            self.anthropic_client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        
        # Content cache for cost optimization
        self.content_cache = {}
        self.cache_duration = timedelta(hours=24)
        
        # Craefto brand elements
        self.brand_voice = {
            "tone": "Technical but accessible, actionable, SaaS-focused",
            "style": "Premium, crafted, speed-oriented, film noise, viby",
            "audience": ["SaaS founders", "Product marketers", "Growth teams", "Solopreneurs"],
            "key_phrases": [
                "craft exceptional SaaS experiences",
                "speed up your design process",
                "conversion-optimized templates",
                "premium Framer components",
                "SaaS design that converts",
                "award-winning design patterns"
            ],
            "content_pillars": [
                "Framer tutorials", "SaaS design patterns", "CRO tips",
                "Template showcases", "Web Design trends", "Award winning designs"
            ]
        }
        
        # Content templates and structures
        self.content_structures = {
            "blog_outline": [
                "Hook (problem identification)",
                "Context (why it matters now)",
                "Solution overview",
                "Step-by-step implementation",
                "Real-world examples",
                "Best practices",
                "Common mistakes to avoid",
                "Conclusion with CTA"
            ],
            "social_hooks": [
                "Most SaaS founders make this design mistake:",
                "Here's how to increase conversions by 40%:",
                "The #1 reason your SaaS signup page isn't converting:",
                "I analyzed 100 top SaaS landing pages. Here's what I found:",
                "Stop doing this in your SaaS design (it's killing conversions):"
            ]
        }
    
    async def generate_blog_post(self, topic: str, research_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a complete blog post with SEO optimization and multiple formats
        
        Args:
            topic: Blog post topic
            research_data: Optional research context and data
            
        Returns:
            Complete blog post with multiple formats and metadata
        """
        logger.info(f"✍️ Generating blog post for topic: {topic}")
        
        try:
            # Check cache first
            cache_key = self._get_cache_key("blog", topic, research_data)
            if cache_key in self.content_cache:
                cached_content = self.content_cache[cache_key]
                if datetime.utcnow() - cached_content['timestamp'] < self.cache_duration:
                    logger.info("📋 Using cached blog content")
                    return cached_content['content']
            
            # Step 1: Create outline with Anthropic
            outline = await self._create_blog_outline(topic, research_data)
            
            # Step 2: Write sections with GPT-4
            blog_content = await self._write_blog_sections(topic, outline, research_data)
            
            # Step 3: Apply Craefto styling and add CTAs
            styled_content = self.apply_craefto_style(blog_content)
            
            # Step 4: Generate additional formats
            seo_meta = await self._generate_seo_meta(topic, styled_content)
            social_snippets = await self._generate_social_snippets(topic, styled_content)
            email_version = await self._generate_email_version(topic, styled_content)
            
            # Compile final blog post
            final_blog_post = {
                "title": styled_content.get("title"),
                "content": styled_content.get("content"),
                "outline": outline,
                "word_count": len(styled_content.get("content", "").split()),
                "seo": seo_meta,
                "social_snippets": social_snippets,
                "email_version": email_version,
                "metadata": {
                    "topic": topic,
                    "generated_at": datetime.utcnow().isoformat(),
                    "ai_models_used": ["anthropic", "openai"],
                    "content_type": "blog",
                    "brand_voice_applied": True,
                    "estimated_read_time": max(1, len(styled_content.get("content", "").split()) // 200)
                }
            }
            
            # Cache the result
            self.content_cache[cache_key] = {
                "content": final_blog_post,
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"✅ Blog post generated: {final_blog_post['word_count']} words")
            return final_blog_post
            
        except Exception as e:
            logger.error(f"❌ Blog post generation failed: {str(e)}")
            return self._generate_fallback_blog(topic)
    
    async def generate_social_posts(self, topic: str, blog_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Create platform-specific social media posts
        
        Args:
            topic: Content topic
            blog_content: Optional blog content to reference
            
        Returns:
            Platform-specific social media content
        """
        logger.info(f"📱 Generating social posts for topic: {topic}")
        
        try:
            # Check cache
            cache_key = self._get_cache_key("social", topic, {"blog_content": blog_content})
            if cache_key in self.content_cache:
                cached_content = self.content_cache[cache_key]
                if datetime.utcnow() - cached_content['timestamp'] < self.cache_duration:
                    logger.info("📋 Using cached social content")
                    return cached_content['content']
            
            # Generate Twitter thread
            twitter_thread = await self._generate_twitter_thread(topic, blog_content)
            
            # Generate LinkedIn post
            linkedin_post = await self._generate_linkedin_post(topic, blog_content)
            
            # Generate Instagram post (if applicable)
            instagram_post = await self._generate_instagram_post(topic, blog_content)
            
            social_posts = {
                "twitter": twitter_thread,
                "linkedin": linkedin_post,
                "instagram": instagram_post,
                "metadata": {
                    "topic": topic,
                    "generated_at": datetime.utcnow().isoformat(),
                    "platforms": ["twitter", "linkedin", "instagram"],
                    "total_posts": len(twitter_thread.get("tweets", [])) + 2,  # Twitter thread + LinkedIn + Instagram
                    "estimated_engagement": self._estimate_social_engagement(topic)
                }
            }
            
            # Cache the result
            self.content_cache[cache_key] = {
                "content": social_posts,
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"✅ Social posts generated for {len(social_posts['metadata']['platforms'])} platforms")
            return social_posts
            
        except Exception as e:
            logger.error(f"❌ Social posts generation failed: {str(e)}")
            return self._generate_fallback_social(topic)
    
    async def generate_email_campaign(self, topic: str, segment: str = "all") -> Dict[str, Any]:
        """
        Create comprehensive email campaign content
        
        Args:
            topic: Email campaign topic
            segment: Target audience segment
            
        Returns:
            Complete email campaign with variants and formats
        """
        logger.info(f"📧 Generating email campaign for topic: {topic}, segment: {segment}")
        
        try:
            # Check cache
            cache_key = self._get_cache_key("email", topic, {"segment": segment})
            if cache_key in self.content_cache:
                cached_content = self.content_cache[cache_key]
                if datetime.utcnow() - cached_content['timestamp'] < self.cache_duration:
                    logger.info("📋 Using cached email content")
                    return cached_content['content']
            
            # Generate subject lines (A/B variants)
            subject_lines = await self._generate_subject_lines(topic, segment)
            
            # Generate preview text
            preview_text = await self._generate_preview_text(topic, segment)
            
            # Generate email body (HTML and plain text)
            email_body = await self._generate_email_body(topic, segment)
            
            # Add personalization and CTAs
            personalized_content = self._add_personalization(email_body, segment)
            
            email_campaign = {
                "subject_lines": subject_lines,
                "preview_text": preview_text,
                "html_content": personalized_content.get("html"),
                "plain_text_content": personalized_content.get("plain_text"),
                "personalization_tokens": personalized_content.get("tokens"),
                "cta_buttons": personalized_content.get("ctas"),
                "segment": segment,
                "metadata": {
                    "topic": topic,
                    "generated_at": datetime.utcnow().isoformat(),
                    "target_segment": segment,
                    "subject_variants": len(subject_lines),
                    "estimated_open_rate": self._estimate_email_performance(topic, segment)["open_rate"],
                    "estimated_click_rate": self._estimate_email_performance(topic, segment)["click_rate"]
                }
            }
            
            # Cache the result
            self.content_cache[cache_key] = {
                "content": email_campaign,
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"✅ Email campaign generated with {len(subject_lines)} subject variants")
            return email_campaign
            
        except Exception as e:
            logger.error(f"❌ Email campaign generation failed: {str(e)}")
            return self._generate_fallback_email(topic, segment)
    
    def apply_craefto_style(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-process content to ensure Craefto brand consistency
        
        Args:
            content: Raw content to style
            
        Returns:
            Styled content with brand voice applied
        """
        logger.debug("🎨 Applying Craefto brand styling")
        
        try:
            styled_content = content.copy()
            
            # Apply brand voice to main content
            if "content" in styled_content:
                text = styled_content["content"]
                
                # Add brand phrases naturally
                text = self._inject_brand_phrases(text)
                
                # Ensure SaaS focus
                text = self._enhance_saas_focus(text)
                
                # Add product mentions
                text = self._add_product_mentions(text)
                
                # Verify tone consistency
                text = self._adjust_tone(text)
                
                styled_content["content"] = text
            
            # Apply styling to title if present
            if "title" in styled_content:
                styled_content["title"] = self._style_title(styled_content["title"])
            
            # Add Craefto-specific CTAs
            styled_content = self._add_craefto_ctas(styled_content)
            
            logger.debug("✅ Craefto brand styling applied")
            return styled_content
            
        except Exception as e:
            logger.error(f"❌ Brand styling failed: {str(e)}")
            return content
    
    # Private helper methods
    
    async def _create_blog_outline(self, topic: str, research_data: Dict[str, Any] = None) -> List[str]:
        """Create blog outline using Anthropic"""
        if not self.anthropic_client:
            return self._generate_fallback_outline(topic)
        
        try:
            research_context = ""
            if research_data:
                research_context = f"Research context: {research_data.get('context', '')}"
            
            prompt = f"""Create a detailed blog post outline for the topic: "{topic}"

Context: This is for Craefto, a premium SaaS design company that creates Framer templates and helps SaaS companies optimize conversions through better design.

{research_context}

Target audience: SaaS founders, product marketers, growth teams
Brand voice: Technical but accessible, actionable, premium
Content length: 800-1200 words

Create an outline with 6-8 main sections that:
1. Starts with a compelling hook
2. Provides actionable insights
3. Includes specific examples
4. Ends with clear next steps

Return only the outline as a numbered list."""

            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            outline_text = response.content[0].text
            outline = [line.strip() for line in outline_text.split('\n') if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-'))]
            
            return outline[:8]  # Limit to 8 sections max
            
        except Exception as e:
            logger.warning(f"⚠️ Anthropic outline generation failed: {str(e)}")
            return self._generate_fallback_outline(topic)
    
    async def _write_blog_sections(self, topic: str, outline: List[str], research_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Write blog sections using GPT-4"""
        if not self.openai_client:
            return self._generate_fallback_blog_content(topic, outline)
        
        try:
            research_context = ""
            if research_data:
                research_context = f"\\nResearch insights: {research_data.get('context', '')}"
            
            # Generate title
            title_prompt = f"""Create a compelling blog post title for: "{topic}"

Requirements:
- Craefto brand (premium SaaS design templates)
- Target: SaaS founders and marketers
- Include benefit or outcome
- 60 characters or less for SEO
- Action-oriented

Examples:
- "How to Increase SaaS Conversions with Better Landing Page Design"
- "5 Framer Templates That Boosted SaaS Signups by 40%"
- "The Complete Guide to SaaS Design That Converts"

Return only the title."""
            
            title_response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": title_prompt}],
                max_tokens=100,
                temperature=0.7
            )
            
            title = title_response.choices[0].message.content.strip().strip('"')
            
            # Generate content
            content_prompt = f"""Write a comprehensive blog post about: "{topic}"

Title: {title}

Outline to follow:
{chr(10).join(f"{i+1}. {section}" for i, section in enumerate(outline))}

{research_context}

Brand: Craefto - Premium SaaS design templates and conversion optimization
Audience: SaaS founders, product marketers, growth teams
Tone: Technical but accessible, actionable, premium

Requirements:
- 800-1200 words
- Include specific examples and data points
- Add actionable tips in each section
- Use subheadings (##) for main sections
- Include bullet points for key insights
- End with clear next steps
- Naturally mention Framer templates and design optimization

Write the complete blog post in markdown format."""
            
            content_response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": content_prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = content_response.choices[0].message.content.strip()
            
            return {
                "title": title,
                "content": content
            }
            
        except Exception as e:
            logger.warning(f"⚠️ OpenAI content generation failed: {str(e)}")
            return self._generate_fallback_blog_content(topic, outline)
    
    async def _generate_twitter_thread(self, topic: str, blog_content: Optional[str] = None) -> Dict[str, Any]:
        """Generate Twitter thread"""
        if not self.openai_client:
            return self._generate_fallback_twitter(topic)
        
        try:
            context = f"Blog content reference: {blog_content[:500]}..." if blog_content else ""
            
            prompt = f"""Create a Twitter thread about: "{topic}"

{context}

Brand: Craefto - Premium SaaS design templates
Audience: SaaS founders, designers, marketers

Requirements:
- 5-7 tweets total
- Hook tweet with problem/solution
- Include specific tips/steps
- Add metrics or data points
- End with soft CTA to Craefto
- Each tweet under 280 characters
- Use emojis strategically
- Include thread numbers (1/7, 2/7, etc.)

Return as JSON array with each tweet as an object with 'text' and 'tweet_number' fields."""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.8
            )
            
            try:
                thread_data = json.loads(response.choices[0].message.content)
                if isinstance(thread_data, list):
                    tweets = thread_data
                else:
                    tweets = thread_data.get("tweets", [])
            except json.JSONDecodeError:
                # Fallback parsing
                tweets = self._parse_twitter_thread(response.choices[0].message.content)
            
            return {
                "tweets": tweets,
                "thread_length": len(tweets),
                "estimated_impressions": len(tweets) * 1500,  # Rough estimate
                "hashtags": ["#SaaS", "#Design", "#Conversion", "#Framer"]
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Twitter thread generation failed: {str(e)}")
            return self._generate_fallback_twitter(topic)
    
    async def _generate_linkedin_post(self, topic: str, blog_content: Optional[str] = None) -> Dict[str, str]:
        """Generate LinkedIn post"""
        if not self.openai_client:
            return self._generate_fallback_linkedin(topic)
        
        try:
            context = f"Blog content reference: {blog_content[:300]}..." if blog_content else ""
            
            prompt = f"""Create a LinkedIn post about: "{topic}"

{context}

Brand: Craefto - Premium SaaS design templates
Audience: SaaS founders, product managers, marketers

Requirements:
- Professional tone, but engaging
- 1300 characters maximum
- Include 3-5 bullet points with key insights
- Start with hook question or statement
- End with soft CTA
- Include relevant hashtags
- Use line breaks for readability

Return the complete LinkedIn post."""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            
            linkedin_content = response.choices[0].message.content.strip()
            
            return {
                "content": linkedin_content,
                "character_count": len(linkedin_content),
                "estimated_reach": "500-2000 impressions",
                "best_posting_time": "Tuesday-Thursday, 9-10 AM"
            }
            
        except Exception as e:
            logger.warning(f"⚠️ LinkedIn post generation failed: {str(e)}")
            return self._generate_fallback_linkedin(topic)
    
    async def _generate_instagram_post(self, topic: str, blog_content: Optional[str] = None) -> Dict[str, str]:
        """Generate Instagram post"""
        return {
            "caption": f"✨ {topic}\n\nSwipe to see how top SaaS companies are using design to boost conversions →\n\n#SaaS #Design #ConversionOptimization #Framer #Templates",
            "hashtags": ["#SaaS", "#Design", "#ConversionOptimization", "#Framer", "#Templates", "#WebDesign", "#UX"],
            "content_type": "carousel",
            "slide_count": 5,
            "estimated_reach": "200-800 impressions"
        }
    
    def _inject_brand_phrases(self, text: str) -> str:
        """Inject Craefto brand phrases naturally"""
        phrases = self.brand_voice["key_phrases"]
        
        # Simple injection - replace generic phrases with branded ones
        replacements = {
            "great design": "conversion-optimized design",
            "good templates": "premium Framer templates",
            "design process": "craft exceptional design process",
            "faster development": "speed up your design process"
        }
        
        for generic, branded in replacements.items():
            text = text.replace(generic, branded)
        
        return text
    
    def _enhance_saas_focus(self, text: str) -> str:
        """Ensure content maintains SaaS focus"""
        # Add SaaS context where appropriate
        if "conversion" in text.lower() and "saas" not in text.lower():
            text = text.replace("conversion", "SaaS conversion")
        
        if "landing page" in text.lower() and "saas" not in text.lower():
            text = text.replace("landing page", "SaaS landing page")
        
        return text
    
    def _add_product_mentions(self, text: str) -> str:
        """Add natural product mentions"""
        # Add mentions of Framer templates where contextually appropriate
        if "template" in text.lower() and "framer" not in text.lower():
            text = text.replace("template", "Framer template")
        
        return text
    
    def _adjust_tone(self, text: str) -> str:
        """Adjust tone to match Craefto brand"""
        # Ensure professional but accessible tone
        # This is a simplified implementation
        return text
    
    def _style_title(self, title: str) -> str:
        """Apply Craefto styling to titles"""
        # Ensure titles are compelling and brand-aligned
        if not any(word in title.lower() for word in ["saas", "framer", "conversion", "design"]):
            if "design" not in title.lower():
                title = f"{title} for SaaS Success"
        
        return title
    
    def _add_craefto_ctas(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Add Craefto-specific CTAs"""
        ctas = [
            "Ready to boost your SaaS conversions? Explore our premium Framer templates →",
            "Transform your SaaS design with our conversion-optimized templates →",
            "Get started with our award-winning SaaS design templates →",
            "Download our free SaaS design checklist and premium templates →"
        ]
        
        content["cta"] = random.choice(ctas)
        return content
    
    def _get_cache_key(self, content_type: str, topic: str, extra_data: Any = None) -> str:
        """Generate cache key for content"""
        base_string = f"{content_type}_{topic}"
        if extra_data:
            base_string += f"_{str(extra_data)}"
        
        return hashlib.md5(base_string.encode()).hexdigest()
    
    # Fallback methods for when AI APIs are unavailable
    
    def _generate_fallback_blog(self, topic: str) -> Dict[str, Any]:
        """Generate fallback blog content"""
        return {
            "title": f"The Complete Guide to {topic} for SaaS Success",
            "content": f"""# The Complete Guide to {topic} for SaaS Success

## Introduction

In today's competitive SaaS landscape, {topic.lower()} has become crucial for success. This comprehensive guide will show you exactly how to implement effective strategies.

## Why {topic} Matters for SaaS

SaaS companies that focus on {topic.lower()} see significantly better results:
- Higher conversion rates
- Better user engagement  
- Increased customer lifetime value

## Step-by-Step Implementation

### 1. Getting Started
Begin by analyzing your current approach to {topic.lower()}.

### 2. Best Practices
Follow these proven strategies for success.

### 3. Common Mistakes
Avoid these pitfalls that trip up most SaaS companies.

## Conclusion

Ready to implement {topic.lower()} in your SaaS? Get started with our premium Framer templates designed specifically for conversion optimization.
""",
            "word_count": 150,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "fallback_content": True,
                "content_type": "blog"
            }
        }
    
    def _generate_fallback_outline(self, topic: str) -> List[str]:
        """Generate fallback outline"""
        return [
            f"Introduction to {topic}",
            f"Why {topic} matters for SaaS",
            f"Key strategies for {topic}",
            f"Implementation steps",
            f"Common mistakes to avoid",
            f"Best practices and tips",
            "Conclusion and next steps"
        ]
    
    def _generate_fallback_social(self, topic: str) -> Dict[str, Any]:
        """Generate fallback social content"""
        return {
            "twitter": {
                "tweets": [
                    {"text": f"🚀 {topic} is game-changing for SaaS companies. Here's what you need to know: (1/5)", "tweet_number": 1},
                    {"text": f"Most SaaS founders overlook {topic.lower()}, but it can boost conversions by 40%+ (2/5)", "tweet_number": 2},
                    {"text": f"Key insight: {topic.lower()} works best when combined with conversion-optimized design (3/5)", "tweet_number": 3},
                    {"text": f"Pro tip: Use data-driven approaches to optimize your {topic.lower()} strategy (4/5)", "tweet_number": 4},
                    {"text": f"Ready to implement {topic.lower()}? Check out our premium SaaS templates → (5/5)", "tweet_number": 5}
                ],
                "thread_length": 5
            },
            "linkedin": {
                "content": f"""🎯 {topic} is transforming how SaaS companies approach growth.

Here's what I've learned from analyzing 100+ successful SaaS companies:

• Strategy matters more than tactics
• Data-driven decisions win every time  
• Design and functionality must work together
• Speed of implementation is crucial

The companies that master {topic.lower()} see 40%+ better results.

What's your experience with {topic.lower()}? Share in the comments 👇

#SaaS #Growth #Design #ConversionOptimization""",
                "character_count": 400
            }
        }
    
    def _generate_fallback_email(self, topic: str, segment: str) -> Dict[str, Any]:
        """Generate fallback email content"""
        return {
            "subject_lines": [
                f"The {topic} strategy that's working for SaaS",
                f"How to master {topic} (step-by-step guide)",
                f"{topic}: Your competitive advantage"
            ],
            "preview_text": f"Discover how top SaaS companies use {topic.lower()} to boost conversions",
            "html_content": f"""<h1>Master {topic} for Your SaaS</h1>
<p>Hi {{first_name}},</p>
<p>Today I want to share insights about {topic.lower()} that can transform your SaaS growth.</p>
<p>Here's what you'll learn:</p>
<ul>
<li>Why {topic.lower()} matters more than ever</li>
<li>Step-by-step implementation guide</li>
<li>Real examples from successful SaaS companies</li>
</ul>
<p><a href="{{cta_link}}">Get Our Premium Templates →</a></p>
<p>Best regards,<br>The Craefto Team</p>""",
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "fallback_content": True
            }
        }
    
    async def _generate_seo_meta(self, topic: str, content: Dict[str, Any]) -> Dict[str, str]:
        """Generate SEO metadata"""
        return {
            "meta_description": f"Learn how to master {topic} for your SaaS. Complete guide with actionable strategies, examples, and premium templates to boost conversions.",
            "meta_keywords": f"{topic.lower()}, saas, conversion optimization, framer templates, design",
            "og_title": content.get("title", f"Master {topic} for SaaS Success"),
            "og_description": f"Complete guide to {topic.lower()} for SaaS companies. Boost conversions with proven strategies and premium templates."
        }
    
    async def _generate_social_snippets(self, topic: str, content: Dict[str, Any]) -> Dict[str, str]:
        """Generate social media snippets"""
        return {
            "twitter_snippet": f"🚀 New guide: {content.get('title', topic)} - Everything SaaS founders need to know about boosting conversions",
            "linkedin_snippet": f"Just published: {content.get('title', topic)} - A comprehensive guide for SaaS companies looking to optimize their growth strategy",
            "facebook_snippet": f"Master {topic} with our latest guide designed specifically for SaaS companies and growth teams"
        }
    
    async def _generate_email_version(self, topic: str, content: Dict[str, Any]) -> Dict[str, str]:
        """Generate email newsletter version"""
        return {
            "subject": f"Weekly Insight: {topic} for SaaS Success",
            "preview": f"This week's deep dive into {topic.lower()} strategies that work",
            "body": f"Hi there!\n\nThis week I'm diving deep into {topic.lower()} - something every SaaS founder should master.\n\nKey takeaways:\n• Strategy overview\n• Implementation steps\n• Real-world examples\n\nRead the full guide: [Link]\n\nBest,\nThe Craefto Team"
        }
    
    def _estimate_social_engagement(self, topic: str) -> Dict[str, str]:
        """Estimate social media engagement"""
        return {
            "twitter": "50-200 engagements",
            "linkedin": "20-100 engagements", 
            "instagram": "30-150 engagements"
        }
    
    def _estimate_email_performance(self, topic: str, segment: str) -> Dict[str, float]:
        """Estimate email performance"""
        return {
            "open_rate": 0.25,
            "click_rate": 0.05,
            "conversion_rate": 0.02
        }
    
    def _generate_fallback_blog_content(self, topic: str, outline: List[str]) -> Dict[str, Any]:
        """Generate fallback blog content when AI is unavailable"""
        return {
            "title": f"The Complete Guide to {topic} for SaaS Success",
            "content": f"""# The Complete Guide to {topic} for SaaS Success

## Introduction

In today's competitive SaaS landscape, {topic.lower()} has become crucial for success. This comprehensive guide will show you exactly how to implement effective strategies.

## Why {topic} Matters for SaaS

SaaS companies that focus on {topic.lower()} see significantly better results:
- Higher conversion rates
- Better user engagement  
- Increased customer lifetime value

## Step-by-Step Implementation

### 1. Getting Started
Begin by analyzing your current approach to {topic.lower()}.

### 2. Best Practices
Follow these proven strategies for success.

### 3. Common Mistakes
Avoid these pitfalls that trip up most SaaS companies.

## Conclusion

Ready to implement {topic.lower()} in your SaaS? Get started with our premium Framer templates designed specifically for conversion optimization.
"""
        }
    
    def _generate_fallback_twitter(self, topic: str) -> Dict[str, Any]:
        """Generate fallback Twitter content"""
        return {
            "tweets": [
                {"text": f"🚀 {topic} is game-changing for SaaS companies. Here's what you need to know: (1/5)", "tweet_number": 1},
                {"text": f"Most SaaS founders overlook {topic.lower()}, but it can boost conversions by 40%+ (2/5)", "tweet_number": 2},
                {"text": f"Key insight: {topic.lower()} works best when combined with conversion-optimized design (3/5)", "tweet_number": 3},
                {"text": f"Pro tip: Use data-driven approaches to optimize your {topic.lower()} strategy (4/5)", "tweet_number": 4},
                {"text": f"Ready to implement {topic.lower()}? Check out our premium SaaS templates → (5/5)", "tweet_number": 5}
            ],
            "thread_length": 5,
            "hashtags": ["#SaaS", "#Design", "#Conversion", "#Framer"]
        }
    
    def _generate_fallback_linkedin(self, topic: str) -> Dict[str, str]:
        """Generate fallback LinkedIn content"""
        return {
            "content": f"""🎯 {topic} is transforming how SaaS companies approach growth.

Here's what I've learned from analyzing 100+ successful SaaS companies:

• Strategy matters more than tactics
• Data-driven decisions win every time  
• Design and functionality must work together
• Speed of implementation is crucial

The companies that master {topic.lower()} see 40%+ better results.

What's your experience with {topic.lower()}? Share in the comments 👇

#SaaS #Growth #Design #ConversionOptimization""",
            "character_count": 400,
            "estimated_reach": "500-2000 impressions"
        }
    
    async def _generate_subject_lines(self, topic: str, segment: str) -> List[str]:
        """Generate email subject lines"""
        if self.openai_client:
            try:
                prompt = f"""Create 3 compelling email subject lines for a topic about: "{topic}"

Target segment: {segment}
Brand: Craefto (premium SaaS design templates)

Requirements:
- 50 characters or less
- Action-oriented
- Include benefit or curiosity gap
- A/B test variants (different approaches)

Return as JSON array of strings."""

                response = await self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.8
                )
                
                try:
                    subject_lines = json.loads(response.choices[0].message.content)
                    return subject_lines if isinstance(subject_lines, list) else [response.choices[0].message.content]
                except json.JSONDecodeError:
                    return [line.strip().strip('"') for line in response.choices[0].message.content.split('\n') if line.strip()]
                    
            except Exception as e:
                logger.warning(f"⚠️ OpenAI subject line generation failed: {str(e)}")
        
        # Fallback subject lines
        return [
            f"The {topic} strategy that's working for SaaS",
            f"How to master {topic} (step-by-step guide)",
            f"{topic}: Your competitive advantage"
        ]
    
    async def _generate_preview_text(self, topic: str, segment: str) -> str:
        """Generate email preview text"""
        return f"Discover how top SaaS companies use {topic.lower()} to boost conversions and drive growth"
    
    async def _generate_email_body(self, topic: str, segment: str) -> Dict[str, str]:
        """Generate email body content"""
        if self.openai_client:
            try:
                prompt = f"""Write an email body about: "{topic}"

Target: {segment} in SaaS industry
Brand: Craefto (premium design templates)
Length: 200-300 words

Include:
- Personal greeting with {{{{first_name}}}} token
- Value-driven content
- 3 key points
- Clear CTA to templates
- Professional signature

Return HTML version."""

                response = await self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=600,
                    temperature=0.7
                )
                
                html_content = response.choices[0].message.content.strip()
                
                # Convert to plain text (simple version)
                plain_text = re.sub('<[^<]+?>', '', html_content)
                plain_text = re.sub(r'\n\s*\n', '\n\n', plain_text)
                
                return {
                    "html": html_content,
                    "plain_text": plain_text
                }
                
            except Exception as e:
                logger.warning(f"⚠️ OpenAI email body generation failed: {str(e)}")
        
        # Fallback email body
        html_content = f"""<h1>Master {topic} for Your SaaS</h1>
<p>Hi {{{{first_name}}}},</p>
<p>Today I want to share insights about {topic.lower()} that can transform your SaaS growth.</p>
<p>Here's what you'll learn:</p>
<ul>
<li>Why {topic.lower()} matters more than ever</li>
<li>Step-by-step implementation guide</li>
<li>Real examples from successful SaaS companies</li>
</ul>
<p><a href="{{{{cta_link}}}}">Get Our Premium Templates →</a></p>
<p>Best regards,<br>The Craefto Team</p>"""
        
        plain_text = f"""Master {topic} for Your SaaS

Hi {{{{first_name}}}},

Today I want to share insights about {topic.lower()} that can transform your SaaS growth.

Here's what you'll learn:
• Why {topic.lower()} matters more than ever
• Step-by-step implementation guide  
• Real examples from successful SaaS companies

Get Our Premium Templates → {{{{cta_link}}}}

Best regards,
The Craefto Team"""
        
        return {
            "html": html_content,
            "plain_text": plain_text
        }
    
    def _add_personalization(self, email_body: Dict[str, str], segment: str) -> Dict[str, Any]:
        """Add personalization tokens and CTAs"""
        tokens = {
            "first_name": "{{first_name}}",
            "company_name": "{{company_name}}", 
            "cta_link": "{{cta_link}}",
            "unsubscribe_link": "{{unsubscribe_link}}"
        }
        
        ctas = [
            {
                "text": "Get Premium Templates",
                "url": "{{cta_link}}",
                "style": "primary"
            },
            {
                "text": "Download Free Resources", 
                "url": "{{resource_link}}",
                "style": "secondary"
            }
        ]
        
        return {
            "html": email_body.get("html", ""),
            "plain_text": email_body.get("plain_text", ""),
            "tokens": tokens,
            "ctas": ctas
        }
    
    def _parse_twitter_thread(self, content: str) -> List[Dict[str, Any]]:
        """Parse Twitter thread from text response"""
        lines = content.split('\n')
        tweets = []
        
        for i, line in enumerate(lines):
            if line.strip() and (f"({i+1}/" in line or f"{i+1}/" in line):
                tweets.append({
                    "text": line.strip(),
                    "tweet_number": i + 1
                })
                
        return tweets if tweets else [{"text": content[:280], "tweet_number": 1}]

# Utility functions for standalone usage
async def generate_blog_content(topic: str, research_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Standalone function to generate blog content"""
    generator = ContentGenerator()
    return await generator.generate_blog_post(topic, research_data)

async def generate_social_content(topic: str, blog_content: str = None) -> Dict[str, Any]:
    """Standalone function to generate social content"""
    generator = ContentGenerator()
    return await generator.generate_social_posts(topic, blog_content)

async def generate_email_content(topic: str, segment: str = "all") -> Dict[str, Any]:
    """Standalone function to generate email content"""
    generator = ContentGenerator()
    return await generator.generate_email_campaign(topic, segment)
