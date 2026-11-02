from flask import Flask, render_template_string, redirect, Response, request
import docker, threading
from guardian import safe_update, logger
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
client = docker.from_env()
USERNAME = 'admin'
PASSWORD_HASH = generate_password_hash('guardian123') 

HTML_TEMPLATE = """
<!DOCTYPE html><html><head><title>Docker Guardian</title><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#121212;color:#e0e0e0;font-family:sans-serif;padding:20px}h1{color:#FFD700;text-align:center}.card{background:#1e1e1e;border-radius:12px;padding:20px;margin-bottom:20px;border-left:6px solid #4CAF50;display:flex;justify-content:space-between;align-items:center}.name{font-weight:bold;font-size:1.3em;color:#fff}.status{color:#4CAF50;font-size:0.9em;font-weight:bold}.image{font-family:monospace;color:#64B5F6;margin-top:5px}.btn{background:#333;color:#fff;border:1px solid #FFD700;padding:10px 15px;border-radius:5px;cursor:pointer}</style></head>
<body><h1>🛡️ Docker Guardian</h1>
{% for c in containers %}
<div class="card"><div><div class="name">📦 {{ c.name }}</div><div class="status">● {{ c.status.upper() }}</div><div class="image">{{ c.image.tags[0] if c.image.tags else 'none' }}</div></div>
<button class="btn" onclick="updateContainer('{{ c.name }}')">Update</button></div>
{% endfor %}
<script>function updateContainer(name) { if(confirm("Update " + name + "?")) { window.location.href = "/update/" + name; } }</script>
</body></html>
"""

def check_auth():
    auth = request.authorization
    return auth and auth.username == USERNAME and check_password_hash(PASSWORD_HASH, auth.password)

@app.route('/')
def index():
    if not check_auth(): return Response('Login Required', 401, {'WWW-Authenticate': 'Basic realm="Login"'})
    return render_template_string(HTML_TEMPLATE, containers=client.containers.list())

@app.route('/update/<name>')
def update(name):
    if not check_auth(): return Response('Login Required', 401, {'WWW-Authenticate': 'Basic realm="Login"'})
    try:
        c = client.containers.get(name)
        image = c.image
        repo, tag = image.tags[0].split(':') if ':' in image.tags[0] else (image.tags[0], 'latest')
        new_image = client.images.pull(repo, tag=tag)
        if new_image.id != image.id: threading.Thread(target=safe_update, args=(client, c, new_image)).start()
    except Exception as e: logger.error(e)
    return redirect('/')

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)