from flask import Flask,request,json,jsonify,Response,abort
import global_vars
from google.appengine.ext import ndb
from google.appengine.api import search
from gcloud import storage
from models import User, Item_Type
from error_handlers import InvalidUsage

app = Flask(__name__)




@app.route('/discovery/default_home_page', methods=['GET'])
def get_default_home_page_data():

	layout_data = [{'type':0, 'title':'Play Some Games', 'item_type_ids':['5629652273987584', '5685925472370688', '5695159920492544']}, 
	{'type':0, 'title':'Play Some More Games', 'item_type_ids':['5695159920492544', '5685925472370688', '5629652273987584']}]

	resp = jsonify({'layout_data': layout_data})
	resp.status_code = 200
	return resp



# Note: This is a POST method to allow for search queries with spaces/non-alphabetic characters 
# For example: If a user presses a ' ' or '?' or '#' a regular GET request with a query parameter will fail
@app.route('/discovery/search_item_types', methods=['POST'])
def search_item_types():

	json_data = request.get_json()
	query = json_data.get('query', '')
	layout_data = [{'type':1, 'id':'5695159920492544'}, {'type':1, 'id':'5685925472370688'}]

	resp = jsonify({'layout_data': layout_data})
	resp.status_code = 200
	return resp



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