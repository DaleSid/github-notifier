from flask import Flask, jsonify
import pymongo

app = Flask(__name__)

@app.route("/")
def ping_server():
    return "Hello World"

def main():
    print("Hello World!")

if __name__ == "__main__":
    main()
    app.run(host='0.0.0.0', port=5000)
