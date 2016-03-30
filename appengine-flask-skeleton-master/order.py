from flask import Flask,request,json,jsonify,Response,abort
from google.appengine.ext import ndb
from google.appengine.api import search
from models import User,Listing,Order
from geopy.geocoders import Nominatim
from error_handlers import InvalidUsage

app = Flask(__name__)


# Create a new order, put into Datastore, send requests to neighbors within 25 miles
radius_miles = 25 # Miles
METERS_PER_MILE = 1609.344 # Meters
@app.route('/order/create', methods=['POST'])
def create_listing():
	json_data 	= request.get_json()
	user_id 	= json_data.get('user_id','')
	type_id 	= json_data.get('type_id', '')
	address		= json_data.get('type_id', '')

	# Check to see if the user exists
	u = User.get_by_id(int(user_id))
	if u is None:
		raise InvalidUsage('UserID does not match any existing user', status_code=400)
	user_key = ndb.Key('User', int(user_id))

	# Check to see if the type_id exists
	item_type = Item_Type.get_by_id(int(type_id))
	if item_type is None:
		raise InvalidUsage('TagID does not match any existing tag', status_code=400)
	type_key = ndb.Key('Item_Type', int(type_id))

	# Get latitude/longitude info
	location = geolocator.geocode(address)
	if location is None:
		raise InvalidUsage('Location not found, please enter a valid address.', status_code=400)


	# Calculate radius in meters
	radius_meters = radius_miles*METERS_PER_MILE

	# Get all of the Listings local to the current user
	query_string = 'distance(location, geopoint('+str(location.latitude)+','+str(location.longitude)+')) < '+str(radius_meters)+' AND NOT owner_id='+str(user_id)

	listing_ids, num_results = get_matched_listings_ids(query_string)

	return 'Orders successfully created.', 201






# Helper function that returns a list of listing_ids info given a a query_string
def get_matched_listings_ids(query_string):
	index = search.Index(name='Listing')
	try:
		results = index.search(search.Query(query_string=query_string,
						options=search.QueryOptions(limit=NumListingsToReturn, ids_only=True)))
	except search.Error:
		abort(500)

	listing_ids = []
	for matched_listing in results:
		listing_ids += [int(matched_listing.doc_id)]

	num_results = results.number_found if results.number_found < NumListingsToReturn else NumListingsToReturn

	return listing_ids, num_results




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