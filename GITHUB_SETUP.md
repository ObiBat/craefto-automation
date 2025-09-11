# 🚀 GitHub Repository Setup Guide

This guide walks you through setting up your CRAEFTO Automation Platform on GitHub with complete CI/CD integration.

## 📋 Quick Setup Steps

### 1. Run the Automated Setup Script
```bash
cd /Users/obi/craefto-automation
./scripts/setup-github.sh
```

The script will guide you through:
- ✅ Git repository initialization
- ✅ GitHub repository creation (if GitHub CLI is installed)
- ✅ Initial commit with comprehensive project structure
- ✅ Repository configuration setup

### 2. Manual GitHub Repository Creation (if needed)

If you don't have GitHub CLI installed:

1. **Go to GitHub**: https://github.com/new
2. **Repository Settings**:
   - Repository name: `craefto-automation`
   - Description: `Enterprise-grade content automation platform using AI agents`
   - Visibility: Public or Private (your choice)
   - ❌ Don't initialize with README (we have one)

3. **Connect Local Repository**:
```bash
git remote add origin https://github.com/YOUR_USERNAME/craefto-automation.git
git branch -M main
git push -u origin main
```

## 🔐 GitHub Secrets Configuration

### Required Secrets Setup

Go to: `https://github.com/YOUR_USERNAME/craefto-automation/settings/secrets/actions`

#### Core Infrastructure
```bash
DOCKERHUB_USERNAME          # Your Docker Hub username
DOCKERHUB_TOKEN            # Docker Hub access token
```

#### AI & Content Generation
```bash
OPENAI_API_KEY             # OpenAI GPT-4 API key
ANTHROPIC_API_KEY          # Anthropic Claude API key
REPLICATE_API_TOKEN        # Replicate API token for image generation
```

#### Database & Storage
```bash
SUPABASE_URL               # https://your-project.supabase.co
SUPABASE_KEY               # Your Supabase API key
DATABASE_URL               # Production PostgreSQL URL
REDIS_URL                  # Redis connection string
```

#### Social Media APIs
```bash
TWITTER_API_KEY            # Twitter/X API key
TWITTER_API_SECRET         # Twitter/X API secret
LINKEDIN_CLIENT_ID         # LinkedIn API client ID
LINKEDIN_CLIENT_SECRET     # LinkedIn API client secret
```

#### Email & Marketing
```bash
CONVERTKIT_API_KEY         # ConvertKit email service
SENDGRID_API_KEY          # SendGrid for notifications
```

#### Monitoring & Security
```bash
SENTRY_DSN                 # Error tracking
GRAFANA_ADMIN_PASSWORD     # Grafana dashboard access
GRAFANA_SECRET_KEY         # Grafana security key
```

### Automated Secrets Setup
```bash
# Run the secrets setup script
./setup-secrets.sh
```

## 🛡️ Branch Protection Setup

Enable branch protection for the `main` branch:

```bash
# Run the branch protection script
./setup-branch-protection.sh
```

Or manually configure at:
`https://github.com/YOUR_USERNAME/craefto-automation/settings/branches`

**Recommended Settings**:
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Required status checks: `test`, `integration-tests`
- ✅ Require pull request reviews before merging (1 reviewer)
- ✅ Dismiss stale reviews when new commits are pushed
- ✅ Restrict pushes that create files larger than 100MB

## 🔄 CI/CD Pipeline Overview

### GitHub Actions Workflow (`.github/workflows/ci.yml`)

#### **Test Job** - Runs on every push/PR
- 🐍 Python 3.12 setup with pip caching
- 🗄️ PostgreSQL test database
- 🧹 Code linting with flake8
- 🧪 Comprehensive test suite with pytest
- 📊 Code coverage reporting to Codecov
- 🔒 Security scanning with bandit

#### **Integration Tests** - Main/develop branches only
- 🔄 End-to-end workflow testing
- ⚡ Performance testing with load simulation
- 📈 System health validation

#### **Build Job** - Main branch only
- 🐳 Multi-platform Docker builds (AMD64/ARM64)
- 📦 Automated image tagging with git SHA
- 🚀 Push to Docker Hub registry

#### **Deploy Jobs** - Environment-specific
- **Staging**: Automatic deployment on `develop` branch
- **Production**: Automatic deployment on `main` branch
- 🧪 Smoke tests after deployment
- 📢 Team notifications

#### **Security Scanning** - PR validation
- 🛡️ Trivy vulnerability scanner
- 📋 SARIF results uploaded to GitHub Security tab

### Pipeline Triggers
```yaml
# Automatic triggers
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
```

## 📊 Monitoring & Observability

### GitHub Actions Dashboard
Monitor your CI/CD pipeline at:
`https://github.com/YOUR_USERNAME/craefto-automation/actions`

