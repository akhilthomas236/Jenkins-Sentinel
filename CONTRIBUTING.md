# Contributing to Jenkins Sentinel

Thank you for your interest in contributing to Jenkins Sentinel! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- Jenkins server (for testing)
- AWS account with Bedrock access (for testing)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/jenkins-build-analyzer.git
   cd jenkins-build-analyzer
   ```

2. **Set up Environment**
   ```bash
   # Install UV package manager
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create virtual environment
   uv venv .venv
   source .venv/bin/activate
   
   # Install dependencies
   uv pip install -r requirements.txt
   uv pip install -r requirements-dev.txt
   ```

3. **Set up Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize Database**
   ```bash
   python dbmanage.py init
   ```

## 🔧 Development Workflow

### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Urgent fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Making Changes

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write tests first (TDD approach)
   - Implement your changes
   - Ensure tests pass
   - Update documentation

3. **Run Quality Checks**
   ```bash
   ./scripts/check_all.sh
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 Code Standards

### Python Style Guide
- Follow PEP 8
- Use Black for formatting
- Maximum line length: 88 characters
- Use type hints for all functions
- Document all public functions and classes

### Code Quality Tools
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security scanning
- **pytest**: Testing

### Testing Requirements
- Write tests for all new features
- Maintain test coverage above 80%
- Use pytest for testing
- Mock external dependencies
- Test both success and failure scenarios

### Documentation
- Update README.md for significant changes
- Add docstrings to all functions and classes
- Update API documentation
- Include examples in documentation

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/services/test_agent_manager.py

# Run tests with specific markers
pytest -m "unit"
pytest -m "integration"
```

### Test Categories
- **Unit Tests**: Test individual functions/methods
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Performance Tests**: Test system performance

### Writing Tests
```python
import pytest
from unittest.mock import Mock, patch
from app.services.agent_manager import AgentManager

class TestAgentManager:
    @pytest.fixture
    def agent_manager(self):
        # Setup test fixtures
        pass
    
    def test_feature_functionality(self, agent_manager):
        # Test implementation
        pass
    
    @pytest.mark.asyncio
    async def test_async_feature(self, agent_manager):
        # Test async functionality
        pass
```

## 🗄️ Database Changes

### Creating Migrations
1. **Modify Models**
   ```python
   # Edit files in app/models/
   ```

2. **Generate Migration**
   ```bash
   cd alembic
   alembic revision --autogenerate -m "Add new feature table"
   ```

3. **Review Migration**
   ```bash
   # Check generated file in alembic/versions/
   # Ensure migration is correct
   ```

4. **Test Migration**
   ```bash
   python dbmanage.py migrate
   python dbmanage.py rollback  # Test rollback
   python dbmanage.py migrate   # Re-apply
   ```

### Migration Guidelines
- Always review auto-generated migrations
- Test both upgrade and downgrade paths
- Include data migration scripts if needed
- Document breaking changes

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] No sensitive information in commits

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### Review Process
1. Automated checks must pass
2. At least one code review required
3. All feedback addressed
4. Final approval from maintainer

## 🐛 Reporting Issues

### Bug Reports
Include:
- Python version
- Operating system
- Jenkins version
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

### Feature Requests
Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Additional context

## 📚 Resources

### Documentation
- [API Documentation](docs/api/)
- [Integration Guide](docs/INTEGRATION.md)
- [Product Requirements](docs/PRD.md)

### External Resources
- [Jenkins API Documentation](https://www.jenkins.io/doc/book/using/remote-access-api/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## 💬 Community

### Communication Channels
- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and community support
- Discord: Real-time chat and collaboration

### Code of Conduct
Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.

## 🏆 Recognition

Contributors are recognized in:
- CHANGELOG.md
- GitHub contributors page
- Project documentation
- Release notes

Thank you for contributing to Jenkins Sentinel!
