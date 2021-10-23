from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient
import os
import requests
import json
import sys
from bson import json_util

app = Flask(__name__)

client = MongoClient(host='backend_db',
                     port=27017,
                     username='root',
                     password='pass',
                     authSource="admin")
db = client["subscribers_db"]
topics = client["topics_db"]


def get_return_dict(username: str, message: str = ""):
    query = {"username": username}
    doc = db.subscribers_db.find(query)

    return {
        "Message": message,
        "Subscriptions": doc[0]['subscriptions'],
        "Publishers": ["GitHub", "BitBucket", "GitLab"]
    }


@app.route('/')
def check1():
    return 'Hello mic testing 1,2,3!'

@app.route('/register')
def register_form():
    return render_template('register.html', message="Register Here for publishing!")

@app.route('/advertise')
def advertise_form():
    query = {"advertise": 0}
    doc = db.topics_db.find(query)
    items = []
    for i in doc:
        items.append(i)
    return render_template('advertise.html', message="Select Topics to advertise!", items=items)

@app.route('/deadvertise')
def deadvertise_form():
    query = {"advertise": 1}
    doc = db.topics_db.find(query)
    items = []
    for i in doc:
        items.append(i)
    return render_template('deadvertise.html', message="Select Topics to deadvertise!", items=items)

@app.route('/login', methods=['POST'])
def login_request():
    username = request.form["UserName"]
    query = {"username": username}
    doc = db.subscribers_db.find(query)
    if doc.count():
        newvalues = {
            "$set": {
                "online": 1,
                "current_ip": request.remote_addr
            }
        }
        db.subscribers_db.update_one(query, newvalues)
    else:
        item_doc = {
            'username': username,
            'online': 1,
            'subscriptions': [],
            'current_ip': request.remote_addr
        }
        db.subscribers_db.insert_one(item_doc)
    refresh_advertisements()
    return get_return_dict(username=username, message=username + " logged in successfully")


@app.route('/logout', methods=['POST'])
def logout_request():
    username = request.form["UserName"]
    query = {"username": username}
    doc = db.subscribers_db.find(query)
    if doc.count():
        newvalues = {
            "$set": {
                "online": 0,
                "current_ip": request.remote_addr
            }
        }
        db.subscribers_db.update_one(query, newvalues)

    return get_return_dict(username=username, message=username + " logged out successfully")


def update_topics(publisher, owner, repo):
    query = {"publisher": publisher, "owner": owner, "repo": repo}
    doc = db.topics_db.find(query)
    if doc.count() == 0:
        query["last_update"] = "2000-01-01T00:00:00Z"
        query["advertise"] = 0
        db.topics_db.insert_one(query)


@app.route('/subscribe', methods=['POST'])
def subscription_request():
    username = request.form["UserName"]
    owner = request.form["Owner"]
    repo = request.form["Repo"]
    publisher = request.form["Provider"]
    query = {"username": username}
    doc = db.subscribers_db.find(query)
    if doc.count():
        newvalues = {
            "$push": {
                "subscriptions": {
                    "publisher": publisher,
                    "owner": owner,
                    "repo": repo,
                    "last_update": "2000-01-01T00:00:00Z"
                }
            },
            "$set": {
                "current_ip": request.remote_addr,
                "online": 1
            }
        }
        db.subscribers_db.update_one(query, newvalues)
    else:
        item_doc = {
            'username': username,
            'online': 1,
            'subscriptions': [
                {
                    'publisher': publisher,
                    'owner': owner,
                    'repo': repo,
                    'last_update': "2000-01-01T00:00:00Z",
                    'current_ip': request.remote_addr
                }
            ]
        }
        db.subscribers_db.insert_one(item_doc)

    update_topics(publisher, owner, repo)

    return get_return_dict(username=username, message=username + " requested access to " + repo + " repo from " + owner)


@app.route('/unsubscribe', methods=['POST'])
def unsubscribe_request():
    username = request.form["UserName"]
    repo = request.form["Repo"]
    query = {"username": username}
    doc = db.subscribers_db.find(query)
    if doc.count():
        deleteValue = {
            "$pull": {
                'subscriptions': {
                    'repo': repo
                }
            }
        }
        db.subscribers_db.update_one(query, deleteValue)

    return get_return_dict(username=username, message=username + " unsubscribed for " + repo)


@app.route('/register', methods=['POST'])
def registration_request():
    publisher_name = request.form["publisher"]
    hostname = request.form["hostname"]
    payload = {"publisher": publisher_name}
    doc = db.publishers_db.find(payload)
    if doc.count() == 0:
        payload["hostname"] = hostname
        db.topics_db.insert_one(payload)
    else:
        newvalues = {
            "$set": {
                "hostname": hostname
            }
        }
        db.subscribers_db.update_one(payload, newvalues)

    try:
        response = requests.post('http://' + hostname + ':5002/start_server', data=payload)
    except requests.exceptions.RequestException as e:
        return "Registration for " + publisher_name + " is failed"

    return "Registration for " + publisher_name + " is successful"

def refresh_advertisement_send_request(ip: str, topics: dict):
    try:
        response = requests.post('http://' + ip + ':5000/refresh_advertisements', data=json_util.dumps(topics))
    except requests.exceptions.RequestException as e:
        return False
    return True

def refresh_advertisements():
    topics: dict = {"Topics": []}
    topics["Topics"] = list(db.topics_db.find())

    query = {"online": 1}
    doc = db.subscribers_db.find(query)
    ret_val = False
    for subscriber in doc:
        ip = subscriber["current_ip"]
        ret_val = refresh_advertisement_send_request(ip, topics)
        if not ret_val:
            temp_query = {"username": subscriber["username"]}
            newvalues = {
                "$set": {
                    "online": 0
                }
            }
            db.subscribers_db.update_one(temp_query, newvalues)
    return ret_val
            


@app.route('/advertise', methods=['POST'])
def advertise_request():
    topic_to_advertise = request.form["topic"]
    payload = {"repo": topic_to_advertise}
    doc = db.topics_db.find(payload)
    if doc.count():
        newvalues = {
            "$set": {
                "advertise": 1
            }
        }
        db.topics_db.update_one(payload, newvalues)
    ret_val = refresh_advertisements()
    return redirect(url_for('advertise_form'))

@app.route('/deadvertise', methods=['POST'])
def deadvertise_request():
    print('It is working',file=sys.stderr)
    topic_to_deadvertise = request.form["topic"]
    payload = {"repo": topic_to_deadvertise}
    doc = db.topics_db.find(payload)
    if doc.count():
        newvalues = {
            "$set": {
                "advertise": 0
            }
        }
        db.topics_db.update_one(payload, newvalues)
    ret_val = refresh_advertisements()
    return redirect(url_for('deadvertise_form'))


@app.route('/viewtable')
def view_table():
    _items = db.subscribers_db.find()
    items = [item for item in _items]

    return render_template('viewtable.html', items=items)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