### Key Metrics Tracked
- ✅ **Test Success Rate**: Percentage of passing tests
- ⏱️ **Build Duration**: Time to complete full pipeline
- 🚀 **Deployment Frequency**: How often code is deployed
- 🐛 **Failure Recovery Time**: Time to fix broken builds

### Notification Channels
- **GitHub**: Automatic PR status checks
- **Email**: Critical deployment failures
- **Slack**: Build status and warnings (configure webhook)

## 🏷️ Release Management

### Semantic Versioning
```bash
# Create a new release
git tag v1.0.0
git push origin v1.0.0

# GitHub will automatically:
# 1. Trigger production deployment
# 2. Create GitHub release
# 3. Build and tag Docker images
```

### Release Notes Template
```markdown
## 🚀 CRAEFTO Automation v1.0.0

### ✨ New Features
- AI-powered content generation with GPT-4
- Multi-platform social media publishing
- Real-time performance analytics

### 🐛 Bug Fixes
- Fixed rate limiting issues
- Improved error handling

### 🔧 Infrastructure
- Enhanced monitoring and alerting
- Optimized Docker builds
- Updated security scanning
```

## 🚀 Deployment Environments

### Development Environment
- **Branch**: `develop`
- **URL**: `https://dev-api.craefto.com`
- **Database**: Development Supabase project
- **Purpose**: Feature testing and integration

### Staging Environment
- **Branch**: `develop` (auto-deploy)
- **URL**: `https://staging-api.craefto.com`
- **Database**: Staging Supabase project
- **Purpose**: Pre-production validation

### Production Environment
- **Branch**: `main` (auto-deploy)
- **URL**: `https://api.craefto.com`
- **Database**: Production Supabase project
- **Purpose**: Live customer traffic

## 🔧 Local Development Workflow

### 1. Clone and Setup
```bash
git clone https://github.com/YOUR_USERNAME/craefto-automation.git
cd craefto-automation

# Setup environment
cp env.template .env
# Edit .env with your API keys

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Development Cycle
```bash
# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
pytest tests/ -v
flake8 app/ tests/

# Commit and push
git add .
git commit -m "✨ Add amazing feature"
git push origin feature/amazing-feature
```

### 3. Pull Request Process
1. **Create PR** on GitHub
2. **Automated Checks**: CI pipeline runs automatically
3. **Code Review**: Team reviews changes
4. **Merge**: Auto-deploy to staging
5. **Production**: Merge to main for production deployment

## 📈 Performance Optimization

### Build Optimization
- 🐳 **Multi-stage Docker builds**: Separate dev/prod images
- 📦 **Layer caching**: Faster subsequent builds
- 🗜️ **Image compression**: Smaller deployment artifacts

### Test Optimization
- ⚡ **Parallel testing**: Multiple test jobs
- 🎯 **Smart test selection**: Only run affected tests
- 📊 **Coverage caching**: Faster coverage reports

### Deployment Optimization
- 🚀 **Zero-downtime deployments**: Rolling updates
- 🔄 **Health checks**: Automated service validation
- 📊 **Performance monitoring**: Real-time metrics

## 🛠️ Troubleshooting

### Common Issues

#### 1. **Build Failures**
```bash
# Check GitHub Actions logs
https://github.com/YOUR_USERNAME/craefto-automation/actions

# Common fixes:
- Update dependencies in requirements.txt
- Fix linting errors with flake8
- Ensure all tests pass locally
```

#### 2. **Deployment Failures**
```bash
# Check deployment logs
kubectl logs -f deployment/craefto-app

# Common fixes:
- Verify environment variables
- Check database connectivity
- Validate API keys
```

#### 3. **Test Failures**
```bash
# Run tests locally
pytest tests/ -v --tb=short

# Debug specific test
pytest tests/test_automation.py::TestCraeftoAutomation::test_full_content_pipeline -v
```

### Getting Help

1. **GitHub Issues**: Report bugs and feature requests
2. **GitHub Discussions**: Community support and questions
3. **Documentation**: Comprehensive guides in `/docs`
4. **CI/CD Logs**: Detailed pipeline execution logs

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Repository created and accessible
- [ ] All required secrets configured
- [ ] Branch protection rules enabled
- [ ] First CI/CD pipeline run successful
- [ ] Docker image built and pushed
- [ ] Tests passing (90%+ coverage)
- [ ] Security scans clean
- [ ] Deployment successful
- [ ] Health checks passing
- [ ] Monitoring dashboards accessible

## 🎉 Next Steps

1. **Configure API Keys**: Add your production API keys to GitHub secrets
2. **Set Up Monitoring**: Configure Grafana dashboards and alerts
3. **Create Content**: Start generating content with the AI agents
4. **Scale Up**: Add more agent workers for higher throughput
5. **Customize**: Adapt the platform for your specific needs

---

**🚀 Your CRAEFTO Automation Platform is now ready for enterprise-scale content generation!**

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).
For API documentation, visit the live docs at `https://your-domain.com/docs`.
