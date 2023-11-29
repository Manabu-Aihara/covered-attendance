from app import db


class TodoOrm(db.Model):
    __tablename__ = "T_TODO"

    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement=True)
    summary = db.Column(db.String(50), index=True, nullable=False)
    owner = db.Column(db.String(20), index=True, nullable=False)
    done = db.Column(db.Boolean, index=True, nullable=False, default=False)

    def __init__(self, summary, owner):
        self.summary = summary
        self.owner = owner
