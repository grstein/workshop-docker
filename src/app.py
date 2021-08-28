from flask import Flask

import redis #4
import os # 1

redis_cache = redis.Redis(host='redis', port=6379, db=0, password="") #5

app = Flask(__name__)

appname = os.getenv('APP_NAME') #2

@app.route("/")
def hello_world():
    return f"<p>Hello, World from {appname}!</p>" #3

# Comando SET no REDIS #6
@app.route('/set/<string:key>/<string:value>')
def set(key, value):
	if redis_cache.exists(key):
		return f"{appname}: {key} já existe"
	else:
		redis_cache.set(key, value)
		return f"{appname}: registrado no REDIS"

# Comando GET no REDIS #7
@app.route('/get/<string:key>')
def get(key):
	if redis_cache.exists(key):
		return f"{appname}: {redis_cache.get(key)}"
	else:
		return f"{appname}: {key} não existe"