# -*- coding: utf-8 -*-
from flask import Flask, request, session, redirect, url_for, render_template, flash
from models import User, Post, Comment, get_recent_posts

import re

app = Flask(__name__)

@app.route('/')
def index():
    user_id = session.get('user_id')
    if user_id:
        user = User.find_by_id(user_id)
        posts = User.retrieve_feed(user_id)
        return render_template('index.html',  posts = posts, nickname=user['nickname'])
    else:
        posts = get_recent_posts()
        return render_template('index.html', posts = posts)


@app.route('/recent_posts')
def recent_posts():
    if session.get('user_id'):
        posts = get_recent_posts()
        return render_template('recent_posts.html', posts = posts)
    else:
        return redirect(url_for('index'))


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        nickname = request.form['nickname']
        email    = request.form['email']
        password = request.form['password']

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('电子邮件格式不正确','danger')
        elif len(password) < 6:
            flash('密码长度须大于等于6', 'danger')
        elif len(nickname) < 6:
            flash('昵称不能为空', 'danger')
        elif not User.register(email, password, nickname):
            flash('该邮箱已被用于注册', 'danger')
        else:
            user = User.find_by_email(email)
            session['user_id'] = user['id']
            flash('成功登陆', 'success')
            return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    if not User.verify_password(email, password):
        flash('错误的邮箱或密码','danger')
    else:
        user = User.find_by_email(email)
        session['user_id'] = user['id']
        flash('成功登陆', 'success')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('成功登出', 'success')
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


@app.route('/unfollow/<target_id>')
def unfollow(target_id):
    self_id = session.get('user_id')
    target = User.find_by_id(target_id)
    posts = User.retrieve_posts(target_id)
    if self_id and target:
        User.unfollow_user(self_id, target_id)
        return redirect(url_for('show_user', user_id=target_id))
    return redirect(url_for('index'))


@app.route('/add_post', methods=['POST'])
def add_post():
    user_id = session.get('user_id')
    if user_id:
        content = request.form['content']
        if not content or len(content) == 0:
            flash('微博内容不能为空','danger')
        else:
            User.add_post(user_id, content, [])
            flash('成功发布', 'success')
            return redirect(url_for('show_user', user_id=user_id))

    return redirect(url_for('index'))

@app.route('/post/<post_id>', methods=['GET'])
def show_post(post_id):
    # Check login status
    post = Post.find_by_id(post_id)
    if post:
        return render_template('post_page.html', post=post)
    else:
        return redirect(url_for('index'))



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

@app.route('/comment/<post_id>', methods=['GET'])
def comment_page(post_id):
    user_id = session.get('user_id')
    if user_id:
        post = Post.find_by_id(post_id)
        return render_template('comment_post.html', post = post,user_id=user_id)
    else:
        return redirect(url_for('index'))
		

@app.route('/add_comment', methods=['POST'])
def add_comment():
    user_id = session.get('user_id')
    if user_id:
        content = request.form['content']
        post_id = request.form['post_id']
        if not content or len(content) == 0:
            flash('评论内容不能为空','danger')
        else:
            User.add_comment_on_post(user_id, post_id, content, 'tags')
            flash('成功评论', 'success')
            post = Post.find_by_id(post_id)
            return render_template('post_page.html', post=post)
    return redirect(url_for('index'))
