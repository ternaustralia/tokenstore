import pytest


@pytest.fixture
def app_config(app_config):
    app_config["SESSION_TYPE"] = "null"
    return app_config

# Test to get to 100% test coverage
def test_session_config(app):
    from flask import session
    with app.test_request_context():
        assert session.__class__.__name__ == "NullSession"
