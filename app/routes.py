from flask import render_template, url_for, flash, redirect, request, abort
import secrets
import os
from PIL import Image
from app import app, db, bcrypt, mail
from app.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                       PostForm, RequestResetForm, ResetPasswordForm)
from app.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


@app.route("/")
@app.route("/anasayfa")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page,
                                                                  per_page=10)
    return render_template("index.html", posts=posts)


answers = ["answer1", "answer2", "answer3"]


@app.route("/giris", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        print(user.password)
        if user and bcrypt.check_password_hash(user.password,
                                               form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next', '/')
            return redirect(next_page)
        flash("Kullanıcı adı veya şifre yanlış.", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/kayitol", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode("utf-8")
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Hesabınız oluşturuldu. Giriş yapabilirsiniz.")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/cikis")
def logout():
    logout_user()
    return redirect(url_for("home"))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, "static/profile_pics",
                                picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


@app.route("/profil", methods=["GET", "POST"])
@login_required
def profile():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            old_path = f"app/static/profile_pics/{current_user.image_file}"
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
            os.remove(old_path)
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Hesap bilgileriniz güncellendi.")
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static',
                         filename='profile_pics/' + current_user.image_file)
    return render_template('profile.html', image_file=image_file, form=form)


@app.route("/soru/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('question.html',
                           title=post.title,
                           post=post,
                           answers=answers)


@app.route("/soru/yeni", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,
                    content=form.content.data,
                    author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Sorunuz gönderilmiştir!")
        return redirect(url_for('home'))
    return render_template('new_question.html',
                           title="Yeni Soru",
                           form=form,
                           legend="Yeni Soru")


@app.route("/soru/<int:post_id>/duzenle", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Sorunuz güncellenmiştir!", "success")
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    form.title.data = post.title
    form.content.data = post.content
    return render_template('new_question.html',
                           title="Düzenle",
                           form=form,
                           post=post,
                           legend="Güncelle")


@app.route("/soru/<int:post_id>/sil", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Sorunuz silinmiştir.", "success")
    return redirect(url_for("home"))


@app.route("/kullanici/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(
        Post.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template("user_posts.html", posts=posts, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f"""Şifrenizi sıfırlamak için gönderilen linki ziyaret ediniz.

{url_for('reset_password', token=token, _external=True)}

Eğer bu talebi siz yapmadıysanız, birisi şifrenizi ele geçirmeye çalışıyor olabilir.

"""
    mail.send(msg)


@app.route("/sifre_yenileme", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash("Şifre sıfırlama maili gönderilmiştir.")
        return redirect(url_for("login"))
    return render_template("reset_request.html",
                           title="Şifre Yenile",
                           form=form)


@app.route("/sifre_yenileme/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if not user:
        flash("Geçerli değil! Şifre yenileme süreniz dolmuş da olabilir!")
        return redirect(url_for(reset_request))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode("utf-8")
        user.password = hashed_password
        db.session.commit()
        flash("Şifreniz yenilenmiştir. Giriş yapabilirsiniz.")
        return redirect(url_for("login"))
    return render_template("reset_password.html",
                           title="Şifre Yenile",
                           form=form)


@app.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def error_403(error):
    return render_template('403.html'), 403


@app.errorhandler(500)
def error_500(error):
    return render_template('500.html'), 500