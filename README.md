# Jenkins Sentinel 🛡️

```
     🏗️ Jenkins Sentinel 🛡️
    ┌─────────────────────────┐
    │   🔍 Monitor & Watch    │
    │   🧠 Learn & Analyze    │  
    │   ⚡ Act & Protect      │
    │   📈 Improve & Evolve   │
    └─────────────────────────┘
```

An autonomous Jenkins monitoring agent powered by Amazon Bedrock LLM that continuously watches, analyzes, and self-improves its build analysis capabilities. It automatically detects issues, learns from patterns, and takes proactive actions to resolve build failures.

## 🚀 Features

### Autonomous Monitoring
- **Real-time Monitoring**: Continuous monitoring of all Jenkins jobs including multibranch pipelines
- **Intelligent Job Discovery**: Automatic detection of new jobs and branches
- **Self-managing Tasks**: Intelligent resource usage and automatic task management
- **Proactive Issue Detection**: Early warning system for potential build issues

### AI-Powered Analysis
- **LLM-driven Analysis**: Real-time build log analysis using Amazon Bedrock
- **Pattern Recognition**: Learns from build history and identifies recurring issues
- **Root Cause Analysis**: Deep analysis with context awareness
- **Comparative Analysis**: Automatic comparison with successful builds
- **Parameter Optimization**: Intelligent build parameter recommendations

### Automated Actions
- **Self-healing**: Automatic resolution of common build issues
- **Smart Retries**: Intelligent build retries with parameter adjustments
- **Notification Routing**: Context-aware team notifications
- **Proactive Alerts**: Early warning alerts with actionable insights

### Advanced Analytics
- **Test Failure Analysis**: Pattern detection in test failures
- **Performance Monitoring**: Build timing and performance analysis
- **Dependency Management**: Automatic dependency conflict resolution
- **Compilation Diagnostics**: Intelligent compilation issue detection
- **Historical Trends**: Long-term pattern analysis and reporting

### Self-Learning System
- **Pattern Database**: Continuously updated knowledge base
- **Success Learning**: Learning from successful build resolutions
- **Adaptive Strategies**: Continuous improvement of analysis approaches
- **Confidence Scoring**: Reliability metrics for recommendations

## 📋 Requirements

### Core Requirements
- **Python**: 3.9 or higher
- **Jenkins**: Server with API access
- **AWS Account**: With Amazon Bedrock access
- **Package Manager**: UV (recommended) or pip

### Optional Components
- **Database**: PostgreSQL (production), SQLite (development)
- **Cache**: Redis (for improved performance)
- **Monitoring**: Prometheus/Grafana
- **Container**: Docker/Kubernetes (for deployment)

## 🔧 Installation & Setup

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd jenkins-build-analyzer

# Install UV package manager (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration file
nano .env
```

**Required Configuration:**
```bash
# Jenkins Configuration
JENKINS_URL=https://your-jenkins-server.com
JENKINS_USER=your-username
JENKINS_TOKEN=your-api-token

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-v2

# Application Configuration
LOG_LEVEL=INFO
ANALYSIS_TIMEOUT=300
MAX_RETRIES=3
LEARNING_ENABLED=true
```

**Optional Configuration:**
```bash
# Database (default: SQLite)
DATABASE_URL=postgresql://user:pass@localhost/buildanalyzer

# Redis Cache
REDIS_URL=redis://localhost:6379

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
```

### 3. Database Setup

The application uses Alembic for database migrations. Use the provided `dbmanage.py` script for all database operations.

#### Initial Database Setup
```bash
# Initialize database and run all migrations
python dbmanage.py init
```

#### Database Management Commands

```bash
# Check current migration status
python dbmanage.py status

# Run pending migrations
python dbmanage.py migrate

# Rollback last migration
python dbmanage.py rollback

# Clean up old data (patterns older than 30 days, analyses older than 7 days)
python dbmanage.py cleanup

