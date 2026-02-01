from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
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

# --- FUNÇÃO AUXILIAR ---
def slugify(value):
    if not value: return ""
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)

app.jinja_env.filters['slugify'] = slugify

# --- MODELOS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))
    orders = db.relationship('Order', backref='buyer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    image = db.Column(db.String(200)) 
    category = db.Column(db.String(50))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float)
    items_description = db.Column(db.String(500))
    
    # NOVOS CAMPOS PARA FICAR PROFISSIONAL
    status = db.Column(db.String(50), default='Aguardando Pagamento') # Ex: Pago, Enviado
    payment_method = db.Column(db.String(50)) # Pix, Cartão
    address_city = db.Column(db.String(100))
    address_street = db.Column(db.String(200))
    address_zip = db.Column(db.String(20))
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROTAS BÁSICAS ---
@app.route('/')
def home():
    if not Product.query.first():
        roupas = [
            Product(name="Camiseta Oversized Thunder", price=89.90, image="image.png", category="Masculino"),
            Product(name="Bermuda Sarja Side Stripe", price=119.90, image="image2.png", category="Masculino"),
            Product(name="Jaqueta Bomber Preta", price=259.90, image="https://images.unsplash.com/photo-1551028919-ac7bcb5fb8eb?w=500", category="Masculino"),
            Product(name="Vestido Midi Floral", price=149.90, image="https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=500", category="Feminino"),
            Product(name="Tênis Urban White", price=299.00, image="https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500", category="Acessórios"),
        ]
        db.session.add_all(roupas)
        db.session.commit()
    produtos = Product.query.all()
    return render_template('index.html', produtos=produtos)

@app.route('/masculino')
def masculino(): return redirect(url_for('ver_categoria', slug='masculino'))
@app.route('/feminino')
def feminino(): return redirect(url_for('ver_categoria', slug='feminino'))
@app.route('/acessorios')
def acessorios(): return redirect(url_for('ver_categoria', slug='acessorios'))

@app.route('/categoria/<slug>')
def ver_categoria(slug):
    categories = db.session.query(Product.category).distinct().all()
    for (cat_name,) in categories:
        if slugify(cat_name) == slug:
            produtos = Product.query.filter_by(category=cat_name).all()
            return render_template('categoria.html', titulo=cat_name, produtos=produtos)
    return "Categoria não encontrada", 404

@app.route('/categorias')
def categorias():
    categories = db.session.query(Product.category).distinct().all()
    return render_template('categorias.html', categories=[c[0] for c in categories])

@app.route('/colecoes')
def colecoes(): return render_template('colecoes.html')

# --- LOGIN/LOGOUT ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('perfil'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            # Se tiver algo no carrinho, vai para o checkout, senão vai pro perfil
            if session.get('cart'):
                return redirect(url_for('checkout'))
            return redirect(url_for('perfil'))
        flash('Email ou senha incorretos.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    if User.query.filter_by(email=request.form.get('email')).first():
        flash('Email já cadastrado.', 'error')
        return redirect(url_for('login'))
    new_user = User(username=request.form.get('username'), email=request.form.get('email'))
    new_user.set_password(request.form.get('password'))
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    if session.get('cart'): return redirect(url_for('checkout'))
    return redirect(url_for('perfil'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/perfil')
@login_required
def perfil():
    meus_pedidos = Order.query.filter_by(user_id=current_user.id).order_by(Order.date_created.desc()).all()
    return render_template('perfil.html', user=current_user, pedidos=meus_pedidos)

# --- CARRINHO E CHECKOUT PROFISSIONAL ---

@app.route('/carrinho')
def carrinho():
    cart_ids = session.get('cart', [])
    itens_db = []
    total = 0
    if cart_ids:
        from collections import Counter
        counts = Counter(cart_ids)
        products = Product.query.filter(Product.id.in_(list(counts.keys()))).all()
        for p in products:
            qtd = counts[p.id]
            total += p.price * qtd
            itens_db.append({'product': p, 'qtd': qtd, 'subtotal': p.price * qtd})
    return render_template('carrinho.html', itens=itens_db, total=total)

@app.route('/adicionar/<int:id>')
def adicionar(id):
    if 'cart' not in session: session['cart'] = []
    session['cart'].append(id)
    session.modified = True
    flash('Produto adicionado ao carrinho!', 'success')
    return redirect(url_for('carrinho'))

@app.route('/limpar_carrinho')
def limpar_carrinho():
    session.pop('cart', None)
    return redirect(url_for('carrinho'))

# ROTA NOVA: PÁGINA DE CHECKOUT (ENDEREÇO E PAGAMENTO)
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_ids = session.get('cart', [])
    if not cart_ids: return redirect(url_for('home'))
    
    # Calcula totais para exibir no resumo
    from collections import Counter
    counts = Counter(cart_ids)
    products = Product.query.filter(Product.id.in_(list(counts.keys()))).all()
    total = sum(p.price * counts[p.id] for p in products)
    
    if request.method == 'POST':
        # PROCESSAR A COMPRA
        desc_list = [f"{counts[p.id]}x {p.name}" for p in products]
        
        novo_pedido = Order(
            total_price=total,
            items_description=", ".join(desc_list),
            user_id=current_user.id,
            status='Pago', # Em um sistema real, aqui entraria a API do Banco
            payment_method=request.form.get('payment_method'),
            address_city=request.form.get('city'),
            address_street=request.form.get('address'),
            address_zip=request.form.get('zip')
        )
        db.session.add(novo_pedido)
        db.session.commit()
        session.pop('cart', None)
        return redirect(url_for('pedido_sucesso', order_id=novo_pedido.id))
        
    return render_template('checkout.html', total=total, qtd_itens=len(cart_ids))

@app.route('/pedido-sucesso/<int:order_id>')
@login_required
def pedido_sucesso(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('sucesso.html', order=order)

if __name__ == '__main__':
    with app.app_context():
        # db.drop_all() # ATENÇÃO: RODE UMA VEZ SEM COMENTARIO PARA ATUALIZAR TABELAS
        db.create_all()
    app.run(debug=True)