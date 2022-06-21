import logging

from flask import abort, redirect, request, session, url_for
from flask_tern import openapi
from flask_tern.auth import current_user, require_login
from flask_tern.logging import create_audit_event, log_audit
from tokenstore.models import RefreshToken, db
from tokenstore import crypto
from tokenstore import providers

from .blueprint import bp


# TODO: GET .. return with redirect ... POST return with 201 and location header
@bp.route("/<provider>/authorize", endpoint="tokenstore_authorize")
@require_login
@openapi.validate()
# TODO: audit this?
def authorize(provider):
    log = logging.getLogger(__name__)
    params = request.openapi.parameters
    # get provider_id from request
    provider_id = provider
    # get provider config based on id
    provider = providers.get(provider_id)
    if not provider:
        abort(404)

    # store return url after authorization
    came_from = (
        params.query.get("return_url")
        or request.referrer
    )

    # create redirect response plus session state for redirect validation (including nonce and state)
    redirect_uri = url_for("api_v1.tokenstore_redirect_uri", provider=provider_id, _external=True)
    rv = provider.create_authorization_url(redirect_uri=redirect_uri, prompt="consent")
    provider.save_authorize_data(redirect_uri=redirect_uri, **rv)

    # store additional info for authorize request state
    session["_tokenstore_state_{}".format(rv["state"])] = {
        "user_id": current_user.id,
        "came_from": came_from,
        "provider": provider_id,
    }

    return redirect(rv["url"])


# TODO: certainly audit this
@bp.route("/<provider>/redirect_uri", endpoint="tokenstore_redirect_uri")
@openapi.validate()
def return_uri(provider):
    log = logging.getLogger(__name__)
    # get parameters
    provider_id = provider
    provider = providers.get(provider_id)
    if not provider:
        abort(404)

    # get session state
    state = request.args.get("state")
    state_data = session.pop("_tokenstore_state_{}".format(state), {})

    # trade code for token
    token = provider.authorize_access_token()

    token_user_id = token["userinfo"]["sub"]
    # validate user id claim ... token returned must be for same user
    if (token_user_id != state_data["user_id"]):
        abort(403)

    # update token in db
    db_token = db.session.query(RefreshToken).filter_by(
        provider=provider_id,
        user_id=state_data["user_id"],
    ).one_or_none()
    if db_token is None:
        # create a new one
        db_token = RefreshToken(
            provider=provider_id,
            user_id=state_data["user_id"],
        )
        db.session.add(db_token)
    # update db token (encrypt at rest)
    db_token.token = crypto.encrypt(token['refresh_token'])
    db_token.expires_in = token['refresh_expires_in']
    if db_token.expires_in != 0:
        db_token.expires_at = token['expires_at'] - token['expires_in'] + token['refresh_expires_in']
    else:
        db_token.expires_at = None

    # TODO: could do more claim validations ... e.g. aud, iss, sub etc...
    db.session.commit()

    # return redirect to came_from
    # TODO: success failure info in return url could be nice ... hard to do this with redirects
    #       can we just pass oidc error on ?
    #       would probably error somewhere above in provider.authorize_access_token()
    # TODO: came_from may be empty ... where to go ?
    return redirect(state_data['came_from'])
