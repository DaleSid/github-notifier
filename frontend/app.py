from flask import Flask, request, render_template
import requests

app = Flask(__name__)


@app.route('/')
def form_center():
    return render_template('form.html')


@app.route('/', methods=['POST'])
def my_form_post():
    payload = dict()
    payload["UserName"] = request.form['username']
    payload["Owner"] = request.form['owner']
    payload["Repo"] = request.form['repo']

    try:
        response = requests.post('http://backend_middle_1:5001/middle', data = payload)
    except requests.exceptions.RequestException as e:
        return 'Cannot reach Server\n'

    return str(payload) + "<br>Entry Successfully Sent" + response.text


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
