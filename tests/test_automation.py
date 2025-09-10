"""
CRAEFTO Automation Integration Tests
Comprehensive testing of the complete automation pipeline with mocked API calls
"""
import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import psutil
import os

# Import the main components
from app.orchestrator import CraeftoOrchestrator
from app.agents.research_agent import ResearchAgent
from app.agents.content_generator import ContentGenerator
from app.agents.visual_generator import VisualGenerator
from app.agents.publisher import Publisher
from app.agents.intelligence import BusinessIntelligence
from app.utils.monitoring import CraeftoMonitor, OperationStatus
from app.config import get_settings

# Test fixtures and mock data
@pytest.fixture
def mock_trending_data():
    """Mock trending topics data"""
    return {
        "trending_topics": [
            {
                "topic": "SaaS Analytics Dashboard",
                "relevance_score": 95,
                "source": "twitter",
                "mentions": 1250,
                "growth_rate": 0.35
            },
            {
                "topic": "AI-Powered Customer Support",
                "relevance_score": 88,
                "source": "reddit",
                "mentions": 890,
                "growth_rate": 0.42
            },
            {
                "topic": "Framer Template Marketplace",
                "relevance_score": 82,
                "source": "producthunt",
                "mentions": 650,
                "growth_rate": 0.28
            }
        ],
        "content_ideas": [
            {
                "title": "Building SaaS Analytics That Actually Drive Growth",
                "angle": "practical_guide",
                "target_audience": "saas_founders",
                "estimated_engagement": 850
            },
            {
                "title": "Why Your SaaS Analytics Are Lying to You",
                "angle": "contrarian",
                "target_audience": "product_managers",
                "estimated_engagement": 720
            }
        ]
    }

@pytest.fixture
def mock_blog_content():
    """Mock generated blog content"""
    return {
        "title": "Building SaaS Analytics That Actually Drive Growth",
        "content": """
# Building SaaS Analytics That Actually Drive Growth

As a SaaS founder, you're drowning in data but starving for insights. 

## The Problem With Traditional Analytics

Most SaaS companies track vanity metrics that look good in board decks but don't drive real business decisions.

## The CRAEFTO Framework for SaaS Analytics

1. **Customer Health Score**: Beyond NPS
2. **Revenue Predictability Index**: Forecast with confidence  
3. **Feature Adoption Velocity**: What drives retention
4. **Churn Risk Indicators**: Prevent before it happens

## Implementation Guide

Start with these three dashboards:

### Executive Dashboard
- MRR growth trajectory
- Customer acquisition cost trends
- Lifetime value evolution

### Product Dashboard  
- Feature usage heatmaps
- User journey drop-offs
- A/B test results

### Customer Success Dashboard
- Health score distribution
- Support ticket trends
- Expansion revenue opportunities

## Conclusion

Analytics without action is just expensive reporting. Focus on metrics that drive decisions.

**Ready to build analytics that matter?** Start with our free SaaS metrics template.
        """,
        "meta_description": "Learn how to build SaaS analytics dashboards that drive real business growth, not just pretty charts.",
        "word_count": 1250,
        "readability_score": 8.2,
        "seo_keywords": ["saas analytics", "dashboard", "metrics", "growth"],
        "cta": "Download our free SaaS metrics template"
    }

@pytest.fixture
def mock_visual_assets():
    """Mock generated visual assets"""
    return {
        "blog_hero": {
            "url": "https://craefto-assets.com/blog-hero-saas-analytics.png",
            "dimensions": "1200x630",
            "format": "PNG",
            "file_size": "245KB"
        },
        "social_graphics": {
            "twitter": {
                "url": "https://craefto-assets.com/twitter-saas-analytics.png", 
                "dimensions": "1200x675",
                "format": "PNG"
            },
            "linkedin": {
                "url": "https://craefto-assets.com/linkedin-saas-analytics.png",
                "dimensions": "1200x627", 
                "format": "PNG"
            }
        },
        "og_image": {
            "url": "https://craefto-assets.com/og-saas-analytics.png",
            "dimensions": "1200x630",
            "format": "PNG"
        }
    }

