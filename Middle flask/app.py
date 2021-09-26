from flask import Flask

app =  Flask(__name__)

@app.route('/')
def check1():
    return 'Hello mic testing 1,2,3!'

@app.route('/middle', methods = ['GET'])
def middle_check():
    return 'You have reached middle!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 5001, debug = True)