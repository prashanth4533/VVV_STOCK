from app import db


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key_name = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.String(255))
