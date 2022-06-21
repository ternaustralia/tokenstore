import base64

import pytest


def test_authorizations_403(client):
    response = client.get("/api/v1.0/authorizations")
    assert response.status_code == 403


def test_authorizations_user(client, basic_auth):
    response = client.get(
        "/api/v1.0/authorizations",
        headers={"Authorization": basic_auth["user"].auth},
    )
    # TODO: check list of authorizations
    assert len(response.json) == 2
    assert response.json[0]['provider'] == 'idp1'
    assert response.json[0]['active'] == True
    assert response.json[1]['provider'] == 'idp2'
    assert response.json[1]['active'] == False
