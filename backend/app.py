from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import os
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

    return get_return_dict(username=username, message=username + " logged in successfully")


def update_topics(publisher, owner, repo):
    query = {"publisher": publisher, "owner": owner, "repo": repo}
    doc = db.topics_db.find(query)
    if doc.count() == 0:
        query["last_update"] = "2000-01-01T00:00:00Z"
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
                    "last_update": "0"
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
                    'last_update': "0",
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

@app.route('/viewtable')
def view_table():
    _items = db.subscribers_db.find()
    items = [item for item in _items]

    return render_template('viewtable.html', items=items)

@app.route('/commits_notifier', methods=['POST'])
def commit_notif_push():
    msg = dict(request.get_json())

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
        # if i==0:
        #     topic_doc = {
        #         'publisher': publisher,
        #         'repo_owner': owner,
        #         'repo': repo
        #     }
        #     topic_doc_updated = {"$set": {
        #         'last_update': commit_messages[i]['commit']['committer']['date']
        #         }
        #     }
        #     db.repos_tb.update_one(topic_doc, topic_doc_updated)

    subscribers_db = db.subscribers_db
    commit_messages_db = db.commit_messages_db

    sdb = subscribers_db.find({})
    cmdb = pd.DataFrame(list(commit_messages_db.find({})))

    for cursor in sdb:
        if cursor['online'] == 1:
            ip = cursor['current_ip']
            subscriptions_list = pd.DataFrame(list(cursor['subscriptions']))
            for index, row in subscriptions_list.iterrows():
                cmdb_filtered = cmdb[((cmdb['publisher'] == row['publisher']) & (cmdb['repo_owner'] == row['owner']) & (cmdb['repo'] == row['repo']))]
                idx = np.where(cmdb_filtered['commit_datetime'] == row['last_update'])
                notif = cmdb_filtered.iloc[:idx,:]
                try:
                    response = requests.post(f'http://frontend_1:5000/notifications', json = notif.to_dict(orient = 'index'))
                except requests.exceptions.RequestException as e:
                    return 'Cannot reach Server\n'


    return 'commit_notifier_completed!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)