from google.appengine.ext import ndb

class Delivery_Address(ndb.Model):
	address_line_1 	= ndb.StringProperty(required=True, indexed=False)
	address_line_2 	= ndb.StringProperty(indexed=False)
	city 			= ndb.StringProperty(indexed=False)
	state 			= ndb.StringProperty(indexed=False)
	country 		= ndb.StringProperty(indexed=False)
	zip_code 		= ndb.StringProperty(indexed=False)
	geo_point 		= ndb.GeoPtProperty(indexed=False)

class User(ndb.Model):
	first_name 												= ndb.StringProperty(required=True)
	last_name 												= ndb.StringProperty(required=True)
	notification_tokens										= ndb.StringProperty(repeated=True)
	phone_number 											= ndb.StringProperty()
	is_phone_number_verified 								= ndb.BooleanProperty(default=False)
	email 													= ndb.StringProperty(required=True)
	is_email_verified 										= ndb.BooleanProperty(default=False)
	password 												= ndb.StringProperty()
	facebook_id												= ndb.StringProperty()
	signup_method 											= ndb.StringProperty(required=True, choices=['Facebook', 'Email', 'Phone Number'])
	home_address											= ndb.StructuredProperty(kind=Delivery_Address)
	credit 													= ndb.FloatProperty(default=0.0) # How much money the user owes at the end of the week
	debit 													= ndb.FloatProperty(default=0.0) # How much money the user has credited to their account (i.e. $15 from signing up or promotions)
	date_created 											= ndb.DateTimeProperty(auto_now_add=True)
	date_last_modified 										= ndb.DateTimeProperty(auto_now=True)
	status													= ndb.StringProperty(default='Active', choices=['Active', 'Inactive', 'Deactivated'])
	profile_picture_path									= ndb.StringProperty()

class Verification(ndb.Model):
	account													= ndb.KeyProperty(required=True, kind=User)
	phone_number_verification_code 							= ndb.IntegerProperty()
	email_verification_code 								= ndb.IntegerProperty()
	verification_code_distribution_datetime 				= ndb.DateTimeProperty(auto_now_add=True)


class Item_Type(ndb.Model):
	name 				= ndb.StringProperty(required=True, indexed=True)
	tags				= ndb.StringProperty(repeated=True)
	delivery_fee	 	= ndb.FloatProperty(required=True, indexed=False)
	total_value 		= ndb.FloatProperty(indexed=False)
	daily_rate 			= ndb.FloatProperty(indexed=False)
	weekly_rate			= ndb.FloatProperty(indexed=False)
	semester_rate 		= ndb.FloatProperty(indexed=False)

class Listing(ndb.Model):
	owner 				= ndb.KeyProperty(required=True, kind=User)
	renter 				= ndb.KeyProperty(kind=User)
	status 				= ndb.StringProperty(required=True, default='Available', choices=['Available', 'Rented', 'Unavailable', 'Damaged', 'Deleted'])
	item_type  			= ndb.KeyProperty(required=True, kind=Item_Type)
	item_description 	= ndb.StringProperty()
	location			= ndb.GeoPtProperty(required=True)
	rating		 		= ndb.FloatProperty(default=-1.0)	# Value of -1 is used to signal no rating
	date_created		= ndb.DateTimeProperty(auto_now_add=True)
	date_last_modified 	= ndb.DateTimeProperty(auto_now=True)


class Request(ndb.Model):
	owner 					= ndb.KeyProperty(required=True, kind=User)
	renter 					= ndb.KeyProperty(required=True, kind=User)
	listing 				= ndb.KeyProperty(required=True, kind=Listing)
	renter_location 		= ndb.GeoPtProperty(indexed=False)
	status 					= ndb.StringProperty(required=True, choices=['Inquired', 'Owner accepted', 'Owner rejected', 'Renter accepted', 'Renter rejected'])
	date_created			= ndb.DateTimeProperty(auto_now_add=True)
	owner_response_time 	= ndb.DateTimeProperty()
	renter_response_time 	= ndb.DateTimeProperty()


class Rent_Event(ndb.Model):
	request 					= ndb.KeyProperty(required=True, kind=Request, indexed=False)
	owner 						= ndb.KeyProperty(required=True, kind=User)
	renter 						= ndb.KeyProperty(required=True, kind=User)
	owner_location				= ndb.StructuredProperty(kind=Delivery_Address)
	renter_location				= ndb.StructuredProperty(kind=Delivery_Address)
	listing 					= ndb.KeyProperty(required=True, kind=Listing)
	rental_rate 				= ndb.FloatProperty()
	rental_duration				= ndb.IntegerProperty()
	rental_time_frame 			= ndb.StringProperty(choices=['Hourly', 'Daily', 'Weekly', 'Semesterly'])
	rental_fee					= ndb.FloatProperty()
	delivery_fee				= ndb.FloatProperty()
	total_rental_cost			= ndb.FloatProperty()
	status 						= ndb.StringProperty(required=True, choices=['Scheduled', 'In Transit', 'Ongoing', 'Concluded', 'Canceled'])
	delivery_pickup_time		= ndb.DateTimeProperty() # Bygo picks item up from owner
	delivery_dropoff_time		= ndb.DateTimeProperty() # Bygo drops item off at renter
	return_pickup_time			= ndb.DateTimeProperty() # Bygo picks item up from renter
	return_dropoff_time			= ndb.DateTimeProperty() # Bygo drops item off at owner

