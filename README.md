# 🚀 CRAEFTO Automation Platform

[![CI/CD Pipeline](https://github.com/your-username/craefto-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/craefto-automation/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/your-username/craefto-automation/branch/main/graph/badge.svg)](https://codecov.io/gh/your-username/craefto-automation)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-312/)

An enterprise-grade content automation platform that generates, optimizes, and publishes high-quality content across multiple channels using AI agents.

## ✨ Features

### 🤖 AI-Powered Content Generation
- **Research Agent**: Analyzes trending topics across Twitter, Reddit, ProductHunt, and Google Trends
- **Content Generator**: Creates blog posts, social media content, and email campaigns with brand consistency
- **Visual Generator**: Generates blog heroes, social graphics, and OG images with Midjourney and Pillow fallbacks
- **Publisher Agent**: Automated publishing to Twitter, LinkedIn, and email platforms
- **Intelligence Agent**: Performance analytics, competitor tracking, and virality prediction

### 🏗️ Enterprise Architecture
- **FastAPI Backend**: High-performance async API with automatic documentation
- **Comprehensive Monitoring**: Health checks, performance tracking, and alerting system
- **Smart Retry Logic**: Exponential backoff with intelligent API fallbacks
- **Circuit Breaker Pattern**: Prevents cascading failures across services
- **Rate Limiting**: Protects against API abuse and ensures fair usage
- **Database Integration**: Supabase/PostgreSQL with connection pooling

### 🧪 Quality Assurance
- **Comprehensive Testing**: Integration tests with 90%+ coverage
- **Content Quality Validation**: Brand voice, SEO optimization, and hallucination detection
- **Performance Testing**: Stress testing with concurrent load simulation
- **Security Scanning**: Automated vulnerability detection and dependency auditing

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/craefto-automation.git
cd craefto-automation
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Required API keys:
- `OPENAI_API_KEY`: For content generation
- `ANTHROPIC_API_KEY`: For content outlining
- `SUPABASE_URL` & `SUPABASE_KEY`: For database
- `TWITTER_API_KEY` & `TWITTER_API_SECRET`: For Twitter publishing
- `LINKEDIN_CLIENT_ID` & `LINKEDIN_CLIENT_SECRET`: For LinkedIn publishing
- `CONVERTKIT_API_KEY`: For email campaigns
- `MIDJOURNEY_WEBHOOK_URL`: For image generation

### 4. Run with Docker (Recommended)
```bash
# Development environment
docker-compose up -d

# Check logs
docker-compose logs -f craefto-app
```

### 5. Run Locally
```bash
# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Access the API
open http://localhost:8000
```

## 📖 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Research & Analytics
```bash
# Get trending topics
POST /api/research/trending
{
  "sources": ["twitter", "reddit"],
  "keywords": ["SaaS", "AI"],
  "limit": 10
}

# Analyze competitor
POST /research/competitor
{
  "competitor_url": "https://framer.com",
  "analysis_depth": "comprehensive"
}
```

#### Content Generation
```bash
# Generate blog post
POST /api/generate/blog
{
  "topic": "SaaS Onboarding Best Practices",
  "target_audience": "saas_founders",
  "content_type": "comprehensive_guide"
}

# Generate social campaign
POST /api/generate/campaign
{
  "content_id": "blog_123",
  "platforms": ["twitter", "linkedin"],
  "campaign_type": "product_launch"
}
```

#### Publishing
```bash
# Batch publish content
POST /api/publish/batch
{
  "content_items": [
    {
      "content_id": "post_123",
      "platforms": ["twitter", "linkedin"],
      "schedule_time": "2025-09-11T10:00:00Z"
    }
  ]
}

# Get dashboard analytics
GET /api/dashboard
```

#### Orchestration
```bash
# Run manual content sprint
POST /orchestrator/content-sprint
{
  "topic_hint": "SaaS Analytics",
  "target_platforms": ["twitter", "linkedin"]
}

# Execute GTM test cycle
POST /orchestrator/gtm-test
{
  "hypothesis": "Visual templates drive 3x more engagement",
  "test_platforms": ["linkedin", "twitter"]
}

# Full content pipeline
POST /orchestrator/full-pipeline
{
  "topic": "SaaS Growth Strategies",
  "platforms": ["blog", "social", "email"]
}
```

## 🧪 Testing

### Run All Tests
```bash
# Unit and integration tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Performance tests only
pytest tests/test_automation.py::TestCraeftoAutomation::test_performance_limits -v
```

### Test Categories
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Load testing with 50+ concurrent operations
- **Quality Tests**: Content validation and brand consistency
- **Monitoring Tests**: Health checks and alerting systems

## 🏗️ Architecture

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Research      │    │   Content       │    │   Visual        │
│   Agent         │────│   Generator     │────│   Generator     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         │   Publisher     │────│  Orchestrator   │────│  Intelligence   │
         │   Agent         │    │                 │    │   Agent         │
         └─────────────────┘    └─────────────────┘    └─────────────────┘
                                         │
                 ┌─────────────────┐    ┌─────────────────┐
                 │   Monitoring    │────│   Database      │
                 │   System        │    │   Layer         │
                 └─────────────────┘    └─────────────────┘
```

### Tech Stack
- **Backend**: FastAPI, Python 3.12, Pydantic
- **Database**: Supabase (PostgreSQL), Redis (caching)
- **AI APIs**: OpenAI GPT-4, Anthropic Claude, Midjourney
- **Social APIs**: Twitter API v2, LinkedIn API, ConvertKit
- **Monitoring**: Prometheus, Grafana, Custom health checks
- **Testing**: Pytest, Coverage.py, Bandit security scanning
- **Deployment**: Docker, GitHub Actions, Multi-stage builds

## 🚀 Deployment

### Docker Production
```bash
# Build production image
docker build -t craefto-automation:latest .

# Run production stack
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables
```bash
# Production environment
ENVIRONMENT=production
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@host:5432/craefto
REDIS_URL=redis://host:6379/0

# API Keys (required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...

# Social Media APIs
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...

# Additional Services
CONVERTKIT_API_KEY=...
MIDJOURNEY_WEBHOOK_URL=...
MAKE_WEBHOOK_SECRET=...
```

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status

# Monitoring metrics
curl http://localhost:9090/metrics
```

## 📊 Monitoring & Analytics

### Health Monitoring
- **API Availability**: External service health checks
- **Database Connection**: Connection pool and query performance
- **Memory Usage**: System resource monitoring
- **Error Rates**: Real-time failure tracking
- **Circuit Breakers**: Service failure isolation

### Performance Metrics
- **Content Generation Speed**: Average processing time
- **API Costs**: Real-time cost tracking and projections
- **Success Rates**: Operation success/failure ratios
- **Queue Depth**: Processing backlog monitoring

### Alerting
- **Email**: Critical system failures
- **Slack**: Warnings and performance issues
- **Dashboard**: Real-time status updates

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest tests/ -v`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Standards
- **Python**: Follow PEP 8, use type hints
- **Testing**: Maintain 90%+ test coverage
- **Documentation**: Update docstrings and README
- **Security**: Run `bandit` security scans

### Testing Requirements
```bash
# Run all checks before PR
pytest tests/ --cov=app --cov-report=html
flake8 app/ tests/
bandit -r app/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI**: GPT-4 API for content generation
- **Anthropic**: Claude API for content outlining
- **Supabase**: Database and authentication services
- **FastAPI**: High-performance web framework
- **Docker**: Containerization platform

## 📞 Support

- **Documentation**: [Wiki](https://github.com/your-username/craefto-automation/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-username/craefto-automation/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/craefto-automation/discussions)
- **Email**: support@craefto.com

---

**Built with ❤️ for the CRAEFTO content automation platform**