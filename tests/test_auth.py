from fastapi import status


def test_register_user(client, db, monkeypatch):
    """Test user registration."""
    # Mock the session to store and retrieve the captcha answer
    test_captcha = "ABC123"
    session_data = {"captcha_answer": test_captcha}
    
    # Create a mock session that returns our test data
    class MockSession(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.update(session_data)
        
        def get(self, key, default=None):
            return self[key] if key in self else default
    
    # Patch the request.session access
    def mock_session_getter(request):
        if not hasattr(request, "_session"):
            request._session = MockSession()
        return request._session
    
    monkeypatch.setattr("starlette.requests.Request.session", property(mock_session_getter))
    
    # Get the register page first to set up the session
    client.get("/register")
    
    # Now submit the form with the correct captcha
    response = client.post(
        "/register",
        files={
            "email": (None, "newuser@example.com"),
            "password": (None, "testpass123"),
            "confirm_password": (None, "testpass123"),
            "captcha": (None, test_captcha),
        },
    )
    
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/login"
    assert "HX-Trigger" in response.headers  # Check for toast notification


def test_register_user_password_mismatch(client, db, monkeypatch):
    """Test registration with mismatched passwords."""
    # Mock the session to store and retrieve the captcha answer
    test_captcha = "ABC123"
    session_data = {"captcha_answer": test_captcha}
    
    # Create a mock session that returns our test data
    class MockSession(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.update(session_data)
        
        def get(self, key, default=None):
            return self[key] if key in self else default
    
    # Patch the request.session access
    def mock_session_getter(request):
        if not hasattr(request, "_session"):
            request._session = MockSession()
        return request._session
    
    monkeypatch.setattr("starlette.requests.Request.session", property(mock_session_getter))
    
    # Get the register page first to set up the session
    client.get("/register")
    
    # Now submit the form with mismatched passwords
    response = client.post(
        "/register",
        files={
            "email": (None, "newuser@example.com"),
            "password": (None, "testpass123"),
            "confirm_password": (None, "wrongpass"),
            "captcha": (None, test_captcha),
        },
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert "Passwords do not match" in response.text


def test_register_existing_user(client, regular_user, monkeypatch):
    """Test registration with existing email."""
    # Mock the session to store and retrieve the captcha answer
    test_captcha = "ABC123"
    session_data = {"captcha_answer": test_captcha}
    
    # Create a mock session that returns our test data
    class MockSession(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.update(session_data)
        
        def get(self, key, default=None):
            return self[key] if key in self else default
    
    # Patch the request.session access
    def mock_session_getter(request):
        if not hasattr(request, "_session"):
            request._session = MockSession()
        return request._session
    
    monkeypatch.setattr("starlette.requests.Request.session", property(mock_session_getter))
    
    # Get the register page first to set up the session
    client.get("/register")
    
    # Now submit the form with an existing email
    response = client.post(
        "/register",
        files={
            "email": (None, regular_user.email),
            "password": (None, "testpass123"),
            "confirm_password": (None, "testpass123"),
            "captcha": (None, test_captcha),
        },
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert "Email already registered" in response.text


def test_invalid_captcha(client, db, monkeypatch):
    """Test registration with invalid captcha."""
    # Mock the session to store and retrieve the captcha answer
    correct_captcha = "ABC123"
    session_data = {"captcha_answer": correct_captcha}
    
    # Create a mock session that returns our test data
    class MockSession(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.update(session_data)
        
        def get(self, key, default=None):
            return self[key] if key in self else default
    
    # Patch the request.session access
    def mock_session_getter(request):
        if not hasattr(request, "_session"):
            request._session = MockSession()
        return request._session
    
    monkeypatch.setattr("starlette.requests.Request.session", property(mock_session_getter))
    
    # Get the register page first to set up the session
    client.get("/register")
    
    # Submit the form with an incorrect captcha
    response = client.post(
        "/register",
        files={
            "email": (None, "newuser@example.com"),
            "password": (None, "testpass123"),
            "confirm_password": (None, "testpass123"),
            "captcha": (None, "WRONG"),  # Wrong captcha
        },
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert "Invalid security code" in response.text


def test_login_success(client, regular_user, test_password):
    """Test successful login."""
    response = client.post(
        "/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "email": regular_user.email,
            "password": test_password,
            "remember_me": "",  # Optional remember_me field
        },
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/"
    cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in cookie  # Cookie exists
    assert "httponly" in cookie.lower()  # Cookie is httponly
    assert "HX-Trigger" in response.headers


def test_login_remember_me(client, regular_user, test_password):
    """Test login with remember me option."""
    response = client.post(
        "/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "email": regular_user.email,
            "password": test_password,
            "remember_me": "on",
        },
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    cookie = response.headers.get("set-cookie", "")
    assert "max-age=2592000" in cookie.lower()  # 30 days = 30 * 24 * 60 * 60 = 2592000


def test_login_invalid_credentials(client, regular_user):
    """Test login with invalid credentials."""
    response = client.post(
        "/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "email": regular_user.email,
            "password": "wrongpassword",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert "Invalid email or password" in response.text


def test_login_inactive_user(client, inactive_user, test_password):
    """Test login with inactive user."""
    response = client.post(
        "/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "email": inactive_user.email,
            "password": test_password,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert "Invalid email or password" in response.text


def test_logout(client, user_headers):
    """Test logout functionality."""
    response = client.get("/logout", headers=user_headers)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/login"
    cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in cookie  # Cookie exists
    assert "max-age=0" in cookie.lower()  # Cookie is being deleted
    assert "HX-Trigger" in response.headers


def test_access_protected_route_without_token(client):
    """Test accessing protected route without token."""
    response = client.get("/profile")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_access_protected_route_with_invalid_token(client):
    """Test accessing protected route with invalid token."""
    response = client.get(
        "/profile",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_access_protected_route_with_expired_token(client):
    """Test accessing protected route with expired token."""
    from datetime import timedelta

    from app.auth import create_access_token

    # Create token that expired 1 hour ago
    expired_token = create_access_token(
        data={"sub": "test@example.com"}, expires_delta=timedelta(hours=-1)
    )
    response = client.get(
        "/profile",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_access_protected_route_success(client, user_headers):
    """Test accessing protected route with valid token."""
    response = client.get("/profile", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK


def test_token_endpoint(client, regular_user, test_password):
    """Test token endpoint for API access."""
    # OAuth2 form data must be properly encoded
    response = client.post(
        "/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "password",  # Required for OAuth2 password flow
            "username": regular_user.email,
            "password": test_password,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_token_endpoint_invalid_credentials(client, regular_user):
    """Test token endpoint with invalid credentials."""
    response = client.post(
        "/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "password",  # Required for OAuth2 password flow
            "username": regular_user.email,
            "password": "wrongpassword",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
