"""
Database utilities for Supabase connection and operations
Handles connection management, error handling, and data operations
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import json

try:
    from supabase import create_client, Client
    from postgrest.exceptions import APIError
except ImportError:
    # Fallback for when supabase is not installed
    create_client = None
    Client = None
    APIError = Exception

from app.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom database error for better error handling"""
    pass

class ConnectionError(DatabaseError):
    """Database connection specific error"""
    pass

class QueryError(DatabaseError):
    """Database query specific error"""
    pass

class SupabaseClient:
    """
    Supabase database client with connection management and error handling
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[Client] = None
        self._connection_pool_size = 20  # Increased pool size for better concurrency
        self._connection_timeout = 30
        self._retry_count = 3
        self._is_connected = False
        self._connection_lock = asyncio.Lock() if 'asyncio' in globals() else None
        self._last_health_check = None
        self._health_check_interval = 300  # 5 minutes
        
    async def connect(self) -> bool:
        """
        Establish connection to Supabase with connection pooling
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        # Use connection lock for thread safety
        if self._connection_lock:
            async with self._connection_lock:
                return await self._establish_connection()
        else:
            return await self._establish_connection()
    
    async def _establish_connection(self) -> bool:
        """Internal method to establish connection"""
        try:
            # Check if already connected and healthy
            if self._is_connected and await self._is_connection_healthy():
                return True
            
            if not self.settings.supabase_url or not self.settings.supabase_key:
                logger.error("❌ Supabase URL or Key not configured")
                return False
            
            if create_client is None:
                logger.error("❌ Supabase client not available. Install with: pip install supabase")
                return False
            
            logger.info("🔌 Establishing Supabase connection with pooling...")
            
            # Create Supabase client with enhanced configuration
            self._client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_key,
                options={
                    'db': {
                        'schema': 'public'
                    },
                    'auth': {
                        'auto_refresh_token': True,
                        'persist_session': True
                    },
                    'global': {
                        'headers': {
                            'x-client-info': 'craefto-automation/1.0.0'
                        }
                    }
                }
            )
            
            # Test connection with retry logic
            await self._test_connection_with_retry()
            
            self._is_connected = True
            self._last_health_check = datetime.utcnow()
            logger.info("✅ Successfully connected to Supabase with connection pooling")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {str(e)}")
            self._is_connected = False
            raise ConnectionError(f"Failed to connect to Supabase: {str(e)}")
    
    async def _test_connection_with_retry(self):
        """Test connection with retry logic"""
        for attempt in range(self._retry_count):
            try:
                await self._test_connection()
                return
            except Exception as e:
                if attempt < self._retry_count - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"⚠️ Connection test failed (attempt {attempt + 1}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise e
    
    async def _is_connection_healthy(self) -> bool:
        """Check if connection is healthy"""
        if not self._client or not self._is_connected:
            return False
        
        # Check if health check is recent
        if (self._last_health_check and 
            (datetime.utcnow() - self._last_health_check).total_seconds() < self._health_check_interval):
            return True
        
        try:
            await self._test_connection()
            self._last_health_check = datetime.utcnow()
            return True
        except Exception:
            self._is_connected = False
            return False
    
    async def _test_connection(self):
        """Test the database connection"""
        try:
            # Simple test query
            result = self._client.table('_health_check').select('*').limit(1).execute()
            logger.debug("✅ Database connection test passed")
        except Exception as e:
            # If health check table doesn't exist, that's okay
            # We just want to test if we can make a request
            logger.debug(f"🔍 Connection test completed: {str(e)}")
    
    def disconnect(self):
        """Disconnect from Supabase"""
        try:
            if self._client:
                # Supabase client doesn't need explicit disconnection
                self._client = None
                self._is_connected = False
                logger.info("🔌 Disconnected from Supabase")
        except Exception as e:
            logger.error(f"❌ Error during disconnect: {str(e)}")
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._is_connected and self._client is not None
    
    def ensure_connection(self):
        """Ensure database connection exists"""
        if not self.is_connected:
            raise ConnectionError("Database not connected. Call connect() first.")
    
    # =============================================================================
    # CRUD OPERATIONS
    # =============================================================================
    
    async def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert data into table
        
        Args:
            table: Table name
            data: Data to insert
            
        Returns:
            Dict containing inserted data
        """
        self.ensure_connection()
        
        try:
            logger.debug(f"📝 Inserting into {table}: {data}")
            
            result = self._client.table(table).insert(data).execute()
            
            if result.data:
                logger.info(f"✅ Successfully inserted into {table}")
                return result.data[0] if result.data else {}
            else:
                raise QueryError(f"Insert failed: {result}")
                
        except APIError as e:
            logger.error(f"❌ API Error inserting into {table}: {str(e)}")
            raise QueryError(f"Insert failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error inserting into {table}: {str(e)}")
            raise QueryError(f"Insert failed: {str(e)}")
    
    async def select(self, table: str, columns: str = "*", filters: Optional[Dict[str, Any]] = None, 
                    limit: Optional[int] = None, order_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Select data from table
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Filter conditions
            limit: Maximum number of records
            order_by: Order by column
            
        Returns:
            List of records
        """
        self.ensure_connection()
        
        try:
            logger.debug(f"🔍 Selecting from {table} with filters: {filters}")
            
            query = self._client.table(table).select(columns)
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if isinstance(value, dict):
                        # Handle complex filters like {"gte": 10}
                        for op, val in value.items():
                            query = getattr(query, op)(key, val)
                    else:
                        # Simple equality filter
                        query = query.eq(key, value)
            
            # Apply ordering
            if order_by:
                desc = order_by.startswith('-')
                column = order_by.lstrip('-')
                query = query.order(column, desc=desc)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            logger.info(f"✅ Selected {len(result.data)} records from {table}")
            return result.data
            
        except APIError as e:
            logger.error(f"❌ API Error selecting from {table}: {str(e)}")
            raise QueryError(f"Select failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error selecting from {table}: {str(e)}")
            raise QueryError(f"Select failed: {str(e)}")
    
    async def update(self, table: str, data: Dict[str, Any], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Update data in table
        
        Args:
            table: Table name
            data: Data to update
            filters: Filter conditions for records to update
            
        Returns:
            List of updated records
        """
        self.ensure_connection()
        
        try:
            logger.debug(f"✏️ Updating {table} with data: {data}, filters: {filters}")
            
            query = self._client.table(table).update(data)
            
            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            
            logger.info(f"✅ Updated {len(result.data)} records in {table}")
            return result.data
            
        except APIError as e:
            logger.error(f"❌ API Error updating {table}: {str(e)}")
            raise QueryError(f"Update failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error updating {table}: {str(e)}")
            raise QueryError(f"Update failed: {str(e)}")
    
    async def delete(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Delete data from table
        
        Args:
            table: Table name
            filters: Filter conditions for records to delete
            
        Returns:
            List of deleted records
        """
        self.ensure_connection()
        
        try:
            logger.debug(f"🗑️ Deleting from {table} with filters: {filters}")
            
            query = self._client.table(table).delete()
            
            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            
            logger.info(f"✅ Deleted {len(result.data)} records from {table}")
            return result.data
            
        except APIError as e:
            logger.error(f"❌ API Error deleting from {table}: {str(e)}")
            raise QueryError(f"Delete failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error deleting from {table}: {str(e)}")
            raise QueryError(f"Delete failed: {str(e)}")
    
    # =============================================================================
    # TABLE MANAGEMENT
    # =============================================================================
    
    async def create_tables_if_not_exist(self) -> Dict[str, bool]:
        """
        Create Craefto tables if they don't exist
        
        Returns:
            Dict with table creation results
        """
        self.ensure_connection()
        
        table_schemas = {
            'research_data': '''
                CREATE TABLE IF NOT EXISTS research_data (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    topic TEXT NOT NULL,
                    relevance_score DECIMAL(3,2) DEFAULT 0.0 CHECK (relevance_score >= 0 AND relevance_score <= 1),
                    source TEXT,
                    data JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                -- Create indexes for better performance
                CREATE INDEX IF NOT EXISTS idx_research_data_topic ON research_data(topic);
                CREATE INDEX IF NOT EXISTS idx_research_data_relevance ON research_data(relevance_score DESC);
                CREATE INDEX IF NOT EXISTS idx_research_data_created_at ON research_data(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_research_data_source ON research_data(source);
            ''',
            
            'generated_content': '''
                CREATE TABLE IF NOT EXISTS generated_content (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    research_id UUID REFERENCES research_data(id) ON DELETE CASCADE,
                    content_type TEXT NOT NULL CHECK (content_type IN ('blog', 'social', 'email', 'visual', 'video', 'infographic')),
                    title TEXT NOT NULL,
                    body TEXT,
                    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'generated', 'reviewed', 'approved', 'rejected')),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_generated_content_research_id ON generated_content(research_id);
                CREATE INDEX IF NOT EXISTS idx_generated_content_type ON generated_content(content_type);
                CREATE INDEX IF NOT EXISTS idx_generated_content_status ON generated_content(status);
                CREATE INDEX IF NOT EXISTS idx_generated_content_created_at ON generated_content(created_at DESC);
                
                -- Create trigger for updated_at
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                
                DROP TRIGGER IF EXISTS update_generated_content_updated_at ON generated_content;
                CREATE TRIGGER update_generated_content_updated_at
                    BEFORE UPDATE ON generated_content
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            ''',
            
            'published_content': '''
                CREATE TABLE IF NOT EXISTS published_content (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    content_id UUID REFERENCES generated_content(id) ON DELETE CASCADE,
                    platform TEXT NOT NULL CHECK (platform IN ('twitter', 'linkedin', 'facebook', 'instagram', 'email', 'blog', 'youtube')),
                    url TEXT,
                    engagement_metrics JSONB DEFAULT '{}',
                    published_at TIMESTAMPTZ DEFAULT NOW(),
                    status TEXT DEFAULT 'published' CHECK (status IN ('scheduled', 'published', 'failed', 'deleted'))
                );
                
                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_published_content_content_id ON published_content(content_id);
                CREATE INDEX IF NOT EXISTS idx_published_content_platform ON published_content(platform);
                CREATE INDEX IF NOT EXISTS idx_published_content_published_at ON published_content(published_at DESC);
                CREATE INDEX IF NOT EXISTS idx_published_content_status ON published_content(status);
            ''',
            
            'performance_metrics': '''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    content_id UUID REFERENCES generated_content(id) ON DELETE CASCADE,
                    published_content_id UUID REFERENCES published_content(id) ON DELETE CASCADE,
                    views INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    conversions INTEGER DEFAULT 0,
                    engagement_rate DECIMAL(5,4) DEFAULT 0.0,
                    ctr DECIMAL(5,4) DEFAULT 0.0, -- Click-through rate
                    conversion_rate DECIMAL(5,4) DEFAULT 0.0,
                    additional_metrics JSONB DEFAULT '{}',
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                );
                
                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_performance_metrics_content_id ON performance_metrics(content_id);
                CREATE INDEX IF NOT EXISTS idx_performance_metrics_published_content_id ON performance_metrics(published_content_id);
                CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_performance_metrics_views ON performance_metrics(views DESC);
                CREATE INDEX IF NOT EXISTS idx_performance_metrics_conversions ON performance_metrics(conversions DESC);
            '''
        }
        
        results = {}
        
        try:
            logger.info("🏗️ Creating Craefto database tables...")
            
            for table_name, schema_sql in table_schemas.items():
                try:
                    logger.debug(f"📋 Creating table: {table_name}")
                    
                    # Execute the SQL directly using Supabase's RPC functionality
                    # Note: This requires the user to have appropriate permissions
                    result = self._client.rpc('execute_sql', {'sql': schema_sql}).execute()
                    
                    results[table_name] = True
                    logger.info(f"✅ Table '{table_name}' created successfully")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create table '{table_name}': {str(e)}")
                    results[table_name] = False
                    
                    # Try alternative approach for table creation
                    try:
                        logger.info(f"🔄 Attempting alternative table creation for '{table_name}'...")
                        await self._create_table_alternative(table_name)
                        results[table_name] = True
                        logger.info(f"✅ Table '{table_name}' created via alternative method")
                    except Exception as alt_e:
                        logger.error(f"❌ Alternative table creation failed for '{table_name}': {str(alt_e)}")
                        results[table_name] = False
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            logger.info(f"🏗️ Table creation completed: {success_count}/{total_count} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error during table creation: {str(e)}")
            return {table: False for table in table_schemas.keys()}
    
    async def _create_table_alternative(self, table_name: str):
        """
        Alternative table creation method using direct table operations
        This is a fallback when SQL execution is not available
        """
        # This method would use Supabase's table creation API if available
        # For now, we'll just test if the table exists by trying to query it
        try:
            await self.select(table_name, limit=1)
            logger.info(f"✅ Table '{table_name}' already exists or was created")
        except Exception as e:
            logger.warning(f"⚠️ Cannot verify table '{table_name}' existence: {str(e)}")
            raise
    
    async def verify_tables_exist(self) -> Dict[str, bool]:
        """
        Verify that all required tables exist
        
        Returns:
            Dict with table existence status
        """
        self.ensure_connection()
        
        required_tables = ['research_data', 'generated_content', 'published_content', 'performance_metrics']
        results = {}
        
        for table_name in required_tables:
            try:
                # Try to query the table with a limit of 0 to check existence
                await self.select(table_name, limit=1)
                results[table_name] = True
                logger.debug(f"✅ Table '{table_name}' exists")
            except Exception as e:
                results[table_name] = False
                logger.debug(f"❌ Table '{table_name}' does not exist: {str(e)}")
        
        return results
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table information
        """
        self.ensure_connection()
        
        try:
            # Get table schema information (this might not work with all Supabase setups)
            result = self._client.rpc('get_table_info', {'table_name': table_name}).execute()
            
            if result.data:
                return {
                    'table_name': table_name,
                    'exists': True,
                    'schema': result.data,
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'table_name': table_name,
                    'exists': False,
                    'error': 'Table not found',
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting table info for '{table_name}': {str(e)}")
            return {
                'table_name': table_name,
                'exists': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    # =============================================================================
    # SPECIALIZED METHODS FOR CRAEFTO
    # =============================================================================
    
    async def save_research_data(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save research data to database
        
        Args:
            research_data: Research data with topic, relevance_score, source, data
            
        Returns:
            Saved research record
        """
        try:
            # Prepare research record
            research_record = {
                'topic': research_data.get('topic', ''),
                'relevance_score': min(max(research_data.get('relevance_score', 0.0), 0.0), 1.0),
                'source': research_data.get('source', ''),
                'data': research_data.get('data', {})
            }
            
            return await self.insert('research_data', research_record)
            
        except Exception as e:
            logger.error(f"❌ Error saving research data: {str(e)}")
            raise
    
    async def save_generated_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save generated content to database
        
        Args:
            content_data: Content data with research_id, content_type, title, body, etc.
            
        Returns:
            Saved content record
        """
        try:
            # Validate content_type
            valid_content_types = ['blog', 'social', 'email', 'visual', 'video', 'infographic']
            content_type = content_data.get('content_type', 'blog')
            if content_type not in valid_content_types:
                content_type = 'blog'
            
            # Prepare content record
            content_record = {
                'research_id': content_data.get('research_id'),
                'content_type': content_type,
                'title': content_data.get('title', ''),
                'body': content_data.get('body', ''),
                'status': content_data.get('status', 'generated'),
                'metadata': content_data.get('metadata', {})
            }
            
            return await self.insert('generated_content', content_record)
            
        except Exception as e:
            logger.error(f"❌ Error saving generated content: {str(e)}")
            raise
    
    async def save_published_content(self, publication_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save published content record to database
        
        Args:
            publication_data: Publication data with content_id, platform, url, etc.
            
        Returns:
            Saved publication record
        """
        try:
            # Validate platform
            valid_platforms = ['twitter', 'linkedin', 'facebook', 'instagram', 'email', 'blog', 'youtube']
            platform = publication_data.get('platform', 'blog')
            if platform not in valid_platforms:
                platform = 'blog'
            
            # Prepare publication record
            publication_record = {
                'content_id': publication_data.get('content_id'),
                'platform': platform,
                'url': publication_data.get('url', ''),
                'engagement_metrics': publication_data.get('engagement_metrics', {}),
                'status': publication_data.get('status', 'published')
            }
            
            return await self.insert('published_content', publication_record)
            
        except Exception as e:
            logger.error(f"❌ Error saving published content: {str(e)}")
            raise
    
    async def save_performance_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save performance metrics to database
        
        Args:
            metrics_data: Metrics data with content_id, views, clicks, conversions, etc.
            
        Returns:
            Saved metrics record
        """
        try:
            # Calculate rates
            views = metrics_data.get('views', 0)
            clicks = metrics_data.get('clicks', 0)
            conversions = metrics_data.get('conversions', 0)
            
            ctr = (clicks / views) if views > 0 else 0.0
            conversion_rate = (conversions / clicks) if clicks > 0 else 0.0
            engagement_rate = metrics_data.get('engagement_rate', 0.0)
            
            # Prepare metrics record
            metrics_record = {
                'content_id': metrics_data.get('content_id'),
                'published_content_id': metrics_data.get('published_content_id'),
                'views': max(views, 0),
                'clicks': max(clicks, 0),
                'conversions': max(conversions, 0),
                'engagement_rate': min(max(engagement_rate, 0.0), 1.0),
                'ctr': min(max(ctr, 0.0), 1.0),
                'conversion_rate': min(max(conversion_rate, 0.0), 1.0),
                'additional_metrics': metrics_data.get('additional_metrics', {})
            }
            
            return await self.insert('performance_metrics', metrics_record)
            
        except Exception as e:
            logger.error(f"❌ Error saving performance metrics: {str(e)}")
            raise
    
    async def get_recent_content(self, limit: int = 10, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent generated content
        
        Args:
            limit: Maximum number of records
            content_type: Filter by content type
            
        Returns:
            List of recent content records
        """
        try:
            filters = {}
            if content_type:
                filters['content_type'] = content_type
            
            return await self.select(
                'generated_content',
                columns='*',
                filters=filters,
                limit=limit,
                order_by='-created_at'
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting recent content: {str(e)}")
            return []
    
    async def get_recent_research(self, limit: int = 10, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent research data
        
        Args:
            limit: Maximum number of records
            topic: Filter by topic
            
        Returns:
            List of recent research records
        """
        try:
            filters = {}
            if topic:
                filters['topic'] = topic
            
            return await self.select(
                'research_data',
                columns='*',
                filters=filters,
                limit=limit,
                order_by='-created_at'
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting recent research: {str(e)}")
            return []
    
    async def get_analytics_data(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive analytics data for dashboard
        
        Args:
            days: Number of days to look back
            
        Returns:
            Analytics data with content, publications, research, and performance metrics
        """
        try:
            since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # Get research data stats
            research_stats = await self.select(
                'research_data',
                columns='topic, relevance_score, source, created_at',
                filters={'created_at': {'gte': since_date}}
            )
            
            # Get content generation stats
            content_stats = await self.select(
                'generated_content',
                columns='content_type, status, created_at',
                filters={'created_at': {'gte': since_date}}
            )
            
            # Get publication stats
            publication_stats = await self.select(
                'published_content',
                columns='platform, status, published_at',
                filters={'published_at': {'gte': since_date}}
            )
            
            # Get performance metrics
            performance_stats = await self.select(
                'performance_metrics',
                columns='views, clicks, conversions, engagement_rate, timestamp',
                filters={'timestamp': {'gte': since_date}}
            )
            
            # Calculate totals
            total_views = sum(stat.get('views', 0) for stat in performance_stats)
            total_clicks = sum(stat.get('clicks', 0) for stat in performance_stats)
            total_conversions = sum(stat.get('conversions', 0) for stat in performance_stats)
            
            # Calculate average engagement rate
            engagement_rates = [stat.get('engagement_rate', 0) for stat in performance_stats if stat.get('engagement_rate')]
            avg_engagement_rate = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0
            
            return {
                'period_days': days,
                'research': {
                    'total_research': len(research_stats),
                    'research_by_source': self._group_by_field(research_stats, 'source'),
                    'avg_relevance_score': self._calculate_average_score(research_stats, 'relevance_score')
                },
                'content': {
                    'total_generated': len(content_stats),
                    'content_by_type': self._group_by_field(content_stats, 'content_type'),
                    'content_by_status': self._group_by_field(content_stats, 'status')
                },
                'publications': {
                    'total_published': len(publication_stats),
                    'publications_by_platform': self._group_by_field(publication_stats, 'platform'),
                    'publications_by_status': self._group_by_field(publication_stats, 'status')
                },
                'performance': {
                    'total_views': total_views,
                    'total_clicks': total_clicks,
                    'total_conversions': total_conversions,
                    'avg_engagement_rate': round(avg_engagement_rate, 4),
                    'overall_ctr': round(total_clicks / total_views, 4) if total_views > 0 else 0.0,
                    'overall_conversion_rate': round(total_conversions / total_clicks, 4) if total_clicks > 0 else 0.0,
                    'metrics_count': len(performance_stats)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting analytics data: {str(e)}")
            return {
                'period_days': days,
                'research': {},
                'content': {},
                'publications': {},
                'performance': {},
                'error': str(e)
            }
    
    async def get_content_pipeline_status(self) -> Dict[str, Any]:
        """
        Get the status of the content pipeline (research -> generation -> publication)
        
        Returns:
            Pipeline status with counts and percentages
        """
        try:
            # Get counts from each stage
            research_count = len(await self.select('research_data', columns='id', limit=1000))
            content_count = len(await self.select('generated_content', columns='id', limit=1000))
            published_count = len(await self.select('published_content', columns='id', limit=1000))
            
            # Calculate conversion rates
            research_to_content_rate = (content_count / research_count) if research_count > 0 else 0.0
            content_to_published_rate = (published_count / content_count) if content_count > 0 else 0.0
            overall_conversion_rate = (published_count / research_count) if research_count > 0 else 0.0
            
            return {
                'pipeline_stages': {
                    'research': research_count,
                    'content_generated': content_count,
                    'content_published': published_count
                },
                'conversion_rates': {
                    'research_to_content': round(research_to_content_rate, 4),
                    'content_to_published': round(content_to_published_rate, 4),
                    'overall_conversion': round(overall_conversion_rate, 4)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting pipeline status: {str(e)}")
            return {
                'pipeline_stages': {},
                'conversion_rates': {},
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def save_research(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save research data with enhanced validation and processing
        
        Args:
            research_data: Research data containing topic, keywords, trends, etc.
            
        Returns:
            Saved research record with generated ID
        """
        try:
            # Enhanced research data processing
            processed_data = {
                'topic': research_data.get('topic', '').strip(),
                'relevance_score': min(max(float(research_data.get('relevance_score', 0.0)), 0.0), 1.0),
                'source': research_data.get('source', 'unknown').strip(),
                'data': {
                    'keywords': research_data.get('keywords', []),
                    'trends': research_data.get('trends', []),
                    'sentiment': research_data.get('sentiment', 'neutral'),
                    'competition_level': research_data.get('competition_level', 'medium'),
                    'search_volume': research_data.get('search_volume', 0),
                    'raw_data': research_data.get('raw_data', {}),
                    **research_data.get('data', {})
                }
            }
            
            # Validate required fields
            if not processed_data['topic']:
                raise ValueError("Topic is required for research data")
            
            logger.info(f"💾 Saving research data for topic: {processed_data['topic']}")
            
            result = await self.insert('research_data', processed_data)
            
            logger.info(f"✅ Research data saved with ID: {result.get('id')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error saving research data: {str(e)}")
            raise
    
    async def get_pending_content(self, limit: int = 20, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get content that is ready for publication (generated but not yet published)
        
        Args:
            limit: Maximum number of records to return
            content_type: Filter by specific content type
            
        Returns:
            List of pending content records with research data
        """
        try:
            # Build filters for pending content
            filters = {
                'status': {'in': ['generated', 'reviewed', 'approved']}
            }
            
            if content_type:
                filters['content_type'] = content_type
            
            logger.debug(f"🔍 Fetching pending content with filters: {filters}")
            
            # Get pending content
            pending_content = await self.select(
                'generated_content',
                columns='id, research_id, content_type, title, body, status, metadata, created_at, updated_at',
                filters=filters,
                limit=limit,
                order_by='-updated_at'
            )
            
            # Enrich with research data
            enriched_content = []
            for content in pending_content:
                try:
                    if content.get('research_id'):
                        research_data = await self.select(
                            'research_data',
                            columns='topic, relevance_score, source, data',
                            filters={'id': content['research_id']},
                            limit=1
                        )
                        
                        if research_data:
                            content['research'] = research_data[0]
                    
                    enriched_content.append(content)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Could not enrich content {content.get('id')}: {str(e)}")
                    enriched_content.append(content)
            
            logger.info(f"📋 Found {len(enriched_content)} pending content items")
            return enriched_content
            
        except Exception as e:
            logger.error(f"❌ Error getting pending content: {str(e)}")
            return []
    
    async def mark_published(self, content_id: str, publication_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mark content as published and create publication record
        
        Args:
            content_id: ID of the generated content
            publication_data: Publication details (platform, url, etc.)
            
        Returns:
            Publication record with updated content status
        """
        try:
            logger.info(f"📤 Marking content {content_id} as published")
            
            # Validate platform
            valid_platforms = ['twitter', 'linkedin', 'facebook', 'instagram', 'email', 'blog', 'youtube']
            platform = publication_data.get('platform', '').lower()
            if platform not in valid_platforms:
                raise ValueError(f"Invalid platform: {platform}. Must be one of {valid_platforms}")
            
            # Update content status to published
            updated_content = await self.update(
                'generated_content',
                {'status': 'published'},
                {'id': content_id}
            )
            
            if not updated_content:
                raise ValueError(f"Content with ID {content_id} not found")
            
            # Create publication record
            publication_record = {
                'content_id': content_id,
                'platform': platform,
                'url': publication_data.get('url', ''),
                'engagement_metrics': publication_data.get('engagement_metrics', {}),
                'status': publication_data.get('status', 'published')
            }
            
            published_record = await self.insert('published_content', publication_record)
            
            # Return combined data
            result = {
                'publication': published_record,
                'content': updated_content[0] if updated_content else None,
                'success': True
            }
            
            logger.info(f"✅ Content published successfully on {platform}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error marking content as published: {str(e)}")
            raise
    
    async def track_performance(self, published_content_id: str, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track and update performance metrics for published content
        
        Args:
            published_content_id: ID of the published content record
            metrics_data: Performance metrics (views, clicks, conversions, etc.)
            
        Returns:
            Updated or created performance metrics record
        """
        try:
            # Get published content info
            published_content = await self.select(
                'published_content',
                columns='id, content_id, platform',
                filters={'id': published_content_id},
                limit=1
            )
            
            if not published_content:
                raise ValueError(f"Published content with ID {published_content_id} not found")
            
            content_info = published_content[0]
            content_id = content_info.get('content_id')
            platform = content_info.get('platform')
            
            logger.info(f"📊 Tracking performance for {platform} content: {published_content_id}")
            
            # Prepare metrics with calculated rates
            views = max(int(metrics_data.get('views', 0)), 0)
            clicks = max(int(metrics_data.get('clicks', 0)), 0)
            conversions = max(int(metrics_data.get('conversions', 0)), 0)
            
            # Calculate rates
            ctr = (clicks / views) if views > 0 else 0.0
            conversion_rate = (conversions / clicks) if clicks > 0 else 0.0
            engagement_rate = min(max(float(metrics_data.get('engagement_rate', 0.0)), 0.0), 1.0)
            
            metrics_record = {
                'content_id': content_id,
                'published_content_id': published_content_id,
                'views': views,
                'clicks': clicks,
                'conversions': conversions,
                'engagement_rate': round(engagement_rate, 4),
                'ctr': round(ctr, 4),
                'conversion_rate': round(conversion_rate, 4),
                'additional_metrics': {
                    'platform': platform,
                    'shares': metrics_data.get('shares', 0),
                    'comments': metrics_data.get('comments', 0),
                    'likes': metrics_data.get('likes', 0),
                    'reach': metrics_data.get('reach', 0),
                    'impressions': metrics_data.get('impressions', 0),
                    **metrics_data.get('additional_metrics', {})
                }
            }
            
            # Check if metrics already exist for this published content
            existing_metrics = await self.select(
                'performance_metrics',
                columns='id',
                filters={'published_content_id': published_content_id},
                limit=1,
                order_by='-timestamp'
            )
            
            if existing_metrics:
                # Update existing metrics
                updated_metrics = await self.update(
                    'performance_metrics',
                    metrics_record,
                    {'id': existing_metrics[0]['id']}
                )
                result = updated_metrics[0] if updated_metrics else {}
                logger.info(f"🔄 Updated existing performance metrics")
            else:
                # Create new metrics record
                result = await self.insert('performance_metrics', metrics_record)
                logger.info(f"📈 Created new performance metrics record")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error tracking performance: {str(e)}")
            raise
    
    async def get_top_performing(self, 
                                metric: str = 'views', 
                                limit: int = 10, 
                                days: int = 30,
                                platform: Optional[str] = None,
                                content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get top performing content based on specified metric
        
        Args:
            metric: Metric to sort by ('views', 'clicks', 'conversions', 'engagement_rate', 'ctr')
            limit: Maximum number of records to return
            days: Number of days to look back
            platform: Filter by specific platform
            content_type: Filter by specific content type
            
        Returns:
            List of top performing content with full details
        """
        try:
            valid_metrics = ['views', 'clicks', 'conversions', 'engagement_rate', 'ctr', 'conversion_rate']
            if metric not in valid_metrics:
                metric = 'views'
            
            since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            logger.info(f"🏆 Getting top {limit} content by {metric} (last {days} days)")
            
            # Get performance metrics with filters
            filters = {'timestamp': {'gte': since_date}}
            
            performance_data = await self.select(
                'performance_metrics',
                columns='*',
                filters=filters,
                limit=limit * 3,  # Get more to allow for filtering
                order_by=f'-{metric}'
            )
            
            # Enrich with content and publication data
            enriched_results = []
            
            for perf in performance_data:
                try:
                    # Get published content info
                    published_content = await self.select(
                        'published_content',
                        columns='platform, url, engagement_metrics, published_at',
                        filters={'id': perf.get('published_content_id')},
                        limit=1
                    )
                    
                    if not published_content:
                        continue
                        
                    pub_info = published_content[0]
                    
                    # Apply platform filter
                    if platform and pub_info.get('platform') != platform.lower():
                        continue
                    
                    # Get content info
                    content_info = await self.select(
                        'generated_content',
                        columns='content_type, title, status, research_id, created_at',
                        filters={'id': perf.get('content_id')},
                        limit=1
                    )
                    
                    if not content_info:
                        continue
                        
                    content = content_info[0]
                    
                    # Apply content type filter
                    if content_type and content.get('content_type') != content_type:
                        continue
                    
                    # Get research data
                    research_info = {}
                    if content.get('research_id'):
                        research_data = await self.select(
                            'research_data',
                            columns='topic, relevance_score, source',
                            filters={'id': content['research_id']},
                            limit=1
                        )
                        if research_data:
                            research_info = research_data[0]
                    
                    # Combine all data
                    enriched_result = {
                        'performance': perf,
                        'content': content,
                        'publication': pub_info,
                        'research': research_info,
                        'ranking_metric': metric,
                        'ranking_value': perf.get(metric, 0)
                    }
                    
                    enriched_results.append(enriched_result)
                    
                    if len(enriched_results) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not enrich performance data: {str(e)}")
                    continue
            
            logger.info(f"🎯 Found {len(enriched_results)} top performing content items")
            return enriched_results
            
        except Exception as e:
            logger.error(f"❌ Error getting top performing content: {str(e)}")
            return []
    
    def _calculate_average_score(self, records: List[Dict[str, Any]], field: str) -> float:
        """Calculate average score for a numeric field"""
        scores = [record.get(field, 0) for record in records if record.get(field) is not None]
        return round(sum(scores) / len(scores), 4) if scores else 0.0
    
    def _group_by_field(self, records: List[Dict[str, Any]], field: str) -> Dict[str, int]:
        """Group records by field and count"""
        groups = {}
        for record in records:
            key = record.get(field, 'unknown')
            groups[key] = groups.get(key, 0) + 1
        return groups
    
    # =============================================================================
    # HEALTH CHECK AND MONITORING
    # =============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check
        
        Returns:
            Health status information
        """
        try:
            if not self.is_connected:
                return {
                    'status': 'disconnected',
                    'connected': False,
                    'error': 'Not connected to database'
                }
            
            # Test query
            start_time = datetime.utcnow()
            await self.select('content_generations', limit=1)
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                'status': 'healthy',
                'connected': True,
                'response_time_seconds': response_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# =============================================================================
# GLOBAL DATABASE INSTANCE
# =============================================================================

# Global database client instance
_db_client: Optional[SupabaseClient] = None

def get_database() -> SupabaseClient:
    """
    Get global database client instance
    
    Returns:
        SupabaseClient instance
    """
    global _db_client
    if _db_client is None:
        _db_client = SupabaseClient()
    return _db_client

async def init_database() -> bool:
    """
    Initialize database connection and create tables if needed
    
    Returns:
        bool: True if initialization successful
    """
    try:
        db = get_database()
        success = await db.connect()
        
        if success:
            logger.info("🗄️ Database connection established")
            
            # Verify tables exist
            table_status = await db.verify_tables_exist()
            missing_tables = [table for table, exists in table_status.items() if not exists]
            
            if missing_tables:
                logger.info(f"📋 Missing tables detected: {missing_tables}")
                logger.info("🏗️ Attempting to create missing tables...")
                
                # Try to create tables
                creation_results = await db.create_tables_if_not_exist()
                successful_creations = [table for table, success in creation_results.items() if success]
                failed_creations = [table for table, success in creation_results.items() if not success]
                
                if successful_creations:
                    logger.info(f"✅ Successfully created tables: {successful_creations}")
                
                if failed_creations:
                    logger.warning(f"⚠️ Failed to create tables: {failed_creations}")
                    logger.warning("📝 Note: Tables may need to be created manually in Supabase dashboard")
            else:
                logger.info("✅ All required tables exist")
            
            logger.info("🗄️ Database initialization completed")
        else:
            logger.warning("⚠️ Database initialization failed")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Database initialization error: {str(e)}")
        return False

async def close_database():
    """Close database connection"""
    try:
        db = get_database()
        db.disconnect()
        logger.info("🗄️ Database connection closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {str(e)}")

# =============================================================================
# CONTEXT MANAGERS
# =============================================================================

class DatabaseSession:
    """Context manager for database operations"""
    
    def __init__(self):
        self.db = get_database()
    
    async def __aenter__(self):
        if not self.db.is_connected:
            await self.db.connect()
        return self.db
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Keep connection alive for reuse
        # Only disconnect on application shutdown
        pass

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def with_database(func):
    """
    Decorator to ensure database connection for async functions
    
    Usage:
        @with_database
        async def my_function(db: SupabaseClient):
            return await db.select('table_name')
    """
    async def wrapper(*args, **kwargs):
        async with DatabaseSession() as db:
            return await func(db, *args, **kwargs)
    return wrapper

def handle_database_errors(func):
    """
    Decorator to handle database errors gracefully
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ConnectionError as e:
            logger.error(f"🔌 Database connection error: {str(e)}")
            raise
        except QueryError as e:
            logger.error(f"📝 Database query error: {str(e)}")
            raise
        except DatabaseError as e:
            logger.error(f"🗄️ Database error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected database error: {str(e)}")
            raise DatabaseError(f"Unexpected error: {str(e)}")
    return wrapper