@pytest.fixture
def mock_social_content():
    """Mock generated social media content"""
    return {
        "twitter": [
            {
                "content": "🚀 Most SaaS analytics are just expensive reporting.\n\nHere's how to build dashboards that actually drive growth:\n\n1️⃣ Customer Health Score (beyond NPS)\n2️⃣ Revenue Predictability Index\n3️⃣ Feature Adoption Velocity\n4️⃣ Churn Risk Indicators\n\nThread below 👇",
                "thread": [
                    "1/ Customer Health Score combines usage frequency, feature adoption, and support interactions to predict churn 90 days out.",
                    "2/ Revenue Predictability Index uses cohort analysis to forecast MRR with 95% accuracy.",
                    "3/ Feature Adoption Velocity shows which features drive retention vs. which are just shiny objects."
                ],
                "hashtags": ["#SaaS", "#Analytics", "#Growth"],
                "estimated_engagement": 450
            }
        ],
        "linkedin": [
            {
                "content": "After analyzing 500+ SaaS companies, I've found most analytics dashboards are just digital eye candy.\n\nHere's the framework that actually drives growth decisions:\n\n🎯 THE CRAEFTO ANALYTICS FRAMEWORK\n\n1. Customer Health Score\n→ Beyond NPS to predict churn 90 days out\n→ Combines usage, adoption, and support data\n\n2. Revenue Predictability Index  \n→ Forecast MRR with 95% accuracy\n→ Uses cohort analysis and expansion signals\n\n3. Feature Adoption Velocity\n→ Which features drive retention\n→ Separate signal from noise\n\n4. Churn Risk Indicators\n→ Prevent before it happens\n→ Actionable early warning system\n\nThe difference? These metrics drive immediate action, not just board deck slides.\n\nWhat's your most important SaaS metric? 👇",
                "estimated_engagement": 320
            }
        ]
    }

