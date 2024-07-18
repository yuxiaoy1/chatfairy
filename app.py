from functools import wraps

from flask import (
    Flask,
    json,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = "secret"

messages = []


def send_message(message):
    messages.append(message)


def login_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return inner


@app.get("/")
@login_required
def index():
    return render_template("chat.html", username=session["username"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form["username"]
        session["username"] = username
        send_message(
            {
                "username": username,
                "message": f"{username} has joined.",
                "type": "auth",
            },
        )
        return redirect(url_for("index"))
    return render_template("login.html")


@app.get("/logout")
def logout():
    if "username" in session:
        send_message(
            {
                "username": session["username"],
                "message": f"{session['username']} has left.",
                "type": "auth",
            }
        )
        session.pop("username")
    return redirect(url_for("index"))


@app.get("/events")
@login_required
def events():
    def generate_response():
        while True:
            if messages:
                yield f"data: {json.dumps(messages[-1])}\n\n"
                messages.clear()

    return app.response_class(generate_response(), mimetype="text/event-stream")


@app.post("/message")
@login_required
def message():
    username = session["username"]
    message = request.json["message"]
    send_message({"username": username, "message": message})
    return "OK"
