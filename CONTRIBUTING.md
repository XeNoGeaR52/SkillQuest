# Contributing to SkillQuest

Thank you for your interest in contributing to SkillQuest! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git
- A code editor (VS Code, PyCharm, etc.)

### Setting Up Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/SkillQuest.git
   cd SkillQuest
   ```

2. **Start the development environment**
   ```bash
   make demo
   # Or manually:
   docker-compose up --build
   docker-compose exec web alembic upgrade head
   docker-compose exec web python -m scripts.seed_data
   ```

3. **Verify setup**
   ```bash
   # Check API
   curl http://localhost:8000/health

   # Run tests
   make test
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

### 2. Make Changes

#### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for functions/classes
- Keep functions focused and small
- Use meaningful variable names

#### Example:

```python
async def calculate_user_level(total_xp: int) -> int:
    """
    Calculate user level based on total XP.

    Args:
        total_xp: User's total experience points

    Returns:
        Calculated level (minimum 1)
    """
    if total_xp <= 0:
        return 1
    return int(math.sqrt(total_xp / 100)) + 1
```

### 3. Run Linter

```bash
make lint
# Or manually:
ruff check app/ --select E,F,W,I
```

Fix any linting errors before committing.

### 4. Write Tests

All new features should include tests.

**Test files location**: `app/tests/`

**Example test**:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_new_feature(client: AsyncClient):
    """Test description."""
    response = await client.get("/endpoint")
    assert response.status_code == 200
    assert response.json()["field"] == expected_value
```

Run tests:
```bash
make test
# Or:
pytest app/tests/ -v
```

### 5. Update Documentation

If your changes affect:
- **API**: Update docstrings and README.md
- **Setup**: Update QUICKSTART.md
- **Architecture**: Update ARCHITECTURE.md
- **Features**: Update PROJECT_SUMMARY.md

### 6. Commit Changes

Use conventional commit messages:

```bash
git commit -m "feat: add user profile endpoint"
git commit -m "fix: correct XP calculation for edge cases"
git commit -m "docs: update API documentation"
git commit -m "test: add tests for badge system"
git commit -m "refactor: simplify authentication logic"
```

Commit message format:
```
<type>: <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title describing the change
- Description of what changed and why
- Link to any related issues
- Screenshots (if UI changes)

## Adding New Features

### Example: Adding a New Endpoint

1. **Create Pydantic schemas** (if needed)
   ```python
   # app/schemas/new_feature.py
   from pydantic import BaseModel

   class NewFeatureRequest(BaseModel):
       field: str
   ```

2. **Create router**
   ```python
   # app/api/v1/new_feature.py
   from fastapi import APIRouter, Depends

   router = APIRouter()

   @router.get("/")
   async def get_new_feature():
       return {"message": "New feature"}
   ```

3. **Register router in main.py**
   ```python
   from app.api.v1 import new_feature

   app.include_router(
       new_feature.router,
       prefix="/new-feature",
       tags=["New Feature"]
   )
   ```

4. **Add tests**
   ```python
   # app/tests/test_new_feature.py
   @pytest.mark.asyncio
   async def test_get_new_feature(client: AsyncClient):
       response = await client.get("/new-feature/")
       assert response.status_code == 200
   ```

### Example: Adding a Database Model

1. **Define model**
   ```python
   # app/db/models.py
   class NewModel(Base):
       __tablename__ = "new_models"

       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       name = Column(String(100), nullable=False)
       created_at = Column(DateTime, default=datetime.utcnow)
   ```

2. **Create migration**
   ```bash
   docker-compose exec web alembic revision --autogenerate -m "add new_model table"
   docker-compose exec web alembic upgrade head
   ```

3. **Create schema**
   ```python
   # app/schemas/new_model.py
   class NewModelResponse(BaseModel):
       id: UUID
       name: str
       created_at: datetime

       model_config = {"from_attributes": True}
   ```

## Database Migrations

### Creating a Migration

```bash
# Auto-generate from model changes
docker-compose exec web alembic revision --autogenerate -m "description"

# Review the generated migration in alembic/versions/
# Edit if necessary

# Apply migration
docker-compose exec web alembic upgrade head
```

### Rolling Back

```bash
# Rollback one migration
docker-compose exec web alembic downgrade -1

# Rollback to specific version
docker-compose exec web alembic downgrade <revision_id>
```

## Testing Guidelines

### What to Test

✅ **Do test**:
- API endpoint responses
- Business logic functions
- Database operations
- Authentication/authorization
- Error handling

❌ **Don't test**:
- Third-party libraries
- Framework internals
- Trivial getters/setters

### Test Structure

```python
class TestFeatureName:
    """Group related tests."""

    @pytest.mark.asyncio
    async def test_success_case(self, client):
        """Test successful operation."""
        # Arrange
        data = {"field": "value"}

        # Act
        response = await client.post("/endpoint", json=data)

        # Assert
        assert response.status_code == 200
        assert response.json()["field"] == "value"

    @pytest.mark.asyncio
    async def test_error_case(self, client):
        """Test error handling."""
        response = await client.post("/endpoint", json={})
        assert response.status_code == 400
```

### Running Specific Tests

```bash
# Run specific file
pytest app/tests/test_auth.py

# Run specific test
pytest app/tests/test_auth.py::test_login

# Run with coverage
pytest --cov=app app/tests/
```

## Code Review Process

### Before Requesting Review

- [ ] All tests pass
- [ ] Linter shows no errors
- [ ] Documentation updated
- [ ] Commits are clean and logical
- [ ] Branch is up to date with main

### During Review

- Be responsive to feedback
- Ask questions if unclear
- Make requested changes promptly
- Keep discussions professional and constructive

## Project Structure Guidelines

```
app/
├── api/v1/          # API endpoints (one file per resource)
├── core/            # Core functionality (config, security, deps)
├── db/              # Database (models, session)
├── schemas/         # Pydantic models (one file per resource)
├── services/        # Business logic (reusable functions)
├── tasks/           # Background tasks (Celery)
└── tests/           # Tests (mirror app structure)
```

### File Naming

- Use snake_case for all Python files
- Name test files with `test_` prefix
- Group related functionality

### Import Order

```python
# Standard library
import os
from datetime import datetime

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy import select

# Local
from app.db.models import User
from app.schemas.user import UserResponse
from app.core.deps import get_current_user
```

## Common Tasks

### Adding a New Badge Type

1. Update `badge_service.py` to handle new condition type
2. Add example badge in seed script
3. Document in README.md
4. Add tests for evaluation logic

### Adding Rate Limiting

1. Install `slowapi`: Add to requirements.txt
2. Create middleware in `app/core/rate_limit.py`
3. Apply to specific endpoints
4. Add tests

### Adding Metrics

1. Install `prometheus-client` (already in requirements)
2. Create metrics in `app/core/metrics.py`
3. Add `/metrics` endpoint
4. Document in README.md

## Getting Help

- **Questions**: Open an issue with the `question` label
- **Bugs**: Open an issue with the `bug` label
- **Feature Requests**: Open an issue with the `enhancement` label
- **Security**: Email directly (don't open public issues)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be added to CONTRIBUTORS.md (coming soon).

Thank you for contributing to SkillQuest! 🎉
