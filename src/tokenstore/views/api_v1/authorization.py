from flask import jsonify, url_for
from flask_tern import openapi
from flask_tern.auth import current_user, require_user, oauth
from flask_tern.logging import create_audit_event, log_audit
from tokenstore.models import RefreshToken, db
from tokenstore import providers

from .blueprint import bp


@bp.route("/authorizations", endpoint="tokenstore_authorizations")
@require_user
@openapi.validate()
def get_authorizations():
    active_providers = {
        row.provider
        for row in db.session.query(RefreshToken).filter_by(user_id=current_user.id)
    }
    res = []
    for provider in providers.providers():
        # build return value for this provider
        authorization = {
            "active": provider.name in active_providers,
            "provider": provider.name,
            "actions": {
                "authorize": url_for(
                    "api_v1.tokenstore_authorize",
                    provider=provider.name,
                    _external=True,
                ),
                "token": url_for(
                    "api_v1.tokenstore_token", provider=provider.name, _external=True
                ),
                "revoke": url_for(
                    "api_v1.tokenstore_revoke", provider=provider.name, _external=True
                ),
            },
            "metadata": provider.server_metadata["metadata"],
        }
        res.append(authorization)
    return jsonify(res)