# Custom cleanup (patterns older than 60 days, analyses older than 14 days)
python dbmanage.py cleanup --pattern-ttl-days 60 --analysis-ttl-days 14
```

#### When to Use Database Migrations

- **Initial Setup**: Always run `python dbmanage.py init` when setting up a new installation
- **After Updates**: Run `python dbmanage.py migrate` after pulling code updates
- **Schema Changes**: Create new migrations when modifying database models
- **Rollback**: Use `python dbmanage.py rollback` to undo the last migration if issues occur
- **Maintenance**: Run `python dbmanage.py cleanup` regularly to maintain database performance

#### Creating New Migrations

```bash
# Generate a new migration after model changes
cd alembic
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file in alembic/versions/
# Then run the migration
python dbmanage.py migrate
```

## 🚀 Usage

### Standard Deployment

1. **Start the Application:**
   ```bash
   python -m app.main
   ```

2. **Access Interfaces:**
   - **Web API**: http://localhost:8002
   - **API Documentation**: http://localhost:8002/docs
   - **ReDoc**: http://localhost:8002/redoc
   - **Health Check**: http://localhost:8002/health

3. **Monitor Activity:**
   - **Logs**: `logs/agent.log`
   - **Error Logs**: `logs/errors.log`
   - **Database**: `data/analyzer.db` (SQLite)

### API Endpoints

```bash
# Manual build analysis
curl -X POST "http://localhost:8002/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"job_name": "my-job", "build_number": 123}'

# Get analysis results
curl "http://localhost:8002/api/v1/analysis/my-job/123"

# Get learned patterns
curl "http://localhost:8002/api/v1/patterns"

# Health check
curl "http://localhost:8002/health"
```

### Jenkins Integration

#### Method 1: Webhook (Recommended)
```bash
# Configure Jenkins webhook to notify the analyzer
# In Jenkins: Manage Jenkins > Configure System > Build Analyzer
# Webhook URL: http://your-analyzer:8002/webhook
```

#### Method 2: Plugin
```bash
# Install the Jenkins plugin from jenkins-plugin/ directory
# Configure in Jenkins: Manage Jenkins > Configure System
```

## 🐳 Docker Deployment

### Build and Run
```bash
# Build image
docker build -t jenkins-analyzer .

# Run with environment file
docker run -d \
  --name jenkins-analyzer \
  --env-file .env \
  -p 8002:8002 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  jenkins-analyzer
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f analyzer

# Stop services
docker-compose down
```

## ☸️ Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace jenkins-analyzer

# Apply configurations
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n jenkins-analyzer
kubectl get services -n jenkins-analyzer

# Access logs
kubectl logs -f deployment/jenkins-analyzer -n jenkins-analyzer
```

## 🔧 Development

### Development Setup
```bash
# Install development dependencies
uv pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run in development mode
python -m app.main --reload
```

### Code Quality
```bash
# Format code
black .
isort .

# Type checking
mypy app/

# Linting
pylint app/

# Run tests
pytest

# Test coverage
pytest --cov=app --cov-report=html
```

### Database Development
```bash
# Reset database (development only)
rm data/analyzer.db
python dbmanage.py init

# Create migration after model changes
alembic revision --autogenerate -m "Your change description"

# Test migration
python dbmanage.py migrate
```

## 📊 Monitoring & Observability

### Logging
- **Application Logs**: `logs/agent.log`
- **Error Logs**: `logs/errors.log`
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Metrics (if Prometheus enabled)
- Build analysis success/failure rates
- Pattern matching accuracy
- Response times
- Queue lengths
- System resource usage

### Health Checks
```bash
# Application health
curl http://localhost:8002/health

# Database connectivity
curl http://localhost:8002/health/db

# Jenkins connectivity
curl http://localhost:8002/health/jenkins

# AWS Bedrock connectivity
curl http://localhost:8002/health/bedrock
```

## 🔒 Security Considerations

### Environment Variables
- Never commit `.env` files with sensitive data
- Use `.env.example` as a template
- Rotate API tokens regularly
- Use IAM roles in production (AWS)

### Jenkins Security
- Use API tokens instead of passwords
- Limit Jenkins user permissions to necessary jobs
- Enable CSRF protection
- Use HTTPS in production

