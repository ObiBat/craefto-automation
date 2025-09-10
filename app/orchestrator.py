"""
CRAEFTO Orchestrator - Coordinates all agents for complete content workflows
Manages end-to-end content creation, testing, and optimization processes
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json

from app.agents.research_agent import ResearchAgent
from app.agents.content_generator import ContentGenerator
from app.agents.visual_generator import VisualGenerator
from app.agents.publisher import Publisher
from app.agents.intelligence import BusinessIntelligence
from app.config import get_settings
from app.utils.database import get_database

# Configure logging
logger = logging.getLogger(__name__)

class QualityController:
    """Quality assurance and content validation"""
    
    def __init__(self):
        self.settings = get_settings()
        self.brand_voice_keywords = self.settings.get_brand_voice_keywords()
        
    def pre_publish_checklist(self, content_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive pre-publish quality checks
        
        Args:
            content_package: Dictionary containing content for different platforms
            
        Returns:
            Quality assessment with scores and recommendations
        """
        qa_results = {
            "overall_score": 0,
            "platform_scores": {},
            "brand_voice_check": {},
            "factual_accuracy": {},
            "cta_effectiveness": {},
            "recommendations": [],
            "approval_status": "pending_review"
        }
        
        total_score = 0
        platform_count = 0
        
        for platform, content in content_package.items():
            if platform == "image":
                continue  # Skip image content for text analysis
                
            platform_score = self._analyze_content_quality(content, platform)
            qa_results["platform_scores"][platform] = platform_score
            
            # Brand voice analysis
            brand_score = self._check_brand_voice(content)
            qa_results["brand_voice_check"][platform] = brand_score
            
            # CTA effectiveness
            cta_score = self._analyze_cta_effectiveness(content, platform)
            qa_results["cta_effectiveness"][platform] = cta_score
            
            # Calculate platform total
            platform_total = (platform_score + brand_score + cta_score) / 3
            total_score += platform_total
            platform_count += 1
        
        # Calculate overall score
        qa_results["overall_score"] = round(total_score / platform_count if platform_count > 0 else 0, 1)
        
        # Generate recommendations
        qa_results["recommendations"] = self._generate_qa_recommendations(qa_results)
        
        # Determine approval status
        if qa_results["overall_score"] >= 80:
            qa_results["approval_status"] = "approved"
        elif qa_results["overall_score"] >= 60:
            qa_results["approval_status"] = "needs_minor_edits"
        else:
            qa_results["approval_status"] = "needs_major_revision"
        
        return qa_results
    
    def _analyze_content_quality(self, content: Any, platform: str) -> float:
        """Analyze content quality for specific platform"""
        if isinstance(content, dict):
            text = content.get("content", "") or content.get("text", "") or str(content)
        else:
            text = str(content)
        
        score = 70  # Base score
        
        # Length appropriateness
        if platform == "linkedin":
            if 100 <= len(text) <= 1300:
                score += 10
        elif platform == "x" or platform == "twitter":
            if 50 <= len(text) <= 280:
                score += 10
        
        # Engagement elements
        if "?" in text:  # Questions increase engagement
            score += 5
        if any(word in text.lower() for word in ["you", "your", "we", "us"]):  # Personal pronouns
            score += 5
        if text.count("\n") >= 1:  # Good formatting
            score += 5
        
        return min(100, score)
    
    def _check_brand_voice(self, content: Any) -> float:
        """Check alignment with CRAEFTO brand voice"""
        if isinstance(content, dict):
            text = content.get("content", "") or content.get("text", "") or str(content)
        else:
            text = str(content)
        
        text_lower = text.lower()
        score = 50  # Base score
        
        # Check for brand voice keywords
        brand_matches = sum(1 for keyword in self.brand_voice_keywords if keyword.lower() in text_lower)
        score += min(30, brand_matches * 10)  # Up to 30 points for brand alignment
        
        # Check for SaaS relevance
        saas_keywords = ["saas", "software", "product", "growth", "conversion", "user", "customer"]
        saas_matches = sum(1 for keyword in saas_keywords if keyword in text_lower)
        score += min(20, saas_matches * 5)  # Up to 20 points for SaaS relevance
        
        return min(100, score)
    
    def _analyze_cta_effectiveness(self, content: Any, platform: str) -> float:
        """Analyze call-to-action effectiveness"""
        if isinstance(content, dict):
            text = content.get("content", "") or content.get("text", "") or str(content)
        else:
            text = str(content)
        
        text_lower = text.lower()
        score = 40  # Base score
        
        # Check for CTA presence
        cta_indicators = ["link in bio", "dm me", "comment below", "share this", "save this", "visit", "check out", "learn more"]
        if any(indicator in text_lower for indicator in cta_indicators):
            score += 30
        
        # Check for urgency/action words
        action_words = ["now", "today", "limited", "exclusive", "free", "download", "get", "start"]
        action_matches = sum(1 for word in action_words if word in text_lower)
        score += min(30, action_matches * 10)
        
        return min(100, score)
    
    def _generate_qa_recommendations(self, qa_results: Dict[str, Any]) -> List[str]:
        """Generate actionable QA recommendations"""
        recommendations = []
        overall_score = qa_results["overall_score"]
        
        if overall_score < 60:
            recommendations.append("🔴 Major revision needed - content doesn't meet quality standards")
        elif overall_score < 80:
            recommendations.append("🟡 Minor edits needed - good foundation with room for improvement")
        else:
            recommendations.append("🟢 Content approved - meets quality standards")
        
        # Platform-specific recommendations
        for platform, score in qa_results["platform_scores"].items():
            if score < 70:
                recommendations.append(f"📝 {platform.title()}: Improve content structure and engagement")
        
        # Brand voice recommendations
        for platform, score in qa_results["brand_voice_check"].items():
            if score < 70:
                recommendations.append(f"🎯 {platform.title()}: Strengthen brand voice alignment")
        
        # CTA recommendations
        for platform, score in qa_results["cta_effectiveness"].items():
            if score < 70:
                recommendations.append(f"📢 {platform.title()}: Add stronger call-to-action")
        
        return recommendations

