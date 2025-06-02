# Testing Utilities: conftest.py and Pytest Fixtures

## Purpose of conftest.py

The conftest.py file is a special configuration file used by **pytest** to define fixtures and hooks that are shared across multiple test files in your project. By placing fixtures in conftest.py, you make them automatically available to all your tests without needing to import them explicitly.

---

## Fixtures Defined in This Project

### 1. `database`

**Scope:** `function`  
**Purpose:**  
Sets up a database session for each test function, ensuring isolation and a clean state for every test.

**How it works:**
- Opens a new database connection and transaction.
- Binds a session to this connection.
- Overrides the app’s `get_db` dependency so all code under test uses this session.
- After the test, clears the override, closes the session, rolls back the transaction, and closes the connection.

**Benefit:**  
Each test runs in its own transaction, which is rolled back after the test, preventing side effects between tests.

---

### 2. `client`

**Scope:** `function`  
**Purpose:**  
Provides a FastAPI `TestClient` instance for making HTTP requests to your app during tests.

**How it works:**
- Depends on the `database` fixture, so all requests use the test database session.
- Yields a `TestClient` for use in your test functions.

---

### 3. `superuser_token_headers`

**Scope:** `function`  
**Purpose:**  
Returns authentication headers for a superuser, allowing you to test endpoints that require superuser privileges.

**How it works:**
- Uses a utility function to get a valid token for a superuser via the test client.

---

### 4. `normal_user_token_headers`

**Scope:** `function`  
**Purpose:**  
Returns authentication headers for a normal user, allowing you to test endpoints that require regular user authentication.

**How it works:**
- Uses a utility function to get a valid token for a normal user, using the test client and test database.

---

## How to Use These Fixtures

Simply add the fixture name as a parameter to your test function, and pytest will inject it automatically. For example:

```python
def test_protected_route(client, superuser_token_headers):
    response = client.get("/protected-endpoint", headers=superuser_token_headers)
    assert response.status_code == 200
```

You do **not** need to import these fixtures in your test files—pytest will discover them automatically from conftest.py.

---

## Summary

- conftest.py centralizes shared test setup logic.
- Fixtures provide reusable, isolated resources for your tests.
- Using these fixtures ensures your tests are reliable, isolated, and easy to write.