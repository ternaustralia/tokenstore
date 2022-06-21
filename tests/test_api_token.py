import base64

import pytest
import requests


def test_token_403(client):
    response = client.get("/api/v1.0/idp1/token")
    assert response.status_code == 403


def test_token_404_403(client):
    response = client.get("/api/v1.0/unknown/token")
    assert response.status_code == 403


def test_token_404(client, basic_auth):
    response = client.get(
        "/api/v1.0/unknown/token",
        headers={"Authorization": basic_auth["user"].auth},
    )
    assert response.status_code == 404


def test_token_400(client, basic_auth):
    response = client.get(
        "/api/v1.0/idp2/token",
        headers={"Authorization": basic_auth["user"].auth},
    )
    assert response.status_code == 400


def test_token_get(client, basic_auth, mock_kc):
    with client:
        response = client.get(
            "/api/v1.0/idp1/token",
            headers={"Authorization": basic_auth["user"].auth},
        )

        assert response.status_code == 200
        assert 'access_token' in response.json


@pytest.mark.parametrize('oidc_overrides', [{"aud": "idp2", "refresh_expires_in": 3600}])
def test_token_get_expires(client, basic_auth, mock_kc):
    with client:
        response = client.get(
            "/api/v1.0/idp1/token",
            headers={"Authorization": basic_auth["user"].auth},
        )

        assert response.status_code == 200
        assert 'access_token' in response.json


def test_revoke_403(client):
    response = client.post("/api/v1.0/idp1/revoke")
    assert response.status_code == 403


def test_revoke_404_403(client):
    response = client.post("/api/v1.0/unknown/revoke")
    assert response.status_code == 403


def test_revoke_404(client, basic_auth):
    response = client.post(
        "/api/v1.0/unknown/revoke",
        headers={"Authorization": basic_auth["user"].auth},
    )
    assert response.status_code == 404


def test_revoke(client, basic_auth):
    from tokenstore import models
    with client:
        response = client.post(
            "/api/v1.0/idp1/revoke",
            headers={"Authorization": basic_auth["user"].auth},
        )
        assert response.status_code == 200
        assert response.json == "Token revoked"
        db_token = models.db.session.query(models.RefreshToken).filter_by(user_id="user", provider="idp1").one_or_none()
        assert db_token is None
