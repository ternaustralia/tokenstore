import logging
from flask import abort, jsonify, request
from flask_tern import openapi
from flask_tern.auth import current_user, require_user
from flask_tern.logging import create_audit_event, log_audit
from tokenstore import crypto
from tokenstore import models
from tokenstore import providers

from .blueprint import bp

# get an access token for provider and current user
@bp.route("/<provider>/token", endpoint="tokenstore_token")
# TODO: audit this
@require_user
@openapi.validate()
def get_token(provider):
    log = logging.getLogger(__name__)
    provider_id = provider
    provider = providers.get(provider_id)
    if not provider:
        raise abort(404)

    # log_audit(create_audit_event("increment", "success"))
    # get token
    db_token = models.db.session.query(models.RefreshToken).filter_by(
        provider=provider_id,
        user_id=current_user.id,
    ).one_or_none()
    if db_token is None:
        # FIXME: need an error messages, client not authorized or refresh
        #        token expired?
        return abort(400)

    # We need a new access_token
    refresh_token = crypto.decrypt(db_token.token)
    token = provider.fetch_access_token(refresh_token=refresh_token, grant_type="refresh_token")
    # update refresh token
    db_token.token = crypto.encrypt(token['refresh_token'])
    db_token.expires_in = token['refresh_expires_in']
    if db_token.expires_in != 0:
        db_token.expires_at = token['expires_at'] - token['expires_in'] + token['refresh_expires_in']
    else:
        db_token.expires_at = None
    models.db.session.commit()

    return jsonify({
        'access_token': token['access_token'],
        'expires_in': token['expires_in'],
        'token_type': token['token_type'],
        'expires_at': token['expires_at'],
        # TODO: check which scopes we add ... do we want to add all ? (e.g. is offline_access included)
        #       to fix tests I'd need to add scope to token returned via conftest.py
        # 'scope': token['scope'],
    })


# get an access token for provider and current user
@bp.route("/<provider>/revoke", methods=["POST"], endpoint="tokenstore_revoke")
# TODO: audit this
@require_user
@openapi.validate()
def revoke_token(provider):
    provider_id = provider
    provider = providers.get(provider_id)
    if not provider:
        raise abort(404)

    # We don't really care whether a refresh_token exists or not
    models.db.session.query(models.RefreshToken).filter_by(
        provider=provider_id,
        user_id=current_user.id,
    ).delete()
    models.db.session.commit()

    return jsonify("Token revoked")
