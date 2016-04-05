from flask import Flask,request,json,jsonify,Response,abort
import logging
import global_vars
from google.appengine.ext import ndb
from google.appengine.api import search
from gcloud import storage
from models import User, Listing, Item_Type
from error_handlers import InvalidUsage, ServerError

app = Flask(__name__)


# Create a new listing object and put into Datastore and Search App
@app.route('/listing/create', methods=['POST'])
def create_listing():
	json_data 		= request.get_json()
	user_id 		= json_data.get('user_id','')
	type_id 		= json_data.get('type_id', '')

	# Check to see if the user exists
	u = User.get_by_id(int(user_id))
	if u is None:
		raise InvalidUsage('User not found', status_code=400)
	user_key = ndb.Key('User', int(user_id))

	# Check to see if the tag exists
	item_type = Item_Type.get_by_id(int(type_id))
	if item_type is None:
		raise InvalidUsage('Item type not found', status_code=400)
	type_key = ndb.Key('Item_Type', int(type_id))

	# Check to see if the user has a home address
	if u.home_address is None:
		raise InvalidUsage('Home address not found', status_code=400)


	# Check to see if the phone number is verified
	if u.phone_number is None:
		raise InvalidUsage('Phone number not found', status_code=400)

	if u.phone_number_verification is None or not u.phone_number_verification.is_verified:
		raise InvalidUsage('Phone number not verified', status_code=400)

	# Set default listing data
	status = 'Available'
	rating = -1.0

	try:
		# Add listing to Datastore
		l = Listing(owner=user_key, item_type=type_key, status=status, rating=rating)
		listing_key = l.put()
		listing_id	= str(listing_key.id())

		# Add listing to Search App
		new_item = search.Document(
			doc_id=listing_id,
			fields=[search.TextField(name='type_id', value=str(type_id)),
					search.GeoField(name='location', value=search.GeoPoint(u.home_address.geo_point.lat, u.home_address.geo_point.lon)),
					search.TextField(name='owner_id', value=str(user_id))])

		index = search.Index(name='Listing')
		index.put(new_item)

	except ndb.Error:
		raise ServerError('Datastore put failed.', 500)
	except search.Error:
		raise ServerError('Search API put failed.', 500)
	except:
		abort(500)

	# Return the new Listing data
	data = {'listing_id':str(listing_id), 'owner_id':str(user_id), 'renter_id':None,
			'type_id':str(type_id), 'status':status, 'item_description':None, 
			'rating':rating}
	resp = jsonify(data)
	resp.status_code = 201
	logging.info('Listing successfully created: %s', data)
	return resp




# set status to 'Deleted' in Datastore
@app.route('/listing/delete/listing_id=<int:listing_id>', methods=['DELETE'])
def delete_listing(listing_id):
	# Get the listing
	l = Listing.get_by_id(listing_id)
	if l is None:
		raise InvalidUsage('Listing ID does not match any existing Listing.', 400)

	# Set listing status to 'Deleted'
	l.status = 'Deleted'

	# Add the updated listing status to the Datastore
	try:
		l.put()
	except ndb.Error:
		raise ServerError('Datastore put failed.', 500)

	# Delete Search App entity
	try:
		index = search.Index(name='Listing')
		index.delete(str(listing_id))
	except search.Error:
		raise ServerError('Search API put failed.', 500)

	# Return response
	logging.info('Listing successfully deleted: %d', listing_id)
	return 'Listing successfully deleted.', 204




# Update a listing
@app.route('/listing/update/listing_id=<int:listing_id>', methods=['POST'])
def update_listing(listing_id):
	json_data 		 = request.get_json()
	status 			 = json_data.get('status','')
	item_description = json_data.get('item_description','')

	# Get the listing
	l = Listing.get_by_id(listing_id)
	if l is None:
		raise InvalidUsage('ItemID does not match any existing item', status_code=400)

	# Update the item attributes
	l.item_description 	= item_description
	l.status 			= status

	# Add the updated item to the Datastore
	try:
		l.put()
	except ndb.Error:
		raise ServerError('Datastore put failed.', 500)

	# Return the attributes of the updated item
	data = {'listing_id':str(listing_id), 'owner_id':str(l.owner.id()),
			'renter_id':str(l.renter.id()) if l.renter else None,
			'type_id':str(l.item_type.id()), 'status':status,
			'item_description':item_description, 'rating':l.rating}
	resp = jsonify(data)
	resp.status_code = 200
	logging.info('Listing successfully updated: %s', data)
	return resp



# Add a listing image
@app.route('/listing/create_listing_image/listing_id=<int:listing_id>', methods=['POST'])
def create_listing_image(listing_id):
	userfile = request.files['userfile']
	filename = userfile.filename

	# Check if listing exists
	l = Listing.get_by_id(listing_id)
	if l is None:
		raise InvalidUsage('Listing does not exist!', status_code=400)

	# Create client for interfacing with Cloud Storage API
	client = storage.Client()
	bucket = client.get_bucket(global_vars.LISTING_IMG_BUCKET)

	# Calculating size this way is not very efficient. Is there another way?
	userfile.seek(0, 2)
	size = userfile.tell()
	userfile.seek(0)

	# upload the item image
	path = str(listing_id)+'/'+filename
	image = bucket.blob(blob_name=path)
	image.upload_from_file(file_obj=userfile, size=size, content_type='image/jpeg')
	
	# Hacky way of making the image public..
	image.acl.all().grant_read()
	image.acl.save()

	# Add path to list of img_paths
	try:
		if path not in l.listing_img_paths:
			l.listing_img_paths.append(path)
		l.put()
	except ndb.Error:
		raise ServerError('Datastore put failed.', 500)

	image_data = {'image_path':path, 'image_media_link':image.media_link}
	resp = jsonify(image_data)
	resp.status_code = 201
	logging.info('Listing image successfully uploaded: %s', image_data)
	return resp



