from flask import Flask,request,json,jsonify,Response,abort
from google.appengine.ext import ndb
from models import Delivery_Address
from geopy.geocoders import Nominatim
from error_handlers import InvalidUsage

app = Flask(__name__)

# Create a new delivery_address object and put into Datastore
# Update_delivery_address should be done using the same function
@app.route('/delivery_address/create/user_id=<user_id>', methods=['POST'])
def create_delivery_address(user_id):
	json_data 		= request.get_json()
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
	address_info = [address_line_1, address_line_2, city, state, zip_code, country]
	geolocator = Nominatim()
	location = geolocator.geocode(" ".join(address_info))
	geo_point = ndb.GeoPt(location.latitude,location.longitude)


	a = Delivery_Address(address_line_1=address_line_1, address_line_1=address_line_1, 
						 city=city, state=state, country=country, zip_code=zip_code, 
						 geo_point=geo_point)

	# Wrap in try/except block?
	u.home_address = a
	u.put()

	return "User home address successfully created.", 201




# Delete a delivery address from Datastore
@app.route('/delivery_address/delete/user_id=<user_id>', methods=['DELETE'])
def delete_delivery_address(user_id):
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('UserID does not match any existing user', status_code=400)

	u.home_address = None
	u.put()

	return "User home address successfully deleted.", 200




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