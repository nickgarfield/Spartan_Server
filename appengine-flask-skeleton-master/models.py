from google.appengine.ext import ndb


class Verification(ndb.Model):
	code 					= ndb.IntegerProperty(indexed=False, required=False)
	distribution_datetime 	= ndb.DateTimeProperty(auto_now_add=True, indexed=False)
	is_verified 			= ndb.BooleanProperty(default=False, indexed=False)

class Delivery_Address(ndb.Model):
	name = ndb.StringProperty(indexed=False)
	google_places_id = ndb.StringProperty(indexed=False)
	address = ndb.StringProperty(required=True, indexed=False)
	geo_point = ndb.GeoPtProperty(required=True, indexed=False)

class User(ndb.Model):
	first_name 					= ndb.StringProperty(required=True, indexed=False)
	last_name 					= ndb.StringProperty(required=True, indexed=False)
	notification_tokens			= ndb.StringProperty(repeated=True, indexed=False)
	phone_number 				= ndb.StringProperty()
	phone_number_verification 	= ndb.StructuredProperty(Verification, indexed=False, required=False)
	email 						= ndb.StringProperty(required=True)
	email_verification 			= ndb.StructuredProperty(Verification, indexed=False, required=False)
	password 					= ndb.StringProperty()
	facebook_id					= ndb.StringProperty()
	signup_method 				= ndb.StringProperty(required=True, choices=['Facebook', 'Email', 'Phone Number'], indexed=False)
	home_address				= ndb.StructuredProperty(Delivery_Address, indexed=False)
	credit 						= ndb.FloatProperty(default=0.0, indexed=False) # How much money the user owes at the end of the week
	debit 						= ndb.FloatProperty(default=0.0, indexed=False) # How much money the user has credited to their account (i.e. $15 from signing up or promotions)
	date_created 				= ndb.DateTimeProperty(auto_now_add=True, indexed=False)
	date_last_modified 			= ndb.DateTimeProperty(auto_now=True, indexed=False)
	status						= ndb.StringProperty(default='Active', choices=['Active', 'Inactive', 'Deactivated'])
	profile_picture_path		= ndb.StringProperty(indexed=False)


class Item_Type(ndb.Model):
	name 				= ndb.StringProperty(required=True, indexed=True)
	value 				= ndb.FloatProperty(indexed=True)
	delivery_fee	 	= ndb.FloatProperty(required=True, indexed=False)
	

class Listing(ndb.Model):
	owner 				= ndb.KeyProperty(required=True, kind=User)
	renter 				= ndb.KeyProperty(kind=User)
	status 				= ndb.StringProperty(required=True, default='Available', choices=['Available', 'Rented', 'Unavailable', 'Damaged', 'Deleted'])
	item_type  			= ndb.KeyProperty(required=True, kind=Item_Type, indexed=False)
	item_description 	= ndb.StringProperty(indexed=False)
	rating		 		= ndb.FloatProperty(default=-1.0, indexed=False)	# Value of -1 is used to signal no rating
	listing_img_paths	= ndb.StringProperty(repeated=True, indexed=False)
	date_created		= ndb.DateTimeProperty(auto_now_add=True, indexed=False)
	date_last_modified 	= ndb.DateTimeProperty(auto_now=True, indexed=False)


class Order(ndb.Model):
	owner 					= ndb.KeyProperty(required=True, kind=User)
	renter 					= ndb.KeyProperty(required=True, kind=User)
	listing 				= ndb.KeyProperty(required=True, kind=Listing)
	geo_point 				= ndb.GeoPtProperty(indexed=False)
	status 					= ndb.StringProperty(required=True, choices=['Unfilled', 'Filled', 'Accepted', 'Rejected'])
	date_created			= ndb.DateTimeProperty(auto_now_add=True, indexed=False)
	owner_response_time 	= ndb.DateTimeProperty(indexed=False)
	renter_response_time 	= ndb.DateTimeProperty(indexed=False)


class Delivery_Event(ndb.Model):
	direction 			= ndb.StringProperty(choices=['Pickup', 'Dropoff'])
	listing 			= ndb.KeyProperty(kind=Listing, required=True)
	user 				= ndb.KeyProperty(kind=User, required=True)
	location 			= ndb.StructuredProperty(Delivery_Address, indexed=False)
	scheduled_time 		= ndb.DateTimeProperty(indexed=False)
	confirmation_time 	= ndb.DateTimeProperty(indexed=False)


class Rent_Event(ndb.Model):
	order 				= ndb.KeyProperty(required=True, kind=Order, indexed=False)
	owner 				= ndb.KeyProperty(required=True, kind=User, indexed=False)
	renter 				= ndb.KeyProperty(required=True, kind=User, indexed=False)
	listing 			= ndb.KeyProperty(required=True, kind=Listing, indexed=False)
	rental_rate 		= ndb.FloatProperty(indexed=False)
	rental_duration		= ndb.IntegerProperty(indexed=False)
	rental_time_frame 	= ndb.StringProperty(choices=['Daily', 'Weekly', 'Semesterly'], indexed=False)
	rental_fee			= ndb.FloatProperty(indexed=False)
	delivery_fee		= ndb.FloatProperty(indexed=False)
	total_rental_cost	= ndb.FloatProperty(indexed=False)
	status 				= ndb.StringProperty(required=True, choices=['Scheduled', 'In Transit', 'Ongoing', 'Concluded', 'Canceled'])
	delivery_pickup 	= ndb.KeyProperty(kind=Delivery_Event, indexed=False)
	delivery_dropoff 	= ndb.KeyProperty(kind=Delivery_Event, indexed=False)
	return_pickup 		= ndb.KeyProperty(kind=Delivery_Event, indexed=False)
	return_dropoff 		= ndb.KeyProperty(kind=Delivery_Event, indexed=False)

