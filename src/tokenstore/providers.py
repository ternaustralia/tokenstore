import logging

from flask import current_app
from flask_tern.auth import oauth


def init_app(app):
    """Initialise extrenal OAuth2 providers.

    Required settings:

    OAUTH_PROVIDERS:
      - id: internal id
        client_id:
        client_secret:
        discovery_url: .well-known/openid-configuration
        # Provider METADATA (UI helper data)
        name: display name
        description: short description
        home_page: home url
        logo: url to logo
        icon: url to icon
      - .......
    """
    # TODO: nothing to do yet .... but probably want to validate settings in some way
    for provider_id in (x.strip() for x in app.config.get("TOKEN_PROVIDERS", "").split(",") if x.strip()):
        # rename DISCOVER_URL to SERVER_METADATA_URL
        app.config["{}_SERVER_METADATA_URL".format(provider_id.upper())] = app.config["{}_DISCOVERY_URL".format(provider_id).upper()]
        md = {}
        for key in ("name", "url", "icon", "description", "logo"):
            provider_key = "{}_md_{}".format(provider_id, key).upper()
            md[key] = app.config.get(provider_key, None)
        oauth.register(
            provider_id,
            client_kwargs={"scope": app.config.get("{}_SCOPE".format(provider_id.upper()), "openid email offline_access")},
            metadata=md,
        )


def providers():
    for provider_id, provider in oauth._clients.items():
        if provider_id != "oidc":
            yield provider


def get(provider_id):
    provider = getattr(oauth, provider_id, None)
    return provider