# Delete a listing image
@app.route('/listing/delete_listing_image/listing_id=<int:listing_id>/image=<int:image_num>', methods=['DELETE'])
def delete_listing_image(listing_id, image_num):
	# Check if listing exists
	l = Listing.get_by_id(listing_id)
	if l is None:
		raise InvalidUsage('Listing does not exist!', status_code=400)

	path = l.listing_img_paths[image_num]

	# Create client for interfacing with Cloud Storage API
	client = storage.Client()
	bucket = client.get_bucket(global_vars.LISTING_IMG_BUCKET)
	
	# Delete the image from the given path
	bucket.delete_blob(path)

	# Delete path from list of img_paths
	try:
		while path in l.listing_img_paths:
			l.listing_img_paths.remove(path)
		
		l.put()
	
	except ndb.Error:
		raise ServerError('Datastore put failed.', 500)

	# Return response
	logging.info('Listing image successfully deleted: %s', path)
	return 'Listing image successfully deleted.', 204




# Get a listing's info
@app.route('/listing/listing_id=<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
	# Check to make sure the Listing exists
	l = Listing.get_by_id(listing_id)
	if l is None:
		raise InvalidUsage('Listing does not exist!', status_code=400)

	listing_img_media_links = get_listing_images(listing_id)

	# Return the attributes of the listing
	data = {'listing_id':str(l.key.id()), 'owner_id':str(l.owner.id()),
			'item_type_id':str(l.item_type.id()),
			'renter_id':str(l.renter.id()) if l.renter else None,'status':l.status,
			'item_description':l.item_description,'rating':l.rating,
			'image_media_links':listing_img_media_links}

	resp = jsonify(data)
	resp.status_code = 200
	logging.info('Listing info successfully retrieved: %s', data)
	return resp



# Get a user's listings
@app.route('/listing/get_users_listings/user_id=<int:user_id>', methods=['GET'])
def get_users_listings(user_id):
	# Check to make sure the User exists
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User ID does not match any existing user', 400)

	# Fetch Listings
	u_key	= ndb.Key('User', user_id)
	qry 	= Listing.query(Listing.owner == u_key)
	listings = qry.fetch()

	# Parse data
	data = []
	for l in listings:
		listing_img_media_links = get_listing_images(l.key.id())
		listing_data = {'listing_id':str(l.key.id()), 'owner_id':str(l.owner.id()),
						'type_id':str(l.item_type.id()),
						'renter_id':str(l.renter.id()) if l.renter else None,'status':l.status,
						'item_description':l.item_description,'rating':l.rating,
						'image_media_links':listing_img_media_links}
		data += [listing_data]

	# Return response
	resp = jsonify({'listings_data':data})
	resp.status_code = 200
	logging.info('Retrieved listings: %s', data)
	return resp



# Get a user's rented listings
@app.route('/listing/get_users_rented_listings/user_id=<int:user_id>', methods=['GET'])
def get_users_rented_listings(user_id):
	# Check to make sure User exists
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User ID does not match any existing user', 400)

	# Fetch Listings
	u_key	= ndb.Key('User', user_id)
	qry 	= Listing.query(Listing.renter == u_key)
	listings = qry.fetch()

	# Parse data
	data = []
	for l in listings:
		listing_img_media_links = get_listing_images(l.key.id())
		listing_data = {'listing_id':str(l.key.id()), 'owner_id':str(l.owner.id()),
						'type_id':str(l.item_type.id()),
						'renter_id':str(l.renter.id()) if l.renter else None,'status':l.status,
						'item_description':l.item_description,'rating':l.rating,
						'image_media_links':listing_img_media_links}
		data += [listing_data]

	# Return response
	resp = jsonify({'listings_data':data})
	resp.status_code = 200
	logging.info('Retrieved listings: %s', data)
	return resp



# Helper function to return a listing's image links
def get_listing_images(listing_id):	
	client = storage.Client()
	bucket = client.get_bucket(global_vars.LISTING_IMG_BUCKET)

	listing_img_objects = bucket.list_blobs(prefix=str(listing_id))
	listing_img_media_links = []
	for img_object in listing_img_objects:
		listing_img_media_links += [img_object.media_link]

	return listing_img_media_links



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

@app.errorhandler(400)
def handle_user_error(e):
	resp = jsonify(e.to_dict())
	resp.status_code = e.status_code
	return resp

@app.errorhandler(404)
def page_not_found(e):
	"""Return a custom 404 error."""
	return 'Sorry, Nothing at this URL.', 404

@app.errorhandler(500)
def application_error(e):
	"""Return a custom 500 error."""
	return 'Sorry, unexpected error: {}'.format(e), 500