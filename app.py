from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Models ---


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---


@app.route('/')
def home():
    products = Product.query.all()
    return render_template('products.html', products=products)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash("Username already exists", 'error')
            return redirect(url_for('register'))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('home'))
        flash("Invalid credentials", 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    cart = session.get('cart', [])
    cart.append(product_id)
    session['cart'] = cart
    flash("Product added to cart!", 'success')
    return redirect(url_for('home'))


@app.route('/cart')
@login_required
def cart():
    cart_ids = session.get('cart', [])
    items = Product.query.filter(Product.id.in_(cart_ids)).all()
    total = sum(p.price for p in items)
    return render_template('cart.html', items=items, total=total)


@app.route('/checkout')
@login_required
def checkout():
    session.pop('cart', None)
    flash("Checkout successful!", 'success')
    return render_template('checkout.html')


# --- Run ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Product.query.first():  # Add some dummy products
            db.session.add_all([
                Product(name="Phone", price=699,
                        description="Smartphone with 128GB storage"),
                Product(name="Laptop", price=999,
                        description="Powerful laptop with 16GB RAM"),
                Product(name="Headphones", price=199,
                        description="Noise-cancelling headphones"),
            ])
            db.session.commit()
    app.run(debug=True)
