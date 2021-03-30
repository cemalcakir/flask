from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User


class RegistrationForm(FlaskForm):
    username = StringField("Kullanıcı Adı",
                           validators=[DataRequired(),
                                       Length(min=4, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Şifre", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Şifre (Tekrar)", validators=[DataRequired(),
                                      EqualTo("password")])
    submit = SubmitField("Kayıt Ol")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "Bu kullanıcı adı zaten kullanılıyor. Lütfen başka bir kullanıcı adı alın."
            )

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                "Bu e-mail zaten kullanılıyor. Lütfen başka bir email kullanın."
            )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Şifre", validators=[DataRequired()])
    submit = SubmitField("Giriş Yap")
    remember = BooleanField('Beni Unutma')


class UpdateAccountForm(FlaskForm):
    username = StringField("Kullanıcı Adı",
                           validators=[DataRequired(),
                                       Length(min=4, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    picture = FileField('Profil Resmini Değiştir',
                        validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField("Güncelle")

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    "Bu kullanıcı adı zaten kullanılıyor. Lütfen başka bir kullanıcı adı alın."
                )

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    "Bu e-mail zaten kullanılıyor. Lütfen başka bir email kullanın."
                )


class PostForm(FlaskForm):
    title = StringField('Başlık',
                        validators=[DataRequired(),
                                    Length(min=10, max=150)])
    content = TextAreaField(
        'Soru', validators=[DataRequired(),
                            Length(min=10, max=10000)])
    submit = SubmitField('Gönder')


class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField('Mail Gönder')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError("Bu email'e ait bir hesap yoktur.")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Şifre", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Şifre (Tekrar)", validators=[DataRequired(),
                                      EqualTo("password")])
    submit = SubmitField('Şifremi yenile')