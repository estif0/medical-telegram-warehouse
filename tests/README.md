# tests/

Unit and integration tests for all modules.

## Structure

```
tests/
├── test_smoke.py              # Basic smoke tests for all major components
├── test_scraper.py           # Tests for telegram_scraper & data_lake_manager
├── test_db_connector.py      # Tests for database connection
├── test_data_loader.py       # Tests for data loading
├── test_yolo_detector.py     # Tests for YOLO detection
├── test_api.py               # Tests for API endpoints
└── integration/
    └── test_full_pipeline.py # End-to-end pipeline tests
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_scraper.py -v

# Run specific test
pytest tests/test_scraper.py::TestTelegramScraper::test_connect -v
```

## Test Standards

### Naming Convention
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<method>_<scenario>`

### Test Structure (Arrange-Act-Assert)
```python
def test_method_returns_expected_value():
    # Arrange
    obj = MyClass("param1", "param2")
    expected = {"key": "value"}
    
    # Act
    result = obj.method()
    
    # Assert
    assert result == expected
```

### Mocking External Dependencies
```python
from unittest.mock import Mock, patch

@patch('src.module.external_service')
def test_with_mock(mock_service):
    mock_service.return_value = {"result": "mocked"}
    # Test code
```

## Coverage Goals

- **Minimum**: 80% code coverage
- **Target**: 90%+ for critical modules

Check coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

## Test Categories

### Unit Tests
Test individual functions/methods in isolation with mocks.

### Integration Tests
Test module interactions with real/test databases.

### End-to-End Tests
Test complete pipeline flow with sample data.

## Notes

- Mock external APIs (Telegram, etc.)
- Use fixtures for common test setup
- Test edge cases and error conditions
- Keep tests fast and deterministic
- Document complex test logic
