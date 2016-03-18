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


# Create a new item_type and put into Datastore and Search App
@app.route('/item_type/create', methods=['POST'])
def create_item_type():
	json_data 			= request.get_json()
	name 				= json_data.get('name','')
	tag_id 				= json_data.get('tag_id', '')

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
	return 'item_type successfully created.', 201






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