### Network Security
- Run behind a reverse proxy (nginx/traefik)
- Use TLS/SSL certificates
- Implement rate limiting
- Monitor for suspicious activity

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors:**
```bash
# Check database status
python dbmanage.py status

# Reinitialize if corrupted
rm data/analyzer.db
python dbmanage.py init
```

**Jenkins Connection Issues:**
```bash
# Test Jenkins connectivity
curl -u username:token http://jenkins-url/api/json

# Check network connectivity
ping jenkins-server

# Verify credentials in .env file
```

**AWS Bedrock Errors:**
```bash
# Test AWS credentials
aws bedrock list-foundation-models --region us-east-1

# Check IAM permissions
aws iam get-user

# Verify region configuration
```

**Performance Issues:**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check database size
ls -lh data/analyzer.db

# Clean up old data
python dbmanage.py cleanup
```

### Debugging

**Enable Debug Mode:**
```bash
# Set in .env file
LOG_LEVEL=DEBUG
DEBUG=true

# Or set environment variable
export LOG_LEVEL=DEBUG
python -m app.main
```

**Check System Resources:**
```bash
# Monitor memory usage
ps aux | grep python

# Check disk space
df -h

# Monitor network connections
netstat -an | grep 8002
```

## 📚 API Documentation

### Analysis Endpoints
- `POST /api/v1/analyze` - Trigger build analysis
- `GET /api/v1/analysis/{job_name}/{build_number}` - Get analysis results
- `GET /api/v1/patterns` - Get learned patterns
- `POST /api/v1/webhook` - Jenkins webhook endpoint

### Management Endpoints
- `GET /health` - Application health status
- `GET /metrics` - Prometheus metrics (if enabled)
- `GET /docs` - OpenAPI documentation
- `GET /redoc` - ReDoc documentation

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run quality checks: `./scripts/check_all.sh`
5. Commit changes: `git commit -m "Description"`
6. Push to branch: `git push origin feature/your-feature`
7. Create a pull request

### Code Standards
- Follow PEP 8 style guide
- Add type hints for all functions
- Write comprehensive tests
- Update documentation
- Add changelog entries

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/services/  # Service tests
pytest tests/models/    # Model tests
pytest -k "test_pattern"  # Pattern-related tests

# Coverage report
pytest --cov=app --cov-report=term-missing
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Jenkins community for the robust CI/CD platform
- Amazon Bedrock team for the powerful LLM capabilities
- Contributors and maintainers of this project
- Open source libraries that make this project possible

## 📞 Support

- **GitHub Issues**: [Bug reports and feature requests](https://github.com/your-repo/issues)
- **Discussions**: [General questions and community support](https://github.com/your-repo/discussions)
- **Documentation**: [Comprehensive guides and API docs](https://your-docs-site.com)
- **Community**: [Join our Discord server](https://discord.gg/your-invite)

---

## 📖 Additional Resources

- [Integration Guide](docs/INTEGRATION.md)
- [Product Requirements](docs/PRD.md)
- [API Reference](docs/api/)
- [Deployment Examples](examples/)
- [Jenkins Plugin Documentation](jenkins-plugin/README.md)

## Installation

1. **Install UV Package Manager:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and Setup Environment:**
   ```bash
   git clone <repository-url>
   cd jenkins-build-analyzer
   uv venv .venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

3. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```
   Configure the environment settings:
   ```bash
   # Jenkins Configuration
   JENKINS_URL=https://your-jenkins-server
   JENKINS_USER=your-username
   JENKINS_TOKEN=your-api-token
   
   # AWS Configuration
   AWS_ACCESS_KEY_ID=your-aws-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret
   AWS_REGION=your-aws-region
   BEDROCK_MODEL_ID=your-model-id
   
   # Agent Configuration
   LEARNING_ENABLED=true
   PATTERN_DB_TTL=30
   CACHE_TTL=7
   MAX_RETRIES=3
   ANALYSIS_TIMEOUT=300
   
   # Advanced Features (Optional)
   REDIS_URL=redis://localhost:6379
   DATABASE_URL=postgresql://user:pass@localhost/buildanalyzer
   PROMETHEUS_ENABLED=true
   ```

## Usage

### Standard Deployment

1. **Start the Agent:**
   ```bash
   uvx python -m app.main
   ```

2. **Monitor Agent Activity:**
   - Web Interface: http://localhost:8000
   - Real-time Logs: `logs/agent.log`
   - Metrics Dashboard: http://localhost:8000/metrics
   - Pattern Database: http://localhost:8000/patterns
   
3. **Access API Documentation:**
   - OpenAPI Docs: http://localhost:8000/docs
   - ReDoc Interface: http://localhost:8000/redoc

### Kubernetes Deployment

1. **Deploy to Kubernetes:**
   ```bash
   kubectl apply -f k8s/
   ```

2. **Verify Deployment:**
   ```bash
   kubectl get pods -l app=build-analyzer
   kubectl get services build-analyzer
   ```

3. **Access Services:**
   - Agent API: http://build-analyzer.your-domain
   - Metrics: http://build-analyzer.your-domain/metrics
   - Health: http://build-analyzer.your-domain/health

### Integration Methods

1. **Jenkins Plugin (Recommended):**
   - Install plugin through Jenkins Plugin Manager
   - Configure in "Manage Jenkins" → "Build Analyzer Configuration"

2. **Direct API Integration:**
   ```bash
   # Configure webhook in Jenkins
   curl -X POST "${JENKINS_URL}/configureNotificationPlugin" \
     --data-urlencode "url=http://build-analyzer:8000/webhook"
   ```

3. **Kubernetes Sidecar:**
   - Use provided Kubernetes manifests
   - Agent automatically discovers Jenkins service

## Development

### Local Development Setup

1. **Setup Development Environment:**
   ```bash
   uv pip install -r requirements.txt
   pre-commit install  # Install git hooks
   ```

2. **Run Tests:**
   ```bash
   uvx pytest                 # Run all tests
   uvx pytest -k pattern     # Test pattern matching
   uvx pytest -k agent       # Test agent behavior
   uvx pytest --cov=app      # Test coverage
   ```

3. **Code Quality:**
   ```bash
   uvx black .               # Code formatting
   uvx isort .              # Import sorting
   uvx mypy .               # Type checking
   uvx pylint app tests     # Linting
   ```

4. **Run Development Server:**
   ```bash
   uvx uvicorn app.main:app --reload --port 8000
   ```

### Docker Development

1. **Build Development Image:**
   ```bash
   docker build -t build-analyzer:dev -f Dockerfile.dev .
   ```

2. **Run with Docker Compose:**
   ```bash
   docker compose -f docker-compose.dev.yml up
   ```

### Monitoring Development

1. **Enable Debug Logging:**
   ```bash
   export LOG_LEVEL=DEBUG
   ```

2. **Run with Profiling:**
   ```bash
   uvx python -m cProfile -o profile.stats -m app.main
   ```

3. **Analyze Performance:**
   ```bash
   uvx snakeviz profile.stats
   ```

## Contributing

### Development Process

1. **Fork and Clone:**
   ```bash
   git clone https://github.com/yourusername/jenkins-build-analyzer.git
   cd jenkins-build-analyzer
   git checkout -b feature/your-feature
   ```

2. **Development Workflow:**
   - Write tests first (TDD approach)
   - Implement your changes
   - Add documentation
   - Update changelog

3. **Quality Checks:**
   ```bash
   # Run all checks
   ./scripts/check_all.sh
   
   # Individual checks
   uvx pytest
   uvx black .
   uvx mypy .
   uvx pylint app
   ```

4. **Submit Changes:**
   - Ensure all tests pass
   - Update documentation
   - Create detailed pull request
   - Reference any related issues

### Documentation

1. **Update Docs:**
   ```bash
   cd docs
   uvx mkdocs serve  # Preview at http://localhost:8000
   ```

2. **Generate API Docs:**
   ```bash
   uvx pdoc --html app -o docs/api
   ```

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

- Jenkins community
- Amazon Bedrock team
- Contributors and maintainers

## Support

- GitHub Issues: Feature requests and bug reports
- Discussions: General questions and ideas
- Discord: Real-time community support
