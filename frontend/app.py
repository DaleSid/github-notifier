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
    global consumer1
    print("Notifications enter")
    if cache.get("gUser_name") == "":
        cache.set("gLatest_message", "Please login first")
        return redirect(url_for('login_form'))
    
    new_notif = 0
    print("Subscribed", consumer1.subscription())
    notifications = cache.get("gNotifications")

    # consumer1 = KafkaConsumer(
    #         bootstrap_servers=['kafka-1:9092', 'kafka-2:9092', 'kafka-3:9092'], 
    #         group_id = cache.get("gUser_name"),
    #         # enable_auto_commit='true',
    #         auto_offset_reset='earliest')
    # consumer1.subscribe(topics = cache.get("gSubscriptions"))
    # for msg in consumer1:
    #     return str(json.loads(msg.value))
    msg_pack = consumer1.poll(timeout_ms=20000)
    # return str(msg_pack)
    # consumer1.commit()

    for tp, messages in msg_pack.items():
        print("Message Bundle: ", new_notif, ")", messages)
        # return str(len(messages))
        for message in messages:
            # return str(message.value)
            notif_message = json.loads(message.value)
            # return notif_message
            print("Inside Loop", notif_message)
            if notif_message not in notifications:
                new_notif += 1
                notifications.append(notif_message)

    # consumer1.commit()
    print("Done with loop")
    cache.set("gNewNotifications", new_notif)
    cache.set("gNotifications", notifications)
    return render_template('notifications.html', user_name=cache.get("gUser_name"),
                           message=cache.get("gLatest_message"), notifications=notifications,
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
            # enable_auto_commit='true',
            auto_offset_reset='earliest')
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
        # consumer1.commit()
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
        topic_name = request.form['repo']
        subscriptions_list = cache.get("gSubscriptions")
        subscriptions_list.remove(topic_name)
        # consumer1.commit()
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
