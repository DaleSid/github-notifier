from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import os
import requests
import json

app = Flask(__name__)

client = MongoClient(host='backend_db',
                        port=27017, 
                        username='root', 
                        password='pass',
                    authSource="admin")
db = client["subscribers_db"]

@app.route('/')
def check1():
    return 'Hello mic testing 1,2,3!'


@app.route('/middle', methods=['POST'])
def middle_check():
    username = request.form["UserName"]
    owner = request.form["Owner"]
    repo = request.form["Repo"]
    item_doc = {
        'username': username,
        'owner': owner,
        'repo': repo
    }
    db.subscribers_db.insert_one(item_doc)
    print("Checkpoint reached!\n")

    return "<br>" + username + " requested access to " + repo + " repo from " + owner
    
@app.route('/viewtable')
def view_table():
    _items = db.subscribers_db.find()
    items = [item for item in _items]

    return render_template('viewtable.html', items = items)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
