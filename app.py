import os

from flask import Flask
from flask import render_template
from gevent.pywsgi import WSGIServer

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    ip = '0.0.0.0'
    app.debug = True
    http = WSGIServer((ip, port), app)
    print 'Listening at http://{ip}:{port}'.format(ip=ip, port=port)
    http.serve_forever()
