from flask import Flask
app = Flask(__name__)

import requests

@app.route('/')
def check():
    return 'Hello, I am client end!'

@app.route('/client')
def client_side():
    ping = 'Client'

    response = ''
    try:
        response = requests.get('http://middle-flask-container:5001/middle')
    except requests.exceptions.RequestException as e:
        print('\n Cannot reach the pong service.')
        return 'Cannot reach\n'

    return response.text

if __name__ == "__main__":
    app.run(host ='0.0.0.0', port = 5000, debug = True)