from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient
import os
import requests
import json
import sys
from bson import json_util
import pandas as pd
import numpy as np
import socket

app = Flask(__name__)

client = MongoClient(host='backend_db',
                     port=27017,
                     username='root',
                     password='pass',
                     authSource="admin")
db = client["subscribers_db"]
topics = client["topics_db"]

subscriptions_list = {}
subscriptions_list['neighbours'] = {'backend_broker_1': '5101' ,'backend_broker_2':'5101', 'backend_broker_3':'5101'}
subscriptions_list['subscriptions'] = []

def EN(msg):
    repo = msg['repo']
    if (((repo[0]>='a') & (repo[0]<='h')) | ((repo[0]>='A') & (repo[0]<='H'))):
        return ['backend_broker_1']
    if (((repo[0]>='i') & (repo[0]<='q')) | ((repo[0]>='I') & (repo[0]<='Q'))):
        return ['backend_broker_2']
    if (((repo[0]>='r') & (repo[0]<='z')) | ((repo[0]>='R') & (repo[0]<='Z'))):
        return ['backend_broker_3']

def SN(msg):
    repo = msg['Repo']
    if (((repo[0]>='a') & (repo[0]<='h')) | ((repo[0]>='A') & (repo[0]<='H'))):
        return ['backend_broker_1']
    if (((repo[0]>='i') & (repo[0]<='q')) | ((repo[0]>='I') & (repo[0]<='Q'))):
        return ['backend_broker_2']
    if (((repo[0]>='r') & (repo[0]<='z')) | ((repo[0]>='R') & (repo[0]<='Z'))):
        return ['backend_broker_3']

def get_return_dict(username: str, message: str = ""):
    query = {"username": username}
    doc = db.subscribers_db.find(query)
    subscriptions = []
    if not doc.count():
        subscriptions = []
    else:
        subscriptions = doc[0]['subscriptions']

    return {
        "Message": message,
        "Subscriptions": subscriptions,
        "Publishers": ["GitHub", "BitBucket", "GitLab"]
    }


@app.route('/')
def check1():
    return 'This is broker 1!'

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
    msg = dict(json.loads(request.get_data()))
    username = msg["UserName"]
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
    # send_notifications()
    return get_return_dict(username=username, message=username + " logged in successfully")


@app.route('/logout', methods=['POST'])
def logout_request():
    msg = dict(json.loads(request.get_data()))
    username = msg["UserName"]
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
    # send_notifications()
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
    msg = dict(json.loads(request.get_data()))
    if msg['message_type'] == 'subscribe':
        rvlist = SN(msg)
        # return str("Dale" + socket.gethostname())
        if socket.gethostname() not in rvlist:
            neighbours = subscriptions_list['neighbours']
            # return str(neighbours)
            for i in neighbours.items():
                try:
                    response = requests.post(f'http://{i[0]}:{i[1]}/subscribe', data = json.dumps(msg))
                except requests.exceptions.RequestException as e:
                    # return str(e)
                    return 'Cannot reach server!'
        else:
            username = msg["UserName"]
            owner = msg["Owner"]
            repo = msg["Repo"]
            publisher = msg["Provider"]
            query = {"username": username}
            doc = db.subscribers_db.find(query)
            if doc.count():
                sub_query = {"username": username, "repo": repo}
                sub_doc = db.subscribers_db.find(sub_query)
                if not sub_doc.count():
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
            # send_notifications()
            return get_return_dict(username=username, message=username + " requested access to " + repo + " repo from " + owner)


@app.route('/unsubscribe', methods=['POST'])
def unsubscribe_request():
    msg = dict(json.loads(request.get_data()))
    if(msg['message_type'] == 'unsubscribe'):
        rvlist = SN(msg)
        if socket.gethostname() not in rvlist:
            neighbours = subscriptions_list['neighbours']
            for i in neighbours.items():
                try:
                    response = requests.post(f'http://{i[0]}:{i[1]}/unsubscribe', data = json.dumps(msg))
                except requests.exceptions.RequestException as e:
                    return 'Cannot reach server!'
        else:
            username = msg["UserName"]
            repo = msg["Repo"]
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
            # send_notifications()
            return get_return_dict(username=username, message=username + " unsubscribed for " + repo)

