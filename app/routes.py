from flask import render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from . import login_manager  # assuming login_manager is defined in __init__.py
from . import db
from .models import User, Expense
from . import bcrypt
from sqlalchemy import or_
from collections import defaultdict
import numpy as np
import pandas as pd  # type: ignore
from sklearn.linear_model import LinearRegression
def init_routes(app):
    # Home Page with Login Form
    @app.route('/', methods=['GET', 'POST'])
    def home():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()

            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')

        return render_template('home.html')

    # Registration route
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            user = User.query.filter_by(username=username).first()
            if user:
                flash('Username already exists!', 'danger')
                return redirect(url_for('register'))

            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully!', 'success')
            login_user(new_user)
            return redirect(url_for('dashboard'))

        return render_template('register.html')
    

    @app.route('/dashboard')
    @login_required
    def dashboard():
        search = request.args.get('search', '').strip()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Base query
        query = Expense.query.filter_by(user_id=current_user.id)

        if search:
            query = query.filter(
                or_(
                    Expense.title.ilike(f"%{search}%"),
                    Expense.category.ilike(f"%{search}%")
                )
            )
        if start_date:
            query = query.filter(Expense.date >= start_date)
        if end_date:
            query = query.filter(Expense.date <= end_date)

        expenses = query.order_by(Expense.date.desc()).all()

        # Summary
        total_expense = sum(exp.amount for exp in expenses)
        category_totals = defaultdict(float)
        date_totals = defaultdict(float)

        for exp in expenses:
            category_totals[exp.category] += exp.amount
            date_totals[exp.date.strftime('%Y-%m-%d')] += exp.amount

        top_category = max(category_totals, key=category_totals.get) if category_totals else "N/A"
        total_transactions = len(expenses)

        # AI-based Prediction
        df = pd.DataFrame([(exp.date, exp.amount) for exp in expenses], columns=['date', 'amount'])
        prediction = None

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.to_period('M')
            monthly_expenses = df.groupby('month')['amount'].sum().reset_index()
            monthly_expenses['month_num'] = np.arange(len(monthly_expenses))

            X = monthly_expenses[['month_num']]
            y = monthly_expenses['amount']

            if len(X) >= 2:
                model = LinearRegression()
                model.fit(X, y)
                next_month = np.array([[X.iloc[-1][0] + 1]])
                predicted_amount = model.predict(next_month)[0]
                prediction = round(predicted_amount, 2)
            else:
                prediction = "Not enough data to predict. We need at least 2 months of data."

        return render_template(
            'dashboard.html',
            expenses=expenses,
            total_expense=total_expense,
            top_category=top_category,
            total_transactions=total_transactions,
            category_totals=category_totals,
            date_totals=date_totals,
            category_labels=list(category_totals.keys()),
            category_values=list(category_totals.values()),
            date_labels=list(date_totals.keys()),
            date_values=list(date_totals.values()),
            predicted_expense=prediction,
            
        )


    # Add expense route
    @app.route('/add-expense', methods=['POST'])
    @login_required
    def add_expense():
        title = request.form['title']
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']

        new_expense = Expense(
            title=title,
            amount=amount,
            category=category,
            date=date,
            user_id=current_user.id
        )
        db.session.add(new_expense)
        db.session.commit()

        flash('Expense added successfully!', 'success')
        return redirect(url_for('dashboard'))

    # Edit expense route
    @app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
    @login_required
    def edit_expense(expense_id):
        expense = Expense.query.get_or_404(expense_id)

        if expense.user_id != current_user.id:
            flash("You are not authorized to edit this expense.", "danger")
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            expense.title = request.form['title']
            expense.amount = request.form['amount']
            expense.category = request.form['category']
            expense.date = request.form['date']

            db.session.commit()
            flash('Expense updated successfully.', 'success')
            return redirect(url_for('dashboard'))

        return render_template('edit_expense.html', expense=expense)

    # Delete expense route
    @app.route('/delete_expense/<int:expense_id>', methods=['POST'])
    @login_required
    def delete_expense(expense_id):
        expense = Expense.query.get_or_404(expense_id)
        if expense.user_id != current_user.id:
            flash("You are not authorized to delete this expense.", "danger")
            return redirect(url_for('dashboard'))

        db.session.delete(expense)
        db.session.commit()
        flash("Expense deleted successfully.", "success")
        return redirect(url_for('dashboard'))

    # Logout route
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('home'))



