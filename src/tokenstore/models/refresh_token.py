from . import db


class RefreshToken(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.Text, index=True)
    # refresh token
    token = db.Column(db.LargeBinary)
    expires_in = db.Column(db.Integer)
    # TODO: date ?
    expires_at = db.Column(db.Float)
    user_id = db.Column(db.Text, index=True)
