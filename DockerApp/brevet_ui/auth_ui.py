# Brevet Authenitcated Consumer Program
# Author: Andrew Werderman

from flask import (
	Flask, redirect, url_for, request, render_template, Response, jsonify 
	)
from wtforms import StringField, PasswordField, BooleanField
from passlib.apps import custom_app_context as pwd_context
from wtforms.validators import InputRequired, Length 
from flask_wtf import FlaskForm, CSRFProtect
from flask_login import LoginManager, login_required, login_user, logout_user
from pymongo import MongoClient
import pymongo
import flask

# Instantiate the app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'

# Create Mongo instance
client = MongoClient('mongodb://mongo:27017/')
brevetdb = client['brevetdb'] 
usersdb = client['usersdb']
BREVET_COLLECTION = brevetdb['brevet']  
USER_COLLECTION = usersdb['UserInfo']

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
csrf = CSRFProtect(app)


#############
# User class
#############

class User():
	def __init__(self, user_id):
		self.user_id = user_id
		
	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return str(self.user_id)


@login_manager.user_loader
def load_user(user_id):
	return User(user_id)	


##################
# WTForms Classes
##################

class LoginForm(FlaskForm):
	username = StringField('Username', validators=[InputRequired(), Length(min=5, max=15)])
	password = PasswordField('Password', validators=[InputRequired(), Length(min=7, max=30)])


class RegisterForm(FlaskForm):
	username = StringField('Username', validators=[InputRequired(), Length(min=5, max=15)])
	password = PasswordField('Password', validators=[InputRequired(), Length(min=7, max=30)])


##########
# Routes
##########

@app.route('/_<items>')
@app.route('/_<items>/<resultFormat>')
@login_required
def listBrevet(items='listAll', resultFormat='json'):
	top = request.args.get('top')
	app.logger.debug('function called.')

	# Handle empty brevet
	if BREVET_COLLECTION.count() == 0:
		return jsonify(result={'Error': 'Empty Brevet'})

	# Handle unexpected query.
	if (items not in ['listAll', 'listOpenOnly', 'listCloseOnly']) or (resultFormat not in ['json', 'csv']):
		return jsonify(result={'Error': 'Invalid Query'})

	# Handle whether top is set or not
	if (top == None) or (top == ''):
		controls = BREVET_COLLECTION.find()
	else:
		# Handle invalid input for top
		try:
			limit = int(top)
			if(limit <= 0):
				return jsonify(result={'Error': 'Invalid number of top elements'})
			else:
				controls = BREVET_COLLECTION.find(limit=limit) # limits the number of results in find()
		except ValueError:
			return jsonify(result={'Error': 'Value Error for top'})

	# Populate results with queried output
	if (items == 'listAll'):
		result = formatResponse(controls, resultFormat, 'open_time', 'close_time')
	elif (items == 'listOpenOnly'):
		result = formatResponse(controls, resultFormat, 'open_time')
	else: # resultFormat == 'listCloseOnly'
		result = formatResponse(controls, resultFormat, 'close_time')
	
	app.logger.debug(result)
	return jsonify(result=result, form=resultFormat)


@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	app.logger.debug("register function called")

	if form.validate_on_submit() and (request.method == 'POST'):
		username = form.username.data
		password = form.password.data
		if not is_taken(username):
			hVal = pwd_context.encrypt(password)
			USER_COLLECTION.insert_one({'username': username, 'password': hVal})
			new_user = USER_COLLECTION.find_one({'username': username})
			user_obj = User(new_user['_id'])
			login_user(user_obj, remember=True)
			return redirect(url_for('index'))
	return render_template('register.html', form=form)


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm(request.form)
	app.logger.debug("login function called")
	if form.validate_on_submit() and (request.method == 'POST'):
		username = form.username.data
		password = form.password.data
		user = is_taken(username)
		if user:
			app.logger.debug("user exists")
			if is_valid_password(username, password):
				obj = User(user['_id'])
				login_user(obj, remember=True)
				return redirect(url_for('index'))
			app.logger.debug("invalid password")

	return render_template('login.html', form=form)


@app.route('/index')
@login_required
def index():
	return render_template('index.html')


@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('login'))


#####################
# HELPER FUNCTIONS
#####################

def is_taken(username):
	'''
	'''
	user_obj = USER_COLLECTION.find_one({'username': username})
	if user_obj:
		return user_obj
	else:
		return False

def is_valid_password(username, password):
	user_obj = USER_COLLECTION.find_one({'username': username})
	hashVal = user_obj['password']
	return pwd_context.verify(password, hashVal)

def formatResponse(brevet, resultFormat, *args):
		'''
		  Input: 
		  	brevet - the db brevet collection instance
		  	resultFormat - the desired output format of the query -- 'json' or 'csv'
		  	*args - the key values of the desired control information -- 'open_time'/'close_time'/etc.
		  Output: 
		  	json - an array of dictionaries of control info
		  	csv - A string formatted to csv
		  Helper function to format the queried resultFormat of controls.
		'''
		json = []
		csv = ''
		if (resultFormat == 'json'):
			for ctrl in brevet:
				# Could possibly be given two args (open_time/close_time) aka 'key', 
				# add each to a dictionary and append control
				jsonDict = {key:ctrl[key] for key in args}
				json.append(jsonDict)
		else:
			csv += str(args[0]) # First argument of format
			if (len(args) > 1):
				csv += ', {}<br>'.format(args[1]) # If two arguments are given, add the second to the first line
				for ctrl in brevet:
					csv += '{}, {}<br>'.format(ctrl[args[0]], ctrl[args[1]])	# Add all controls in csv format
			else:
				csv += '<br>'
				for ctrl in brevet:
					csv += '{}<br>'.format(ctrl[args[0]])	# Else, add all the singleton control values in csv

		output = {'json': json, 'csv': csv}
		return output[resultFormat]

###############################


if __name__ == '__main__':
    app.run(
    	host='0.0.0.0', 
    	port=5000, 
    	debug=True,
    	extra_files = ['./templates/register.html', './templates/login.html'])

