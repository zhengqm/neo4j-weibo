from flask import Flask, request, session, redirect, url_for, render_template, flash
from models import User

app = Flask(__name__)

@app.route('/')
def index():
    user_id = session.get('user_id')
    if user_id:
        user = User.find_by_id(user_id)
        posts = User.retrieve_feed(user_id)
        return render_template('index.html',  nickname=user['nickname'], posts = posts)
    else:
        return render_template('index.html')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        nickname = request.form['nickname']
        email    = request.form['email']
        password = request.form['password']

        if len(email) < 1:
            flash('Your email must be at least one character.')
        elif len(password) < 6:
            flash('Your password must be at least 6 characters.')
        elif not User.register(email, password, nickname):
            flash('A user with that email already exists.')
        else:
            user = User.find_by_email(email)
            session['user_id'] = user['id']
            flash('Logged in.')
            return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    if not User.verify_password(email, password):
        flash('Invalid login.')
    else:
        user = User.find_by_email(email)
        session['user_id'] = user['id']
        flash('Logged in.')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.')
    return redirect(url_for('index'))


@app.route('/follow/<target_id>')
def follow(target_id):
    self_id = session.get('user_id')
    target = User.find_by_id(target_id)
    posts = User.retrieve_posts(target_id)
    if self_id and target:
        User.follow_user(self_id, target_id)
        return redirect(url_for('show_user', user_id=target_id))
    return redirect(url_for('index'))


@app.route('/add_post', methods=['POST'])
def add_post():
    user_id = session.get('user_id')
    if user_id:
        content = request.form['content']
        if not content:
            flash('You must say something.')
        else:
            User.add_post(user_id, content, [])

    return redirect(url_for('index'))

@app.route('/post/<post_id>', methods=['GET'])
def show_post(post_id):
    # Check login status

    return render_template('post_page.html', post_id=post_id)



@app.route('/user/<user_id>', methods=['GET'])
def show_user(user_id):
    self_id = session.get('user_id')
    user = User.find_by_id(user_id)
    posts = User.retrieve_posts(user_id)

    if user:
        if self_id and User.is_following(self_id, user_id):
            return render_template('user_page.html', nickname=user['nickname'], posts=posts, user_id=user_id, is_following = True)
        else:
            return render_template('user_page.html', nickname=user['nickname'], posts=posts, user_id=user_id)

    else:
        return redirect(url_for('index'))



@app.route('/user/<user_id>/profile', methods=['GET'])
def show_user_profile(user_id):
    # Check login status

    return render_template('user_profile_page.html', user_id=user_id)
