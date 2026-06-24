from app import db


class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    mobile = db.Column(db.String(20))
    address = db.Column(db.String(255))
    gst = db.Column(db.String(50))
    notes = db.Column(db.Text)
