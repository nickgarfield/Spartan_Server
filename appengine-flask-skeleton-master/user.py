from flask import Flask,request,json,jsonify,Response,abort
import logging
import global_vars
from google.appengine.ext import ndb
from google.appengine.api import search
from gcloud import storage
from models import User, Listing, Verification, Delivery_Address
from error_handlers import InvalidUsage

app = Flask(__name__)

# Create a new user object and put into Datastore and Search App
@app.route('/user/create', methods=['POST'])
def create_user():
	json_data = request.get_json()
	first_name = json_data.get('first_name','')
	last_name = json_data.get('last_name','')
	email = json_data.get('email','')
	phone_number = json_data.get('phone_number','')
	facebook_id = json_data.get('facebook_id','')
	password = json_data.get('password','')
	signup_method = json_data.get('signup_method','')


	# If object string is empty '', then set object = None
	if not bool(password):
		password = None
	if not bool(phone_number):
		phone_number = None
	if not bool(email):
		email = None		
	if not bool(facebook_id):
		facebook_id = None

	if signup_method == 'Phone Number':
		if not phone_number:
			raise InvalidUsage('Phone number is required!', 400)
		if not password:
			raise InvalidUsage('Password is required!', 400)
	else:
		if not facebook_id:
			raise InvalidUsage('No facebook id given!', 400)
		

	# Validate password, email, and phone_number
	validate_password(password)
	validate_email(email)
	validate_phone(phone_number)

	# Add user to Datastore
	u = User(first_name=first_name, last_name=last_name, phone_number=phone_number, email=email, 
			 password=password, facebook_id=facebook_id, signup_method=signup_method)
	try:
		user_key = u.put()
		user_id  = str(user_key.id())
	except:
		abort(500)

	# Add user to Search App
	new_user = search.Document(
		doc_id=user_id,
		fields=[search.TextField(name='name', value=first_name+' '+last_name),
				search.TextField(name='phone_number', value=phone_number),
				search.TextField(name='email', value=email)])
	
	try:
		index = search.Index(name='User')
		index.put(new_user)

	except:
		abort(500)

	user_img_media_link = get_img_medialink(u.profile_picture_path)

	data = {'user_id':str(user_id), 'first_name':u.first_name, 'last_name':u.last_name, 
			'phone_number':u.phone_number, 'email':u.email, 'password':u.password, 
			'facebook_id':u.facebook_id, 'credit':u.credit, 'debit':u.debit, 'status':u.status,
			'image_path':u.profile_picture_path, 'image_media_link':user_img_media_link}
	
	resp = jsonify(data)
	resp.status_code = 201
	logging.info('%s', data)
	return resp




# Delete a user object from Search API and set User status to 'Deactivated'
@app.route('/user/deactivate/user_id=<int:user_id>', methods=['DELETE'])
def deactivate_user(user_id):# Edit Datastore entity
	# Get the user
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User not found', 400)

	if u.status == 'Deactivated':
		raise InvalidUsage('User is already deactivated!', 400)

	# Set user status to 'Deactivated'
	u.status = 'Deactivated'

	# Set all of the user's listings to 'Deactivated'
	u_key = ndb.Key('User', user_id)
	qry = Listing.query(Listing.owner == u_key)
	listings = qry.fetch()
	for l in listings:
		if l.status != 'Deleted':
			l.status = 'Deactivated'
			try:
				l.put()
			except:
				abort(500)

	# Add the updated user status to the Datastore
	try:
		u.put()
	except:
		abort(500)

	# Delete Search App entity
	try:
		index = search.Index(name='User')
		index.delete(str(user_id))
	except:
		abort(500)

	# Return response
	return 'User successfully deactivated', 204



@app.route('/user/delete_from_search/user_id=<int:user_id>', methods=['DELETE'])
def delete_from_search(user_id):
	# Delete Search App entity
	try:
		index = search.Index(name='User')
		index.delete(str(user_id))
	except:
		abort(500)

	return 'User successfully deleted from Search API.', 204



# Reactivate a user by adding it to Search API and set User status to 'Active'
@app.route('/user/reactivate/user_id=<int:user_id>', methods=['POST'])
def reactivate_user(user_id):
	# Get the user
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User ID does not match any existing user', 400)

	if u.status == 'Active':
		raise InvalidUsage('User is already active!', 400)

	# Set user status to 'Active'
	u.status = 'Active'

	u.phone_number_verification.is_verified = False
	u.email_verification.is_verified = False
	

	# Add the updated user status to the Datastore
	try:
		u.put()
	except:
		abort(500)


	# Add reactivated user to the Search App
	reactivated_user = search.Document(
			doc_id=str(user_id),
			fields=[search.TextField(name='name', value=u.first_name+' '+u.last_name),
					search.TextField(name='phone_number', value=u.phone_number),
					search.TextField(name='email', value=u.email)])
	try:
		index = search.Index(name='User')
		index.put(reactivated_user)
	except:
		abort(500)

	user_img_media_link = get_img_medialink(u.profile_picture_path)


	# TODO: Return HomeAddress data
	data = {'user_id':str(user_id), 'first_name':u.first_name, 'last_name':u.last_name, 
			'phone_number':u.phone_number, 'email':u.email, 'password':u.password, 
			'facebook_id':u.facebook_id, 'credit':u.credit, 'debit':u.debit, 'status':u.status,
			'image_path':u.profile_picture_path, 'image_media_link':user_img_media_link}

	resp = jsonify(data)
	resp.status_code = 200
	return resp

	# Return response
	# return 204




