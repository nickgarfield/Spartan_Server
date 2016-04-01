# These functions will all be internal. Users cannot create item_types nor tags.
# This might change in the future.

from flask import Flask,request,json,jsonify,Response,abort
import logging
import global_vars
from google.appengine.ext import ndb
from google.appengine.api import search
from gcloud import storage
from models import Item_Type
from error_handlers import InvalidUsage, ServerError

app = Flask(__name__)

# To reload the Item_Type data, use the command:
# curl -H "Content-Type: application/json" -X POST -d @test_jsons/item_type_list.json https://bygo-client-server.appspot.com/item_type/load_data
@app.route('/item_type/load_data', methods=['POST'])
def load_item_types():

	# Delete all the Item_Type entities in Datastore
	ndb.delete_multi(Item_Type.query().fetch(keys_only=True))

	# Delete all Item_Type entities in Search API
	doc_index = search.Index(name='Item_Type')
	# looping because get_range by default returns up to 100 documents at a time
	while True:
		# Get a list of documents populating only the doc_id field and extract the ids.
		document_ids = [document.doc_id for document in doc_index.get_range(ids_only=True)]
		if not document_ids:
			break
		# Delete the documents for the given ids from the Index.
		doc_index.delete(document_ids)


	# Add the new Item_Type entities
	json_data = request.get_json()
	for item_type_data in json_data:
		name = item_type_data['name']
		value = item_type_data['value']
		delivery_fee = item_type_data['delivery_fee']
		tags = item_type_data['tags']
		
		
		try:
			# Add the Item_Type to the Datastore
			i = Item_Type(name=name, delivery_fee=delivery_fee, value=value)
			item_type_key = i.put()
			type_id = str(item_type_key.id())

			# Add the Item_Type to the Search API
			new_item = search.Document(
				doc_id=str(type_id),
				fields=[search.TextField(name='name', value=name),
						search.TextField(name='tags', value=tags)])

			index = search.Index(name='Item_Type')
			index.put(new_item)

		except ndb.Error:
			raise ServerError('Datastore put failed.', 500)
		except search.Error:
			raise ServerError('Search API put failed.', 500)
		except:
			abort(500)

	logging.info('Item_types successfully loaded.')
	return 'Item_types successfully loaded.', 201



# Function to ADD a single ITEM_TYPE
# curl -H "Content-Type: application/json" -X POST -d @test_jsons/new_item_type.json https://bygo-client-server.appspot.com/item_type/create
@app.route('/item_type/create', methods=['POST'])
def create_item_type():
	json_data 		= request.get_json()
	name 			= json_data.get('name','')
	value 			= json_data.get('value','')
	delivery_fee	= json_data.get('delivery_fee','')
	tags 			= json_data.get('tags','')
	it = Item_Type(name=name, delivery_fee=delivery_fee, value=value)

	try:
		# Add the Item_Type to the Datastore
		it = Item_Type(name=name, delivery_fee=delivery_fee, value=value)
		item_type_key = it.put()
		type_id = str(item_type_key.id())

		# Add the Item_Type to the Search API
		new_item = search.Document(
			doc_id=str(type_id),
			fields=[search.TextField(name='name', value=name),
					search.TextField(name='tags', value=tags)])

		index = search.Index(name='Item_Type')
		index.put(new_item)

	except ndb.Error:
		raise ServerError('Datastore put failed.', 500)
	except search.Error:
		raise ServerError('Search API put failed.', 500)
	except:
		abort(500)

	data = {'item_type_id':type_id, 'name':it.name, 'value':it.value, 
			'delivery_fee':it.delivery_fee, 'img_path':it.img_path, 'tags':tags}
	resp = jsonify(data)
	resp.status_code = 201
	logging.info('Item_type successfully added: %s', data)
	return resp



# Function to delete an item_type from Datastore and Search
# curl -X DELETE https://bygo-client-server.appspot.com/item_type/delete/item_type_id=<int:type_id>
@app.route('/item_type/delete/item_type_id=<int:type_id>', methods=['DELETE'])
def delete_item_type(type_id):
	it = Item_Type.get_by_id(type_id)
	if it is None:
		raise InvalidUsage('Item_Type ID does not match any existing item_type', 400)

	try:
		# Delete the Item_Type from Datastore
		it.key.delete()

		# Delete the Item_Type from Search API
		index = search.Index(name='Item_Type')
		index.delete(str(type_id))

	except ndb.Error:
		raise ServerError('Datastore delete failed.', 500)
	except search.Error:
		raise ServerError('Search API delete failed.', 500)
	except:
		abort(500)

	logging.info('Item_type successfully deleted: %d', type_id)
	return 'Item_type successfully deleted.', 204





# Function to ADD a single TAG to an existing item_type
# @app.route('/item_type/create_tag/item_type_id=<int:type_id>', methods=['POST'])
# def create_item_type_tag(type_id):
# 	json_data 		= request.get_json()
# 	tag 			= json_data.get('tag','')

# 	qry = Item_Type.query(Item_Type.name == name).fetch(keys_only=True)
# 	if qry is None:
# 		raise InvalidUsage('No matching item_type found!', 400)

# 	try:
# 		# Add the Item_Type to the Search API
# 		new_item = search.Document(
# 			doc_id=type_id,
# 			fields=[search.TextField(name='name', value=name),
# 					search.TextField(name='tags', value=tags)])
# 		index = search.Index(name='Item_Type')
# 		index.put(new_item)
# 	except:
# 		abort(500)


# 	return 'Item_type successfully added.', 201



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



@app.route('/item_type/get/type_id=<int:type_id>', methods=['GET'])
def get_item_type(type_id):

	# Check to make sure the Item_Type exists
	i = Item_Type.get_by_id(type_id)
	if i is None:
		raise InvalidUsage('Item_Type id does not match any existing user', 400)

	item_type_img_media_links = get_item_type_images(type_id)

	data = {'type_id':str(type_id), 'name':i.name, 'value':i.value, 'delivery_fee':i.delivery_fee, 'image_media_links':item_type_img_media_links}
		
	# Return response
	resp = jsonify(data)
	resp.status_code = 200
	return resp


# Return an Item_Type's image links
def get_item_type_images(type_id):	
	client = storage.Client()
	bucket = client.get_bucket(global_vars.ITEM_TYPE_IMG_BUCKET)

	item_type_img_objects = bucket.list_blobs(prefix=str(type_id))
	item_type_img_media_links = []
	for img_object in item_type_img_objects:
		item_type_img_media_links += [img_object.media_link]

	return item_type_img_media_links



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