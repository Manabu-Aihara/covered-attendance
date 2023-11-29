from flask import render_template, redirect, request
from flask_login import current_user
from flask_login.utils import login_required

from app import app, db
from app.dummy_model_todo import TodoOrm


@app.route("/dummy-form/<target_id>", methods=["GET"])
@login_required
def appear_sub(target_id):
    recent_todo = TodoOrm.query.order_by(TodoOrm.id.desc()).first()
    return render_template(
        "admin/dummy.html", t_num=target_id, recent=recent_todo, stf_login=current_user
    )


@app.route("/todo/add", methods=["POST"])
@login_required
def append_todo():
    summary = request.json["summary"]
    owner = request.json["owner"]
    one_todo = TodoOrm(summary=summary, owner=owner)
    db.session.add(one_todo)
    db.session.commit()

    return redirect("/dummy-form")
