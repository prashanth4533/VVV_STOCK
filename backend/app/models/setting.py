from app import db


class Setting(db.Model):
    __tablename__ = "settings"

    key_name = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(
        db.DateTime, nullable=True, server_default=db.func.now(), onupdate=db.func.now()
    )

    def __repr__(self):
        return f"<Setting {self.key_name}>"
