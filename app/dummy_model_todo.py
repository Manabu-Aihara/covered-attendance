from app import db


class TodoOrm(db.Model):
    __tablename__ = "T_TODO"

    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement=True)
    staff_id = db.Column(
        db.Integer, db.ForeignKey("M_RECORD_PAIDHOLIDAY.STAFFID"), nullable=False
    )
    group_id = db.Column(db.Integer, db.ForeignKey("M_TEAM.CODE"), nullable=False)
    summary = db.Column(db.String(50), index=True, nullable=True)
    # owner = db.Column(db.String(20), index=True, nullable=True)
    done = db.Column(db.String(25), index=True, nullable=True)

    def __init__(self, staff_id):
        self.staff_id = staff_id

    def to_dict(self):
        return {
            "staff_id": self.staff_id,
            "group_id": self.group_id,
            "summry": self.summary,
            # "owner": self.owner,
            "done": self.done,
        }
