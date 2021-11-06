from flask import Flask, request, render_template, url_for, redirect, config
from flask_caching import Cache
import requests
import json
import random

config = {
    "DEBUG": True,  # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 0
}

app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)

cache.add("gLatest_message", "")
cache.add("gUser_name", "")
cache.add("gSubscriptions", [])
cache.add("gNotifications", [])
cache.add("gNewNotifications", 0)
cache.add("gPublishers", [])
cache.add("gAdvertisements", [])

def logout():
    payload = dict()
    payload["UserName"] = cache.get("gUser_name")
    try:
        response = requests.post('http://backend_broker_1:5101/logout', data=json.dumps(payload))
    except Exception as e:
        cache.set("gUser_name", "")
        cache.set("gLatest_message", "Logout Failed! Login again!")
        return 'Error'
    
    # return response.text
    try:
        response_json = json.loads(response.text)
        cache.set("gLatest_message", response_json['Message'])
    except Exception as e:
        cache.set("gLatest_message", str(e))
    
    cache.set("gSubscriptions", [])
    cache.set("gNotifications", [])
    cache.set("gNewNotifications", 0)
    cache.set("gPublishers", [])
    cache.set("gAdvertisements", [])

@app.route('/')
def login_form(message_text=""):
    if cache.get("gUser_name") != "":
        logout()
    return render_template('login.html', message=cache.get("gLatest_message"),
                           new_notifications=cache.get("gNewNotifications"))


@app.route('/subscriptions')
def subscribe_form(message_text=""):
    if cache.get("gUser_name") == "":
        cache.set("gLatest_message", "Please login first")
        return redirect(url_for('login_form'))
    publishers = cache.get("gPublishers")
    if not publishers:
        publishers = []
    return render_template('subscribe.html', user_name=cache.get("gUser_name"), message=cache.get("gLatest_message"),
                           publishers=publishers, new_notifications=cache.get("gNewNotifications"))


@app.route('/unsubscribe')
def unsubscribe_form(message_text=""):
    if cache.get("gUser_name") == "":
        cache.set("gLatest_message", "Please login first")
        return redirect(url_for('login_form'))
    subscriptions = cache.get("gSubscriptions")
    if not subscriptions:
        subscriptions = []

    return render_template('unsubscribe.html', user_name=cache.get("gUser_name"), message=cache.get("gLatest_message"),
                           subscriptions=subscriptions, new_notifications=cache.get("gNewNotifications"))


@app.route('/notifications')
def notification_table(message_text=""):
    if cache.get("gUser_name") == "":
        cache.set("gLatest_message", "Please login first")
        return redirect(url_for('login_form'))
    notifications = cache.get("gNotifications")
    if not notifications:
        notifications = []

    return render_template('notifications.html', user_name=cache.get("gUser_name"),
                           message=cache.get("gLatest_message"), notifications=notifications,
                           new_notifications=cache.get("gNewNotifications"), advertisements=cache.get("gAdvertisements"))


@app.route('/', methods=['POST'])
def login_form_post():
    payload = dict()
    cache.set("gUser_name", request.form['username'])
    payload["UserName"] = request.form['username']

    try:
        response = requests.post('http://backend_broker_1:5101/login', data=json.dumps(payload))
    except Exception as e:
        cache.set("gLatest_message", "Login Failed! Try again!")
        return redirect(url_for('login_form'))
    # return response.text
    try:
        response_json = dict(json.loads(response.text))
        cache.set("gLatest_message", response_json['Message'])
        cache.set("gSubscriptions", response_json['Subscriptions'])
        cache.set("gPublishers", response_json['Publishers'])
    except Exception as e:
        cache.set("gLatest_message", str(e))
        cache.set("gSubscriptions", [])
        cache.set("gPublishers", [])
    return redirect(url_for('subscribe_form'))


@app.route('/subscriptions', methods=['POST'])
def subscription_form_post():
    if not cache.get("gUser_name"):
        cache.set("gLatest_message", "Session Expired! Try again!")
        return redirect(url_for('login_form'))
    payload = dict()
    payload["message_type"] = 'subscribe'
    payload["UserName"] = cache.get("gUser_name")
    payload["Owner"] = request.form['owner']
    payload["Repo"] = request.form['repo']
    payload["Provider"] = request.form['publisher']

    try:
        brokers = {'backend_broker_1':'5101', 'backend_broker_2':'5101', 'backend_broker_3':'5101'}
        # brokers = {'backend_broker_1':'5101'}
        broker_add = random.choice(list(brokers.keys()))
        response = requests.post(f'http://{broker_add}:{brokers[broker_add]}/subscribe', data=json.dumps(payload))
    except Exception as e:
        cache.set("gLatest_message", "Cannot reach Server")
        return redirect(url_for('subscribe_form'))
    # return response.text
    try:
        response_json = dict(json.loads(response.text))
        cache.set("gLatest_message", response_json['Message'])
        cache.set("gSubscriptions", response_json['Subscriptions'])
    except Exception as e:
        cache.set("gLatest_message", str(e))
        cache.set("gSubscriptions", [])
    return redirect(url_for('subscribe_form'))


@app.route('/unsubscribe', methods=['POST'])
def unsubscribe_form_post():
    if not cache.get("gUser_name"):
        cache.set("gLatest_message", "Session Expired! Try again!")
        return redirect(url_for('login_form'))
    payload = dict()
    payload["message_type"] = 'unsubscribe'
    payload["UserName"] = cache.get("gUser_name")
    payload["Repo"] = request.form['repo']

    try:
        brokers = {'backend_broker_1':'5101', 'backend_broker_2':'5101', 'backend_broker_3':'5101'}
        # brokers = {'backend_broker_1':'5101'}
        broker_add = random.choice(list(brokers.keys()))
        response = requests.post(f'http://{broker_add}:{brokers[broker_add]}/unsubscribe', data=json.dumps(payload))
    except Exception as e:
        cache.set("gLatest_message", "Cannot reach Server")
        return redirect(url_for('unsubscribe_form'))
    # return response.text
    try:
        response_json = dict(json.loads(response.text))
        cache.set("gLatest_message", response_json['Message'])
        cache.set("gSubscriptions", response_json['Subscriptions'])
    except Exception as e:
        cache.set("gLatest_message", str(e))
        cache.set("gSubscriptions", [])
    return redirect(url_for('unsubscribe_form'))


@app.route('/notifications', methods=['POST'])
def notifications_post():
    try:
        request_data = dict(json.loads(request.get_data()))
        if request_data['UserName'] == cache.get("gUser_name"):
            pass
        cache.set("gNewNotifications", len(request_data['Notifications']))
        notifications = cache.get("gNotifications")
        cache.set("gNotifications", request_data['Notifications'] + notifications)
    except Exception as e:
        cache.set("gNewNotifications", 0)
        notifications = cache.get("gNotifications")
        cache.set("gNotifications", notifications)
    return request_data
    # return redirect(url_for('notification_table'))
    # return "Notifications have been posted successfully!"

@app.route('/refresh_advertisements', methods=['POST'])
def refresh_advertisements_post():
    try:
        request_data = dict(json.loads(request.get_data()))

        topics = request_data["Topics"]
        topics_to_advertise = []
        for topic in topics:
            if "advertise" in topic and topic["advertise"] == 1:
                topics_to_advertise.append(topic)
        cache.set("gAdvertisements", topics_to_advertise)
        return "Advertisements have been posted successfully!"
    except Exception as e:
        cache.set("gAdvertisements", [])
        return "Advertisements posting unsuccessful!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5003, debug=True)
