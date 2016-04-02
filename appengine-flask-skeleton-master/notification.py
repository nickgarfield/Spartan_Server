from flask import Flask
from flask import request
from flask import json
from flask import jsonify
from random import randint
import logging
from twilio.rest import TwilioRestClient
from google.appengine.ext import ndb
from models import User, Delivery_Event, Order
from error_handlers import InvalidUsage, ServerError
import datetime


app = Flask(__name__)


# Return a list of this user's DeliveryEvents and the local Orders for ItemTypes that this user owns
@app.route('/notification/get_users_notification_data/user_id=<int:user_id>', route=['GET'])
def get_users_notification_data(user_id):
	# Check to make sure the User exists
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User ID does not match any existing user', 400)

	# FIXME: Replace with real data from Delivery_Events and Orders related to this user
	data = []
	resp = jsonify({'notification_data': data})
	resp.status_code = 200
	return resp



### Server Error Handlers ###
@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
	response = jsonify(error.to_dict())
	response.status_code = error.status_code
	logging.exception(error)
	return response

@app.errorhandler(ServerError)
def handle_server_error(error):
	response = jsonify(error.to_dict())
	response.status_code = error.status_code
	logging.exception(error)
	return response

@app.errorhandler(404)
def page_not_found(e):
	"""Return a custom 404 error."""
	return 'Sorry, Nothing at this URL.', 404

@app.errorhandler(500)
def application_error(e):
	"""Return a custom 500 error."""
	return 'Sorry, unexpected error: {}'.format(e), 500