from app import db


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku_prefix = db.Column(db.String(20))
    display_color = db.Column(db.String(20))
    display_bg = db.Column(db.String(20))
    sort_order = db.Column(db.Integer, default=0)
