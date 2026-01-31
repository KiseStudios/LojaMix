from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user
import os
import re
import unicodedata

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_ultra_secreta_lojamix'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lojamix.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def slugify(value):
    """Simplifica uma string para usar em URLs."""
    if not value:
        return ""
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)

app.jinja_env.filters['slugify'] = slugify

# --- MODELOS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100)) 
    email = db.Column(db.String(100))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    image = db.Column(db.String(200)) 
    category = db.Column(db.String(50))
    description = db.Column(db.String(200))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- POPULAÇÃO INICIAL ---
def popular_banco():
    if not Product.query.first():
        roupas = [
            Product(name="Camiseta Oversized Thunder", price=89.90, image="image.png", category="Masculino", description="Algodão premium com corte largo."),
            Product(name="Bermuda Sarja Side Stripe", price=119.90, image="image2.png", category="Masculino", description="Conforto e estilo para o verão."),
            Product(name="Jaqueta Bomber Preta", price=259.90, image="https://images.unsplash.com/photo-1551028919-ac7bcb5fb8eb?w=500", category="Masculino", description="Essencial para dias frios."),
            Product(name="Vestido Midi Floral", price=149.90, image="https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=500", category="Feminino", description="Elegância natural."),
            Product(name="Boné Minimalist", price=59.90, image="https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=500", category="Acessórios", description="O toque final no look."),
            Product(name="Tênis Urban White", price=299.00, image="https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500", category="Acessórios", description="Design moderno e leve."),
        ]
        db.session.add_all(roupas)
        db.session.commit()
        print(">>> Base de dados populada.")

# --- ROTAS ---
@app.route('/')
def home():
    produtos = Product.query.all()
    return render_template('index.html', produtos=produtos)

@app.route('/masculino')
def masculino():
    return redirect(url_for('ver_categoria', slug='masculino'))

@app.route('/feminino')
def feminino():
    return redirect(url_for('ver_categoria', slug='feminino'))

@app.route('/acessorios')
def acessorios():
    return redirect(url_for('ver_categoria', slug='acessorios'))

@app.route('/colecoes')
def colecoes():
    return redirect(url_for('categorias'))

@app.route('/categoria/<slug>')
def ver_categoria(slug):
    categories = db.session.query(Product.category).distinct().all()
    for (cat_name,) in categories:
        if slugify(cat_name) == slug:
            produtos = Product.query.filter_by(category=cat_name).all()
            return render_template('categoria.html', titulo=cat_name, produtos=produtos)
    return f"Categoria '{slug}' não encontrada", 404

@app.route('/categorias')
def categorias():
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('categorias.html', categories=categories)

@app.route('/perfil')
def perfil():
    user_data = {
        'nome': 'Visitante VIP',
        'email': 'cliente@exemplo.com',
        'pedidos': 2
    }
    if current_user.is_authenticated:
        user_data['nome'] = current_user.username
    
    return render_template('perfil.html', user=user_data)

@app.route('/carrinho')
def carrinho():
    itens = [
        {'name': 'Camiseta Oversized Thunder', 'price': 89.90, 'image': 'image.png', 'qtd': 1},
    ]
    total = sum(item['price'] * item['qtd'] for item in itens)
    return render_template('carrinho.html', itens=itens, total=total)

@app.route('/adicionar/<int:id>')
def adicionar(id):
    return redirect(url_for('carrinho'))

@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        popular_banco()
        print(">>> SISTEMA PRONTO: Base de dados atualizada e sem erros.")
        
    app.run(debug=True)
