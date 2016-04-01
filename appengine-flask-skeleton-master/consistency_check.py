# This file is for internal consistency checks between Datastore and Search API

from flask import Flask,request,json,jsonify,Response,abort
import logging
import global_vars
from google.appengine.ext import ndb
from google.appengine.api import search
from gcloud import storage
from models import User, Listing, Item_Type, Verification
from error_handlers import InvalidUsage

app = Flask(__name__)

# curl https://bygo-client-server.appspot.com/consistency_check/users
@app.route('/consistency_check/users', methods=['DELETE'])
def user_consistency_check():
	index = search.Index(name='User')

	# Number of users that did not exist in Datastore
	# that were cleared from Search API
	users_to_clear = []
	users_cleared = 0

	# Get all users indexed in the Seach API
	user_ids = get_all_documents(index=index)

	# If user exists in Search but not Datastore, DELETE
	if user_ids is not None:
		for user_id in user_ids:
			u = User.get_by_id(int(user_id))
			if u is None:
				users_to_clear.append(user_id)
				index.delete(user_id)
				users_cleared += 1

				client = storage.Client()
				bucket = client.get_bucket(global_vars.USER_IMG_BUCKET)

				for user_img_blob in bucket.list_blobs(prefix=user_id):
					# bucket.delete_blob(user_img_blob.name)
					user_img_blob.delete()


	# Deleting one by one isn't very efficient, can do up to 200 at a time
	# users_cleared = len(users_to_clear)
	# n = 0
	# while n < users_cleared:
	# 	index.delete(users_to_clear[n:n+users_cleared])
	# 	n+=200

	# num_iters = users_cleared/200
	# last_itr = users_cleared%200

	# for n in range(0, num_iters):
	# 	temp = 200*n
	# 	index.delete(users_to_clear[temp:temp+199])

	logging.debug('Users deleted: %s', users_to_clear)
	logging.info('Users cleared from Search API: %d', users_cleared)

	# Return response
	return 'Users cleared from Search API: ' + str(users_cleared), 200




# curl https://bygo-client-server.appspot.com/consistency_check/listings
@app.route('/consistency_check/listings', methods=['DELETE'])
def listing_consistency_check():
	index = search.Index(name='Listing')

	# Number of listings that did not exist in Datastore
	# that were cleared from Search API
	listings_to_clear = []
	listings_cleared = 0

	# Get all listings indexed in the Seach API
	listing_ids = get_all_documents(index=index)

	# If listing exists in Search but not Datastore, DELETE
	if listing_ids is not None:
		for listing_id in listing_ids:
			l = Listing.get_by_id(int(listing_id))
			if l is None:
				listings_to_clear.append(listing_id)
				index.delete(listing_id)
				listings_cleared += 1

				client = storage.Client()
				bucket = client.get_bucket(global_vars.LISTING_IMG_BUCKET)

				for listing_img_blob in bucket.list_blobs(prefix=listing_id):
					listing_img_blob.delete()




	logging.debug('Listings deleted: %s', listings_to_clear)
	logging.info('Listings cleared from Search API: %d', listings_cleared)
	
	# Return response
	return 'Listings cleared from Search API: ' + str(listings_cleared), 200




# curl https://bygo-client-server.appspot.com/consistency_check/item_types
@app.route('/consistency_check/item_types', methods=['DELETE'])
def item_type_consistency_check():
	index = search.Index(name='Item_Type')

	# Number of item_types that did not exist in Datastore
	# that were cleared from Search API
	item_types_to_clear = []
	item_types_cleared = 0

	# Get all item_types indexed in the Seach API
	item_type_ids = get_all_documents(index=index)

	# If item_type exists in Search but not Datastore, DELETE
	if item_type_ids is not None:
		for item_type_id in item_type_ids:
			l = Item_Type.get_by_id(int(item_type_id))
			if l is None:
				item_types_to_clear.append(item_type_id)
				index.delete(item_type_id)
				item_types_cleared += 1

				client = storage.Client()
				bucket = client.get_bucket(global_vars.ITEM_TYPE_IMG_BUCKET)

				for item_type_img_blob in bucket.list_blobs(prefix=item_type_id):
					item_type_img_blob.delete()


	logging.debug('Item_Types deleted: %s', item_types_to_clear)
	logging.info('Item_Types cleared from Search API: %d', item_types_cleared)
	
	# Return response
	return 'Item_Types cleared from Search API: ' + str(item_types_cleared), 200





def get_all_documents(index):
	# users_to_clear = []
	doc_ids = []

	index_range = index.get_range(ids_only=True, limit=1000)

	while len(index_range) > 1:
		for document in index_range:
			doc_ids.append(document.doc_id)

		index_range = index.get_range(start_id=index_range[-1].doc_id, ids_only=True, limit=1000)

	logging.debug('Current entries in Search:%s', doc_ids)
	return doc_ids




	# index_range = index.get_range(start_id=start_id, ids_only=True, limit=1000)
	# doc_ids = [document.doc_id for document in index_range]
	# for document in index_range:
	# 	doc_ids += document.doc_id 
	# for user_id in user_ids:
	# 	u = User.get_by_id(int(user_id))
	# 	if u is None:
	# 		users_to_clear.append(user_id)

	# if index_range is not None:
	# 	doc_ids += get_all_documents(index=index, start_id=index_range[-1].doc_id)
	# else:
	# 	return doc_ids