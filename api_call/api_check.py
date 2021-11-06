import requests
import os
import json
import pymongo
from flask import Flask
import time
import random

app = Flask(__name__)

@app.route('/')
def api_pull_to_db():
    client = pymongo.MongoClient(host='backend_db',
                        port=27017,
                        username='root',
                        password='pass',
                        authSource="admin")
    db = client.subscribers_db
    topics_db = db.topics_db

    timeout = time.time() + 1200

    while(time.time() <= timeout):
        cursor = topics_db.find({})
        for document in cursor:
            publisher = document['publisher']
            if(publisher == 'GitHub'):
                owner = document['owner']
                repo = document['repo']
                last_update = document['last_update']
                query_url = f"https://api.github.com/repos/{owner}/{repo}/commits?since={last_update}"
                
                r = requests.get(query_url, headers={'Authorization': 'Bearer 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'})
                commit_messages = r.json()

                if 'documentation_url' in commit_messages:
                    return 'API Limit exceeded!'

                # with open('checkfile.json') as f:
                #     commit_messages = json.load(f)

                db_push_dict =  {}
                db_push_dict['message_type'] = 'publish'
                db_push_dict['publisher'] = publisher
                db_push_dict['owner'] = owner
                db_push_dict['repo'] = repo
                db_push_dict['commit_messages'] = commit_messages

                if len(commit_messages):
                    # db_push_json = json.dumps(db_push_dict)
                    try:
                        brokers = {'backend_broker_1':'5101', 'backend_broker_2':'5101', 'backend_broker_3':'5101'}
                        # brokers = {'backend_broker_1':'5101'}
                        broker_add = random.choice(list(brokers.keys()))
                        response = requests.post(f'http://{broker_add}:{brokers[broker_add]}/commits_notifier', data = json.dumps(db_push_dict))
                    except requests.exceptions.RequestException as e:
                        return str(e)
                        # return 'Cannot reach server!'
                    # return str(db_push_dict)
                    # return response.text
        time.sleep(60)
    client.close()
    return 'This is done!'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)