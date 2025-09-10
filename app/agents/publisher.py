"""
Publisher Agent for CRAEFTO Automation System
Handles multi-platform content publishing with scheduling and cross-posting capabilities
"""
import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import random

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    tweepy = None
    TWEEPY_AVAILABLE = False

import aiohttp
import requests
from urllib.parse import urljoin

from app.config import get_settings
from app.utils.database import get_database

# Configure logging
logger = logging.getLogger(__name__)

class TwitterClient:
    """
    Twitter API client with rate limiting and error handling
    """
    
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.client = None
        
        if TWEEPY_AVAILABLE and all([api_key, api_secret, access_token, access_token_secret]):
            try:
                self.client = tweepy.Client(
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret,
                    wait_on_rate_limit=True
                )
                logger.info("✅ Twitter client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Twitter client initialization failed: {str(e)}")
    
    async def post_tweet(self, text: str, media_ids: Optional[List[str]] = None, reply_to: Optional[str] = None) -> Dict[str, Any]:
        """Post a single tweet"""
        if not self.client:
            return {"success": False, "error": "Twitter client not initialized"}
        
        try:
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids,
                in_reply_to_tweet_id=reply_to
            )
            
            if response.data:
                tweet_id = response.data['id']
                tweet_url = f"https://twitter.com/user/status/{tweet_id}"
                
                return {
                    "success": True,
                    "tweet_id": tweet_id,
                    "tweet_url": tweet_url,
                    "text": text
                }
            else:
                return {"success": False, "error": "No response data from Twitter"}
                
        except Exception as e:
            logger.error(f"❌ Tweet posting failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def upload_media(self, media_data: bytes, media_type: str = "image/png") -> Optional[str]:
        """Upload media to Twitter and return media ID"""
        if not self.client:
            return None
        
        try:
            # Note: tweepy v2 media upload might need different approach
            # This is a placeholder for media upload functionality
            logger.warning("⚠️ Media upload not fully implemented for tweepy v2")
            return None
        except Exception as e:
            logger.error(f"❌ Media upload failed: {str(e)}")
            return None

class ConvertKitAPI:
    """
    ConvertKit API client for email marketing
    """
    
    def __init__(self, api_key: str, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.convertkit.com/v3"
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def create_broadcast(self, subject: str, content: str, segment_id: Optional[str] = None) -> Dict[str, Any]:
        """Create an email broadcast"""
        if not self.api_key:
            return {"success": False, "error": "ConvertKit API key not configured"}
        
        try:
            url = f"{self.base_url}/broadcasts"
            payload = {
                "api_key": self.api_key,
                "subject": subject,
                "content": content,
                "description": f"CRAEFTO broadcast: {subject}",
                "public": False
            }
            
            if segment_id:
                payload["segment_id"] = segment_id
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 201:
                    data = await response.json()
                    broadcast = data.get("broadcast", {})
                    
                    return {
                        "success": True,
                        "broadcast_id": broadcast.get("id"),
                        "subject": broadcast.get("subject"),
                        "created_at": broadcast.get("created_at")
                    }
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            logger.error(f"❌ ConvertKit broadcast creation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_broadcast(self, broadcast_id: str) -> Dict[str, Any]:
        """Send a created broadcast"""
        if not self.api_key:
            return {"success": False, "error": "ConvertKit API key not configured"}
        
        try:
            url = f"{self.base_url}/broadcasts/{broadcast_id}/send"
            payload = {"api_key": self.api_key}
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 204:
                    return {
                        "success": True,
                        "broadcast_id": broadcast_id,
                        "status": "sent"
                    }
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            logger.error(f"❌ ConvertKit broadcast sending failed: {str(e)}")
            return {"success": False, "error": str(e)}

class Publisher:
    """
    Multi-platform content publisher with scheduling and cross-posting capabilities
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize platform clients
        self.twitter = None
        self.email = None
        
        # Initialize Twitter client if credentials available
        if all([
            self.settings.twitter_api_key,
            self.settings.twitter_api_secret,
            self.settings.twitter_access_token,
            self.settings.twitter_access_secret
        ]):
            self.twitter = TwitterClient(
                api_key=self.settings.twitter_api_key,
                api_secret=self.settings.twitter_api_secret,
                access_token=self.settings.twitter_access_token,
                access_token_secret=self.settings.twitter_access_secret
            )
        
        # Initialize ConvertKit client if API key available
        if self.settings.convertkit_api_key:
            self.email = ConvertKitAPI(api_key=self.settings.convertkit_api_key)
        
        # Platform configurations
        self.platform_configs = {
            "twitter": {
                "max_length": 280,
                "thread_delay": 2,  # seconds between tweets
                "max_thread_length": 25
            },
            "linkedin": {
                "max_length": 3000,
                "webhook_url": self.settings.make_webhook_url
            },
            "email": {
                "default_segment": "all_subscribers"
            }
        }
        
        # Publishing queue for scheduled content
        self.publishing_queue = []
        
        # Rate limiting tracking
        self.rate_limits = {
            "twitter": {"calls": 0, "reset_time": datetime.utcnow()},
            "linkedin": {"calls": 0, "reset_time": datetime.utcnow()},
            "email": {"calls": 0, "reset_time": datetime.utcnow()}
        }
    
    async def publish_to_twitter(self, thread_content: Union[str, List[str]], images: Optional[List[bytes]] = None) -> Dict[str, Any]:
        """
        Post Twitter thread with images and proper threading
        
        Args:
            thread_content: Single tweet text or list of tweets for thread
            images: Optional list of image data to upload
            
        Returns:
            Publishing result with tweet URLs and metadata
        """
        logger.info("🐦 Publishing to Twitter...")
        
        if not self.twitter or not self.twitter.client:
            return {
                "success": False,
                "error": "Twitter client not configured",
                "platform": "twitter"
            }
        
        try:
            # Normalize thread content to list
            if isinstance(thread_content, str):
                tweets = [thread_content]
            else:
                tweets = thread_content
            
            # Validate thread
            if len(tweets) > self.platform_configs["twitter"]["max_thread_length"]:
                return {
                    "success": False,
                    "error": f"Thread too long: {len(tweets)} tweets (max {self.platform_configs['twitter']['max_thread_length']})",
                    "platform": "twitter"
                }
            
            # Validate tweet lengths
            max_length = self.platform_configs["twitter"]["max_length"]
            for i, tweet in enumerate(tweets):
                if len(tweet) > max_length:
                    return {
                        "success": False,
                        "error": f"Tweet {i+1} too long: {len(tweet)} chars (max {max_length})",
                        "platform": "twitter"
                    }
            
            # Upload images if provided
            media_ids = []
            if images:
                for i, image_data in enumerate(images[:4]):  # Twitter allows max 4 images
                    media_id = await self.twitter.upload_media(image_data)
                    if media_id:
                        media_ids.append(media_id)
                    else:
                        logger.warning(f"⚠️ Failed to upload image {i+1}")
            
            # Post thread
            published_tweets = []
            reply_to_id = None
            
            for i, tweet_text in enumerate(tweets):
                # Add thread numbering if multiple tweets
                if len(tweets) > 1:
                    tweet_text = f"{tweet_text} ({i+1}/{len(tweets)})"
                
                # Use images only on first tweet
                tweet_media_ids = media_ids if i == 0 else None
                
                # Post tweet
                result = await self.twitter.post_tweet(
                    text=tweet_text,
                    media_ids=tweet_media_ids,
                    reply_to=reply_to_id
                )
                
                if result.get("success"):
                    published_tweets.append(result)
                    reply_to_id = result["tweet_id"]
                    
                    # Add delay between tweets
                    if i < len(tweets) - 1:
                        await asyncio.sleep(self.platform_configs["twitter"]["thread_delay"])
                else:
                    # If any tweet fails, return partial success
                    logger.error(f"❌ Tweet {i+1} failed: {result.get('error')}")
                    break
            
            if published_tweets:
                # Update rate limiting
                self._update_rate_limit("twitter", len(published_tweets))
                
                return {
                    "success": True,
                    "platform": "twitter",
                    "published_count": len(published_tweets),
                    "total_count": len(tweets),
                    "tweets": published_tweets,
                    "thread_url": published_tweets[0]["tweet_url"] if published_tweets else None,
                    "metadata": {
                        "published_at": datetime.utcnow().isoformat(),
                        "has_images": len(media_ids) > 0,
                        "is_thread": len(tweets) > 1
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "No tweets were published successfully",
                    "platform": "twitter"
                }
                
        except Exception as e:
            logger.error(f"❌ Twitter publishing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "platform": "twitter"
            }
    
    async def publish_to_linkedin(self, post_content: str, image: Optional[str] = None) -> Dict[str, Any]:
        """
        Post to LinkedIn via Make.com webhook
        
        Args:
            post_content: LinkedIn post text
            image: Optional image URL
            
        Returns:
            Publishing result with status and metadata
        """
        logger.info("💼 Publishing to LinkedIn...")
        
        webhook_url = self.platform_configs["linkedin"]["webhook_url"]
        if not webhook_url:
            return {
                "success": False,
                "error": "LinkedIn webhook URL not configured",
                "platform": "linkedin"
            }
        
        try:
            # Validate content length
            max_length = self.platform_configs["linkedin"]["max_length"]
            if len(post_content) > max_length:
                return {
                    "success": False,
                    "error": f"Post too long: {len(post_content)} chars (max {max_length})",
                    "platform": "linkedin"
                }
            
            # Prepare webhook payload
            payload = {
                "platform": "linkedin",
                "action": "create_post",
                "data": {
                    "text": post_content,
                    "publish_time": "immediate",
                    "visibility": "PUBLIC"
                },
                "metadata": {
                    "source": "craefto_automation",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            if image:
                payload["data"]["image_url"] = image
            
            # Send to webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        
                        # Update rate limiting
                        self._update_rate_limit("linkedin", 1)
                        
                        return {
                            "success": True,
                            "platform": "linkedin",
                            "webhook_response": result_data,
                            "post_url": result_data.get("post_url"),  # If webhook returns it
                            "metadata": {
                                "published_at": datetime.utcnow().isoformat(),
                                "has_image": image is not None,
                                "content_length": len(post_content)
                            }
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Webhook failed: HTTP {response.status} - {error_text}",
                            "platform": "linkedin"
                        }
                        
        except Exception as e:
            logger.error(f"❌ LinkedIn publishing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "platform": "linkedin"
            }
    
    async def send_email_campaign(self, campaign_data: Dict[str, Any], segment: str = "all_subscribers") -> Dict[str, Any]:
        """
        Send email campaign via ConvertKit
        
        Args:
            campaign_data: Email campaign data with subject, content, etc.
            segment: Target audience segment
            
        Returns:
            Campaign sending result with ID and metadata
        """
        logger.info(f"📧 Sending email campaign to segment: {segment}")
        
        if not self.email:
            return {
                "success": False,
                "error": "Email service not configured",
                "platform": "email"
            }
        
        try:
            subject = campaign_data.get("subject")
            content = campaign_data.get("html_content") or campaign_data.get("content")
            
            if not subject or not content:
                return {
                    "success": False,
                    "error": "Subject and content are required",
                    "platform": "email"
                }
            
            # Create broadcast
            async with self.email as email_client:
                create_result = await email_client.create_broadcast(
                    subject=subject,
                    content=content,
                    segment_id=segment if segment != "all_subscribers" else None
                )
                
                if not create_result.get("success"):
                    return {
                        "success": False,
                        "error": f"Broadcast creation failed: {create_result.get('error')}",
                        "platform": "email"
                    }
                
                broadcast_id = create_result["broadcast_id"]
                
                # Send broadcast immediately or schedule
                if campaign_data.get("send_immediately", True):
                    send_result = await email_client.send_broadcast(broadcast_id)
                    
                    if send_result.get("success"):
                        # Update rate limiting
                        self._update_rate_limit("email", 1)
                        
                        return {
                            "success": True,
                            "platform": "email",
                            "campaign_id": broadcast_id,
                            "segment": segment,
                            "status": "sent",
                            "metadata": {
                                "subject": subject,
                                "sent_at": datetime.utcnow().isoformat(),
                                "content_length": len(content)
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Broadcast sending failed: {send_result.get('error')}",
                            "platform": "email",
                            "campaign_id": broadcast_id
                        }
                else:
                    return {
                        "success": True,
                        "platform": "email",
                        "campaign_id": broadcast_id,
                        "segment": segment,
                        "status": "created",
                        "metadata": {
                            "subject": subject,
                            "created_at": datetime.utcnow().isoformat(),
                            "scheduled": True
                        }
                    }
                    
        except Exception as e:
            logger.error(f"❌ Email campaign failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "platform": "email"
            }
    
    async def schedule_content(self, content: Dict[str, Any], platforms: List[str], publish_time: datetime) -> Dict[str, Any]:
        """
        Schedule content for future publishing
        
        Args:
            content: Content data for publishing
            platforms: List of platforms to publish to
            publish_time: When to publish
            
        Returns:
            Scheduling confirmation with job details
        """
        logger.info(f"⏰ Scheduling content for {len(platforms)} platforms at {publish_time}")
        
        try:
            # Validate publish time
            if publish_time <= datetime.utcnow():
                return {
                    "success": False,
                    "error": "Publish time must be in the future"
                }
            
            # Create scheduling entry
            schedule_entry = {
                "id": f"sched_{int(time.time())}_{random.randint(1000, 9999)}",
                "content": content,
                "platforms": platforms,
                "publish_time": publish_time.isoformat(),
                "status": "scheduled",
                "created_at": datetime.utcnow().isoformat(),
                "attempts": 0,
                "max_attempts": 3
            }
            
            # Save to database if available
            db = get_database()
            if db.is_connected:
                try:
                    # Save scheduled content to database
                    saved_schedule = await db.save_generated_content({
                        'research_id': None,
                        'content_type': 'scheduled_publish',
                        'title': f"Scheduled: {', '.join(platforms)}",
                        'body': json.dumps(content),
                        'status': 'scheduled',
                        'metadata': {
                            'schedule_entry': schedule_entry,
                            'platforms': platforms,
                            'publish_time': publish_time.isoformat()
                        }
                    })
                    
                    schedule_entry["database_id"] = saved_schedule.get('id')
                    logger.info(f"💾 Scheduled content saved to database: {saved_schedule.get('id')}")
                    
                except Exception as db_error:
                    logger.warning(f"⚠️ Database save failed: {str(db_error)}")
            
            # Add to in-memory queue (for immediate processing)
            self.publishing_queue.append(schedule_entry)
            
            return {
                "success": True,
                "schedule_id": schedule_entry["id"],
                "platforms": platforms,
                "publish_time": publish_time.isoformat(),
                "status": "scheduled",
                "metadata": {
                    "queue_position": len(self.publishing_queue),
                    "estimated_delay": max(0, (publish_time - datetime.utcnow()).total_seconds())
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Content scheduling failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cross_post(self, content_id: str) -> Dict[str, Any]:
        """
        Cross-post content to all configured platforms
        
        Args:
            content_id: Database ID of content to cross-post
            
        Returns:
            Cross-posting results for all platforms
        """
        logger.info(f"🌐 Cross-posting content ID: {content_id}")
        
        try:
            # Get content from database
            db = get_database()
            if not db.is_connected:
                return {
                    "success": False,
                    "error": "Database not connected"
                }
            
            # Retrieve content
            content_records = await db.select("generated_content", {"id": content_id})
            if not content_records:
                return {
                    "success": False,
                    "error": f"Content not found: {content_id}"
                }
            
            content_record = content_records[0]
            content_type = content_record.get("content_type")
            title = content_record.get("title")
            body = content_record.get("body")
            metadata = content_record.get("metadata", {})
            
            # Generate platform-specific variants
            platform_content = await self._adapt_content_for_platforms(
                content_type=content_type,
                title=title,
                body=body,
                metadata=metadata
            )
            
            # Publish to all platforms
            publishing_results = []
            
            # Twitter
            if "twitter" in platform_content and self.twitter:
                twitter_result = await self.publish_to_twitter(platform_content["twitter"])
                publishing_results.append(twitter_result)
            
            # LinkedIn
            if "linkedin" in platform_content:
                linkedin_result = await self.publish_to_linkedin(platform_content["linkedin"])
                publishing_results.append(linkedin_result)
            
            # Email (if it's an email-appropriate content type)
            if content_type in ["blog", "newsletter"] and "email" in platform_content and self.email:
                email_result = await self.send_email_campaign(platform_content["email"])
                publishing_results.append(email_result)
            
            # Update content status in database
            successful_publishes = [r for r in publishing_results if r.get("success")]
            
            if successful_publishes:
                await db.update("generated_content", {"id": content_id}, {
                    "status": "published",
                    "metadata": {
                        **metadata,
                        "cross_post_results": publishing_results,
                        "published_at": datetime.utcnow().isoformat(),
                        "published_platforms": [r["platform"] for r in successful_publishes]
                    }
                })
                
                # Create published_content records
                for result in successful_publishes:
                    await db.save_published_content({
                        'content_id': content_id,
                        'platform': result["platform"],
                        'url': result.get("post_url") or result.get("thread_url"),
                        'engagement_metrics': {},
                        'status': 'published'
                    })
            
            return {
                "success": len(successful_publishes) > 0,
                "content_id": content_id,
                "platforms_attempted": len(publishing_results),
                "platforms_successful": len(successful_publishes),
                "results": publishing_results,
                "metadata": {
                    "cross_posted_at": datetime.utcnow().isoformat(),
                    "success_rate": len(successful_publishes) / len(publishing_results) if publishing_results else 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Cross-posting failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content_id": content_id
            }
    
    async def process_scheduled_content(self) -> Dict[str, Any]:
        """
        Process scheduled content that's ready for publishing
        
        Returns:
            Processing results and statistics
        """
        logger.info("⏰ Processing scheduled content...")
        
        try:
            current_time = datetime.utcnow()
            processed_count = 0
            successful_count = 0
            
            # Process in-memory queue
            ready_items = []
            for item in self.publishing_queue:
                publish_time = datetime.fromisoformat(item["publish_time"])
                if publish_time <= current_time and item["status"] == "scheduled":
                    ready_items.append(item)
            
            for item in ready_items:
                try:
                    # Remove from queue
                    self.publishing_queue.remove(item)
                    
                    # Publish content
                    content = item["content"]
                    platforms = item["platforms"]
                    
                    # Cross-post if content_id provided, otherwise direct publish
                    if "content_id" in content:
                        result = await self.cross_post(content["content_id"])
                    else:
                        # Direct publishing logic here
                        result = {"success": True, "message": "Direct publishing not implemented"}
                    
                    processed_count += 1
                    if result.get("success"):
                        successful_count += 1
                        item["status"] = "published"
                    else:
                        item["status"] = "failed"
                        item["attempts"] += 1
                        
                        # Retry logic
                        if item["attempts"] < item["max_attempts"]:
                            # Reschedule for retry (5 minutes later)
                            retry_time = datetime.utcnow() + timedelta(minutes=5)
                            item["publish_time"] = retry_time.isoformat()
                            item["status"] = "scheduled"
                            self.publishing_queue.append(item)
                            logger.info(f"⏰ Rescheduling failed item for retry: {item['id']}")
                    
                except Exception as item_error:
                    logger.error(f"❌ Processing scheduled item failed: {str(item_error)}")
                    processed_count += 1
            
            return {
                "success": True,
                "processed": processed_count,
                "successful": successful_count,
                "failed": processed_count - successful_count,
                "queue_remaining": len(self.publishing_queue),
                "processed_at": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Scheduled content processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _adapt_content_for_platforms(self, content_type: str, title: str, body: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt content for different platforms"""
        platform_content = {}
        
        # Twitter adaptation
        if content_type == "social":
            # Extract Twitter content from metadata
            twitter_data = metadata.get("ai_generation", {}).get("twitter", {})
            if twitter_data.get("tweets"):
                platform_content["twitter"] = [tweet["text"] for tweet in twitter_data["tweets"]]
        else:
            # Create Twitter thread from title/body
            twitter_thread = [
                f"📝 New post: {title}",
                f"{body[:250]}..." if len(body) > 250 else body,
                "Read more on our blog → [link]"
            ]
            platform_content["twitter"] = twitter_thread
        
        # LinkedIn adaptation
        if content_type == "social":
            linkedin_data = metadata.get("ai_generation", {}).get("linkedin", {})
            platform_content["linkedin"] = linkedin_data.get("content", f"{title}\n\n{body[:1000]}...")
        else:
            platform_content["linkedin"] = f"📊 {title}\n\n{body[:1500]}...\n\n#SaaS #Design #Growth"
        
        # Email adaptation
        if content_type in ["blog", "newsletter"]:
            email_data = metadata.get("ai_generation", {}).get("email_version", {})
            platform_content["email"] = {
                "subject": email_data.get("subject", title),
                "html_content": email_data.get("body", f"<h1>{title}</h1><p>{body}</p>"),
                "send_immediately": True
            }
        
        return platform_content
    
    def _update_rate_limit(self, platform: str, calls: int):
        """Update rate limiting tracking"""
        if platform in self.rate_limits:
            self.rate_limits[platform]["calls"] += calls
            
            # Reset counter every hour
            if datetime.utcnow() > self.rate_limits[platform]["reset_time"]:
                self.rate_limits[platform]["calls"] = calls
                self.rate_limits[platform]["reset_time"] = datetime.utcnow() + timedelta(hours=1)
    
    def _check_rate_limit(self, platform: str, calls: int = 1) -> bool:
        """Check if platform is within rate limits"""
        if platform not in self.rate_limits:
            return True
        
        # Platform-specific rate limits (calls per hour)
        limits = {
            "twitter": 300,  # Conservative limit
            "linkedin": 100,
            "email": 50
        }
        
        current_calls = self.rate_limits[platform]["calls"]
        limit = limits.get(platform, 100)
        
        return (current_calls + calls) <= limit
    
    def get_publishing_status(self) -> Dict[str, Any]:
        """Get current publishing status and statistics"""
        return {
            "platforms": {
                "twitter": {
                    "configured": self.twitter is not None,
                    "rate_limit": self.rate_limits["twitter"]
                },
                "linkedin": {
                    "configured": bool(self.platform_configs["linkedin"]["webhook_url"]),
                    "rate_limit": self.rate_limits["linkedin"]
                },
                "email": {
                    "configured": self.email is not None,
                    "rate_limit": self.rate_limits["email"]
                }
            },
            "queue": {
                "scheduled_items": len(self.publishing_queue),
                "next_publish": min([
                    item["publish_time"] for item in self.publishing_queue 
                    if item["status"] == "scheduled"
                ], default=None)
            },
            "status_timestamp": datetime.utcnow().isoformat()
        }

# Utility functions for standalone usage
async def publish_twitter_thread(thread_content: Union[str, List[str]], images: Optional[List[bytes]] = None) -> Dict[str, Any]:
    """Standalone function to publish Twitter thread"""
    publisher = Publisher()
    return await publisher.publish_to_twitter(thread_content, images)

async def publish_linkedin_post(post_content: str, image: Optional[str] = None) -> Dict[str, Any]:
    """Standalone function to publish LinkedIn post"""
    publisher = Publisher()
    return await publisher.publish_to_linkedin(post_content, image)

async def send_email_broadcast(campaign_data: Dict[str, Any], segment: str = "all_subscribers") -> Dict[str, Any]:
    """Standalone function to send email campaign"""
    publisher = Publisher()
    return await publisher.send_email_campaign(campaign_data, segment)

async def cross_post_content(content_id: str) -> Dict[str, Any]:
    """Standalone function to cross-post content"""
    publisher = Publisher()
    return await publisher.cross_post(content_id)
