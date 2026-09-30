import os
import uuid
from flask import Flask, g, request, render_template, redirect, url_for
from db import init_db
import people
import ideas

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


@app.route("/person/<int:person_id>", methods=["GET", "POST"])
def person_page(person_id):
    person = ideas.get_person(g.user_id, person_id)
    if person is None:
        return "Not found", 404

    error = None
    if request.method == "POST":
        url = request.form.get("url", "")
        note = request.form.get("note", "")
        if not url.strip() and not note.strip():
            error = "Add a link or a note"
        else:
            ideas.add_idea(person_id, url, note)
            return redirect(url_for("person_page", person_id=person_id))

    return render_template(
        "person_detail.html",
        person=person,
        ideas=ideas.list_ideas(person_id),
        error=error,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)