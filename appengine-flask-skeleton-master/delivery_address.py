from flask import Flask,request,json,jsonify,Response,abort
from google.appengine.ext import ndb
import logging, googlemaps, global_vars, requests
from models import User,Delivery_Address
from error_handlers import InvalidUsage, ServerError

app = Flask(__name__)

# Create a new delivery_address paramater for the user object and put into Datastore
# Update_delivery_address should be done using the same function
@app.route('/delivery_address/create/user_id=<int:user_id>', methods=['POST'])
def create_delivery_address(user_id):
	json_data 		= request.get_json()
	name 			= json_data.get('name','')
	address_line_1 	= json_data.get('address_line_1','')
	address_line_2 	= json_data.get('address_line_2','')
	city 			= json_data.get('city','')
	state 			= json_data.get('state','')
	zip_code 		= json_data.get('zip_code','')
	country			= json_data.get('country','')
	# geo_point 		= json_data.get('geo_point','')

	# Check to see if the user exists
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('UserID does not match any existing user', status_code=400)

	# Get latitude/longitude info
	address = ', '.join([address_line_1, address_line_2, city, state, zip_code, country])
	gmaps = googlemaps.Client(key=global_vars.API_KEY)
	logging.debug('Google Maps API key: %s', gmaps.key)
	geocode_result = gmaps.geocode(address)
	if not geocode_result:
		raise InvalidUsage('Location not found, please enter a valid address.', status_code=400)

	location = geocode_result[0]['geometry']['location']
	geo_point = ndb.GeoPt(location['lat'],location['lng'])
	place_id = geocode_result[0]['place_id']


	a = Delivery_Address(name=name, address=address, geo_point=geo_point, google_places_id=place_id)

	# Wrap in try/except block?
	try:
		u.home_address = a
		u.put()
	except ndb.Error:
		raise ServerError('Datastore put failed.', 500)

	logging.info('User home address successfully created: %s', address)
	return "User home address successfully created.", 201




# Delete a delivery address from a user object in Datastore
@app.route('/delivery_address/delete/user_id=<int:user_id>', methods=['DELETE'])
def delete_delivery_address(user_id):
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('UserID does not match any existing user', status_code=400)

	if u.home_address is not None:
		u.home_address = None
	else:
		raise InvalidUsage('No User home address found.', status_code=400)
	
	try:
		u.put()
	except ndb.Error:
		raise ServerError('Datastore put failed.', 500)

	logging.info('User home address successfully deleted')
	return "User home address successfully deleted.", 204




# Get a user's home address
@app.route('/delivery_address/get/user_id=<int:user_id>', methods=['GET'])
def get_user_home_address(user_id):
	# Check to make sure the User exists
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User ID does not match any existing user', 400)

	if u.home_address is None:
		data = {'address_line_1':'', 'address_line_2':'','city':'', 'state':'', 'zip_code':'', 
				'country':''}
	else:
		data = {'address_line_1':u.home_address.address_line_1, 'address_line_2':u.home_address.address_line_2,
				'city':u.home_address.city, 'state':u.home_address.state, 'zip_code':u.home_address.zip_code, 
				'country':u.home_address.country}

	# Return response
	resp = jsonify({'address_data':data})
	resp.status_code = 200
	logging.info('User address data successfully retrieved: %s', data)
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