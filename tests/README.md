# tests/

Unit and integration tests for all modules.

**Status:** ✅ 79/79 tests passing

## Structure

```
tests/
├── conftest.py                   # Pytest fixtures and configuration
├── test_smoke.py                 # Basic smoke tests (1 test)
├── test_data_lake_manager.py     # Data lake tests (10 tests)
├── test_db_connector.py          # Database connection tests (11 tests)
├── test_data_loader.py           # Data loading tests (16 tests)
├── test_yolo_modules.py          # YOLO detector & classifier tests (14 tests)
├── test_detection_manager.py     # Detection manager tests (12 tests)
└── test_api.py                   # API endpoint tests (15 tests)
```

## Test Results

**Total:** 79 tests passing ✅

| Module             | Tests | Status |
| ------------------ | ----- | ------ |
| Data Lake Manager  | 10    | ✅      |
| Database Connector | 11    | ✅      |
| Data Loader        | 16    | ✅      |
| YOLO Modules       | 14    | ✅      |
| Detection Manager  | 12    | ✅      |
| API                | 15    | ✅      |
| Smoke              | 1     | ✅      |

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
