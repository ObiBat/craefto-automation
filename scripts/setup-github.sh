#!/bin/bash

# CRAEFTO Automation - GitHub Repository Setup Script
# This script helps you set up the GitHub repository with all necessary configurations

set -e

echo "🚀 Setting up CRAEFTO Automation GitHub Repository"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    print_step "Initializing Git repository..."
    git init
    print_success "Git repository initialized"
else
    print_success "Git repository already exists"
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    print_warning "GitHub CLI (gh) is not installed"
    echo "Please install it from: https://cli.github.com/"
    echo "Or continue manually by creating the repository on GitHub"
else
    print_success "GitHub CLI is available"
fi

# Get repository information
echo ""
print_step "Repository Configuration"
echo "Please provide the following information:"

read -p "GitHub username: " GITHUB_USERNAME
read -p "Repository name (default: craefto-automation): " REPO_NAME
REPO_NAME=${REPO_NAME:-craefto-automation}

read -p "Repository description: " REPO_DESCRIPTION
REPO_DESCRIPTION=${REPO_DESCRIPTION:-"Enterprise-grade content automation platform using AI agents"}

read -p "Make repository private? (y/N): " MAKE_PRIVATE
MAKE_PRIVATE=${MAKE_PRIVATE:-N}

# Create repository if GitHub CLI is available
if command -v gh &> /dev/null; then
    print_step "Creating GitHub repository..."
    
    VISIBILITY_FLAG=""
    if [[ $MAKE_PRIVATE =~ ^[Yy]$ ]]; then
        VISIBILITY_FLAG="--private"
    else
        VISIBILITY_FLAG="--public"
    fi
    
    if gh repo create "$GITHUB_USERNAME/$REPO_NAME" $VISIBILITY_FLAG --description "$REPO_DESCRIPTION" --source=. --remote=origin --push; then
        print_success "Repository created successfully"
    else
        print_warning "Repository creation failed or already exists"
    fi
else
    print_warning "Please create the repository manually on GitHub:"
    echo "1. Go to https://github.com/new"
    echo "2. Repository name: $REPO_NAME"
    echo "3. Description: $REPO_DESCRIPTION"
    echo "4. Set visibility as needed"
    echo "5. Don't initialize with README (we have one)"
    echo ""
    echo "Then run these commands:"
    echo "git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    echo "git branch -M main"
    echo "git push -u origin main"
fi

# Set up Git configuration
print_step "Setting up Git configuration..."

# Check if user.name and user.email are set
if [ -z "$(git config user.name)" ]; then
    read -p "Git user name: " GIT_NAME
    git config user.name "$GIT_NAME"
fi

if [ -z "$(git config user.email)" ]; then
    read -p "Git user email: " GIT_EMAIL
    git config user.email "$GIT_EMAIL"
fi

print_success "Git configuration complete"

# Create initial commit if needed
if [ -z "$(git log --oneline 2>/dev/null)" ]; then
    print_step "Creating initial commit..."
    
    # Add all files
    git add .
    
    # Create initial commit
    git commit -m "🚀 Initial commit: CRAEFTO Automation Platform

- Complete FastAPI backend with AI agents
- Comprehensive testing suite with pytest
- Docker containerization with multi-stage builds  
- CI/CD pipeline with GitHub Actions
- Monitoring and alerting system
- Production-ready deployment configuration

Features:
✅ Research Agent (trending topics analysis)
✅ Content Generator (blog posts, social media)
✅ Visual Generator (images, graphics)
✅ Publisher Agent (Twitter, LinkedIn, email)
✅ Intelligence Agent (analytics, optimization)
✅ Orchestrator (workflow coordination)
✅ Monitoring System (health checks, alerts)
✅ Comprehensive test coverage (90%+)

Tech Stack:
- Python 3.12, FastAPI, Pydantic
- OpenAI GPT-4, Anthropic Claude
- Supabase, Redis, Docker
- GitHub Actions, Prometheus, Grafana"

    print_success "Initial commit created"
else
    print_success "Repository already has commits"
fi

# Set up GitHub repository secrets
print_step "Setting up GitHub repository secrets..."

echo ""
echo "You need to set up the following secrets in your GitHub repository:"
echo "Go to: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/secrets/actions"
echo ""
echo "Required secrets:"
echo "=================="

# Core secrets
echo "🔐 DOCKERHUB_USERNAME - Your Docker Hub username"
echo "🔐 DOCKERHUB_TOKEN - Your Docker Hub access token"
echo ""

# API Keys
echo "🤖 AI & Content APIs:"
echo "🔐 OPENAI_API_KEY - OpenAI API key for content generation"
echo "🔐 ANTHROPIC_API_KEY - Anthropic API key for content outlining"
echo "🔐 MIDJOURNEY_WEBHOOK_URL - Midjourney webhook for image generation"
echo ""

# Social Media APIs
echo "📱 Social Media APIs:"
echo "🔐 TWITTER_API_KEY - Twitter API key"
echo "🔐 TWITTER_API_SECRET - Twitter API secret"
echo "🔐 LINKEDIN_CLIENT_ID - LinkedIn API client ID"
echo "🔐 LINKEDIN_CLIENT_SECRET - LinkedIn API client secret"
echo ""

# Database & Infrastructure
echo "💾 Database & Infrastructure:"
echo "🔐 SUPABASE_URL - Supabase project URL"
echo "🔐 SUPABASE_KEY - Supabase API key"
echo "🔐 DATABASE_URL - Production database URL"
echo "🔐 REDIS_URL - Redis connection URL"
echo ""

