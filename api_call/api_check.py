import requests
import os
import json
import pymongo
from flask import Flask
import time

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

    timeout = time.time() + 300

    while(time.time() <= timeout):
        cursor = topics_db.find({})
        for document in cursor:
            publisher = document['publisher'].lower()
            if(publisher == 'github'):
                owner = document['owner'].lower()
                repo = document['repo'].lower()
                last_update = document['last_update']
                query_url = f"https://api.github.com/repos/{owner}/{repo}/commits?since={last_update}"
                
                r = requests.get(query_url)
                commit_messages = r.json()
                # with open('checkfile.json') as f:
                #     commit_messages = json.load(f)
                db_push_dict =  {}
                db_push_dict['publisher'] = publisher
                db_push_dict['owner'] = owner
                db_push_dict['repo'] = repo
                db_push_dict['commit_messages'] = commit_messages
                # db_push_json = json.dumps(db_push_dict)

                try:
                    response = requests.post(f'http://backend_middle_1:5001/commits_notifier', data = db_push_dict)
                except requests.exceptions.RequestException as e:
                    print('Cannot reach Server\n')
        break
    # time.sleep(60)
    client.close()
    return 'This is done!'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)