class CraeftoOrchestrator:
    """
    Master orchestrator for CRAEFTO content automation
    Coordinates all agents for complete content workflows
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.db = get_database()
        
        # Initialize all agents
        self.research = ResearchAgent()
        self.generator = ContentGenerator()
        self.visual = VisualGenerator()
        self.publisher = Publisher()
        self.intelligence = BusinessIntelligence()
        self.qa = QualityController()
        
        # v1 SAFE MODE: manual-only, no background schedules
        self.safe_mode = True  # tie to Notion properties: Trigger Mode = "Manual (Owner only)", Automation Enabled = False
        
        # GTM focus areas for initial testing
        self.gtm_entry_focus = [
            "Twitter/X fresh start",
            "LinkedIn authority building", 
            "Email list reactivation (small test cohort)",
        ]
        
        # Content workflow state
        self.current_workflow = None
        self.workflow_history = []
        
        logger.info("🎭 CRAEFTO Orchestrator initialized in SAFE MODE")
    
    async def manual_content_sprint(self, topic_hint: str = None) -> Dict[str, Any]:
        """
        Manual single-run workflow optimized for go-to-market testing.
        
        1) Research: pull 5 lightweight insights around the topic_hint
        2) Generate: 1 short-form pillar (LinkedIn post) + 1 X thread (5-7 tweets)
        3) Visuals: 1 OG image (brand-consistent) for LinkedIn
        4) QA: quick checks (voice, factual, CTA)
        5) Publish: RETURN payloads for manual posting (do not auto-post)
        6) Log draft links + capture test goals
        
        Args:
            topic_hint: Optional topic focus for content generation
            
        Returns:
            Complete content package ready for manual publishing
        """
        logger.info(f"🚀 Starting manual content sprint with topic: {topic_hint or 'trending topics'}")
        
        workflow_id = f"sprint_{int(datetime.utcnow().timestamp())}"
        self.current_workflow = {
            "id": workflow_id,
            "type": "manual_content_sprint",
            "started_at": datetime.utcnow().isoformat(),
            "topic_hint": topic_hint,
            "status": "in_progress"
        }
        
        try:
            # Step 1: Research Phase
            logger.info("📊 Phase 1: Research and insights gathering")
            if topic_hint:
                # Use topic hint for focused research
                insights = await self.research.find_trending_topics()
                # Filter insights related to topic hint
                filtered_insights = [
                    insight for insight in insights 
                    if topic_hint.lower() in insight.get("topic", "").lower() 
                    or topic_hint.lower() in insight.get("context", "").lower()
                ]
                picks = filtered_insights[:3] if filtered_insights else insights[:3]
            else:
                # General trending research
                insights = await self.research.find_trending_topics()
                picks = insights[:5]  # Top 5 insights
            
            # Generate content ideas from research
            content_ideas = await self.research.generate_content_ideas(picks)
            selected_idea = content_ideas[0] if content_ideas else {
                "topic": topic_hint or "SaaS Growth Strategies",
                "angle": "Fresh perspective on digital craftsmanship"
            }
            
            # Step 2: Content Generation Phase
            logger.info("✍️ Phase 2: Content generation")
            
            # Generate LinkedIn post (authority building focus)
            linkedin_topic = f"GTM reset — {selected_idea.get('topic', 'fresh point-of-view')}"
            li_post = await self.generator.generate_social_posts(
                topic=linkedin_topic,
                blog_content=None
            )
            
            # Generate X/Twitter thread (fresh start focus)
            x_topic = f"GTM reset — {selected_idea.get('angle', 'fresh point-of-view')}"
            x_thread = await self.generator.generate_social_posts(
                topic=x_topic,
                blog_content=None
            )
            
            # Step 3: Visual Generation Phase
            logger.info("🎨 Phase 3: Visual asset creation")
            
            # Generate OG image for LinkedIn (brand-consistent)
            og_title = selected_idea.get("topic", "Digital craftsmanship for the product-led age")
            og_image = await self.visual.generate_og_image(
                title=og_title,
                subtitle="CRAEFTO • Premium SaaS Templates"
            )
            
            # Step 4: Quality Assurance Phase
            logger.info("🔍 Phase 4: Quality assurance and validation")
            
            content_package = {
                "linkedin": li_post,
                "x": x_thread,
                "image": og_image,
            }
            
            qa_results = self.qa.pre_publish_checklist(content_package)
            
            # Step 5: Package for Manual Publishing
            logger.info("📦 Phase 5: Packaging for manual publish")
            
            # Create manual publish instructions
            publish_instructions = self._create_publish_instructions(content_package, selected_idea)
            
            # Step 6: Log and Track
            workflow_result = {
                "workflow_id": workflow_id,
                "research_insights": picks,
                "selected_idea": selected_idea,
                "drafts": {
                    "linkedin": li_post,
                    "x": x_thread,
                    "og_image": og_image,
                },
                "qa_assessment": qa_results,
                "publish_instructions": publish_instructions,
                "gtm_focus": self.gtm_entry_focus,
                "notes": "Manual publish only. Capture engagement for baseline testing.",
                "test_metrics": [
                    "LinkedIn: saves, comments, profile clicks",
                    "X/Twitter: retweets, replies, profile clicks", 
                    "Overall: click-through rate to template library"
                ],
                "created_at": datetime.utcnow().isoformat(),
                "status": "ready_for_manual_publish"
            }
            
            # Save to database if available
            if self.db.is_connected:
                try:
                    await self.db.save_research_data({
                        "topic": selected_idea.get("topic", "Manual Content Sprint"),
                        "relevance_score": 85,
                        "source": "orchestrator",
                        "data": {
                            "workflow_id": workflow_id,
                            "insights": picks,
                            "content_package": content_package,
                            "qa_results": qa_results
                        }
                    })
                    logger.info(f"💾 Workflow {workflow_id} saved to database")
                except Exception as e:
                    logger.warning(f"⚠️ Database save failed: {str(e)}")
            
            # Update workflow history
            self.current_workflow["status"] = "completed"
            self.current_workflow["completed_at"] = datetime.utcnow().isoformat()
            self.workflow_history.append(self.current_workflow.copy())
            
            logger.info(f"✅ Manual content sprint completed: {workflow_id}")
            return workflow_result
            
        except Exception as e:
            logger.error(f"❌ Manual content sprint failed: {str(e)}")
            if self.current_workflow:
                self.current_workflow["status"] = "failed"
                self.current_workflow["error"] = str(e)
                self.current_workflow["failed_at"] = datetime.utcnow().isoformat()
            
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "fallback_notes": "Use manual content creation as backup"
            }
    
    async def gtm_test_cycle(self, hypothesis: str) -> Dict[str, Any]:
        """
        Run a short GTM test cycle:
        - Define Hypothesis (message + audience + CTA)
        - Produce 2 variants per platform (LinkedIn, X)
        - Publish manually within a 48-hour window
        - Track: saves, comments, profile clicks, CTR to template library
        - Debrief and store learnings
        
        Args:
            hypothesis: The marketing hypothesis to test
            
        Returns:
            Complete GTM test cycle plan with variants and tracking setup
        """
        logger.info(f"🧪 Starting GTM test cycle for hypothesis: {hypothesis}")
        
        test_id = f"gtm_test_{int(datetime.utcnow().timestamp())}"
        
        try:
            variants = []
            
            # Generate variants for each platform
            for platform in ["linkedin", "x"]:
                logger.info(f"📝 Generating variants for {platform}")
                
                # Variant A: Direct hypothesis approach
                v1 = await self.generator.generate_social_posts(
                    topic=hypothesis,
                    blog_content=None
                )
                
                # Variant B: Contrarian/alternative angle
                contrarian_topic = f"{hypothesis} — contrarian angle"
                v2 = await self.generator.generate_social_posts(
                    topic=contrarian_topic,
                    blog_content=None
                )
                
                # QA check for both variants
                v1_qa = self.qa.pre_publish_checklist({platform: v1})
                v2_qa = self.qa.pre_publish_checklist({platform: v2})
                
                variants.append({
                    "platform": platform,
                    "variant_a": {
                        "content": v1,
                        "approach": "direct",
                        "qa_score": v1_qa["overall_score"]
                    },
                    "variant_b": {
                        "content": v2,
                        "approach": "contrarian",
                        "qa_score": v2_qa["overall_score"]
                    }
                })
            
            # Create test plan
            test_plan = {
                "test_id": test_id,
                "hypothesis": hypothesis,
                "test_type": "A/B content variants",
                "platforms": ["linkedin", "x"],
                "variants": variants,
                "execution_plan": {
                    "timeline": "Manual publish 2x variants per platform within 48h",
                    "schedule": "Stagger posts by 24h for each platform",
                    "tracking_window": "7 days post-publish"
                },
                "success_metrics": [
                    "saves",
                    "comments", 
                    "profile_clicks",
                    "link_ctr",
                    "engagement_rate",
                    "reach"
                ],
                "tracking_setup": self._create_tracking_setup(test_id),
                "debrief_template": self.debrief_template(),
                "created_at": datetime.utcnow().isoformat(),
                "status": "ready_to_execute"
            }
            
            # Save test cycle to database if available
            if self.db.is_connected:
                try:
                    await self.db.save_research_data({
                        "topic": f"GTM Test: {hypothesis}",
                        "relevance_score": 90,
                        "source": "gtm_test_cycle",
                        "data": test_plan
                    })
                    logger.info(f"💾 GTM test cycle {test_id} saved to database")
                except Exception as e:
                    logger.warning(f"⚠️ Database save failed: {str(e)}")
            
            logger.info(f"✅ GTM test cycle created: {test_id}")
            return test_plan
            
        except Exception as e:
            logger.error(f"❌ GTM test cycle failed: {str(e)}")
            return {
                "test_id": test_id,
                "status": "failed",
                "error": str(e),
                "fallback_plan": "Create variants manually using hypothesis as guide"
            }
    
    async def full_content_pipeline(self, topic: str = None, platforms: List[str] = None) -> Dict[str, Any]:
        """
        Complete end-to-end content pipeline (SAFE MODE: returns for manual review)
        
        1) Research trending topics
        2) Generate multi-format content
        3) Create visual assets
        4) Quality assurance
        5) Package for manual publishing (no auto-publish in safe mode)
        
        Args:
            topic: Optional specific topic focus
            platforms: List of target platforms
            
        Returns:
            Complete content package for manual review and publishing
        """
        logger.info(f"🔄 Starting full content pipeline - Topic: {topic}, Platforms: {platforms}")
        
        pipeline_id = f"pipeline_{int(datetime.utcnow().timestamp())}"
        platforms = platforms or ["linkedin", "twitter", "email"]
        
        try:
            # Phase 1: Research
            logger.info("📊 Pipeline Phase 1: Research")
            if topic:
                insights = await self.research.find_trending_topics()
                content_ideas = await self.research.generate_content_ideas(insights[:3])
                selected_topic = topic
            else:
                insights = await self.research.find_trending_topics()
                content_ideas = await self.research.generate_content_ideas(insights[:5])
                selected_topic = content_ideas[0].get("topic") if content_ideas else "SaaS Growth Strategies"
            
            # Phase 2: Content Generation
            logger.info("✍️ Pipeline Phase 2: Content Generation")
            content_assets = {}
            
            if "blog" in platforms:
                blog_post = await self.generator.generate_blog_post(selected_topic, insights[:3])
                content_assets["blog"] = blog_post
            
            if any(platform in platforms for platform in ["linkedin", "twitter", "facebook"]):
                social_posts = await self.generator.generate_social_posts(selected_topic)
                content_assets["social"] = social_posts
            
            if "email" in platforms:
                email_campaign = await self.generator.generate_email_campaign(selected_topic)
                content_assets["email"] = email_campaign
            
            # Phase 3: Visual Generation
            logger.info("🎨 Pipeline Phase 3: Visual Generation")
            visual_assets = {}
            
            # Generate OG image
            og_image = await self.visual.generate_og_image(selected_topic, "CRAEFTO Templates")
            visual_assets["og_image"] = og_image
            
            # Generate social graphics if needed
            if "social" in content_assets:
                social_graphic = await self.visual.generate_social_graphics(selected_topic, "linkedin")
                visual_assets["social_graphic"] = social_graphic
            
            # Phase 4: Quality Assurance
            logger.info("🔍 Pipeline Phase 4: Quality Assurance")
            qa_results = self.qa.pre_publish_checklist({**content_assets, **visual_assets})
            
            # Phase 5: Intelligence Analysis
            logger.info("🧠 Pipeline Phase 5: Intelligence Analysis")
            virality_prediction = self.intelligence.predict_virality({
                "title": selected_topic,
                "body": str(content_assets.get("blog", {}).get("content", "")),
                "content_type": "mixed"
            })
            
            # Package complete pipeline result
            pipeline_result = {
                "pipeline_id": pipeline_id,
                "topic": selected_topic,
                "platforms": platforms,
                "research_insights": insights[:5],
                "content_ideas": content_ideas[:3],
                "content_assets": content_assets,
                "visual_assets": visual_assets,
                "qa_assessment": qa_results,
                "virality_prediction": virality_prediction,
                "intelligence_insights": await self._get_quick_insights(),
                "safe_mode_instructions": self._create_safe_mode_instructions(content_assets, visual_assets),
                "created_at": datetime.utcnow().isoformat(),
                "status": "ready_for_review"
            }
            
            logger.info(f"✅ Full content pipeline completed: {pipeline_id}")
            return pipeline_result
            
        except Exception as e:
            logger.error(f"❌ Full content pipeline failed: {str(e)}")
            return {
                "pipeline_id": pipeline_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def performance_optimization_cycle(self) -> Dict[str, Any]:
        """
        Run a complete performance analysis and optimization cycle
        
        Returns:
            Comprehensive optimization recommendations and action plan
        """
        logger.info("📈 Starting performance optimization cycle")
        
        try:
            # Get comprehensive performance analysis
            performance_analysis = await self.intelligence.analyze_performance()
            
            # Get strategy optimization recommendations
            strategy_optimization = await self.intelligence.optimize_content_strategy()
            
            # Get competitor insights
            competitor_analysis = await self.intelligence.competitor_tracking()
            
            # Generate actionable optimization plan
            optimization_plan = {
                "cycle_id": f"opt_{int(datetime.utcnow().timestamp())}",
                "performance_analysis": performance_analysis,
                "strategy_optimization": strategy_optimization,
                "competitor_insights": competitor_analysis,
                "priority_actions": self._prioritize_optimization_actions(
                    performance_analysis, strategy_optimization, competitor_analysis
                ),
                "implementation_timeline": self._create_implementation_timeline(),
                "success_metrics": self._define_success_metrics(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info("✅ Performance optimization cycle completed")
            return optimization_plan
            
        except Exception as e:
            logger.error(f"❌ Performance optimization cycle failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def debrief_template(self) -> Dict[str, Any]:
        """
        Template for post-campaign debriefing and learning capture
        
        Returns:
            Structured debrief template
        """
        return {
            "campaign_overview": {
                "hypothesis": "",
                "execution_date": "",
                "platforms_used": [],
                "content_variants": 0
            },
            "quantitative_results": {
                "reach": 0,
                "impressions": 0,
                "engagement_rate": 0.0,
                "click_through_rate": 0.0,
                "conversion_rate": 0.0,
                "cost_per_result": 0.0
            },
            "qualitative_insights": {
                "what_worked": [],
                "what_failed": [],
                "audience_signals": [],
                "unexpected_outcomes": []
            },
            "content_performance": {
                "message_clarity": 0,  # 1-10 scale
                "visual_impact": 0,    # 1-10 scale
                "cta_effectiveness": 0, # 1-10 scale
                "brand_alignment": 0   # 1-10 scale
            },
            "learnings_and_actions": {
                "key_learnings": [],
                "next_experiments": [],
                "process_improvements": [],
                "content_adjustments": []
            },
            "roi_analysis": {
                "time_invested": 0,  # hours
                "direct_results": "",
                "indirect_benefits": "",
                "overall_roi_rating": 0  # 1-10 scale
            }
        }
    
    # Helper methods
    
    def _create_publish_instructions(self, content_package: Dict[str, Any], selected_idea: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed manual publishing instructions"""
        return {
            "linkedin_instructions": {
                "timing": "Tuesday or Wednesday, 10 AM - 2 PM EST",
                "content": content_package.get("linkedin"),
                "hashtags": "#SaaS #ProductDesign #Growth #Framer #CRAEFTO",
                "image": content_package.get("image"),
                "engagement_strategy": "Respond to comments within first 2 hours"
            },
            "twitter_instructions": {
                "timing": "Tuesday or Wednesday, 2 PM - 4 PM EST", 
                "content": content_package.get("x"),
                "thread_strategy": "Pin first tweet, engage with replies",
                "hashtags": "#SaaS #BuildInPublic #ProductDesign",
                "engagement_strategy": "Retweet with comments, reply to mentions"
            },
            "tracking_requirements": {
                "metrics_to_capture": ["saves", "comments", "profile_clicks", "link_clicks"],
                "tracking_period": "7 days",
                "reporting_format": "Add to debrief template"
            }
        }
    
    def _create_tracking_setup(self, test_id: str) -> Dict[str, Any]:
        """Create tracking setup for GTM tests"""
        return {
            "test_id": test_id,
            "tracking_urls": {
                "linkedin_variant_a": f"https://craefto.com?utm_source=linkedin&utm_campaign={test_id}&utm_content=variant_a",
                "linkedin_variant_b": f"https://craefto.com?utm_source=linkedin&utm_campaign={test_id}&utm_content=variant_b",
                "twitter_variant_a": f"https://craefto.com?utm_source=twitter&utm_campaign={test_id}&utm_content=variant_a",
                "twitter_variant_b": f"https://craefto.com?utm_source=twitter&utm_campaign={test_id}&utm_content=variant_b"
            },
            "analytics_setup": {
                "google_analytics": "Track custom events for each variant",
                "platform_analytics": "Native analytics for each platform",
                "manual_tracking": "Spreadsheet backup for all metrics"
            },
            "reporting_schedule": {
                "daily_check": "First 3 days",
                "weekly_summary": "Day 7",
                "final_analysis": "Day 14"
            }
        }
    
    def _create_safe_mode_instructions(self, content_assets: Dict[str, Any], visual_assets: Dict[str, Any]) -> Dict[str, Any]:
        """Create safe mode publishing instructions"""
        return {
            "safe_mode_notice": "🔒 SAFE MODE ACTIVE - Manual review and publishing required",
            "review_checklist": [
                "✅ Content aligns with brand voice",
                "✅ Facts and claims are accurate", 
                "✅ CTAs are appropriate and functional",
                "✅ Visual assets are brand-consistent",
                "✅ Platform formatting is optimized"
            ],
            "publishing_workflow": [
                "1. Review all content and assets",
                "2. Make any necessary edits",
                "3. Schedule posts manually on each platform",
                "4. Monitor engagement for first 2 hours",
                "5. Log results in tracking sheet"
            ],
            "approval_required": True,
            "auto_publish_disabled": True
        }
    
    async def _get_quick_insights(self) -> Dict[str, Any]:
        """Get quick intelligence insights"""
        try:
            performance_data = await self.intelligence.analyze_performance()
            return {
                "content_health_score": performance_data.get("content_health_score", 0),
                "top_performing_topics": list(performance_data.get("topic_performance", {}).get("topic_rankings", {}).keys())[:3],
                "optimal_posting_times": performance_data.get("optimal_timing", {}).get("best_hours", [])[:2]
            }
        except Exception:
            return {"status": "insights_unavailable"}
    
    def _prioritize_optimization_actions(self, performance: Dict[str, Any], strategy: Dict[str, Any], competitor: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize optimization actions based on analysis"""
        actions = []
        
        # High priority actions from strategy optimization
        if "strategy_optimization" in strategy:
            focus_topics = strategy["strategy_optimization"].get("focus_topics", [])
            if focus_topics:
                actions.append({
                    "priority": "High",
                    "action": f"Focus on top-performing topic: {focus_topics[0]}",
                    "impact": "15-20% engagement increase",
                    "effort": "Low"
                })
        
        # Medium priority actions from competitor analysis
        content_gaps = competitor.get("content_gaps", [])
        if content_gaps:
            actions.append({
                "priority": "Medium", 
                "action": f"Address content gap: {content_gaps[0].get('topic', 'New opportunity')}",
                "impact": "10-15% reach improvement",
                "effort": "Medium"
            })
        
        # Low priority actions from performance analysis
        health_score = performance.get("content_health_score", 0)
        if health_score < 80:
            actions.append({
                "priority": "Low",
                "action": "Improve overall content quality and consistency",
                "impact": "5-10% performance improvement",
                "effort": "High"
            })
        
        return actions
    
    def _create_implementation_timeline(self) -> Dict[str, List[str]]:
        """Create implementation timeline for optimizations"""
        return {
            "week_1": [
                "Implement high-priority topic focus",
                "Adjust posting schedule based on optimal timing",
                "Create content calendar for next 2 weeks"
            ],
            "week_2": [
                "Address top content gap opportunity", 
                "A/B test new content formats",
                "Monitor performance improvements"
            ],
            "week_3": [
                "Analyze results from weeks 1-2",
                "Refine strategy based on performance",
                "Plan next optimization cycle"
            ]
        }
    
    def _define_success_metrics(self) -> Dict[str, Any]:
        """Define success metrics for optimization cycle"""
        return {
            "engagement_improvement": "15% increase in average engagement rate",
            "reach_expansion": "20% increase in content reach", 
            "conversion_boost": "10% improvement in click-through rate",
            "content_quality": "Content health score above 85",
            "consistency": "95% adherence to posting schedule"
        }


# Utility functions for standalone usage
async def run_content_sprint(topic: str = None) -> Dict[str, Any]:
    """Standalone function to run a content sprint"""
    orchestrator = CraeftoOrchestrator()
    return await orchestrator.manual_content_sprint(topic)

async def run_gtm_test(hypothesis: str) -> Dict[str, Any]:
    """Standalone function to run a GTM test cycle"""
    orchestrator = CraeftoOrchestrator()
    return await orchestrator.gtm_test_cycle(hypothesis)

async def run_full_pipeline(topic: str = None, platforms: List[str] = None) -> Dict[str, Any]:
    """Standalone function to run full content pipeline"""
    orchestrator = CraeftoOrchestrator()
    return await orchestrator.full_content_pipeline(topic, platforms)

async def run_optimization_cycle() -> Dict[str, Any]:
    """Standalone function to run optimization cycle"""
    orchestrator = CraeftoOrchestrator()
    return await orchestrator.performance_optimization_cycle()