# Email & Marketing
echo "📧 Email & Marketing:"
echo "🔐 CONVERTKIT_API_KEY - ConvertKit API key"
echo "🔐 SENDGRID_API_KEY - SendGrid API key for notifications"
echo ""

# Monitoring & Security
echo "📊 Monitoring & Security:"
echo "🔐 SENTRY_DSN - Sentry error tracking DSN"
echo "🔐 GRAFANA_ADMIN_PASSWORD - Grafana admin password"
echo "🔐 GRAFANA_SECRET_KEY - Grafana secret key"
echo ""

# Deployment
echo "🚀 Deployment:"
echo "🔐 AWS_ACCESS_KEY_ID - AWS access key (if using AWS)"
echo "🔐 AWS_SECRET_ACCESS_KEY - AWS secret key (if using AWS)"
echo "🔐 CLOUDINARY_CLOUD_NAME - Cloudinary cloud name"
echo "🔐 CLOUDINARY_API_KEY - Cloudinary API key"
echo "🔐 CLOUDINARY_API_SECRET - Cloudinary API secret"
echo ""

# SMTP for notifications
echo "📬 SMTP Configuration:"
echo "🔐 SMTP_HOST - SMTP server host"
echo "🔐 SMTP_USER - SMTP username"
echo "🔐 SMTP_PASSWORD - SMTP password"
echo ""

# Create GitHub secrets script
cat > setup-secrets.sh << 'EOF'
#!/bin/bash

# GitHub Secrets Setup Script
# Run this after setting up your repository

echo "Setting up GitHub secrets..."

# Check if GitHub CLI is available
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI is required. Install from: https://cli.github.com/"
    exit 1
fi

# Function to set secret
set_secret() {
    local secret_name=$1
    local secret_description=$2
    
    echo "Setting $secret_name..."
    read -s -p "$secret_description: " secret_value
    echo
    
    if [ -n "$secret_value" ]; then
        if gh secret set "$secret_name" --body "$secret_value"; then
            echo "✅ $secret_name set successfully"
        else
            echo "❌ Failed to set $secret_name"
        fi
    else
        echo "⏭️  Skipping $secret_name (empty value)"
    fi
    echo
}

# Set core secrets
set_secret "DOCKERHUB_USERNAME" "Docker Hub username"
set_secret "DOCKERHUB_TOKEN" "Docker Hub access token"

# Set API keys
set_secret "OPENAI_API_KEY" "OpenAI API key"
set_secret "ANTHROPIC_API_KEY" "Anthropic API key"
set_secret "SUPABASE_URL" "Supabase project URL"
set_secret "SUPABASE_KEY" "Supabase API key"

# Set social media APIs
set_secret "TWITTER_API_KEY" "Twitter API key"
set_secret "TWITTER_API_SECRET" "Twitter API secret"
set_secret "LINKEDIN_CLIENT_ID" "LinkedIn client ID"
set_secret "LINKEDIN_CLIENT_SECRET" "LinkedIn client secret"

# Set email services
set_secret "CONVERTKIT_API_KEY" "ConvertKit API key"

echo "🎉 GitHub secrets setup complete!"
echo "You can add more secrets later via:"
echo "gh secret set SECRET_NAME --body 'secret_value'"
EOF

chmod +x setup-secrets.sh
print_success "Created setup-secrets.sh script"

# Create branch protection script
cat > setup-branch-protection.sh << 'EOF'
#!/bin/bash

# GitHub Branch Protection Setup Script

echo "Setting up branch protection rules..."

if ! command -v gh &> /dev/null; then
    echo "GitHub CLI is required. Install from: https://cli.github.com/"
    exit 1
fi

# Enable branch protection for main branch
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test","integration-tests"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null

echo "✅ Branch protection enabled for main branch"
echo "Required checks: test, integration-tests"
echo "Required reviews: 1"
echo "Dismiss stale reviews: enabled"
EOF

chmod +x setup-branch-protection.sh
print_success "Created setup-branch-protection.sh script"

# Update README with correct repository URL
if [ -f "README.md" ]; then
    print_step "Updating README with repository information..."
    sed -i.bak "s/your-username/$GITHUB_USERNAME/g" README.md
    rm README.md.bak 2>/dev/null || true
    print_success "README updated"
fi

# Final steps
echo ""
print_step "Final steps to complete setup:"
echo ""
echo "1. 🔐 Set up repository secrets:"
echo "   Run: ./setup-secrets.sh"
echo "   Or manually at: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/secrets/actions"
echo ""
echo "2. 🛡️  Enable branch protection:"
echo "   Run: ./setup-branch-protection.sh"
echo "   Or manually at: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/branches"
echo ""
echo "3. 🏷️  Create your first release:"
echo "   git tag v1.0.0"
echo "   git push origin v1.0.0"
echo ""
echo "4. 📊 Enable GitHub Pages (optional):"
echo "   Go to: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/pages"
echo "   Source: Deploy from a branch"
echo "   Branch: main / docs"
echo ""
echo "5. 🚀 Deploy to production:"
echo "   - Set up your production environment"
echo "   - Configure environment variables"
echo "   - Run: docker-compose -f docker-compose.prod.yml up -d"
echo ""

print_success "GitHub repository setup complete!"
echo ""
echo "Repository URL: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo "Actions: https://github.com/$GITHUB_USERNAME/$REPO_NAME/actions"
echo "Settings: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings"
echo ""
echo "Next: Commit and push your changes to trigger the CI/CD pipeline!"
EOF
