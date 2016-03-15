from flask import Flask,request,json,jsonify,Response,abort
import datetime, time
import global_vars
from google.appengine.ext import ndb
from google.appengine.api import search
from gcloud import storage
from models import User,Listing
from error_handlers import InvalidUsage

app = Flask(__name__)


# Create a new listing object and put into Datastore and Search App
@app.route('/listing/create', methods=['POST'])
def create_listing(user_id):
	json_data 			= request.get_json()
	user_id 			= json_data.get('user_id','')
	tag_id 				= json_data.get('tag_id', '')

	# Check to see if the user exists
	user = User.get_by_id(int(user_id))
	if user is None:
		raise InvalidUsage('UserID does not match any existing user', status_code=400)
	user_key = ndb.Key('User', int(user_id))

	# Check to see if the tag exists
	tag = Tag.get_by_id(int(tag_id))
	if tag is None:
		raise InvalidUsage('TagID does not match any existing tag', status_code=400)
	tag_key = ndb.Key('Tag', int(tag_id))

	# Set default listing data
	status = 'Available'
	rating = -1.0

	# Add listing to Datastore
	l = Listing(owner=user_key, tag=tag_key, status=status, rating=rating)

	try:
		listing_key = l.put()
		listing_id	= str(listing_key.id())
	except:
		abort(500)

	# TODO: Add listing to Search App
	# TODO: Get location based on user's current delivery address
	# new_item = search.Document(
	# 	doc_id=listing_id,
	# 	fields=[search.TextField(name='name', value=name),
	# 			search.GeoField(name='location', value=search.GeoPoint(location.lat,location.lon)),
	# 			search.TextField(name='owner_id', value=str(user_id))])

	# try:
	# 	index = search.Index(name='Listing')
	# 	index.put(new_item)
	# except:
	# 	abort(500)

	# Return the new Listing data
	data = {'listing_id':listing_id, 'owner_id':user_id, 'renter_id':None, 'tag_id':tag_id, 'status':status, 'item_description':None, 'rating':rating}
	resp = jsonify(data)
	resp.status_code = 201
	return resp



'''
@app.route('/listing/suggested_rates/total_value=<float:total_value>', methods=['GET'])
def pricing_suggested_rates(total_value):
	half_value = 0.5 * total_value

	# Reasoning: If you rent for 3 days at the hourly rate, you pay for half of the item
	hourly_rate = format(half_value/72.0,'.2f')

	# Reasoning: If you rent for 2 weeks at the daily rate, you pay for half of the item
	daily_rate = format(half_value/14.0,'.2f')

	# Reasoning: If you rent for 5 weeks at the weekly rate, you pay for half of the item
	weekly_rate = format(half_value/5.0,'.2f')

	data = {'hourly_rate':hourly_rate, 'daily_rate':daily_rate, 'weekly_rate':weekly_rate}
	resp = jsonify(data)
	resp.status_code = 200
	return resp
'''




# Delete listing from Search API and set status to 'Deleted' in Datastore
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
	except:
		abort(500)

	# Delete Search App entity
	try:
		index = search.Index(name='Listing')
		index.delete(str(listing_id))
	except:
		abort(500)

	# Return response
	return 204




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
	except:
		abort(500)

	# Add the updated item to the Search API
	# if l.status == 'Available':
	# 	updated_item = search.Document(
	# 			doc_id=str(listing_id),
	# 			fields=[search.TextField(name='name', value=name),
	# 					search.GeoField(name='location', value=search.GeoPoint(l.location.lat,l.location.lon)),
	# 					search.TextField(name='owner_id', value=str(l.owner.id()))])

	# 	try:
	# 		index = search.Index(name='Listing')
	# 		index.put(updated_item)
	# 	except:
	# 		abort(500)
	# else:
	# 	try:
	# 		index = search.Index(name='Listing')
	# 		index.delete(str(listing_id))
	# 	except:
	# 		abort(500)


	# Return the attributes of the new item
	data = {'listing_id':str(listing_id), 'owner_id':str(l.owner.id()), 'renter_id':str(l.renter.id()) if l.renter else None, 'tag_id':str(l.tag.id()), 'status':status, 'item_description':item_description, 'rating':l.rating}
	resp = jsonify(data)
	resp.status_code = 200
	return resp




# Add a listing image
# MAX_NUM_ITEM_IMAGES = 5
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

	resp = jsonify({'image_path':path, 'image_media_link':image.media_link})
	resp.status_code = 201
	return resp



# Delete a listing image
@app.route('/listing/delete_listing_image/path=<path:path>', methods=['DELETE'])
def delete_listing_image(path):
	# Create client for interfacing with Cloud Storage API
	client = storage.Client()
	bucket = client.get_bucket(global_vars.LISTING_IMG_BUCKET)
	
	# Delete the image from the given path
	bucket.delete_blob(path)

	# Return response
	return 204




# Get a listing's info
@app.route('/listing/listing_id=<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
	# Check to make sure the Listing exists
	l = Listing.get_by_id(listing_id)
	if l is None:
		raise InvalidUsage('Listing does not exist!', status_code=400)

	listing_img_media_links = get_listing_images(listing_id)

	# Return the attributes of the new item
	data = {'listing_id':l.key.id(), 'owner_id':str(l.owner.id()), 'renter_id':str(l.renter.id()) if l.renter else None, 'status':l.status,
			'item_description':l.item_description, 'rating':l.rating, 'image_media_links':listing_img_media_links}

	resp = jsonify(data)
	resp.status_code = 200
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
		listing_data = {'listing_id':l.key.id(), 'owner_id':str(l.owner.id()), 'renter_id':str(l.renter.id()) if l.renter else None, 'status':l.status,
			'item_description':l.item_description, 'rating':l.rating, 'image_media_links':get_listing_images(l.key.id())}
		data += [listing_data]

	# Return response
	resp = jsonify({'listings_data':data})
	resp.status_code = 200
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
		listing_data = {'listing_id':l.key.id(), 'owner_id':str(l.owner.id()), 'renter_id':str(l.renter.id()) if l.renter else None, 'status':l.status,
			'item_description':l.item_description, 'rating':l.rating, 'image_media_links':get_listing_images(l.key.id())}
		data += [listing_data]

	# Return response
	resp = jsonify({'listings_data':data})
	resp.status_code = 200
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
	return response

@app.errorhandler(404)
def page_not_found(e):
	"""Return a custom 404 error."""
	return 'Sorry, Nothing at this URL.', 404

@app.errorhandler(500)
def application_error(e):
	"""Return a custom 500 error."""
	return 'Sorry, unexpected error: {}'.format(e), 500