# Update a user's information
@app.route('/user/update/user_id=<int:user_id>', methods=['POST'])
def update_user(user_id):
	json_data 		= request.get_json()
	first_name 		= json_data.get('first_name','')
	last_name 		= json_data.get('last_name','')
	email 			= json_data.get('email','')
	phone_number 	= json_data.get('phone_number','')

	if not bool(first_name):
		raise InvalidUsage('First name cannot be left empty.', 400)
	if not bool(last_name):
		raise InvalidUsage('Last name cannot be left empty.', 400)
	if not bool(email):
		raise InvalidUsage('Email cannot be left empty.', 400)		
	if not bool(phone_number):
		raise InvalidUsage('Phone number cannot be left empty.', 400)

	# Get the user
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User not found', 400)

	# Validate email and phone number before updating anything
	if u.email != email:
		validate_email(email)
	if u.phone_number != phone_number:
		validate_phone(phone_number)

	# If the phone number is different, phone number is no longer verified 
	if phone_number != u.phone_number:
		if u.phone_number_verification is not None:
			u.phone_number_verification.is_verified = False

	# If the email is different, email is no longer verified
	if email != u.email:
		if u.email_verification is not None:
			u.email_verification.is_verified = False
	
	# Update user attributes
	u.first_name 		 = first_name
	u.last_name 		 = last_name
	u.email 			 = email
	u.phone_number 		 = phone_number
	
	# Add the updated user to the Datastore
	try:
		u.put()
	except:
		abort(500)

	# Add updated user to the Search App
	updated_user = search.Document(
			doc_id=str(user_id),
			fields=[search.TextField(name='name', value=first_name+' '+last_name),
					search.TextField(name='phone_number', value=phone_number),
					search.TextField(name='email', value=email)])
	try:
		index = search.Index(name='User')
		index.put(updated_user)
	except:
		abort(500)

	user_img_media_link = get_img_medialink(u.profile_picture_path)

	data = {'user_id':str(user_id), 'first_name':u.first_name, 'last_name':u.last_name, 
			'phone_number':u.phone_number, 'email':u.email, 'password':u.password, 
			'facebook_id':u.facebook_id, 'credit':u.credit, 'debit':u.debit, 'status':u.status,
			'image_path':u.profile_picture_path, 'image_media_link':user_img_media_link}

	resp = jsonify(data)
	resp.status_code = 200
	logging.info('%s', data)
	return resp


@app.route('/user/update_home_address/user_id=<int:user_id>', methods=['POST'])
def update_home_address(user_id):
	json_data = request.get_json()
	name = json_data.get('name', '')
	google_places_id = json_data.get('google_places_id', '')
	address = json_data.get('address', '')
	geo_point = json_data.get('geo_point', '')

	# Get the user
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User not found', 400)

	u.home_address = Delivery_Address(address=address, name=name, google_places_id=google_places_id, geo_point=ndb.GeoPt(geo_point))

	try:
		u.put()
	except:
		abort(500)

	data = {'home_address_address':address, 'home_address_name':name, 'home_address_google_places_id':google_places_id}
	resp = jsonify(data)
	resp.status_code = 201
	logging.info('User home address successfully created: %s', data)
	return resp



# Add/update a profile picture for a user
@app.route('/user/create_user_image/user_id=<int:user_id>', methods=['POST'])
def create_user_image(user_id):
	userfile = request.files['userfile']
	filename = userfile.filename

	# Check to see if the user exists
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User not found', status_code=400)

	# Create client for interfacing with Cloud Storage API
	client = storage.Client()
	bucket = client.get_bucket(global_vars.USER_IMG_BUCKET)

	# Calculating size this way is not very efficient. Is there another way?
	userfile.seek(0, 2)
	size = userfile.tell()
	userfile.seek(0)

	# Upload the user's profile image
	path = str(user_id)+'/'+filename
	image = bucket.blob(blob_name=path)
	image.upload_from_file(file_obj=userfile, size=size, content_type='image/jpeg')

	# Hacky way of making our files public..
	image.acl.all().grant_read()
	image.acl.save()

	u.profile_picture_path = path
	u.put()

	data = {'image_path':u.profile_picture_path, 'image_media_link':image.media_link}
	resp = jsonify(data)
	resp.status_code = 201
	logging.info('%s', data)
	return resp




