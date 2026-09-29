import os
import uuid
from flask import Flask, g, request, render_template, redirect, url_for
from db import init_db
import people

app = Flask(__name__)
init_db()

COOKIE_NAME = "giftvault_user"


@app.before_request
def load_user():
    g.user_id = request.cookies.get(COOKIE_NAME)
    g.new_user = g.user_id is None
    if g.new_user:
        g.user_id = uuid.uuid4().hex


@app.after_request
def persist_user(response):
    if getattr(g, "new_user", False):
        response.set_cookie(
            COOKIE_NAME,
            g.user_id,
            max_age=60 * 60 * 24 * 365 * 5,
            httponly=True,
            samesite="Lax",
        )
    return response


@app.route("/")
def index():
    return redirect(url_for("people_list"))


@app.route("/people", methods=["GET", "POST"])
def people_list():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            people.add_person(g.user_id, name)
        return redirect(url_for("people_list"))

    return render_template("people.html", people=people.list_people(g.user_id))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)