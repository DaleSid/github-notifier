from flask import Flask, request, jsonify
import requests
import json

app =  Flask(__name__)

@app.route('/')
def check1():
    return 'Hello mic testing 1,2,3!'

@app.route('/middle', methods = ['POST'])
def middle_check():
    username = request.form["UserName"]
    owner = request.form["Owner"]
    repo = request.form["Repo"]

    print("Checkpoint reached!\n")

    return "<br>" + username + " requested access to " + repo + " repo from " + owner

if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 5001, debug = True)