# Delete a user's profile picture
@app.route('/user/delete_user_image/user_id=<int:user_id>', methods=['DELETE'])
def delete_user_image(user_id):
	# Check to see if the user exists
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User not found', status_code=400)

	path = u.profile_picture_path
	if path is None:
		raise InvalidUsage('User has no profile picture.', status_code=400)

	# Create client for interfacing with Cloud Storage API
	client = storage.Client()
	bucket = client.get_bucket(global_vars.USER_IMG_BUCKET)

	bucket.delete_blob(path)

	u.profile_picture_path = None
	u.put()

	return 'User profile pciture successfully deleted.', 204



# Get a user's information
@app.route('/user/user_id=<int:user_id>', methods=['GET'])
def get_user(user_id):
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User not found', 400)

	user_img_media_link = get_img_medialink(u.profile_picture_path)

	# Return User data
	data = {'user_id':str(user_id), 'first_name':u.first_name, 'last_name':u.last_name, 
			'phone_number':u.phone_number, 'email':u.email, 'password':u.password, 
			'facebook_id':u.facebook_id, 'credit':u.credit, 'debit':u.debit, 'status':u.status,
			'image_path':u.profile_picture_path, 'image_media_link':user_img_media_link}

	resp = jsonify(data)
	resp.status_code = 200
	logging.info('%s', data)
	return resp



# FIXME: Generally should not be using POST methods unless writing to the database..
@app.route('/user/login', methods=['POST'])
def login_user():
	json_data 			= request.get_json()
	login_id 			= json_data.get('login_id','')
	password 			= json_data.get('password','')
	notification_token 	= json_data.get('notification_token', '')

	# Get the user from the database
	q = User.query(User.phone_number == login_id, User.password == password)
	u = q.get()

	# Raise an error if the user's phone number and password do not match
	if u is None:
		raise InvalidUsage('User not found', status_code=400)

	# Get user's profile picture
	user_img_media_link = get_img_medialink(u.profile_picture_path)

	# Return the relevant data in JSON format
	data = {'user_id':str(u.key.id()), 'first_name':u.first_name, 'last_name':u.last_name, 
			'phone_number':u.phone_number, 'email':u.email, 'password':u.password, 
			'facebook_id':u.facebook_id, 'credit':u.credit, 'debit':u.debit, 'status':u.status,
			'image_path':u.profile_picture_path, 'image_media_link':user_img_media_link,
			'home_address_name':u.home_address.name if u.home_address else None, 'home_address_address':u.home_address.address if u.home_address else None, 'home_address_google_places_id':u.home_address.google_places_id if u.home_address else None }

	resp = jsonify(data)
	resp.status_code = 200
	logging.info('Successful phone number login.')
	return resp


@app.route('/user/login_facebook', methods=['POST'])
def login_facebook_user():
	json_data 			= request.get_json()
	facebook_id 		= json_data.get('facebook_id','')
	notification_token 	= json_data.get('notification_token', '')
	
	q = User.query(User.facebook_id == facebook_id)
	u = q.get()

	# Raise an error if no user is found with this particular Facebook ID
	if u is None:
		raise InvalidUsage('User not found', status_code=400)

	# Get user's profile picture
	user_img_media_link = get_img_medialink(u.profile_picture_path)

	# Return the relevant data in JSON format
	data = {'user_id':str(u.key.id()), 'first_name':u.first_name, 'last_name':u.last_name, 
			'phone_number':u.phone_number, 'email':u.email, 'password':u.password, 
			'facebook_id':u.facebook_id, 'credit':u.credit, 'debit':u.debit, 'status':u.status,
			'image_path':u.profile_picture_path, 'image_media_link':user_img_media_link,
			'home_address_name':u.home_address.name if u.home_address else None, 'home_address_address':u.home_address.address if u.home_address else None, 'home_address_google_places_id':u.home_address.google_places_id if u.home_address else None }

	resp = jsonify(data)
	resp.status_code = 200
	logging.info('Successful Facebook login.')
	return resp



# Check if the given password satisfies our requirements
MIN_PASSWORD_SIZE = 8
def validate_password(password):
	if password is not None and len(password) < MIN_PASSWORD_SIZE:
		raise InvalidUsage('Password is too short.', status_code=400)

# Check if a user is already registered with the given email address
def validate_email(email):
	if email is not None:
		q = User.query(ndb.AND(User.email == email, User.status == 'Active'))
		u = q.get()
		if u is not None:
			raise InvalidUsage('Email address already registered', status_code=400)

# Check if a user is already registered with the given phone number
def validate_phone(phone_number):
	if phone_number is not None:
		q = User.query(ndb.AND(User.phone_number == phone_number, User.status == 'Active'))
		u = q.get()
		if u is not None:
			raise InvalidUsage('Phone number already registered', status_code=400)


# Helper function that returns an image media link from cloudstorage given the path
def get_img_medialink(path):
	img_media_link = None
	if path != None:
		client = storage.Client()
		bucket = client.get_bucket(global_vars.USER_IMG_BUCKET)
		img = bucket.get_blob(path)
		img_media_link = img.media_link
		
	return img_media_link


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