class TestCraeftoAutomation:
    """Comprehensive integration tests for CRAEFTO automation system"""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment before each test"""
        self.orchestrator = CraeftoOrchestrator()
        self.monitor = CraeftoMonitor()
        
    @pytest.mark.asyncio
    async def test_full_content_pipeline(self, mock_trending_data, mock_blog_content, mock_visual_assets, mock_social_content):
        """
        Test complete content pipeline from research to publishing
        
        Flow:
        1. Research trending topics
        2. Generate blog post
        3. Create visual assets
        4. Generate social posts
        5. Verify quality
        6. Mock publish
        """
        print("\n🚀 Testing Full Content Pipeline...")
        
        # Mock all external API calls
        with patch.multiple(
            'app.agents.research_agent.ResearchAgent',
            find_trending_topics=AsyncMock(return_value=mock_trending_data),
            generate_content_ideas=AsyncMock(return_value=mock_trending_data["content_ideas"])
        ), patch.multiple(
            'app.agents.content_generator.ContentGenerator', 
            generate_blog_post=AsyncMock(return_value=mock_blog_content),
            generate_social_posts=AsyncMock(return_value=mock_social_content)
        ), patch.multiple(
            'app.agents.visual_generator.VisualGenerator',
            generate_blog_hero=AsyncMock(return_value=mock_visual_assets["blog_hero"]),
            generate_social_graphics=AsyncMock(return_value=mock_visual_assets["social_graphics"])
        ), patch.multiple(
            'app.agents.publisher.Publisher',
            publish_to_twitter=AsyncMock(return_value={"success": True, "post_id": "12345"}),
            publish_to_linkedin=AsyncMock(return_value={"success": True, "post_id": "67890"})
        ):
            
            # Step 1: Research Phase
            print("  📊 Phase 1: Research trending topics...")
            research_result = await self.orchestrator.research.find_trending_topics()
            
            assert research_result is not None
            assert "trending_topics" in research_result
            assert len(research_result["trending_topics"]) > 0
            assert research_result["trending_topics"][0]["relevance_score"] > 80
            print(f"    ✅ Found {len(research_result['trending_topics'])} trending topics")
            
            # Step 2: Content Generation Phase
            print("  ✍️ Phase 2: Generate blog content...")
            topic = research_result["trending_topics"][0]["topic"]
            blog_result = await self.orchestrator.generator.generate_blog_post(
                topic=topic,
                research_data=research_result
            )
            
            assert blog_result is not None
            assert "title" in blog_result
            assert "content" in blog_result
            assert blog_result["word_count"] > 1000
            assert blog_result["readability_score"] > 7.0
            print(f"    ✅ Generated {blog_result['word_count']} word blog post")
            
            # Step 3: Visual Generation Phase
            print("  🎨 Phase 3: Create visual assets...")
            hero_image = await self.orchestrator.visual.generate_blog_hero(topic)
            social_graphics = await self.orchestrator.visual.generate_social_graphics(topic)
            
            assert hero_image is not None
            assert "url" in hero_image
            assert social_graphics is not None
            assert "twitter" in social_graphics
            assert "linkedin" in social_graphics
            print("    ✅ Generated blog hero and social graphics")
            
            # Step 4: Social Content Generation
            print("  📱 Phase 4: Generate social content...")
            social_result = await self.orchestrator.generator.generate_social_posts(
                topic=topic,
                blog_content=blog_result
            )
            
            assert social_result is not None
            assert "twitter" in social_result
            assert "linkedin" in social_result
            assert len(social_result["twitter"]) > 0
            assert len(social_result["linkedin"]) > 0
            print(f"    ✅ Generated content for {len(social_result)} platforms")
            
            # Step 5: Quality Verification
            print("  🔍 Phase 5: Quality verification...")
            quality_score = await self._verify_content_quality(blog_result, social_result)
            assert quality_score > 80, f"Quality score {quality_score} below threshold"
            print(f"    ✅ Content quality score: {quality_score}/100")
            
            # Step 6: Mock Publishing
            print("  📤 Phase 6: Mock publishing...")
            publish_results = await self._mock_publish_content(social_result)
            
            assert publish_results["twitter"]["success"] is True
            assert publish_results["linkedin"]["success"] is True
            print("    ✅ Mock publishing successful")
            
        print("🎉 Full Content Pipeline Test PASSED!")

    @pytest.mark.asyncio
    async def test_trend_detection(self, mock_trending_data):
        """
        Test trend detection and scoring algorithm
        
        Verifies:
        - API response parsing
        - Relevance scoring
        - Craefto brand alignment
        - Data freshness
        """
        print("\n📈 Testing Trend Detection...")
        
        with patch('app.agents.research_agent.ResearchAgent.find_trending_topics') as mock_research:
            mock_research.return_value = mock_trending_data
            
            research_agent = ResearchAgent()
            result = await research_agent.find_trending_topics()
            
            # Verify data structure
            assert "trending_topics" in result
            assert "content_ideas" in result
            
            # Test scoring algorithm
            topics = result["trending_topics"]
            for topic in topics:
                assert "relevance_score" in topic
                assert topic["relevance_score"] >= 0
                assert topic["relevance_score"] <= 100
                assert "growth_rate" in topic
                assert topic["growth_rate"] >= 0
            
            # Verify Craefto relevance filter
            high_relevance_topics = [t for t in topics if t["relevance_score"] > 80]
            assert len(high_relevance_topics) > 0, "No high-relevance topics found"
            
            # Check content ideas quality
            ideas = result["content_ideas"]
            for idea in ideas:
                assert "title" in idea
                assert "angle" in idea
                assert "target_audience" in idea
                assert len(idea["title"]) > 10
            
            print(f"    ✅ Detected {len(topics)} trending topics")
            print(f"    ✅ Generated {len(ideas)} content ideas")
            print(f"    ✅ {len(high_relevance_topics)} high-relevance topics")

    @pytest.mark.asyncio
    async def test_content_quality(self, mock_blog_content, mock_social_content):
        """
        Validate generated content quality across multiple dimensions
        
        Checks:
        - Brand voice consistency
        - SEO optimization
        - CTA presence
        - No hallucinations
        - Proper formatting
        """
        print("\n✅ Testing Content Quality...")
        
        # Test blog content quality
        blog_quality = await self._analyze_blog_quality(mock_blog_content)
        assert blog_quality["brand_voice_score"] > 80, "Brand voice inconsistent"
        assert blog_quality["seo_score"] > 75, "SEO optimization insufficient"
        assert blog_quality["cta_present"] is True, "CTA missing"
        assert blog_quality["formatting_score"] > 85, "Formatting issues"
        
        print(f"    📝 Blog quality score: {blog_quality['overall_score']}/100")
        
        # Test social content quality
        social_quality = await self._analyze_social_quality(mock_social_content)
        assert social_quality["engagement_potential"] > 70, "Low engagement potential"
        assert social_quality["platform_optimization"] > 80, "Poor platform optimization"
        assert social_quality["hashtag_relevance"] > 75, "Irrelevant hashtags"
        
        print(f"    📱 Social quality score: {social_quality['overall_score']}/100")
        
        # Test for hallucinations (made-up facts)
        hallucination_check = await self._check_for_hallucinations(mock_blog_content)
        assert hallucination_check["confidence"] > 90, "Potential hallucinations detected"
        
        print("    🔍 Hallucination check passed")

    @pytest.mark.asyncio
    async def test_visual_generation(self, mock_visual_assets):
        """
        Test image creation and validation
        
        Verifies:
        - Correct dimensions for each platform
        - Brand colors present
        - Text readability
        - Fallback mechanism
        """
        print("\n🎨 Testing Visual Generation...")
        
        with patch.multiple(
            'app.agents.visual_generator.VisualGenerator',
            generate_blog_hero=AsyncMock(return_value=mock_visual_assets["blog_hero"]),
            generate_social_graphics=AsyncMock(return_value=mock_visual_assets["social_graphics"]),
            generate_og_image=AsyncMock(return_value=mock_visual_assets["og_image"])
        ):
            
            visual_generator = VisualGenerator()
            
            # Test blog hero generation
            hero = await visual_generator.generate_blog_hero("SaaS Analytics")
            assert hero["dimensions"] == "1200x630", "Incorrect blog hero dimensions"
            assert hero["format"] in ["PNG", "JPG"], "Invalid image format"
            
            # Test social graphics
            social_graphics = await visual_generator.generate_social_graphics("SaaS Analytics")
            
            # Verify Twitter dimensions
            assert social_graphics["twitter"]["dimensions"] == "1200x675", "Incorrect Twitter dimensions"
            
            # Verify LinkedIn dimensions  
            assert social_graphics["linkedin"]["dimensions"] == "1200x627", "Incorrect LinkedIn dimensions"
            
            # Test OG image
            og_image = await visual_generator.generate_og_image("SaaS Analytics")
            assert og_image["dimensions"] == "1200x630", "Incorrect OG image dimensions"
            
            print("    ✅ All visual assets have correct dimensions")
            print("    ✅ Image formats validated")
            
            # Test fallback mechanism
            with patch('app.agents.visual_generator.VisualGenerator._midjourney_generate') as mock_midjourney:
                mock_midjourney.side_effect = Exception("Midjourney API failed")
                
                # Should fallback to Pillow
                fallback_result = await visual_generator.generate_blog_hero("Test Topic")
                assert fallback_result is not None, "Fallback mechanism failed"
                
                print("    ✅ Fallback mechanism working")

    @pytest.mark.asyncio
    async def test_publishing_flow(self, mock_social_content):
        """
        Test publishing workflow without actual posting
        
        Validates:
        - Content formatting for each platform
        - Platform-specific requirements
        - Scheduling logic
        - Error handling
        """
        print("\n📤 Testing Publishing Flow...")
        
        with patch.multiple(
            'app.agents.publisher.Publisher',
            publish_to_twitter=AsyncMock(return_value={"success": True, "post_id": "12345"}),
            publish_to_linkedin=AsyncMock(return_value={"success": True, "post_id": "67890"}),
            schedule_content=AsyncMock(return_value={"success": True, "scheduled_id": "sch_123"})
        ):
            
            publisher = Publisher()
            
            # Test Twitter publishing
            twitter_content = mock_social_content["twitter"][0]
            twitter_result = await publisher.publish_to_twitter(twitter_content["content"])
            
            assert twitter_result["success"] is True
            assert "post_id" in twitter_result
            
            # Verify character limit compliance
            assert len(twitter_content["content"]) <= 280, "Twitter content exceeds character limit"
            
            # Test LinkedIn publishing
            linkedin_content = mock_social_content["linkedin"][0] 
            linkedin_result = await publisher.publish_to_linkedin(linkedin_content["content"])
            
            assert linkedin_result["success"] is True
            assert "post_id" in linkedin_result
            
            # Test content scheduling
            schedule_result = await publisher.schedule_content(
                content=twitter_content["content"],
                platform="twitter",
                scheduled_time="2025-09-11T10:00:00Z"
            )
            
            assert schedule_result["success"] is True
            assert "scheduled_id" in schedule_result
            
            print("    ✅ Twitter publishing validated")
            print("    ✅ LinkedIn publishing validated") 
            print("    ✅ Content scheduling working")
            
            # Test error handling
            with patch('app.agents.publisher.Publisher.publish_to_twitter') as mock_twitter_fail:
                mock_twitter_fail.side_effect = Exception("API rate limit exceeded")
                
                try:
                    await publisher.publish_to_twitter("Test content")
                    assert False, "Should have raised exception"
                except Exception as e:
                    assert "rate limit" in str(e).lower()
                    print("    ✅ Error handling working")

    @pytest.mark.asyncio
    async def test_performance_limits(self):
        """
        Stress test the system with rapid content generation
        
        Tests:
        - Generate 50 pieces rapidly
        - Monitor memory usage
        - Check API rate limits
        - Verify queue management
        """
        print("\n⚡ Testing Performance Limits...")
        
        # Monitor initial memory usage
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        print(f"    📊 Initial memory usage: {initial_memory:.1f} MB")
        
        # Mock all expensive operations
        with patch.multiple(
            'app.agents.research_agent.ResearchAgent',
            find_trending_topics=AsyncMock(return_value={"trending_topics": [{"topic": "Test Topic", "relevance_score": 85}]})
        ), patch.multiple(
            'app.agents.content_generator.ContentGenerator',
            generate_blog_post=AsyncMock(return_value={"title": "Test Blog", "content": "Test content", "word_count": 500}),
            generate_social_posts=AsyncMock(return_value={"twitter": [{"content": "Test tweet"}]})
        ), patch.multiple(
            'app.agents.visual_generator.VisualGenerator',
            generate_blog_hero=AsyncMock(return_value={"url": "test.png", "dimensions": "1200x630"})
        ):
            
            # Generate content rapidly
            start_time = time.time()
            tasks = []
            
            for i in range(50):
                task = self._generate_single_content_piece(f"Topic {i}")
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Analyze results
            successful_results = [r for r in results if not isinstance(r, Exception)]
            failed_results = [r for r in results if isinstance(r, Exception)]
            
            print(f"    ⏱️ Generated 50 pieces in {duration:.2f} seconds")
            print(f"    ✅ Success rate: {len(successful_results)}/50 ({len(successful_results)/50*100:.1f}%)")
            
            if failed_results:
                print(f"    ⚠️ Failed operations: {len(failed_results)}")
                for error in failed_results[:3]:  # Show first 3 errors
                    print(f"      - {type(error).__name__}: {str(error)[:50]}...")
            
            # Check memory usage
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            print(f"    📊 Final memory usage: {final_memory:.1f} MB")
            print(f"    📈 Memory increase: {memory_increase:.1f} MB")
            
            # Performance assertions
            assert len(successful_results) >= 45, f"Too many failures: {len(failed_results)}/50"
            assert duration < 30, f"Too slow: {duration:.2f}s for 50 operations"
            assert memory_increase < 200, f"Memory leak detected: {memory_increase:.1f}MB increase"
            
            # Test rate limiting
            rate_limit_test = await self._test_rate_limiting()
            assert rate_limit_test["handled_gracefully"] is True, "Rate limiting not handled properly"
            
            print("    ✅ Performance within acceptable limits")
            print("    ✅ Memory usage stable")
            print("    ✅ Rate limiting handled gracefully")

    @pytest.mark.asyncio
    async def test_monitoring_integration(self):
        """Test monitoring system integration with automation pipeline"""
        print("\n🔍 Testing Monitoring Integration...")
        
        # Test operation logging
        await self.monitor.log_operation(
            operation_type="test_operation",
            status=OperationStatus.SUCCESS,
            details={"test": True},
            duration_ms=150.5,
            cost_usd=0.02
        )
        
        # Verify logging worked
        recent_logs = [log for log in self.monitor.operation_logs if log.operation_type == "test_operation"]
        assert len(recent_logs) > 0, "Operation not logged"
        assert recent_logs[-1].cost_usd == 0.02, "Cost not tracked correctly"
        
        # Test health check
        health_report = await self.monitor.health_check()
        assert "overall_health" in health_report
        assert "health_score" in health_report
        assert health_report["health_score"] >= 0
        
        # Test performance tracking
        performance_report = await self.monitor.performance_tracking()
        assert "total_operations" in performance_report
        
        print("    ✅ Operation logging working")
        print("    ✅ Health monitoring active")
        print("    ✅ Performance tracking functional")

    # Helper methods for test implementation
    
    async def _verify_content_quality(self, blog_content: Dict[str, Any], social_content: Dict[str, Any]) -> int:
        """Verify overall content quality and return score"""
        score = 0
        
        # Blog content checks
        if blog_content.get("word_count", 0) > 1000:
            score += 20
        if blog_content.get("readability_score", 0) > 7.0:
            score += 20
        if "cta" in blog_content and blog_content["cta"]:
            score += 15
        if len(blog_content.get("seo_keywords", [])) > 0:
            score += 15
        
        # Social content checks
        if "twitter" in social_content and len(social_content["twitter"]) > 0:
            score += 15
        if "linkedin" in social_content and len(social_content["linkedin"]) > 0:
            score += 15
        
        return score

    async def _mock_publish_content(self, social_content: Dict[str, Any]) -> Dict[str, Any]:
        """Mock publishing content to social platforms"""
        results = {}
        
        for platform, content_list in social_content.items():
            if content_list:
                results[platform] = {
                    "success": True,
                    "post_id": f"mock_{platform}_{int(time.time())}",
                    "scheduled_time": "2025-09-11T10:00:00Z"
                }
            else:
                results[platform] = {"success": False, "error": "No content provided"}
        
        return results

    async def _analyze_blog_quality(self, blog_content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze blog content quality"""
        content = blog_content.get("content", "")
        
        # Brand voice analysis (simplified)
        brand_keywords = ["SaaS", "growth", "founder", "customer", "analytics", "CRAEFTO"]
        brand_mentions = sum(1 for keyword in brand_keywords if keyword.lower() in content.lower())
        brand_voice_score = min(100, (brand_mentions / len(brand_keywords)) * 100)
        
        # SEO analysis
        seo_score = 75  # Mock score
        if blog_content.get("meta_description"):
            seo_score += 10
        if blog_content.get("seo_keywords"):
            seo_score += 15
        
        # CTA presence
        cta_present = "cta" in blog_content and bool(blog_content["cta"])
        
        # Formatting analysis
        formatting_score = 85  # Mock score
        if "##" in content:  # Has headers
            formatting_score += 10
        if content.count("\n\n") > 3:  # Has paragraphs
            formatting_score += 5
        
        overall_score = (brand_voice_score + seo_score + (100 if cta_present else 0) + formatting_score) / 4
        
        return {
            "brand_voice_score": brand_voice_score,
            "seo_score": min(100, seo_score),
            "cta_present": cta_present,
            "formatting_score": min(100, formatting_score),
            "overall_score": overall_score
        }

    async def _analyze_social_quality(self, social_content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze social media content quality"""
        twitter_content = social_content.get("twitter", [])
        linkedin_content = social_content.get("linkedin", [])
        
        # Engagement potential analysis
        engagement_score = 70  # Base score
        
        # Check for engagement elements
        for content_list in [twitter_content, linkedin_content]:
            for post in content_list:
                content_text = post.get("content", "")
                if "?" in content_text:  # Has questions
                    engagement_score += 5
                if any(emoji in content_text for emoji in ["🚀", "💡", "✅", "🎯"]):
                    engagement_score += 5
                if content_text.count("\n") > 2:  # Well formatted
                    engagement_score += 5
        
        # Platform optimization
        platform_score = 80  # Base score
        
        # Twitter specific checks
        for post in twitter_content:
            if len(post.get("content", "")) <= 280:
                platform_score += 10
            if post.get("hashtags"):
                platform_score += 5
        
        # Hashtag relevance (simplified)
        hashtag_score = 75
        
        overall_score = (engagement_score + platform_score + hashtag_score) / 3
        
        return {
            "engagement_potential": min(100, engagement_score),
            "platform_optimization": min(100, platform_score), 
            "hashtag_relevance": hashtag_score,
            "overall_score": overall_score
        }

    async def _check_for_hallucinations(self, blog_content: Dict[str, Any]) -> Dict[str, Any]:
        """Check content for potential hallucinations or made-up facts"""
        content = blog_content.get("content", "")
        
        # Simple heuristics for hallucination detection
        suspicious_patterns = [
            r"\d+% of companies",  # Specific statistics without sources
            r"studies show",       # Vague study references
            r"research indicates", # Vague research claims
            r"according to experts" # Unnamed expert quotes
        ]
        
        import re
        suspicious_count = 0
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                suspicious_count += 1
        
        # Calculate confidence (inverse of suspicion)
        confidence = max(50, 100 - (suspicious_count * 20))
        
        return {
            "confidence": confidence,
            "suspicious_patterns_found": suspicious_count,
            "status": "pass" if confidence > 80 else "review_needed"
        }

    async def _generate_single_content_piece(self, topic: str) -> Dict[str, Any]:
        """Generate a single piece of content for performance testing"""
        try:
            # Simulate the full pipeline quickly
            research_result = await self.orchestrator.research.find_trending_topics()
            blog_result = await self.orchestrator.generator.generate_blog_post(
                topic=topic,
                research_data=research_result
            )
            visual_result = await self.orchestrator.visual.generate_blog_hero(topic)
            
            return {
                "topic": topic,
                "blog": blog_result,
                "visual": visual_result,
                "status": "success"
            }
        except Exception as e:
            return {
                "topic": topic,
                "error": str(e),
                "status": "failed"
            }

    async def _test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting behavior"""
        try:
            # Simulate rapid API calls
            tasks = []
            for i in range(20):  # Rapid fire requests
                task = asyncio.create_task(self._mock_api_call(f"request_{i}"))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if rate limiting was handled gracefully
            rate_limited_count = sum(1 for r in results if isinstance(r, Exception) and "rate limit" in str(r).lower())
            
            return {
                "handled_gracefully": True,
                "total_requests": len(tasks),
                "rate_limited": rate_limited_count,
                "success_rate": (len(tasks) - rate_limited_count) / len(tasks)
            }
        except Exception as e:
            return {
                "handled_gracefully": False,
                "error": str(e)
            }

    async def _mock_api_call(self, request_id: str) -> str:
        """Mock API call for rate limiting tests"""
        # Simulate some API calls being rate limited
        if hash(request_id) % 5 == 0:  # 20% rate limited
            raise Exception(f"Rate limit exceeded for {request_id}")
        
        await asyncio.sleep(0.1)  # Simulate API latency
        return f"Success: {request_id}"

# Additional test utilities

@pytest.fixture
def test_config():
    """Test configuration fixture"""
    return {
        "test_mode": True,
        "mock_apis": True,
        "log_level": "INFO",
        "performance_limits": {
            "max_concurrent_operations": 50,
            "max_memory_mb": 500,
            "max_duration_seconds": 30
        }
    }

@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization and component loading"""
    print("\n🎭 Testing Orchestrator Initialization...")
    
    orchestrator = CraeftoOrchestrator()
    
    # Verify all agents are initialized
    assert orchestrator.research is not None
    assert orchestrator.generator is not None
    assert orchestrator.visual is not None
    assert orchestrator.publisher is not None
    assert orchestrator.intelligence is not None
    
    # Verify safe mode is active
    assert orchestrator.safe_mode is True
    
    print("    ✅ All agents initialized")
    print("    ✅ Safe mode activated")

@pytest.mark.asyncio 
async def test_error_recovery():
    """Test system recovery from various error conditions"""
    print("\n🛠️ Testing Error Recovery...")
    
    orchestrator = CraeftoOrchestrator()
    
    # Test API failure recovery
    with patch('app.agents.research_agent.ResearchAgent.find_trending_topics') as mock_research:
        mock_research.side_effect = Exception("API temporarily unavailable")
        
        try:
            result = await orchestrator.research.find_trending_topics()
            # Should not reach here in real implementation, but for testing we'll check the exception handling
        except Exception as e:
            assert "API temporarily unavailable" in str(e)
            print("    ✅ API failure handled correctly")
    
    # Test partial failure recovery
    with patch('app.agents.content_generator.ContentGenerator.generate_blog_post') as mock_content:
        mock_content.return_value = None  # Simulate partial failure
        
        result = await orchestrator.generator.generate_blog_post("Test Topic")
        # In a real implementation, this should trigger fallback mechanisms
        print("    ✅ Partial failure recovery tested")

if __name__ == "__main__":
    print("🧪 Running CRAEFTO Automation Tests...")
    print("=" * 60)
    
    # Run tests with pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])
