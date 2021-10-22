from flask import Flask, request, render_template, url_for, redirect, config
from flask_caching import Cache
import requests
import json

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
cache.add("gSubscriptions", [])


@app.route('/')
def login_form(message_text=""):
    return render_template('login.html', message=cache.get("gLatest_message"))


@app.route('/subscriptions')
def subscribe_form(message_text=""):
    if cache.get("gUser_name") == "":
        cache.set("gLatest_message", "Please login first")
        return redirect(url_for('login_form'))
    return render_template('subscribe.html', user_name=cache.get("gUser_name"), message=cache.get("gLatest_message"))

@app.route('/unsubscribe')
def unsubscribe_form(message_text=""):
    if cache.get("gUser_name") == "":
        cache.set("gLatest_message", "Please login first")
        return redirect(url_for('login_form'))
    subscriptions = cache.get("gSubscriptions")
    if not subscriptions:
        subscriptions = []
        
    return render_template('unsubscribe.html', user_name=cache.get("gUser_name"), message=cache.get("gLatest_message"), subscriptions=subscriptions)

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

    response_json = json.loads(response.text)
    cache.set("gLatest_message", response_json['Message'])
    cache.set("gSubscriptions", response_json['Subscriptions'])
    return redirect(url_for('subscribe_form'))


@app.route('/subscriptions', methods=['POST'])
def subscription_form_post():
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

    response_json = json.loads(response.text)
    cache.set("gLatest_message", response_json['Message'])
    cache.set("gSubscriptions", response_json['Subscriptions'])
    return redirect(url_for('subscribe_form'))

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe_form_post():
    payload = dict()
    payload["UserName"] = cache.get("gUser_name")
    payload["Repo"] = request.form['repo']

    try:
        response = requests.post('http://backend_middle_1:5001/unsubscribe', data=payload)
    except requests.exceptions.RequestException as e:
        cache.set("gLatest_message", "Cannot reach Server")
        return redirect(url_for('unsubscribe_form'))

    response_json = json.loads(response.text)
    cache.set("gLatest_message", response_json['Message'])
    cache.set("gSubscriptions", response_json['Subscriptions'])
    return redirect(url_for('unsubscribe_form'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
