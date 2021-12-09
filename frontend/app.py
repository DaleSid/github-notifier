from flask import Flask, request, render_template, url_for, redirect, config
from flask_caching import Cache
import requests
import json
import random
import socket
from kafka import KafkaConsumer, TopicPartition, consumer

config = {
    "DEBUG": True,  # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 0
}

subscriptions_list = []

app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)

cache.add("gLatest_message", "")
cache.add("gUser_name", "")
cache.add("gSubscriptions", [])
cache.add("gNotifications", [])
cache.add("gNewNotifications", 0)

hostname = socket.gethostname()

consumer1 = None

def logout():
    global consumer1
    payload = dict()
    payload["UserName"] = cache.get("gUser_name")
    payload["HostName"] = hostname
    try:
        consumer1.close()
        consumer1 = None
        message = cache.get("gUser_name") + ' logged out successfully!'
        cache.set("gLatest_message", message)
        cache.set("gUser_name","")
    except Exception as e:
        cache.set("gLatest_message", str(e))
    
    cache.set("gSubscriptions", [])
    cache.set("gNotifications", [])
    cache.set("gNewNotifications", 0)

@app.route('/')
def login_form(message_text=""):
    if cache.get("gUser_name") != "":
        logout()
    return render_template('login.html', message=cache.get("gLatest_message"),
                           new_notifications=cache.get("gNewNotifications"))


@app.route('/subscriptions')
def subscribe_form(message_text=""):
    global consumer1
    if cache.get("gUser_name") == "":
        cache.set("gLatest_message", "Please login first")
        return redirect(url_for('login_form'))
    
    try:
        subscriptions_list = cache.get("gSubscriptions")
        topics = consumer1.topics()
    except Exception as e:
        cache.set("gLatest_message", str(e))
        return redirect(url_for('login_form'))
    if not topics:
        topics = []

    available_topics = list(set(topics) - set(subscriptions_list))
    return render_template('subscribe.html', user_name=cache.get("gUser_name"), message=cache.get("gLatest_message"),
                           publishers=available_topics, new_notifications=cache.get("gNewNotifications"))


@app.route('/unsubscribe')
def unsubscribe_form(message_text=""):
    if cache.get("gUser_name") == "":
        cache.set("gLatest_message", "Please login first")
        return redirect(url_for('login_form'))

    subscriptions = cache.get("gSubscriptions")

    return render_template('unsubscribe.html', user_name=cache.get("gUser_name"), message=cache.get("gLatest_message"),
                           subscriptions=subscriptions, new_notifications=cache.get("gNewNotifications"))


@app.route('/notifications')
def notification_table(message_text=""):
    # global consumer1
    consumer2 = KafkaConsumer(
            bootstrap_servers=['kafka-1:9092', 'kafka-2:9092', 'kafka-3:9092'], 
            group_id = cache.get("gUser_name"),
            enable_auto_commit=False,
            auto_offset_reset = 'earliest')
    print("Notifications enter")
    if cache.get("gUser_name") == "":
        cache.set("gLatest_message", "Please login first")
        return redirect(url_for('login_form'))
    
    new_notif = 0
    print("Subscribed", consumer1.subscription())
    notifications = cache.get("gNotifications")

    consumer2.subscribe(topics = cache.get("gSubscriptions"))
    msg_pack = consumer2.poll(timeout_ms=5000, update_offsets=False)
    for tp, messages in msg_pack.items():
    # for messages in consumer1:
        print("Message Bundle: ", new_notif, ")", messages)
        for message in messages:
            commits_message = json.loads(message.value)
            # {"Commits": []}
            print("Inside Loop", commits_message["Commits"])
            for notif_message in commits_message["Commits"]:
                if notif_message not in notifications:
                    new_notif += 1
                    notifications.append(notif_message)
                    print("Appended to list")

    # consumer1.commit()
    print("Done with loop")
    consumer2.close()
    cache.set("gNewNotifications", new_notif)
    cache.set("gNotifications", notifications)
    return render_template('notifications.html', user_name=cache.get("gUser_name"),
                           message=cache.get("gLatest_message"), notifications=reversed(notifications),
                           new_notifications=cache.get("gNewNotifications"))


@app.route('/', methods=['POST'])
def login_form_post():
    global consumer1
    payload = dict()
    cache.set("gUser_name", request.form['username'])
    payload["UserName"] = request.form['username']
    payload["HostName"] = hostname

    try:
        consumer1 = KafkaConsumer(
            bootstrap_servers=['kafka-1:9092', 'kafka-2:9092', 'kafka-3:9092'], 
            group_id = cache.get("gUser_name"),
            enable_auto_commit=False)
        if consumer1 == None:
            cache.set("gLatest_message", "Consumer creation failure for" + cache.get("gUser_name"))
            return redirect(url_for('login_form'))
        message = request.form['username'] + ' logged in successfully!'
        cache.set("gLatest_message", message)
        cache.set("gSubscriptions", [])
    except Exception as e:
        cache.set("gLatest_message", str(e))
        cache.set("gSubscriptions", [])
    return redirect(url_for('subscribe_form'))


@app.route('/subscriptions', methods=['POST'])
def subscription_form_post():
    global consumer1
    if not cache.get("gUser_name"):
        cache.set("gLatest_message", "Session Expired! Try again!")
        return redirect(url_for('login_form'))

    try:
        topic_name = request.form['publisher']
        subscriptions_list = cache.get("gSubscriptions")
        subscriptions_list.append(topic_name)
        consumer1.commit()
        consumer1.subscribe(topics = subscriptions_list)
    except Exception as e:
        cache.set("gLatest_message", "Cannot reach Kafka Cluster")
        return redirect(url_for('subscribe_form'))
    message = cache.get("gUser_name") + " requested access to " + topic_name
    cache.set("gLatest_message", message)
    cache.set("gSubscriptions", subscriptions_list)
    return redirect(url_for('subscribe_form'))


@app.route('/unsubscribe', methods=['POST'])
def unsubscribe_form_post():
    global consumer1
    if not cache.get("gUser_name"):
        cache.set("gLatest_message", "Session Expired! Try again!")
        return redirect(url_for('login_form'))

    try:
        topic_name = request.form["repo"]
        subscriptions_list = cache.get("gSubscriptions")
        subscriptions_list.remove(topic_name)
        consumer1.commit()
        if len(subscriptions_list) == 0:
            consumer1.unsubscribe()
        else:
            consumer1.subscribe(topics = subscriptions_list)
    except Exception as e:
        cache.set("gLatest_message", str(e))
        return redirect(url_for('unsubscribe_form'))

    message = cache.get("gUser_name")+" unsubscribed from repo " + request.form['repo']
    cache.set("gLatest_message", message)
    cache.set("gSubscriptions", subscriptions_list)
    return redirect(url_for('unsubscribe_form'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5003, debug=True)
