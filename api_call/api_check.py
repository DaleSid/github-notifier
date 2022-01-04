import requests
import os
import json
import pymongo
from flask import Flask, request, render_template, redirect, url_for
from kafka import KafkaProducer
import time
import random
import json

app = Flask(__name__)

def reset_topics_json():
    with open('topics.json') as topics_file:
        topics_data = json.load(topics_file)
    for index, _ in enumerate(topics_data['topics']):
        topics_data['topics'][index]['last_update'] = "2000-01-01T00:00:00Z"
    with open('topics.json', 'w') as topics_file:
        json.dump(topics_data, topics_file, indent=4, sort_keys=True)

def json_serializer(data):
    return json.dumps(data).encode("utf-8")

@app.route('/addtopics')
def add_topics_form():
    return render_template('addtopics.html', publishers=['GitHub', 'BitBucket', 'GitLab'])

@app.route('/addtopics', methods=['POST'])
def add_topics():
    payload = dict()
    payload["owner"] = request.form['owner']
    payload["repo"] = request.form['repo']
    payload["publisher"] = request.form['publisher']
    payload["last_update"] = "2000-01-01T00:00:00Z"

    with open('topics.json') as topics_file:
        topics_data = json.load(topics_file)
    topics_data['topics'].append(payload)
    with open('topics.json', 'w') as topics_file:
        json.dump(topics_data, topics_file, indent=4, sort_keys=True)
    
    return redirect(url_for('add_topics_form'))

@app.route('/refresh')
def refresh_topics_json():
    reset_topics_json()
    return "topics.json refreshed"

@app.route('/')
def api_pull_to_db():
    producer = KafkaProducer(bootstrap_servers=['kafka-1:9092', 'kafka-2:9092', 'kafka-3:9092'], value_serializer=json_serializer)

    timeout = time.time() + 1200

    while(time.time() <= timeout):
        topics_data: dict = {}
        with open('topics.json') as topics_file:
            topics_data = json.load(topics_file)

        topic_commits: dict = {}
        for index, topic in enumerate(topics_data['topics']):
            publisher = topic['publisher']
            if(publisher == 'GitHub'):
                owner = topic['owner']
                repo = topic['repo']
                last_update = topic['last_update']

                topic_name = publisher + "_" + owner + "_" + repo

                query_url = f"https://api.github.com/repos/{owner}/{repo}/commits?since={last_update}"
                
                r = requests.get(query_url, headers={'Authorization': 'Bearer `insert github access token`'})
                commit_messages = r.json()

                if 'documentation_url' in commit_messages:
                    return 'API Limit exceeded!'

                current_topic_commits: list = []
                for message in commit_messages:
                    new_message: dict = {}
                    new_message['publisher'] = publisher
                    new_message['repo_owner'] = owner
                    new_message['repo'] = repo
                    new_message['commit_sha'] = message['sha']
                    new_message['commit_datetime'] = message['commit']['author']['date']
                    new_message['commit_author'] = message['commit']['author']['name']
                    new_message['commit_message'] = message['commit']['message']

                    current_topic_commits.append(new_message)

                if len(current_topic_commits) > 1:
                    topic_commits[topic_name] = current_topic_commits
                    last_update = topic_commits[topic_name][0]['commit_datetime']
                    topics_data['topics'][index]['last_update'] = last_update


        print("Topic Commits: \n", json.dumps(topic_commits, indent=4, sort_keys=True))

        for topic_name in topic_commits.keys():
            producer.send(topic_name, {"Commits": topic_commits[topic_name]})
            continue

        print("Dumping Data to file", topics_data)
        with open('topics.json', 'w') as topics_file:
            json.dump(topics_data, topics_file, indent=4, sort_keys=True)
        

        time.sleep(60)
    return 'This is done!'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)
