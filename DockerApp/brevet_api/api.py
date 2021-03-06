# Brevet RESTful API
# Author: Andrew Werderman

import flask
from itsdangerous import (TimedJSONWebSignatureSerializer
							as Serializer, BadSignature,
							SignatureExpired)
from flask import (
	Flask, redirect, url_for, request, render_template, Response, jsonify 
	)
from passlib.apps import custom_app_context as pwd_context
from flask_restful import Resource, Api, abort
from basicauth import decode as authDecode
from flask_login import LoginManager, login_required, login_user
from flask_wtf import CSRFProtect
from pymongo import MongoClient
from functools import wraps
import base64
import arrow


# Instantiate the app
app = Flask(__name__)
api = Api(app=app, catch_all_404s=True)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'

# Create Mongo instance
client = MongoClient('mongodb://mongo:27017/')
brevetdb = client['brevetdb'] 
usersdb = client['usersdb']

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)


class Home(Resource):
	def get(self):
		return ''

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


class Register(Resource):
	def __init__(self):
		self.collection = usersdb['UserInfo']

	def post(self):
		'''
		Function executed on a POST request to register. If the username is not
		taken, the function will:
		  1. Hash the user's desired password
		  2. Insert the username and hashed password in the usersdb database.
		  3. Return a JSON object of the unique user_id, username, and date_added
		  with a status code of 201.

		Upon failure, an error with status code 400 (bad request) is returned.

		USE: curl -d "username=<username>&password=<password>" localhost:5001/api/register
		'''
		#Get arguements from cURL
		username = request.form.get('username')
		password = request.form.get('password')

		# Handle invalid inputs
		if ((username == None) or (username == '')) or ((password == None) or (password == '')):
			return {'Error': 'Please provide a username and password.'}, 400

		# Handle username is already in use. (True: return appropriate message)
		if (self.collection.find_one({'username': username})):
			# Bad Request is returned
			return {'Error': '{} already in use.'.format(username)}, 400

		hVal = pwd_context.encrypt(password)
		self.collection.insert_one({'username': username, 'password': hVal})
		new_user = self.collection.find_one({'username': username})
		# Format response
		info = {'location': str(new_user['_id']), 
				'username': username, 
				'date_added': arrow.now().for_json()}
		response = flask.jsonify(info)
		response.status_code = 201
		return response


class Login(Resource):
	def __init__(self):
		self.collection = usersdb['UserInfo']

	def post(self):
		'''
		USE: curl -d "username=<username>&password=<password>" localhost:5001/api/login
		'''
		username = request.form.get('username')
		password = request.form.get('password')

		# Handle invalid inputs
		if ((username == None) or (username == '')) or ((password == None) or (password == '')):
			return {'Error': 'Please provide a username and password.'}, 400

		user = self.collection.find_one({'username': username})

		# Handle username is already in use. (True: return appropriate message)
		if not user:
			# Bad Request is returned
			return {'Error': '{} is not a registered username.'.format(username)}, 400

		hashVal = user['password']

		if pwd_context.verify(password, hashVal):
			obj = User(user['_id'])
			login_user(obj, remember=True)
			return 'User successfully logged in.', 200

		return 'Unauthorized.', 401


class Logout(Resource):
	@login_required
	def get(self):
		logout_user()
		return 'user successfully logged out.', 200


# Can only be accessed when logged in.
class ListBrevet(Resource):
	# All functions in this class must come from an authenticated user
	def __init__(self):
		self.collection = brevetdb['brevet'] 

	@login_required
	def get(self, items='listAll', resultFormat='json'):
		'''
		  Input:
			items - which items to list: 'listAll' (default), 'listOpenOnly', 'listCloseOnly'
			resultFormat - requested format of response
		  Output:
			array of brevet control open and/or close times
			resultFormat='json' gives an array of dictionaries
			resultFormat='csv' gives an array of arrays

		USE: curl -u "<tokenstring>:" localhost:5001/api/token
		'''
		top = request.args.get('top')

		# Handle empty brevet
		if self.collection.count() == 0:
			return jsonify({'Error': 'Empty Brevet'})

		# Handle unexpected query.
		if (items not in ['listAll', 'listOpenOnly', 'listCloseOnly']) or (resultFormat not in ['json', 'csv']):
			return jsonify({'Error': 'Invalid Query'})

		# Handle whether top is set or not
		if (top == None) or (top == ''):
			controls = self.collection.find()
		else:
			# Handle invalid input for top
			try:
				limit = int(top)
				if(limit <= 0):
					return jsonify({'Error': 'Invalid number of top elements'})
				else:
					controls = self.collection.find(limit=limit) # limits the number of results in find()
			except ValueError:
				return jsonify({'Error': 'Value Error for top'})

		# Populate results with queried output
		if (items == 'listAll'):
			result = ListBrevet.formatResponse(controls, resultFormat, 'open_time', 'close_time')
		elif (items == 'listOpenOnly'):
			result = ListBrevet.formatResponse(controls, resultFormat, 'open_time')
		else: # resultFormat == 'listCloseOnly'
			result = ListBrevet.formatResponse(controls, resultFormat, 'close_time')
		
		if (resultFormat == 'csv'):
			return Response(result, mimetype='text/csv')

		return jsonify(result)

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
				csv += ', {}\n'.format(args[1]) # If two arguments are given, add the second to the first line
				for ctrl in brevet:
					csv += '{}, {}\n'.format(ctrl[args[0]], ctrl[args[1]])	# Add all controls in csv format
			else:
				csv += '\n'
				for ctrl in brevet:
					csv += '{}\n'.format(ctrl[args[0]])	# Else, add all the singleton control values in csv

		output = {'json': json, 'csv': csv}
		return output[resultFormat]


# Create routes
api.add_resource(Home, '/')
api.add_resource(Login, '/api/login')
api.add_resource(Logout, '/api/logout')
api.add_resource(Register, '/api/register')
api.add_resource(ListBrevet, '/<items>', '/<items>/<resultFormat>')

# Run the application
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, debug=True)


