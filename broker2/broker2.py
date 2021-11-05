from flask import Flask, request
from pymongo import MongoClient
import requests
import json
import pandas as pd
import numpy as np

app = Flask(__name__)

client = MongoClient(host='backend_db',
                     port=27017,
                     username='root',
                     password='pass',
                     authSource="admin")
db = client["subscribers_db"]
topics = client["topics_db"]

subscriptions_list = {}
subscriptions_list['neighbours'] = {'backend_broker1_1':'5101', 'backend_broker3_1':'5103'}
subscriptions_list['subscriptions'] = []

def EN(msg):
    repo = msg['repo']
    if ((repo[0]>='a') & (repo[0]<='h')):
        return ['5101']
    if ((repo[0]>='i') & (repo[0]<='q')):
        return ['5102']
    if ((repo[0]>='r') & (repo[0]<='z')):
        return ['5103']

def SN(msg):
    repo = msg['Repo']
    if ((repo[0]>='a') & (repo[0]<='h')):
        return ['5101']
    if ((repo[0]>='i') & (repo[0]<='q')):
        return ['5102']
    if ((repo[0]>='r') & (repo[0]<='z')):
        return ['5103']

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

def update_topics(publisher, owner, repo):
    query = {"publisher": publisher, "owner": owner, "repo": repo}
    doc = db.topics_db.find(query)
    if doc.count() == 0:
        query["last_update"] = "2000-01-01T00:00:00Z"
        query["advertise"] = 0
        db.topics_db.insert_one(query)

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
    return 'This is broker 2!'

@app.route('/commits_notifier', methods=['POST'])
def pub_routing():
    msg = dict(json.loads(request.get_data()))
    if msg['message_type'] == 'publish':
        rvlist = EN(msg)
        if '5102' not in rvlist:
            neighbours = subscriptions_list['neighbours']
            for i in neighbours.items():
                try:
                    response = requests.post(f'http://{i[0]}:{i[1]}/commits_notifier', data = json.dumps(msg))
                except requests.exceptions.RequestException as e:
                    return 'Cannot reach server!'
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
            # send_notifications()

@app.route('/subscribe', methods=['POST'])
def subscription_request():
    msg = dict(json.loads(request.get_data()))
    if msg['message_type'] == 'subscribe':
        rvlist = SN(msg)
        return str(rvlist)
        if '5102' not in rvlist:
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
        if '5102' not in rvlist:
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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5102, debug=True)