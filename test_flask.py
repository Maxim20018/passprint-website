#!/usr/bin/env python3
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Serveur fonctionne correctement!'

if __name__ == '__main__':
    print('Flask fonctionne correctement')
    app.run(host='0.0.0.0', port=5000, debug=True)