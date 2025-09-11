"""
Visual Generator Agent for CRAEFTO Automation System
Creates branded visual content using Replicate (image models) and Pillow fallbacks
"""
import asyncio
import logging
import os
import json
import hashlib
import io
import base64
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import random

try:
    from PIL import Image, ImageDraw, ImageFont
    from PIL import ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = ImageDraw = ImageFont = ImageFilter = ImageEnhance = None

import aiohttp
import requests

from app.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

class ReplicateClient:
    """
    Minimal Replicate client for image generation via HTTPS
    """
    def __init__(self, api_token: Optional[str], model: str, version: Optional[str] = None):
        self.api_token = api_token
        self.model = model
        self.version = version
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout for AI generation
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def imagine(self, prompt: str, width: int = 1024, height: int = 1024, **params) -> Dict[str, Any]:
        if not self.api_token:
            logger.warning("⚠️ Replicate API token not configured")
            return {"success": False, "error": "No Replicate token configured"}

        try:
            headers = {"Authorization": f"Token {self.api_token}", "Content-Type": "application/json"}
            body = {
                "input": {
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    **params,
                }
            }
            logger.info(f"🎨 Submitting Replicate request: {prompt[:50]}...")
            url = f"https://api.replicate.com/v1/models/{self.model}/predictions"
            async with self.session.post(url, headers=headers, json=body) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return {"success": True, "id": data.get("id"), "status": data.get("status")}
                else:
                    txt = await resp.text()
                    logger.error(f"❌ Replicate request failed: {resp.status} - {txt}")
                    return {"success": False, "error": f"HTTP {resp.status}: {txt}"}
        except Exception as e:
            logger.error(f"❌ Replicate client error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_result(self, prediction_id: str, timeout: int = 180) -> Dict[str, Any]:
        if not self.api_token:
            return {"success": False, "error": "No Replicate token configured"}

        headers = {"Authorization": f"Token {self.api_token}"}
        start_time = datetime.utcnow()
        poll_interval = 4

        status_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
        while (datetime.utcnow() - start_time).seconds < timeout:
            try:
                async with self.session.get(status_url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        st = data.get("status")
                        if st == "succeeded":
                            output = data.get("output") or []
                            images = output if isinstance(output, list) else [output]
                            return {"success": True, "images": images}
                        if st in ("failed", "canceled"):
                            return {"success": False, "error": st}
                        await asyncio.sleep(poll_interval)
                    else:
                        await asyncio.sleep(poll_interval)
            except Exception:
                await asyncio.sleep(poll_interval)
        return {"success": False, "error": "Generation timeout"}

class VisualGenerator:
    """
    AI-powered visual content generator using Midjourney and Pillow fallbacks
    Creates branded visual content for blogs, social media, and marketing
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.replicate = ReplicateClient(
            api_token=self.settings.replicate_api_token,
            model=self.settings.replicate_model,
            version=self.settings.replicate_model_version or None,
        )
        
        # Visual cache for optimization
        self.visual_cache = {}
        self.cache_duration = timedelta(hours=48)  # Longer cache for visuals
        
        # Craefto brand visual identity
        self.brand_colors = {
            "near_black": "#010101",
            "deep_charcoal": "#151615", 
            "dark_gray": "#333433",
            "muted_dark_gray_green": "#535955",
            "desaturated_green_gray": "#69736c",
            "light_gray": "#ededed"
        }
        
        self.brand_fonts = {
            "primary": "Space Mono",
            "logo": "Source Serif 4 Bold",
            "headings": "Inter Bold",
            "body": "Inter"
        }
        
        self.visual_style = {
            "aesthetic": "minimal, modern, premium SaaS design",
            "color_scheme": "black and white with subtle gray-green accents",
            "elements": "clean geometric shapes, film grain texture",
            "typography": "space mono, source serif, modern sans-serif",
            "inspiration": "brutalist design, swiss typography, calligraphy touches"
        }
        
        # Platform specifications
        self.platform_specs = {
            "twitter": {"width": 1200, "height": 675, "format": "PNG"},
            "linkedin": {"width": 1200, "height": 627, "format": "PNG"},
            "instagram": {"width": 1080, "height": 1080, "format": "PNG"},
            "facebook": {"width": 1200, "height": 630, "format": "PNG"},
            "og_image": {"width": 1200, "height": 630, "format": "PNG"},
            "blog_hero": {"width": 1024, "height": 1024, "format": "PNG"},
            "email_banner": {"width": 600, "height": 200, "format": "PNG"}
        }
    
    async def generate_blog_hero(self, title: str, style: str = "minimal SaaS") -> Dict[str, Any]:
        """
        Generate hero image using Replicate with Pillow fallback
        
        Args:
            title: Blog post title
            style: Visual style preference
            
        Returns:
            Generated image data with URLs and metadata
        """
        logger.info(f"🖼️ Generating blog hero for: {title}")
        
        try:
            # Check cache first
            cache_key = self._get_cache_key("blog_hero", title, style)
            if cache_key in self.visual_cache:
                cached_visual = self.visual_cache[cache_key]
                if datetime.utcnow() - cached_visual['timestamp'] < self.cache_duration:
                    logger.info("📋 Using cached blog hero")
                    return cached_visual['content']
            
            # Create prompt
            prompt = self._create_blog_hero_prompt(title, style)
            
            # Try Replicate generation
            async with self.replicate as rep:
                generation_result = await rep.imagine(
                    prompt,
                    width=self.platform_specs["blog_hero"]["width"],
                    height=self.platform_specs["blog_hero"]["height"],
                )
                
                if generation_result.get("success"):
                    # Wait for completion
                    final_result = await rep.get_result(generation_result["id"])
                    
                    if final_result.get("success") and final_result.get("images"):
                        hero_data = {
                            "success": True,
                            "source": "replicate",
                            "images": final_result["images"],
                            "primary_url": final_result["images"][0],
                            "alt_text": f"Hero image for {title}",
                            "dimensions": self.platform_specs["blog_hero"],
                            "prompt": prompt,
                            "generation_time": final_result.get("generation_time"),
                            "metadata": {
                                "title": title,
                                "style": style,
                                "generated_at": datetime.utcnow().isoformat(),
                                "ai_generated": True
                            }
                        }
                        
                        # Cache the result
                        self.visual_cache[cache_key] = {
                            "content": hero_data,
                            "timestamp": datetime.utcnow()
                        }
                        
                        logger.info(f"✅ Blog hero generated via Replicate")
                        return hero_data
            
            # Fallback to Pillow if Replicate fails
            logger.info("🔄 Falling back to Pillow for blog hero")
            return await self._create_pillow_blog_hero(title, style)
            
        except Exception as e:
            logger.error(f"❌ Blog hero generation failed: {str(e)}")
            return await self._create_pillow_blog_hero(title, style)
    
    async def generate_social_graphics(self, text: str, platform: str) -> Dict[str, Any]:
        """
        Create platform-specific social media graphics
        
        Args:
            text: Text content for the graphic
            platform: Target platform (twitter, linkedin, instagram, facebook)
            
        Returns:
            Generated social graphic with platform optimization
        """
        logger.info(f"📱 Generating {platform} graphic for: {text[:30]}...")
        
        try:
            # Check cache
            cache_key = self._get_cache_key("social", text, platform)
            if cache_key in self.visual_cache:
                cached_visual = self.visual_cache[cache_key]
                if datetime.utcnow() - cached_visual['timestamp'] < self.cache_duration:
                    logger.info("📋 Using cached social graphic")
                    return cached_visual['content']
            
            # Get platform specifications
            specs = self.platform_specs.get(platform, self.platform_specs["twitter"])
            
            # Try Replicate for background
            background_result = None
            try:
                async with self.replicate as rep:
                    bg_prompt = self._create_social_background_prompt(platform)
                    generation_result = await rep.imagine(
                        bg_prompt,
                        width=specs['width'],
                        height=specs['height'],
                    )
                    if generation_result.get("success"):
                        background_result = await rep.get_result(generation_result["id"], timeout=120)
            except Exception as e:
                logger.warning(f"⚠️ Replicate background generation failed: {str(e)}")
            
            # Create final graphic with Pillow (with or without AI background)
            graphic_data = await self._create_social_graphic_pillow(
                text, 
                platform, 
                specs,
                background_url=background_result.get("images", [None])[0] if background_result and background_result.get("success") else None
            )
            
            # Cache the result
            self.visual_cache[cache_key] = {
                "content": graphic_data,
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"✅ {platform} graphic generated")
            return graphic_data
            
        except Exception as e:
            logger.error(f"❌ Social graphic generation failed: {str(e)}")
            return await self._create_fallback_social_graphic(text, platform)
    
    async def generate_og_image(self, title: str, subtitle: str = "") -> Dict[str, Any]:
        """
        Create Open Graph image for social sharing
        
        Args:
            title: Main title text
            subtitle: Optional subtitle text
            
        Returns:
            Generated OG image optimized for social sharing
        """
        logger.info(f"🌐 Generating OG image for: {title}")
        
        try:
            # Check cache
            cache_key = self._get_cache_key("og_image", title, subtitle)
            if cache_key in self.visual_cache:
                cached_visual = self.visual_cache[cache_key]
                if datetime.utcnow() - cached_visual['timestamp'] < self.cache_duration:
                    logger.info("📋 Using cached OG image")
                    return cached_visual['content']
            
            # Create OG image with Pillow for deterministic results
            og_data = await self._create_og_image_pillow(title, subtitle)
            
            # Cache the result
            self.visual_cache[cache_key] = {
                "content": og_data,
                "timestamp": datetime.utcnow()
            }
            
            logger.info("✅ OG image generated")
            return og_data
            
        except Exception as e:
            logger.error(f"❌ OG image generation failed: {str(e)}")
            return await self._create_fallback_og_image(title, subtitle)
    
    def create_email_banner(self, campaign_type: str = "newsletter") -> Dict[str, Any]:
        """
        Generate email header banner
        
        Args:
            campaign_type: Type of email campaign
            
        Returns:
            Generated email banner with CTA design
        """
        logger.info(f"📧 Creating email banner for: {campaign_type}")
        
        try:
            if not PIL_AVAILABLE:
                return self._create_fallback_email_banner(campaign_type)
            
            specs = self.platform_specs["email_banner"]
            
            # Create banner with Pillow
            img = Image.new('RGB', (specs["width"], specs["height"]), self.brand_colors["near_black"])
            draw = ImageDraw.Draw(img)
            
            # Add gradient background
            self._add_gradient_background(img, draw, specs)
            
            # Add campaign-specific content
            if campaign_type == "newsletter":
                main_text = "CRAEFTO WEEKLY"
                sub_text = "Premium SaaS Design Insights"
            elif campaign_type == "product":
                main_text = "NEW TEMPLATES"
                sub_text = "Conversion-Optimized Designs"
            else:
                main_text = "CRAEFTO"
                sub_text = "Premium SaaS Templates"
            
            # Add text
            try:
                # Try to load brand fonts, fallback to default
                title_font = ImageFont.truetype("arial.ttf", 28) if os.name == 'nt' else ImageFont.load_default()
                sub_font = ImageFont.truetype("arial.ttf", 16) if os.name == 'nt' else ImageFont.load_default()
            except:
                title_font = ImageFont.load_default()
                sub_font = ImageFont.load_default()
            
            # Center text
            title_bbox = draw.textbbox((0, 0), main_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (specs["width"] - title_width) // 2
            
            sub_bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
            sub_width = sub_bbox[2] - sub_bbox[0]
            sub_x = (specs["width"] - sub_width) // 2
            
            # Draw text
            draw.text((title_x, 50), main_text, font=title_font, fill=self.brand_colors["light_gray"])
            draw.text((sub_x, 90), sub_text, font=sub_font, fill=self.brand_colors["desaturated_green_gray"])
            
            # Add Craefto logo symbol
            draw.text((specs["width"] - 50, 20), "æ", font=title_font, fill=self.brand_colors["desaturated_green_gray"])
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "success": True,
                "source": "pillow",
                "image_base64": img_base64,
                "image_url": f"data:image/png;base64,{img_base64}",
                "dimensions": specs,
                "campaign_type": campaign_type,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "deterministic": True
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Email banner creation failed: {str(e)}")
            return self._create_fallback_email_banner(campaign_type)
    
    # Private helper methods
    
    def _create_blog_hero_prompt(self, title: str, style: str) -> str:
        """Create optimized prompt for blog hero"""
        # Extract key concepts from title
        key_concepts = self._extract_key_concepts(title)
        
        base_prompt = f"abstract representation of {key_concepts}, {style}"
        
        # Add Craefto style modifiers
        style_modifiers = [
            "minimal modern SaaS design",
            "black and white with subtle gray-green accents",
            "clean geometric shapes",
            "premium web design aesthetic",
            "film grain texture",
            "swiss typography inspiration",
            "professional business illustration"
        ]
        
        technical_modifiers = [
            "high quality",
            "clean composition",
            "negative space",
            "modern minimalism",
            "corporate design"
        ]
        
        full_prompt = f"{base_prompt}, {', '.join(style_modifiers[:3])}, {', '.join(technical_modifiers[:2])}"
        
        return full_prompt
    
    def _create_social_background_prompt(self, platform: str) -> str:
        """Create prompt for social media background"""
        prompts = {
            "twitter": "abstract minimal background, geometric shapes, twitter blue accent, modern tech aesthetic",
            "linkedin": "professional abstract background, business-focused, clean lines, corporate blue tones",
            "instagram": "creative abstract background, visual appeal, modern design, instagram-ready",
            "facebook": "engaging abstract background, social media optimized, clean modern design"
        }
        
        base = prompts.get(platform, prompts["twitter"])
        
        return f"{base}, {self.visual_style['aesthetic']}, {self.visual_style['color_scheme']}, film grain texture"
    
    async def _create_pillow_blog_hero(self, title: str, style: str) -> Dict[str, Any]:
        """Create blog hero using Pillow as fallback"""
        if not PIL_AVAILABLE:
            return self._create_fallback_blog_hero(title, style)
        
        try:
            specs = self.platform_specs["blog_hero"]
            
            # Create base image
            img = Image.new('RGB', (specs["width"], specs["height"]), self.brand_colors["near_black"])
            draw = ImageDraw.Draw(img)
            
            # Add gradient background
            self._add_gradient_background(img, draw, specs)
            
            # Add geometric shapes
            self._add_geometric_shapes(draw, specs)
            
            # Add title text
            self._add_hero_text(draw, title, specs)
            
            # Add film grain effect
            self._add_film_grain(img)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "success": True,
                "source": "pillow_fallback",
                "image_base64": img_base64,
                "image_url": f"data:image/png;base64,{img_base64}",
                "dimensions": specs,
                "alt_text": f"Hero image for {title}",
                "metadata": {
                    "title": title,
                    "style": style,
                    "generated_at": datetime.utcnow().isoformat(),
                    "fallback": True
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Pillow blog hero creation failed: {str(e)}")
            return self._create_fallback_blog_hero(title, style)
    
    async def _create_social_graphic_pillow(self, text: str, platform: str, specs: Dict[str, Any], background_url: Optional[str] = None) -> Dict[str, Any]:
        """Create social graphic using Pillow with optional AI background"""
        if not PIL_AVAILABLE:
            return await self._create_fallback_social_graphic(text, platform)
        
        try:
            # Create base image
            if background_url:
                # Download and use AI background
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(background_url) as response:
                            if response.status == 200:
                                bg_data = await response.read()
                                bg_img = Image.open(io.BytesIO(bg_data))
                                img = bg_img.resize((specs["width"], specs["height"]))
                                # Add overlay for text readability
                                overlay = Image.new('RGBA', (specs["width"], specs["height"]), (*self._hex_to_rgb(self.brand_colors["near_black"]), 128))
                                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                            else:
                                img = Image.new('RGB', (specs["width"], specs["height"]), self.brand_colors["near_black"])
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load AI background: {str(e)}")
                    img = Image.new('RGB', (specs["width"], specs["height"]), self.brand_colors["near_black"])
            else:
                img = Image.new('RGB', (specs["width"], specs["height"]), self.brand_colors["near_black"])
                draw = ImageDraw.Draw(img)
                self._add_gradient_background(img, draw, specs)
            
            draw = ImageDraw.Draw(img)
            
            # Add platform-specific content
            self._add_social_content(draw, text, platform, specs)
            
            # Add branding
            self._add_social_branding(draw, specs)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format=specs["format"])
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "success": True,
                "source": "pillow" + ("_with_ai_bg" if background_url else ""),
                "platform": platform,
                "image_base64": img_base64,
                "image_url": f"data:image/{specs['format'].lower()};base64,{img_base64}",
                "dimensions": specs,
                "alt_text": f"{platform.title()} graphic: {text[:50]}...",
                "metadata": {
                    "text": text,
                    "platform": platform,
                    "generated_at": datetime.utcnow().isoformat(),
                    "ai_background": background_url is not None
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Pillow social graphic creation failed: {str(e)}")
            return await self._create_fallback_social_graphic(text, platform)
    
    async def _create_og_image_pillow(self, title: str, subtitle: str) -> Dict[str, Any]:
        """Create OG image using Pillow"""
        if not PIL_AVAILABLE:
            return await self._create_fallback_og_image(title, subtitle)
        
        try:
            specs = self.platform_specs["og_image"]
            
            # Create base image with gradient
            img = Image.new('RGB', (specs["width"], specs["height"]), self.brand_colors["near_black"])
            draw = ImageDraw.Draw(img)
            
            # Add gradient background
            self._add_gradient_background(img, draw, specs)
            
            # Add geometric elements
            self._add_og_geometric_elements(draw, specs)
            
            # Add text content
            self._add_og_text(draw, title, subtitle, specs)
            
            # Add Craefto branding
            self._add_og_branding(draw, specs)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "success": True,
                "source": "pillow",
                "image_base64": img_base64,
                "image_url": f"data:image/png;base64,{img_base64}",
                "dimensions": specs,
                "alt_text": title,
                "metadata": {
                    "title": title,
                    "subtitle": subtitle,
                    "generated_at": datetime.utcnow().isoformat(),
                    "optimized_for": "social_sharing"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ OG image creation failed: {str(e)}")
            return await self._create_fallback_og_image(title, subtitle)
    
    def _add_gradient_background(self, img: Image.Image, draw: ImageDraw.Draw, specs: Dict[str, Any]):
        """Add subtle gradient background"""
        try:
            # Create vertical gradient from near_black to deep_charcoal
            for y in range(specs["height"]):
                # Calculate gradient position (0.0 to 1.0)
                position = y / specs["height"]
                
                # Interpolate between colors
                start_color = self._hex_to_rgb(self.brand_colors["near_black"])
                end_color = self._hex_to_rgb(self.brand_colors["deep_charcoal"])
                
                r = int(start_color[0] + (end_color[0] - start_color[0]) * position)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * position)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * position)
                
                draw.line([(0, y), (specs["width"], y)], fill=(r, g, b))
        except Exception as e:
            logger.debug(f"Gradient background failed: {str(e)}")
    
    def _add_geometric_shapes(self, draw: ImageDraw.Draw, specs: Dict[str, Any]):
        """Add subtle geometric shapes"""
        try:
            # Add some geometric elements
            accent_color = self.brand_colors["desaturated_green_gray"]
            
            # Circle
            draw.ellipse([specs["width"]-150, 50, specs["width"]-50, 150], outline=accent_color, width=2)
            
            # Rectangle
            draw.rectangle([50, specs["height"]-100, 200, specs["height"]-50], outline=accent_color, width=1)
            
        except Exception as e:
            logger.debug(f"Geometric shapes failed: {str(e)}")
    
    def _add_hero_text(self, draw: ImageDraw.Draw, title: str, specs: Dict[str, Any]):
        """Add title text to hero image"""
        try:
            # Load fonts or use default
            try:
                title_font = ImageFont.truetype("arial.ttf", 48) if os.name == 'nt' else ImageFont.load_default()
            except:
                title_font = ImageFont.load_default()
            
            # Wrap title if too long
            wrapped_title = self._wrap_text(title, 40)
            
            # Calculate position
            text_bbox = draw.multiline_textbbox((0, 0), wrapped_title, font=title_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (specs["width"] - text_width) // 2
            y = (specs["height"] - text_height) // 2
            
            # Draw text
            draw.multiline_text((x, y), wrapped_title, font=title_font, fill=self.brand_colors["light_gray"], align="center")
            
        except Exception as e:
            logger.debug(f"Hero text failed: {str(e)}")
    
    def _add_film_grain(self, img: Image.Image):
        """Add subtle film grain texture"""
        try:
            # Add noise filter for film grain effect
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.1)
            
            # Add slight blur and sharpen for texture
            img = img.filter(ImageFilter.SMOOTH_MORE)
            img = img.filter(ImageFilter.SHARPEN)
            
        except Exception as e:
            logger.debug(f"Film grain effect failed: {str(e)}")
    
    def _add_social_content(self, draw: ImageDraw.Draw, text: str, platform: str, specs: Dict[str, Any]):
        """Add platform-specific content"""
        try:
            # Load fonts
            try:
                title_font = ImageFont.truetype("arial.ttf", 36) if os.name == 'nt' else ImageFont.load_default()
                sub_font = ImageFont.truetype("arial.ttf", 20) if os.name == 'nt' else ImageFont.load_default()
            except:
                title_font = ImageFont.load_default()
                sub_font = ImageFont.load_default()
            
            # Wrap text
            wrapped_text = self._wrap_text(text, 30)
            
            # Position text
            text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=title_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = 80
            y = (specs["height"] - text_height) // 2
            
            # Draw main text
            draw.multiline_text((x, y), wrapped_text, font=title_font, fill=self.brand_colors["light_gray"])
            
            # Add platform-specific elements
            if platform == "twitter":
                draw.text((x, y + text_height + 20), "#SaaS #Design #Framer", font=sub_font, fill=self.brand_colors["desaturated_green_gray"])
            elif platform == "linkedin":
                draw.text((x, y + text_height + 20), "Professional insights for SaaS growth", font=sub_font, fill=self.brand_colors["desaturated_green_gray"])
                
        except Exception as e:
            logger.debug(f"Social content failed: {str(e)}")
    
    def _add_social_branding(self, draw: ImageDraw.Draw, specs: Dict[str, Any]):
        """Add Craefto branding to social graphics"""
        try:
            # Add logo symbol
            try:
                logo_font = ImageFont.truetype("arial.ttf", 32) if os.name == 'nt' else ImageFont.load_default()
            except:
                logo_font = ImageFont.load_default()
            
            draw.text((specs["width"]-80, specs["height"]-60), "æ", font=logo_font, fill=self.brand_colors["desaturated_green_gray"])
            draw.text((specs["width"]-200, specs["height"]-40), "CRAEFTO", font=logo_font, fill=self.brand_colors["muted_dark_gray_green"])
            
        except Exception as e:
            logger.debug(f"Social branding failed: {str(e)}")
    
    def _add_og_geometric_elements(self, draw: ImageDraw.Draw, specs: Dict[str, Any]):
        """Add geometric elements for OG image"""
        try:
            accent_color = self.brand_colors["desaturated_green_gray"]
            
            # Add corner elements
            draw.rectangle([0, 0, 100, 5], fill=accent_color)
            draw.rectangle([specs["width"]-100, specs["height"]-5, specs["width"], specs["height"]], fill=accent_color)
            
            # Add side line
            draw.rectangle([10, 100, 15, specs["height"]-100], fill=accent_color)
            
        except Exception as e:
            logger.debug(f"OG geometric elements failed: {str(e)}")
    
    def _add_og_text(self, draw: ImageDraw.Draw, title: str, subtitle: str, specs: Dict[str, Any]):
        """Add text content to OG image"""
        try:
            # Load fonts
            try:
                title_font = ImageFont.truetype("arial.ttf", 42) if os.name == 'nt' else ImageFont.load_default()
                sub_font = ImageFont.truetype("arial.ttf", 24) if os.name == 'nt' else ImageFont.load_default()
            except:
                title_font = ImageFont.load_default()
                sub_font = ImageFont.load_default()
            
            # Wrap title
            wrapped_title = self._wrap_text(title, 35)
            
            # Position title
            title_bbox = draw.multiline_textbbox((0, 0), wrapped_title, font=title_font)
            title_height = title_bbox[3] - title_bbox[1]
            
            title_y = 150
            draw.multiline_text((100, title_y), wrapped_title, font=title_font, fill=self.brand_colors["light_gray"], align="left")
            
            # Add subtitle if provided
            if subtitle:
                wrapped_subtitle = self._wrap_text(subtitle, 50)
                subtitle_y = title_y + title_height + 30
                draw.multiline_text((100, subtitle_y), wrapped_subtitle, font=sub_font, fill=self.brand_colors["desaturated_green_gray"], align="left")
                
        except Exception as e:
            logger.debug(f"OG text failed: {str(e)}")
    
    def _add_og_branding(self, draw: ImageDraw.Draw, specs: Dict[str, Any]):
        """Add Craefto branding to OG image"""
        try:
            # Add logo and brand name
            try:
                brand_font = ImageFont.truetype("arial.ttf", 28) if os.name == 'nt' else ImageFont.load_default()
            except:
                brand_font = ImageFont.load_default()
            
            # Bottom right branding
            draw.text((specs["width"]-150, specs["height"]-60), "æ CRAEFTO", font=brand_font, fill=self.brand_colors["desaturated_green_gray"])
            
        except Exception as e:
            logger.debug(f"OG branding failed: {str(e)}")
    
    def _extract_key_concepts(self, title: str) -> str:
        """Extract key concepts from title for AI prompts"""
        # Simple keyword extraction
        words = title.lower().split()
        key_words = [w for w in words if len(w) > 3 and w not in ['the', 'and', 'for', 'with', 'your', 'how', 'why', 'what']]
        return ' '.join(key_words[:3])
    
    def _wrap_text(self, text: str, max_width: int) -> str:
        """Wrap text to fit within specified width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            if len(' '.join(current_line + [word])) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)  # Word is longer than max_width
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _get_cache_key(self, visual_type: str, content: str, extra: str = "") -> str:
        """Generate cache key for visual content"""
        base_string = f"{visual_type}_{content}_{extra}"
        return hashlib.md5(base_string.encode()).hexdigest()
    
    # Fallback methods
    
    def _create_fallback_blog_hero(self, title: str, style: str) -> Dict[str, Any]:
        """Create simple fallback blog hero"""
        return {
            "success": True,
            "source": "fallback",
            "image_url": "data:image/svg+xml;base64," + base64.b64encode(
                f'''<svg width="1200" height="600" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100%" height="100%" fill="#010101"/>
                    <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="36" fill="#ededed" text-anchor="middle" dominant-baseline="middle">{title}</text>
                    <text x="95%" y="95%" font-family="Arial, sans-serif" font-size="24" fill="#69736c" text-anchor="end">æ CRAEFTO</text>
                </svg>'''.encode()
            ).decode(),
            "dimensions": self.platform_specs["blog_hero"],
            "metadata": {"fallback": True, "generated_at": datetime.utcnow().isoformat()}
        }
    
    async def _create_fallback_social_graphic(self, text: str, platform: str) -> Dict[str, Any]:
        """Create simple fallback social graphic"""
        specs = self.platform_specs.get(platform, self.platform_specs["twitter"])
        
        return {
            "success": True,
            "source": "fallback",
            "platform": platform,
            "image_url": "data:image/svg+xml;base64," + base64.b64encode(
                f'''<svg width="{specs['width']}" height="{specs['height']}" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100%" height="100%" fill="#010101"/>
                    <text x="10%" y="50%" font-family="Arial, sans-serif" font-size="28" fill="#ededed" dominant-baseline="middle">{text[:50]}...</text>
                    <text x="90%" y="90%" font-family="Arial, sans-serif" font-size="20" fill="#69736c" text-anchor="end">æ CRAEFTO</text>
                </svg>'''.encode()
            ).decode(),
            "dimensions": specs,
            "metadata": {"fallback": True, "generated_at": datetime.utcnow().isoformat()}
        }
    
    async def _create_fallback_og_image(self, title: str, subtitle: str) -> Dict[str, Any]:
        """Create simple fallback OG image"""
        return {
            "success": True,
            "source": "fallback",
            "image_url": "data:image/svg+xml;base64," + base64.b64encode(
                f'''<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100%" height="100%" fill="#010101"/>
                    <text x="10%" y="40%" font-family="Arial, sans-serif" font-size="32" fill="#ededed" dominant-baseline="middle">{title}</text>
                    <text x="10%" y="60%" font-family="Arial, sans-serif" font-size="20" fill="#69736c" dominant-baseline="middle">{subtitle}</text>
                    <text x="90%" y="90%" font-family="Arial, sans-serif" font-size="24" fill="#69736c" text-anchor="end">æ CRAEFTO</text>
                </svg>'''.encode()
            ).decode(),
            "dimensions": self.platform_specs["og_image"],
            "metadata": {"fallback": True, "generated_at": datetime.utcnow().isoformat()}
        }
    
    def _create_fallback_email_banner(self, campaign_type: str) -> Dict[str, Any]:
        """Create simple fallback email banner"""
        return {
            "success": True,
            "source": "fallback",
            "image_url": "data:image/svg+xml;base64," + base64.b64encode(
                f'''<svg width="600" height="200" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100%" height="100%" fill="#010101"/>
                    <text x="50%" y="40%" font-family="Arial, sans-serif" font-size="24" fill="#ededed" text-anchor="middle">CRAEFTO</text>
                    <text x="50%" y="60%" font-family="Arial, sans-serif" font-size="16" fill="#69736c" text-anchor="middle">Premium SaaS Templates</text>
                    <text x="90%" y="20%" font-family="Arial, sans-serif" font-size="20" fill="#69736c" text-anchor="end">æ</text>
                </svg>'''.encode()
            ).decode(),
            "dimensions": self.platform_specs["email_banner"],
            "metadata": {"fallback": True, "generated_at": datetime.utcnow().isoformat()}
        }

# Utility functions for standalone usage
async def generate_blog_hero_image(title: str, style: str = "minimal SaaS") -> Dict[str, Any]:
    """Standalone function to generate blog hero image"""
    generator = VisualGenerator()
    return await generator.generate_blog_hero(title, style)

async def generate_social_graphic(text: str, platform: str) -> Dict[str, Any]:
    """Standalone function to generate social graphic"""
    generator = VisualGenerator()
    return await generator.generate_social_graphics(text, platform)

async def generate_og_image(title: str, subtitle: str = "") -> Dict[str, Any]:
    """Standalone function to generate OG image"""
    generator = VisualGenerator()
    return await generator.generate_og_image(title, subtitle)

def create_email_banner(campaign_type: str = "newsletter") -> Dict[str, Any]:
    """Standalone function to create email banner"""
    generator = VisualGenerator()
    return generator.create_email_banner(campaign_type)
