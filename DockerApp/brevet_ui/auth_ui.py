from flask import (
	Flask, redirect, url_for, request, render_template, Response, jsonify 
	)
from wtforms import StringField, PasswordField, BooleanField
from passlib.apps import custom_app_context as pwd_context
from wtforms.validators import InputRequired, Length 
from flask_wtf import FlaskForm, CSRFProtect
from flask_login import LoginManager, login_required, login_user
from pymongo import MongoClient


# Instantiate the app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'

# Create Mongo instance
client = MongoClient('mongodb://mongo:27017/')
usersdb = client['usersdb']
collection = usersdb['UserInfo']

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
csrf = CSRFProtect(app)


class User():
	def __init__(self, username=None, password=None):
		self.username = username
		self.password = password

	def register_user(self):
		# Handle username is already in use. (True: return appropriate message)
		if (collection.find_one({'username': self.username})):
			return False
		hVal = pwd_context.encrypt(self.password)
		collection.insert_one({'username': self.username, 'password': hVal})
		return True

	@staticmethod
	def is_authenticated(username, password):
		user = collection.find_one({'username': username})
		if user:
			hashVal = user['password']
			return pwd_context.verify(password, hashVal)
		return False

	@staticmethod
	def is_active():
		'''
		this is to check if the user has activated their account
		not been suspended, or any condition the application has 
		for rejecting the account. In our case we'll just always 
		return true.
		'''
		return True

	@staticmethod
	def is_anonymous():
		'''
		Not going to worry about anonymous/guest users
		'''
		return False

	@staticmethod
	def get_id(username):
		'''
		must return unicode that uniquely identifies the user
		and can be used to load the user from user_loader callback. 
		MUST BE UNICODE. 
		'''
		user = collection.find_one({'username': username})
		if user:
			user_id = user['_id']
			return user_id

		return None


class LoginForm(FlaskForm):
	username = StringField('Username', validators=[InputRequired(), Length(min=5, max=15)])
	password = PasswordField('Password', validators=[InputRequired(), Length(min=7, max=30)])
	remember = BooleanField('Remember me?')


class RegisterForm(FlaskForm):
	username = StringField('Username', validators=[InputRequired(), Length(min=5, max=15)])
	password = PasswordField('Password', validators=[InputRequired(), Length(min=7, max=30)])

	def is_available_username(form, field):
		username = form.username.data
		if (collection.find_one({'username': self.username})):
			raise ValidationError('Username is already in use.')


@login_manager.user_loader
def load_user(username):
	return User.get_id(username)


@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm()
	app.logger.debug("register function called")

	if form.validate_on_submit():
		username = form.username.data
		password = form.password.data
		app.logger.debug("username: {} | password: {}".format(username, password))
		new_user = User(username, password).register_user()
		if new_user:
			return redirect(url_for('login'))

	return render_template('register.html', form=form)


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		username = form.username.data
		password = form.password.data
		remember = form.remember.data
		if User.is_authenticated(username, password):
			login_user(User(username, password), remember=remember)
			flask.flash('Logged in successfully.')
			return flask.redirect(url_for('index'))

	return render_template('login.html', form=form)


@app.route('/index')
@login_required
def index():
	return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(
    	host='0.0.0.0', 
    	port=5000, 
    	debug=True,
    	extra_files = ['./templates/register.html', './templates/login.html'])

