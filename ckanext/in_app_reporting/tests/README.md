# Tests for ckanext-in_app_reporting

This directory contains comprehensive unit and integration tests for the ckanext-in_app_reporting CKAN extension.

## Test Structure

The tests are organized into several modules, each focusing on a specific component of the extension:

### Core Test Files

- **`conftest.py`** - Shared test fixtures and configuration
- **`test_plugin.py`** - Tests for the main plugin classes and interfaces
- **`test_actions.py`** - Tests for all action functions (API endpoints)
- **`test_auth.py`** - Tests for authorization functions
- **`test_utils.py`** - Tests for utility functions and helpers
- **`test_models.py`** - Tests for database models
- **`test_blueprint.py`** - Tests for Flask blueprint routes and views

### Test Coverage

The test suite covers:

- ✅ Plugin interface implementations
- ✅ All action functions (CRUD operations, publishing, etc.)
- ✅ Authorization logic for different user types
- ✅ Utility functions (SSO validation, API requests, token generation)
- ✅ Database model operations
- ✅ Flask blueprint routes and view functions
- ✅ Error handling and edge cases
- ✅ Mock external dependencies (Metabase API, JWT tokens)

## Running Tests

### Prerequisites

1. Install test dependencies:
   ```bash
   pip install pytest pytest-cov pytest-mock pytest-ckan
   ```

2. Ensure CKAN is properly configured and the extension is installed in development mode:
   ```bash
   pip install -e .
   ```

### Running All Tests

From the extension root directory:

```bash
# Using the test runner script
python run_tests.py

# Or directly with pytest
pytest ckanext/in_app_reporting/tests/
```

### Running Specific Test Files

```bash
# Test only the plugin functionality
pytest ckanext/in_app_reporting/tests/test_plugin.py

# Test only the action functions
pytest ckanext/in_app_reporting/tests/test_actions.py

# Test only the authorization functions
pytest ckanext/in_app_reporting/tests/test_auth.py
```

### Running Specific Test Classes or Methods

```bash
# Test a specific class
pytest ckanext/in_app_reporting/tests/test_plugin.py::TestInAppReportingPlugin

# Test a specific method
pytest ckanext/in_app_reporting/tests/test_actions.py::TestMetabaseMappingActions::test_metabase_mapping_create_success
```

### Test Options

```bash
# Run with verbose output
pytest -v ckanext/in_app_reporting/tests/

# Run with coverage report
pytest --cov=ckanext.in_app_reporting --cov-report=html ckanext/in_app_reporting/tests/

# Run only fast tests (skip slow integration tests)
pytest -m "not slow" ckanext/in_app_reporting/tests/

# Run tests and stop on first failure
pytest -x ckanext/in_app_reporting/tests/
```

## Test Patterns and Best Practices

### Fixtures

The test suite uses several fixtures defined in `conftest.py`:

- **`clean_db`** - Resets the DB and installs the table for in_app_reporting
- **`metabase_mapping_factory`** - Creates MetabaseMapping objects
- **`mock_metabase_config`** - Mocks Metabase configuration values
- **`mock_requests`** - Mocks HTTP requests to external APIs
- **`mock_is_metabase_sso_user`** - Mocks SSO user validation

### Mocking External Dependencies

Tests avoid making real API calls or database writes by mocking external dependencies:

```python
@mock.patch('requests.get')
def test_metabase_api_call(self, mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'data': 'test'}
    
    result = some_function_that_calls_api()
    
    assert result == {'data': 'test'}
    mock_get.assert_called_once()
```

### Database Tests

Database tests use the `clean_db` fixture to ensure a clean state:

```python
@pytest.mark.usefixtures("clean_db")
def test_database_operation(self):
    # Test database operations here
    pass
```

### Authorization Tests

Authorization tests verify that functions properly check user permissions:

```python
def test_auth_function_with_unauthorized_user(self):
    context = {'user': 'unauthorized-user'}
    data_dict = {}
    
    result = auth_function(context, data_dict)
    
    assert result['success'] is False
```

## Test Configuration

### pytest.ini

The `pytest.ini` file configures test discovery and execution:

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Markers for categorizing tests (unit, integration, slow)

### test.ini

The `test.ini` file configures CKAN for testing:

- Enables the `in_app_reporting` plugin
- Uses test-specific database settings
- Configures logging for test output

## Continuous Integration

The tests are designed to run in CI environments with:

- Proper mocking of external dependencies
- Deterministic test execution
- Comprehensive error reporting
- Coverage metrics

## Adding New Tests

When adding new functionality to the extension, follow these guidelines:

1. **Add tests for new action functions** in `test_actions.py`
2. **Add tests for new auth functions** in `test_auth.py`
3. **Add tests for new utility functions** in `test_utils.py`
4. **Add tests for new model methods** in `test_models.py`
5. **Add tests for new routes/views** in `test_blueprint.py`

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<ComponentName>`
- Test methods: `test_<action>_<expected_outcome>`

Example:
```python
class TestMetabaseMapping:
    def test_create_mapping_with_valid_data_succeeds(self):
        # Test implementation
        pass
    
    def test_create_mapping_with_invalid_data_raises_validation_error(self):
        # Test implementation
        pass
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure the extension is installed in development mode
2. **Database errors**: Make sure you're using the `clean_db` fixture
3. **Mock errors**: Verify that external dependencies are properly mocked
4. **Configuration errors**: Check that `test.ini` is properly configured

### Debug Mode

Run tests with additional debugging:

```bash
pytest --pdb ckanext/in_app_reporting/tests/  # Drop into debugger on failures
pytest -s ckanext/in_app_reporting/tests/     # Show print statements
pytest --lf ckanext/in_app_reporting/tests/   # Run only last failed tests
```

## Test Metrics

The test suite aims for:

- **80%+ code coverage** across all modules
- **Fast execution** (< 30 seconds for full suite)
- **Comprehensive error scenarios** testing
- **Zero external dependencies** during test execution 