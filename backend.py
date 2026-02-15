from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup
DATABASE = 'uzmarket.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price INTEGER NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            phone TEXT NOT NULL,
            seller_name TEXT NOT NULL,
            image TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT NOT NULL
        )
    ''')
    
    # Insert default admin password if not exists
    cursor.execute('SELECT COUNT(*) FROM admins')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO admins (password) VALUES (?)', ('Behruzseller2010uzGlobal',))
    
    # Insert demo product if database is empty
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO products (user_id, title, description, price, category, location, phone, seller_name, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'demo',
            'iPhone 15 Pro Max 256GB',
            'Yangi, karobkada. Barcha aksessuarlar bilan. Garantiya 1 yil.',
            18500000,
            'electronics',
            'Toshkent, Yunusobod',
            '+998 90 123 45 67',
            'Jamshid',
            'https://images.unsplash.com/photo-1632661674596-df8be070a5c5?w=600&h=600&fit=crop'
        ))
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    return jsonify({
        'status': 'success',
        'message': 'UzMarket Backend API ishlamoqda! ✅',
        'version': '1.0'
    })

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'id': row['id'],
                'userId': row['user_id'],
                'title': row['title'],
                'description': row['description'],
                'price': row['price'],
                'category': row['category'],
                'location': row['location'],
                'phone': row['phone'],
                'sellerName': row['seller_name'],
                'image': row['image'],
                'date': row['created_at']
            })
        
        conn.close()
        return jsonify({
            'status': 'success',
            'products': products
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/products', methods=['POST'])
def add_product():
    """Add a new product"""
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO products (user_id, title, description, price, category, location, phone, seller_name, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['userId'],
            data['title'],
            data['description'],
            data['price'],
            data['category'],
            data['location'],
            data['phone'],
            data['sellerName'],
            data['image']
        ))
        
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'E\'lon qo\'shildi!',
            'productId': product_id
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE products 
            SET title = ?, description = ?, price = ?, category = ?, 
                location = ?, phone = ?, seller_name = ?, image = ?
            WHERE id = ?
        ''', (
            data['title'],
            data['description'],
            data['price'],
            data['category'],
            data['location'],
            data['phone'],
            data['sellerName'],
            data['image'],
            product_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'E\'lon yangilandi!'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'E\'lon o\'chirildi!'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    try:
        data = request.get_json()
        password = data.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM admins LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        
        if row and row['password'] == password:
            return jsonify({
                'status': 'success',
                'message': 'Admin login muvaffaqiyatli!'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Parol noto\'g\'ri!'
            }), 401
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Total products
        cursor.execute('SELECT COUNT(*) as count FROM products')
        total = cursor.fetchone()['count']
        
        # Today's products
        cursor.execute('''
            SELECT COUNT(*) as count FROM products 
            WHERE DATE(created_at) = DATE('now')
        ''')
        today = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total': total,
                'today': today
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 UzMarket Backend Server ishga tushmoqda...")
    print("=" * 50)
    print("📡 Server manzili: http://localhost:5000")
    print("🔥 Frontend uchun: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)