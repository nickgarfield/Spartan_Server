"""`main` is the top level module for your Flask application."""
# Imports
from flask import Flask
from flask import request
from flask import json
from flask import jsonify
from error_handlers import InvalidUsage

# Define the Flask app
app = Flask(__name__)

# Hello World!
@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'Welcome to Bygo!\n'


### Server Error Handlers ###
@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
	response = jsonify(error.to_dict())
	response.status_code = error.status_code
	return response

@app.errorhandler(404)
def page_not_found(e):
	"""Return a custom 404 error."""
	return 'Sorry, Nothing at this URL.', 404

@app.errorhandler(500)
def application_error(e):
	"""Return a custom 500 error."""
	return 'Sorry, unexpected error: {}'.format(e), 500