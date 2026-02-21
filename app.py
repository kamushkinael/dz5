import os, redis, json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# База настройка
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
cache = redis.Redis(host='redis', port=6379, db=0)

# Моделька бдшки (или базки)
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

# Здесь типа создаютсся таблицы
with app.app_context():
    db.create_all()

@app.route('/items', methods=['GET'])
def get_items():
    # 1. Проверка redis
    cached = cache.get('items_list')
    if cached: return json.loads(cached), 200
    
    # 2. Если каким-то макаром нет redis, то топаем в Postgres
    items = Item.query.all()
    res = [{"id": i.id, "name": i.name} for i in items]
    
    # 3. Сохрананение redis на 30 сек
    cache.setex('items_list', 30, json.dumps(res))
    return jsonify(res), 200

@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    new_item = Item(name=data['name'])
    db.session.add(new_item)
    db.session.commit()
    cache.delete('items_list') # тут сброс кеша
    return jsonify({"status": "created"}), 201

@app.route('/items/<int:id>', methods=['PUT', 'DELETE'])
def update_delete(id):
    item = Item.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(item)
    else:
        item.name = request.json.get('name', item.name)
    
    db.session.commit()
    cache.delete('items_list')
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0')
