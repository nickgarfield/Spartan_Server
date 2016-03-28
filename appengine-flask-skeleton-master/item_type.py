# These functions will all be internal. Users cannot create item_types nor tags.
# This might change in the future.

from flask import Flask,request,json,jsonify,Response,abort
import global_vars
from google.appengine.ext import ndb
from google.appengine.api import search
from gcloud import storage
from models import Item_Type
from error_handlers import InvalidUsage

app = Flask(__name__)

# To reload the Item_Type data, use the command:
# curl -H "Content-Type: application/json" -X POST -d @item_type_data.json https://bygo-client-server.appspot.com/item_type/load
@app.route('/item_type/load', methods=['POST'])
def load_item_types():

	# Delete all the Item_Type entities
	ndb.delete_multi(Item_Type.query().fetch(keys_only=True))

	# Add the new Item_Type entities
	json_data = request.get_json()
	for item_type_data in json_data:
		name = item_type_data['name']
		value = item_type_data['value']
		delivery_fee = item_type_data['delivery_fee']
		i = Item_Type(name=name, delivery_fee=delivery_fee, value=value)
		
		# Add the Item_Type to the Datastore
		try:
			i.put()
		except:
			abort(500)

	return 'Success', 201


# To create 
# curl -F "userfile=@PlayStation_4_Console.jpg" https://bygo-client-server.appspot.com/item_type/create_image/item_type_id=5629652273987584
@app.route('/item_type/create_image/item_type_id=<int:type_id>', methods=['POST'])
def create_item_type_image(type_id):
	userfile = request.files['userfile']
	filename = userfile.filename

	# Check if listing exists
	i = Item_Type.get_by_id(type_id)
	if i is None:
		raise InvalidUsage('Item_Type does not exist!', status_code=400)

	# Create client for interfacing with Cloud Storage API
	client = storage.Client()
	bucket = client.get_bucket(global_vars.ITEM_TYPE_IMG_BUCKET)

	# Calculating size this way is not very efficient. Is there another way?
	userfile.seek(0, 2)
	size = userfile.tell()
	userfile.seek(0)

	# upload the item image
	path = str(type_id)+'/'+filename
	image = bucket.blob(blob_name=path)
	image.upload_from_file(file_obj=userfile, size=size, content_type='image/jpeg')
	
	# Hacky way of making the image public..
	image.acl.all().grant_read()
	image.acl.save()

	resp = jsonify({'image_path':path, 'image_media_link':image.media_link})
	resp.status_code = 201
	return resp


@app.route('/item_type/get/item_type_id=<int:type_id>', methods=['GET'])
def get_item_type(type_id):

	i = Item_Type.get_by_id(type_id)
	if i is None:
		raise InvalidUsage('Item_Type id does not match any existing user', 400)

	data = {'name':i.name, 'value':i.value, 'delivery_fee':i.delivery_fee}
		
	# Return response
	resp = jsonify(data)
	resp.status_code = 200
	return resp

# Create a new item_type and put into Datastore and Search App
# @app.route('/item_type/create', methods=['POST'])
# def create_item_type():
# 	json_data 			= request.get_json()
# 	name 				= json_data.get('name','')
# 	tag_id 				= json_data.get('tag_id', '')

	# # Check to see if the user exists
	# user = User.get_by_id(int(user_id))
	# if user is None:
	# 	raise InvalidUsage('UserID does not match any existing user', status_code=400)
	# user_key = ndb.Key('User', int(user_id))

	# # Check to see if the tag exists
	# tag = Tag.get_by_id(int(tag_id))
	# if tag is None:
	# 	raise InvalidUsage('TagID does not match any existing tag', status_code=400)
	# tag_key = ndb.Key('Tag', int(tag_id))

	# # Set default listing data
	# status = 'Available'
	# rating = -1.0

	# # Add listing to Datastore
	# l = Listing(owner=user_key, tag=tag_key, status=status, rating=rating)

	# try:
	# 	listing_key = l.put()
	# 	listing_id	= str(listing_key.id())
	# except:
	# 	abort(500)

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
	# data = {'listing_id':listing_id, 'owner_id':user_id, 'renter_id':None, 'tag_id':tag_id, 'status':status, 'item_description':None, 'rating':rating}
	# resp = jsonify(data)
	# resp.status_code = 201
	# return resp
	# return 'item_type successfully created.', 201






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