from functools import wraps

from flask import (
    Flask,
    json,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = "secret"

messages = []


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
    return redirect(url_for("chat"))


@app.get("/chat")
@login_required
def chat():
    return render_template_string(
        """
    <title>Chatfairy</title>
    <h3>Welcom to Chatfairy!</h3>
    <div>Hello {{username}} <a href="{{ url_for('logout') }}">Logout</a></div>
    <div id="chat-box" style="height: 200px; width: 400px; border: 1px solid black; 
        border-radius: 4px; margin: 10px 0; padding: 8px; overflow:auto;"></div>
    <form id="chat-form">
      <input type="text" id="chat-message" placeholder="Type your message" />
      <button>Send</button>
    </form>
    <script>
      let chatBox = document.getElementById('chat-box')
      let chatForm = document.getElementById('chat-form')
      let chatMessage = document.getElementById('chat-message')
      let sse = new EventSource('/events')

      sse.onmessage = ({ data }) => {
        let { username, message, type } = JSON.parse(data)
        if (username === '{{username}}' && type === 'auth') return
        chatBox.innerHTML += type === 'auth' ? `<div style='color: gray'><em>${message}</em></div>` 
        : `<div>${username}: <strong>${message}</strong></div>`
      }

      chatForm.addEventListener('submit', async event => {
        event.preventDefault()

        let message = chatMessage.value.trim()
        if (!message) return

        await fetch('/message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
        })
        chatMessage.value = ''
      })
    </script>""",
        username=session["username"],
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("chat"))
    if request.method == "POST":
        username = request.form["username"]
        session["username"] = username
        messages.append(
            {
                "username": username,
                "message": f"{username} has joined.",
                "type": "auth",
            },
        )
        return redirect(url_for("chat"))
    return render_template_string(
        """
    <title>Chatfairy</title>
    <h3>Welcom to Chatfairy!</h3>
    <form action="{{ url_for('login') }}" method="POST">
      <input required type="text" name="username" placeholder="Input your username" />
      <button>Login</button>
    </form>"""
    )


@app.get("/logout")
def logout():
    if "username" in session:
        messages.append(
            {
                "username": session["username"],
                "message": f"{session["username"]} has left.",
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
    messages.append({"username": username, "message": message})
    return "OK"
