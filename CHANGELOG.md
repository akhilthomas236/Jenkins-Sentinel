# Changelog

All notable changes to the Jenkins Sentinel project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive README with setup instructions
- Database migration management with `dbmanage.py`
- Security hardening with sanitized environment variables
- Pre-commit hooks for code quality
- Development setup with quality checks
- Docker and Kubernetes deployment configurations

### Fixed
- Multibranch pipeline job discovery issues
- Jenkins API parameter validation
- Build description update mechanism
- Database relationship mapping for Build-Analysis models
- Action recording for empty action lists

### Security
- Removed sensitive credentials from version control
- Added comprehensive .gitignore
- Created secure .env.example template
- Implemented proper secret management guidelines

## [1.0.0] - 2025-07-14

### Added
- Initial release of Jenkins Sentinel
- Autonomous build monitoring and analysis
- AI-powered failure analysis using Amazon Bedrock
- Pattern learning and recognition system
- Automated action recommendation engine
- Real-time Jenkins integration
- SQLite database with migration support
- RESTful API with FastAPI
- Comprehensive logging system
- Build parameter correlation analysis
- Multi-job monitoring capabilities

### Features
- **Autonomous Monitoring**: Real-time Jenkins job monitoring
- **AI Analysis**: LLM-powered build failure analysis
- **Pattern Learning**: Continuous improvement through pattern recognition
- **Automated Actions**: Self-healing build processes
- **API Integration**: RESTful API for external integrations
- **Database Persistence**: SQLite with Alembic migrations
- **Comprehensive Logging**: Structured logging with rotation
- **Docker Support**: Containerized deployment ready
- **Kubernetes Ready**: Production deployment manifests

### Infrastructure
- FastAPI web framework
- SQLAlchemy ORM with Alembic migrations
- Amazon Bedrock for AI capabilities
- Jenkins Python API integration
- Loguru for advanced logging
- Pydantic for data validation
- UV for package management
