from flask import Flask, request, render_template, url_for, redirect, config
from flask_caching import Cache
import requests

config = {
    "DEBUG": True,  # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}

app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)

cache.add("gLatest_message", "")
cache.add("gUser_name", "")


@app.route('/')
def login_form(message_text=""):
    return render_template('login.html', message=cache.get("gLatest_message"))


@app.route('/subscriptions')
def subscribe_form(message_text=""):
    if cache.get("gUser_name") == "":
        login_form()
    return render_template('subscribe.html', user_name=cache.get("gUser_name"), message=cache.get("gLatest_message"))


@app.route('/', methods=['POST'])
def login_form_post():
    payload = dict()
    cache.set("gUser_name", request.form['username'])
    payload["UserName"] = request.form['username']

    try:
        response = requests.post('http://backend_middle_1:5001/login', data=payload)
    except requests.exceptions.RequestException as e:
        cache.set("gLatest_message", "Login Failed! Try again!")
        return redirect(url_for('login_form'))

    cache.set("gLatest_message", response.text)
    return redirect(url_for('subscribe_form'))


@app.route('/subscriptions', methods=['POST'])
def my_form_post():
    payload = dict()
    payload["UserName"] = cache.get("gUser_name")
    payload["Owner"] = request.form['owner']
    payload["Repo"] = request.form['repo']
    payload["Provider"] = request.form['publisher']

    try:
        response = requests.post('http://backend_middle_1:5001/subscribe', data=payload)
    except requests.exceptions.RequestException as e:
        cache.set("gLatest_message", "Cannot reach Server")
        return redirect(url_for('subscribe_form'))

    cache.set("gLatest_message", response.text)
    return redirect(url_for('subscribe_form'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
