from flask import Flask, render_template, request, redirect, url_for,flash,session
from models import db, User, Expense, UserExpense
from forms import ExpenseForm
from functools import wraps
app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'] 
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully!', 'info')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first() 
        if user:
            session['user_id'] = user.id
            flash('Logged in successfully!', 'info')
            return redirect(url_for('index'))
        flash('Login failed. Check your username and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('index'))


@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    users = User.query.all()
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        if amount <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('add_expense'))
        selected_users = request.form.getlist('users') 
        new_expense = Expense(description=description, amount=amount)
        db.session.add(new_expense)
        db.session.commit()

        share_per_user = amount / len(selected_users)
        for user_id in selected_users:
            user_expense = UserExpense(user_id=user_id, expense_id=new_expense.id, amount_owed=share_per_user)
            db.session.add(user_expense)

        db.session.commit()
        flash('Expense added successfully!', 'info')
        return redirect(url_for('view_expenses'))
    
    return render_template('add_expense.html', users=users)

@app.route('/view_expenses')
@login_required
def view_expenses():
    # expenses = Expense.query.all()
    user_id = session['user_id']
    user_expenses = UserExpense.query.filter_by(user_id=user_id).all()
    total_expense = sum(user_expense.amount_owed for user_expense in user_expenses)
    expenses = Expense.query.join(UserExpense).filter(UserExpense.user_id == session['user_id']).all()
    return render_template('view_expenses.html', expenses=expenses,total_expense=total_expense)

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    for user_expense in expense.user_expenses:
        db.session.delete(user_expense)
    
    db.session.delete(expense)
    db.session.commit()
    
    flash('Expense deleted successfully!', 'info')
    return redirect(url_for('view_expenses'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)
