import base64

import pytest
import requests


def test_authorize_403(client):
    response = client.get("/api/v1.0/idp1/authorize")
    assert response.status_code == 403


def test_authorize_404_403(client):
    response = client.get("/api/v1.0/unknown/authorize")
    assert response.status_code == 403


def test_authorize_404(client, basic_auth):
    response = client.get(
        "/api/v1.0/unknown/authorize",
        headers={"Authorization": basic_auth["user"].auth},
    )
    assert response.status_code == 404


def test_authorizate_start_get(client, basic_auth, mock_kc):
    with client:
        response = client.get(
            "/api/v1.0/idp2/authorize",
            headers={"Authorization": basic_auth["user"].auth},
            query_string={"return_url": "http://localhost/"}
        )
        # client.cookie_jar
        assert response.status_code == 302
        assert response.headers['Location'].startswith('https://auth.example.com/')


@pytest.mark.parametrize('oidc_overrides', [{"aud": "idp2"}])
def test_authorize_get(client, basic_auth, mock_kc):
    with client:
        from flask import session
        from tokenstore import models
        # initiate authorization
        response = client.get(
            "/api/v1.0/idp2/authorize",
            headers={"Authorization": basic_auth["user"].auth},
            query_string={"return_url": "http://localhost/"}
        )
        # follow redirect to external authorize
        location = response.headers["Location"]
        response = requests.get(location, allow_redirects=False)
        # follow redirect to exchange code for token
        response = client.get(
            response.headers["Location"],
            # FIXME: we shouldn't need auth here ... do we ?
            headers={"Authorization": basic_auth["user"].auth},
        )
        assert response.status_code == 302
        assert response.headers['Location'] == "http://localhost/"
        # session should be empty now
        assert bool(session) == False
        # check db entry is there
        db_token = models.db.session.query(models.RefreshToken).filter_by(user_id="user", provider="idp2").one_or_none()
        assert bool(db_token.token) == True
        assert db_token.expires_in == 0
        assert db_token.expires_at is None


@pytest.mark.parametrize('oidc_overrides', [{"aud": "idp2", "refresh_expires_in": 3600}])
def test_authorize_refresh_expires(client, basic_auth, oidc_config, mock_kc):
    with client:
        from flask import session
        from tokenstore import models
        # initiate authorization
        response = client.get(
            "/api/v1.0/idp2/authorize",
            headers={"Authorization": basic_auth["user"].auth},
            query_string={"return_url": "http://localhost/"}
        )
        # follow redirect to external authorize
        location = response.headers["Location"]
        response = requests.get(location, allow_redirects=False)
        # follow redirect to exchange code for token
        response = client.get(
            response.headers["Location"],
            # FIXME: we shouldn't need auth here ... do we ?
            headers={"Authorization": basic_auth["user"].auth},
        )
        assert response.status_code == 302
        assert response.headers['Location'] == "http://localhost/"
        # session should be empty now
        assert bool(session) == False
        # check db entry is there
        db_token = models.db.session.query(models.RefreshToken).filter_by(user_id="user", provider="idp2").one_or_none()
        assert bool(db_token.token) == True
        assert db_token.expires_in == 3600
        assert bool(db_token.expires_at) == True


@pytest.mark.parametrize('oidc_overrides', [{"aud": "idp2"}])
def test_authorize_wrong_redirect(client, basic_auth, mock_kc):
    with client:
        from flask import session
        from tokenstore import models
        # initiate authorization
        response = client.get(
            "/api/v1.0/idp2/authorize",
            headers={"Authorization": basic_auth["user"].auth},
            query_string={"return_url": "http://localhost/"}
        )
        # follow redirect to external authorize
        location = response.headers["Location"]
        response = requests.get(location, allow_redirects=False)
        # follow redirect to exchange code for token
        # here we patch the redicet to follow to a non existent provider
        location = response.headers["Location"].replace("/idp2/", "/unknown/")
        response = client.get(
            location,
            # FIXME: we shouldn't need auth here ... do we ?
            headers={"Authorization": basic_auth["user"].auth},
        )
        assert response.status_code == 404


@pytest.mark.parametrize('oidc_overrides', [{"aud": "idp2"}])
def test_authorize_wrong_user(client, basic_auth, oidc_config, mock_kc):
    with client:
        from flask import session
        from tokenstore import models
        # initiate authorization
        response = client.get(
            "/api/v1.0/idp2/authorize",
            headers={"Authorization": basic_auth["user"].auth},
            query_string={"return_url": "http://localhost/"}
        )
        # follow redirect to external authorize
        location = response.headers["Location"]
        response = requests.get(location, allow_redirects=False)
        # follow redirect to exchange code for token
        # here we patch the redicet to follow to a non existent provider
        oidc_config["user_info"]["sub"] = "other_user"
        # manipulate session ... or token return ?
        response = client.get(
            response.headers["Location"],
            # FIXME: we shouldn't need auth here ... do we ?
            headers={"Authorization": basic_auth["user"].auth},
        )
        assert response.status_code == 403
