from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_ultra_secreta_lojamix'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lojamix.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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

# --- ROTAS ---
@app.route('/')
def home():
    # Cria produtos APENAS se não existirem
    if not Product.query.first():
        roupas = [
            Product(name="Camiseta Oversized Thunder", price=89.90, image="image.png", category="Streetwear", description="Algodão premium com corte largo."),
            Product(name="Bermuda Sarja Side Stripe", price=119.90, image="image2.png", category="Casual", description="Conforto e estilo para o verão."),
            Product(name="Jaqueta Bomber Preta", price=259.90, image="https://images.unsplash.com/photo-1551028919-ac7bcb5fb8eb?w=500", category="Casacos", description="Essencial para dias frios."),
            Product(name="Vestido Midi Floral", price=149.90, image="https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=500", category="Feminino", description="Elegância natural."),
            Product(name="Boné Minimalist", price=59.90, image="https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=500", category="Acessórios", description="O toque final no look."),
            Product(name="Tênis Urban White", price=299.00, image="https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500", category="Calçados", description="Design moderno e leve."),
        ]
        db.session.add_all(roupas)
        db.session.commit()
    
    produtos = Product.query.all()
    return render_template('index.html', produtos=produtos)

@app.route('/perfil')
def perfil():
    # Simulação de dados de usuário para não dar erro se não estiver logado
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
    # Carrinho simulado (visual)
    itens_carrinho = [
        {'name': 'Camiseta Oversized Thunder', 'price': 89.90, 'image': 'image.png', 'qtd': 1},
    ]
    total = sum(item['price'] * item['qtd'] for item in itens_carrinho)
    return render_template('carrinho.html', itens=itens_carrinho, total=total)

@app.route('/adicionar/<int:id>')
def adicionar(id):
    # Apenas redireciona por agora
    return redirect(url_for('carrinho'))

@app.route('/login')
def login():
    return render_template('login.html') # Precisarias criar este arquivo, ou redireciona home

if __name__ == '__main__':
    with app.app_context():
        # Limpa tudo e recria para evitar erros de coluna
        db.drop_all()
        db.create_all()
        print(">>> SISTEMA PRONTO: Base de dados atualizada e sem erros.")
        
    app.run(debug=True)