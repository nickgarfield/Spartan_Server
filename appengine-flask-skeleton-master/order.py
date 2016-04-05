from flask import Flask,request,json,jsonify,Response,abort
import logging
from google.appengine.ext import ndb
from google.appengine.api import search
from models import User,Listing,Item_Type,Order
from error_handlers import InvalidUsage,ServerError

app = Flask(__name__)


# Create a new order, put into Datastore, send requests to neighbors within 25 miles
radius_miles = 25 # Miles
METERS_PER_MILE = 1609.344 # Meters
# curl -H "Content-Type: application/json" -X POST -d @test_jsons/order.json https://bygo-client-server.appspot.com/order/create
@app.route('/order/create', methods=['POST'])
def create_order():
	json_data 	= request.get_json()
	user_id 	= json_data.get('user_id','')
	type_id 	= json_data.get('type_id', '')
	geo_point 	= json_data.get('geo_point', '')
	duration	= json_data.get('duration', '')
	time_frame	= json_data.get('time_frame', '')
	rental_fee	= json_data.get('rental_fee', '')

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

	# given geo_point format: 'lat, lon' (sent as a string)
	# need to convert to ndb.GeoPt..
	geopt_array = geo_point.replace(' ','').split(',')
	geo_point = ndb.GeoPt(float(geopt_array[0]), float(geopt_array[1]))

	# Create Order object
	o = Order(renter=user_key, item_type=type_key, geo_point=geo_point, rental_duration=int(duration),
				rental_time_frame=time_frame, rental_fee=int(rental_fee), status='Requested')
	o_key = o.put()

	new_order = search.Document(
			doc_id=str(o_key.id()),
			fields=[search.TextField(name='type_id', value=str(type_id)),
					search.TextField(name='owner_id', value=str(ouser_id)),
					search.GeoField(name='location', value=search.GeoPoint(u.home_address.geo_point.lat, u.home_address.geo_point.lon))])
	index = search.Index(name='Order')
	index.put(new_order)


	# Calculate radius in meters
	radius_meters = radius_miles*METERS_PER_MILE

	# Get all of the Listings local to the renter matching the item_type they want
	query_string = 'distance(location, geopoint('+str(geo_point)+')) < '+str(radius_meters)+' AND type_id='+str(type_id)+' AND NOT owner_id='+str(user_id)
	owners_listings_ids, num_results = get_matched_listings_ids(query_string)

	# Send notification to each owner that somebody in the are wants their item
	for matched_listing in owners_listings_ids:
		send_notification(matched_listing['listing_id'], matched_listing['owner_id'])

	# FIXME: What to send back?
	data = {'order_id':str(o_key.id()),	'matching listings found':num_results}

	resp = jsonify(data)
	resp.status_code = 201
	logging.info('Order successfully created: %s', data)
	return resp



# Given a user, get his/her listings and check if there are any orders they can fulfill
# curl https://bygo-client-server.com/order/get_possible/user_id=<int:user_id>
@app.route('/order/get_possible/user_id=<int:user_id>', methods=['GET'])
def get_possible_orders(user_id):
	# Check to see if the user exists
	u = User.get_by_id(int(user_id))
	if u is None:
		raise InvalidUsage('UserID does not match any existing user', status_code=400)
	user_key = ndb.Key('User', int(user_id))

	user_item_type_ids = []
	qry = Listing.query(Listing.owner==user_key)
	# for listing in qry.fetch(projection=['item_type']):
	for listing in qry.fetch():
		item_type_id = listing.item_type.id()
		if item_type_id not in user_item_type_ids:
			user_item_type_ids.append(item_type_id)

	logging.debug('user_item_type_ids: %s', user_item_type_ids)

	radius_meters = radius_miles*METERS_PER_MILE
	distance_query_string = 'distance(location, geopoint('+str(u.home_address.geo_point.lat)+','+str(u.home_address.geo_point.lat)+')) < '+str(radius_meters)
	# not_self_query_string = 'NOT owner_id = '+str(user_id)
	item_type_ids_query_string ='type_id = ('+' OR '.join(str(elem) for elem in user_item_type_ids) + ')'

	# query_string = ' AND '.join([distance_query_string,not_self_query_string,item_type_ids_query_string])
	query_string = ' AND '.join([distance_query_string,item_type_ids_query_string])

	logging.debug('query_string: %s', query_string)


	matched_orders, num_results = get_matched_orders(item_type_ids_query_string)

	data = []
	for order in matched_orders:
		data += [{'order_id':order['order_id'], 'type_id':order['type_id']}]

	resp = jsonify({'matched_orders':data})
	resp.status_code = 200
	logging.info('%d matched orders found: %s', num_results, data)
	return resp



MaxNumReturn = 200
# Helper function that returns a list of listings and their respective owners' info given a a query_string
def get_matched_listings_ids(query_string):
	index = search.Index(name='Listing')
	try:
		results = index.search(search.Query(query_string=query_string,
						options=search.QueryOptions(limit=MaxNumReturn)))
	except search.Error:
		raise ServerError('Search failed', status_code=400)

	owners_listings_ids = []
	for matched_listing in results:
		owners_listings_ids += [{'listing_id':int(matched_listing.doc_id), 'owner_id':int(matched_listing.field('owner_id').value)}]
		# owners_listings_ids += [(int(matched_listing.doc_id), int(matched_listing.field('owner_id').value))]

	num_results = results.number_found if results.number_found < MaxNumReturn else MaxNumReturn

	return owners_listings_ids, num_results



def get_matched_orders(query_string):
	index = search.Index(name='Order')
	try:
		results = index.search(search.Query(query_string=query_string,
						options=search.QueryOptions(limit=MaxNumReturn)))
	except search.Error:
		raise ServerError('Search failed', status_code=400)

	matched_orders = []
	for order in results:
		matched_orders += [{'order_id':int(order.doc_id), 'type_id':int(order.field('type_id').value)}]

	num_results = results.number_found if results.number_found < MaxNumReturn else MaxNumReturn

	return matched_orders, num_results





# Helper function to send a push notification to the owner
def send_notification(listing_id, owner_id):
	# TODO
	logging.info('Notification sent to owner %d for listing %d.', owner_id, listing_id)
	return None


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