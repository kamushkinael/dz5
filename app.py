import os, redis, json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

# Чтобы Flask видел реальные IP за Nginx/Gunicorn
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Настройа пупупупуп
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
cache = redis.Redis(host='redis', port=6379, db=0)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

# тут содаются таблицы когда мы бахаем воркер
with app.app_context():
    db.create_all()

# тут пути для запросов
@app.route('/items', methods=['GET'])
def get_items():
    cached = cache.get('items_list')
    if cached: 
        return json.loads(cached), 200
    
    items = Item.query.all()
    res = [{"id": i.id, "name": i.name} for i in items]
    cache.setex('items_list', 30, json.dumps(res))
    return jsonify(res), 200

@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400
        
    new_item = Item(name=data['name'])
    db.session.add(new_item)
    db.session.commit()
    cache.delete('items_list')
    return jsonify({"status": "created", "id": new_item.id}), 201

@app.route('/items/<int:id>', methods=['PUT'])
def update_item(id):
    item = Item.query.get_or_404(id)
    data = request.get_json()
    
    if data and 'name' in data:
        item.name = data['name']
        db.session.commit()
        cache.delete('items_list')
        return jsonify({"status": "updated"}), 200
    
    return jsonify({"error": "Invalid data"}), 400

@app.route('/items/<int:id>', methods=['DELETE'])
def delete_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    cache.delete('items_list')
    return jsonify({"status": "deleted"}), 200
