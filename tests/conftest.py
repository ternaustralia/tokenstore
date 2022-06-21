import base64
import json
import time
from urllib.parse import parse_qs

from authlib.jose import jwk, jwt
from authlib.oidc.core.grants.util import generate_id_token
import pytest
import responses
from flask_tern.testing.fixtures import monkeypatch_session, cache_spec, basic_auth

from tokenstore import create_app
from tokenstore import models


@pytest.fixture
def app_config():
    return {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_ENGINE_OPTIONS": {},
        "OIDC_DISCOVERY_URL": "https://auth.example.com/.well-known/openid-configuration",
        "OIDC_CLIENT_ID": "oidc-test",

        "CRYPTOKEY": "1"*32,

        "TOKEN_PROVIDERS": "idp1, idp2",
        "IDP1_DISCOVERY_URL": "https://auth.example.com/.well-known/openid-configuration",
        "IDP1_CLIENT_ID": "idp1",
        "IDP1_CLIENT_SECRET": "idp1_secret",
        "IDP1_MD_NAME": "Provider 1",

        "IDP2_DISCOVERY_URL": "https://auth.example.com/.well-known/openid-configuration",
        "IDP2_CLIENT_ID": "idp2",
        "IDP2_CLIENT_SECRET": "idp2_secret",
        "IDP2_MD_NAME": "Provider 2",
    }


@pytest.fixture
def app(app_config):
    from tokenstore import crypto
    app = create_app(app_config)
    # setup db
    with app.app_context():
        models.db.drop_all()
        models.db.create_all()
        # here we would set up initial data for all tests if needed

        models.db.session.add(models.RefreshToken(
            provider="idp1",
            user_id="user",
            token=crypto.encrypt("refresh token"),
        ))
        models.db.session.commit()

    yield app


@pytest.fixture
def client(app, basic_auth):
    return app.test_client()


def get_bearer_token(config):
    return {
        "token_type": "Bearer",
        "access_token": "a",
        "refresh_token": "b",
        "refresh_expires_in": config["refresh_expires_in"],
        "expires_in": 3600,
        "expires_at": int(time.time()) + 3600,
    }


def generate_access_token(key, expires_in=3600):
    return jwt.encode(
        {"alg": "HS256", "kid": key["kid"]},
        {
            "iss": "https://auth.example.com",
            "sub": "123",
            "aud": "oidc-test",
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time()),
            "name": "Test User",
            "email": "test_user@example.com",
            "email_verified": True,
            "family_name": "User",
            "given_name": "Test",
            # "roles": {"resource_access": {"client": ["roles", "roles"]}},
            "scope": "openid profile email",
        },
        key,
        # returns a url-safe string (bytes here), so convert it to python string
    ).decode("utf-8")


@pytest.fixture
def oidc_overrides():
    return {}

@pytest.fixture
def oidc_config(oidc_overrides):
    key = jwk.dumps("secret", "oct", kid="f")
    config = {
        "discovery": {
            "issuer": "https://auth.example_com",
            "authorization_endpoint": "https://auth.example.com/authorize",
            "token_endpoint": "https://auth.example.com/token",
            "jwks_uri": "https://auth.example.com/certs",
            "id_token_signing_alg_values_supported": ["HS256"],
        },
        "jwks": {
            "keys": [key],
        },
        "key": key,
        # user info to put into id_token
        "user_info": {
            # "azp": aud, .. only add if different to aud
            "sub": "user",
            "name": "Test User",
            "email": "test_user@example.com",
            "email_verified": True,
            "family_name": "User",
            "given_name": "Test",
        },
        # apply overrides ?
        "iss": "https://auth.example_com",
        "aud": "example_client_id",
        # token statements
        "refresh_expires_in": 0,
    }
    # apply overrides:
    for key in ("discovery", "usser_info"):
        config.update(oidc_overrides.get(key, {}))
    for key in ("aud", "iss", "refresh_expires_in"):
        config[key] = oidc_overrides.get(key, config[key])
    return config

@pytest.fixture
def mock_kc(oidc_config):
    state = {}

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        # /.well-known/openid-configuration
        rsps.add(
            responses.GET,
            "https://auth.example.com/.well-known/openid-configuration",
            content_type="application/json",
            status=200,
            body=json.dumps(oidc_config["discovery"]),
        )
        # /certs
        rsps.add(
            responses.GET,
            "https://auth.example.com/certs",
            content_type="application/json",
            status=200,
            body=json.dumps(oidc_config["jwks"]),
        )
        # /authorize ... generate code response, but remmember nonce because we have to put nonce into id_token later
        def authorize_callback(request):
            state["nonce"] = request.params["nonce"]
            return (
                302,
                {"location": request.params["redirect_uri"] + "?code=" + "code" + "&state=" + request.params["state"]},
                None,
            )
        rsps.add_callback(
            responses.GET,
            "https://auth.example.com/authorize",
            content_type="application/json",
            callback=authorize_callback,
        )
        # /token
        def token_callback(request):
            body = parse_qs(request.body)
            # fake token response
            token = get_bearer_token(oidc_config)
            token["access_token"] = generate_access_token(oidc_config["key"])
            # grant_type: client_credentials, scope, client_id (oidc-test)
            # grant_type: authorization_code, redirecturi, code, client_id
            if body["grant_type"][0] == "authorization_code":
                # TODO: aud claim only works here
                # aud = body["redirect_uri"][0].split("/")[-2]
                # add id_token in case authorization_code grant
                token["id_token"] = generate_id_token(
                    token,
                    oidc_config["user_info"],
                    oidc_config["key"],
                    alg="HS256",
                    iss=oidc_config["iss"],
                    aud=oidc_config["aud"],
                    exp=3600,
                    nonce=state.get("nonce"),
                )
            if body["grant_type"][0] == "refresh_token":
                token["id_token"] = generate_id_token(
                    token,
                    oidc_config["user_info"],
                    oidc_config["key"],
                    alg="HS256",
                    iss=oidc_config["iss"],
                    aud=oidc_config["aud"],
                    exp=3600,
                    nonce=state.get("nonce"),
                )
            return (200, {}, json.dumps(token))

        rsps.add_callback(
            responses.POST, "https://auth.example.com/token", content_type="application/json", callback=token_callback
        )

        yield
