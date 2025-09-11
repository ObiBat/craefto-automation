# Supabase Database Setup Guide

## Quick Setup Steps

### 1. Open Supabase Dashboard
- Go to: https://supabase.com/dashboard/project/keygkhvkooylrwuryqda/sql
- Or navigate to: Your Project → SQL Editor

### 2. Run the SQL Script
- Copy the contents of `supabase_tables.sql`
- Paste into the SQL Editor
- Click "Run" or press Ctrl+Enter

### 3. Verify Tables Created
After running the script, you should see:
- ✅ 10 tables created successfully
- ✅ Indexes created for performance
- ✅ Initial configuration data inserted

## Tables Created

1. **research_data** - Trending topics and research findings
2. **generated_content** - AI-generated content (blogs, social, emails)
3. **published_content** - Published content tracking
4. **performance_metrics** - Engagement and performance data
5. **content_generations** - Generation request tracking
6. **workflow_tracking** - Automation workflow status
7. **api_usage** - API usage and cost tracking
8. **user_sessions** - User session management
9. **system_config** - System configuration
10. **notifications** - System notifications

## After Setup

Once tables are created, your backend will:
- ✅ Save research data to database
- ✅ Store generated content
- ✅ Track performance metrics
- ✅ Enable full analytics dashboard
- ✅ Remove all "table not found" errors

## Troubleshooting

If you get permission errors:
1. Make sure you're logged into the correct Supabase project
2. Check that your API key has admin permissions
3. Try running the script in smaller chunks

## Test Connection

After creating tables, test with:
```bash
curl -H "x-api-key: cc6fc50edd48edcdb3e0e9d3fecdb1ed7f27ab5e19d4b226" http://127.0.0.1:8000/status
```

You should see database status as "connected" instead of errors.
