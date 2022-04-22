from http.client import UNAUTHORIZED
from flask import Flask, render_template, redirect, session, flash, jsonify, request
from werkzeug.exceptions import Unauthorized

from models import Feedback, db, connect_db, User
from forms import RegisterForm, LoginForm, FeedbackForm, DeleteForm
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///feedback_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "oh-so-secret"

connect_db(app)


@app.route('/')
def index():
    return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(
            username, password, email, first_name, last_name)

        db.session.add(user)
        try:
            db.session.commit()
            session['username'] = user.username
            flash('Welcome! Successfully Created Your Account!', "success")
            return redirect(f'/users/{username}')
        except IntegrityError:
            form.username.errors.append('Username taken.  Please pick another')
            return render_template('register.html', form=form)

    return render_template('register.html', form=form)


@ app.route('/login', methods=['GET', 'POST'])
def login_user():
    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", "primary")
            session['username'] = user.username
            return redirect(f'/users/{username}')
        else:
            form.username.errors = ['Invalid username/password.']

    return render_template('login.html', form=form)


@ app.route('/logout')
def logout_user():
    session.pop('username')
    flash("Goodbye!", "info")
    return redirect('/')


@ app.route('/users/<username>')
def show_user(username):
    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect('/login')
    user = User.query.get(username)

    form = DeleteForm()
    return render_template('user_detail.html', user=user, form=form)


@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def feedback_form(username):
    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect('/login')

    user = User.query.get(username)
    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(
            title=title, content=content, username=username)

        db.session.add(feedback)

        db.session.commit()
        flash("Feedback Submitted!", 'success')
        return redirect(f'/users/{username}')

    return render_template('feedback_form.html', user=user, form=form)


@app.route('/users/<username>/delete')
def delete_user(username):
    user = User.query.get(username)

    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect('/login')

    db.session.delete(user)
    db.session.commit()
    session.pop('username')

    flash('User deleted!', 'info')
    return redirect('/')


@app.route('/feedback/<id>/update', methods=['GET', 'POST'])
def feedback_detail(id):
    feedback = Feedback.query.get(id)
    form = FeedbackForm(obj=feedback)

    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect('/login')

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()
        flash("Feedback Updated!", 'info')
        return redirect(f'/users/{feedback.username}')

    return render_template('feedback_detail.html', form=form, feedback=feedback)


@app.route('/feedback/<id>/delete', methods=["POST"])
def delete_feedback(id):
    feedback = Feedback.query.get(id)

    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect('/login')

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    flash('Feedback deleted!', 'info')
    return redirect(f'/users/{feedback.username}')


@app.route('/error')
def error():
    raise Unauthorized()