@app.route('/viewtable')
def view_table():
    _items = db.subscribers_db.find()
    items = [item for item in _items]

    return render_template('viewtable.html', items=items)

@app.route('/commits_notifier', methods = ['POST'])
def pub_routing():
    msg = dict(json.loads(request.get_data()))
    if msg['message_type'] == 'publish':
        rvlist = EN(msg)
        if socket.gethostname() not in rvlist:
            neighbours = subscriptions_list['neighbours']
            for i in neighbours.items():
                try:
                    response = requests.post(f'http://{i[0]}:{i[1]}/commits_notifier', data = json.dumps(msg))
                except requests.exceptions.RequestException as e:
                    return 'Cannot reach server!'
            return "Propagated Request!"
        else:
            publisher = msg['publisher']
            owner = msg['owner']
            repo = msg['repo']
            commit_messages = msg['commit_messages']
            
            for i in range(0,len(commit_messages)-1):
                item_doc = {
                    'publisher': publisher,
                    'repo_owner': owner,
                    'repo': repo,
                    'commit_sha': commit_messages[i]['sha'],
                    'commit_author': commit_messages[i]['commit']['author']['name'],
                    'commit_message': commit_messages[i]['commit']['message'],
                    'commit_datetime': commit_messages[i]['commit']['author']['date']
                }
                db.commit_messages_db.insert_one(item_doc)
                if i==0:
                    topic_doc = {
                        'publisher': publisher,
                        'owner': owner,
                        'repo': repo
                    }
                    topic_doc_updated = {"$set": {
                        'last_update': commit_messages[i]['commit']['committer']['date']
                        }
                    }
                    db.topics_db.update_one(topic_doc, topic_doc_updated)
            send_notifications()
            return "Sent Notification!"
    return "Not a publish request!"

def send_notifications():
    subscribers_db = db.subscribers_db
    commit_messages_db = db.commit_messages_db

    sdb = subscribers_db.find()
    cdb = commit_messages_db.find()
    temp_dict = {}
    temp_list = []
    i = 0
    for cursor in cdb:
        temp_dict['publisher'] = cursor['publisher']
        temp_dict['repo_owner'] = cursor['repo_owner']
        temp_dict['repo'] = cursor['repo']
        temp_dict['commit_sha'] = cursor['commit_sha']
        temp_dict['commit_message'] = cursor['commit_message']
        temp_dict['commit_datetime'] = cursor['commit_datetime']
        temp_dict['commit_author'] = cursor['commit_author']
        temp_list.append(temp_dict.copy())
    cmdb = pd.DataFrame(temp_list)

    for cursor in sdb:
        if cursor['online'] == 1:
            ip = cursor['current_ip']
            username = cursor['username']
            subscriptions_list = pd.DataFrame(list(cursor['subscriptions']))
            for index, row in subscriptions_list.iterrows():
                cmdb_filtered = cmdb[(cmdb['publisher'] == row['publisher']) & (cmdb['repo_owner'] == row['owner']) & (cmdb['repo'] == row['repo'])]
                try:
                    idx = cmdb_filtered.index[cmdb_filtered['commit_datetime'] == row['last_update']].tolist()
                    notif = cmdb_filtered.iloc[:idx[0]]
                except IndexError:
                    notif = cmdb_filtered
                notif_json = {}
                notif_json['UserName'] = cursor['username']
                notif_json['Notifications'] = [v for v in notif.to_dict(orient = 'index').values()]

                try:
                    response = requests.post(f'http://{ip}:5003/notifications', data = json.dumps(notif_json))
                except requests.exceptions.RequestException as e:
                    return 'Cannot reach Server'
                
                if len(notif):
                    subscriber_query = {
                        'username': username,
                        'subscriptions.publisher': row['publisher'],
                        'subscriptions.owner': row['owner'],
                        'subscriptions.repo': row['repo'],
                    }
                    subscriber_doc_updated = {"$set": {
                        'subscriptions.$.last_update': notif['commit_datetime'][0]
                        }
                    }
                    db.subscribers_db.update_one(subscriber_query, subscriber_doc_updated)
    return True

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
        response = requests.post('http://' + ip + ':5003/refresh_advertisements', data=json_util.dumps(topics))
    except requests.exceptions.RequestException as e:
        return False
    # send_notifications()
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5101, debug=True)
