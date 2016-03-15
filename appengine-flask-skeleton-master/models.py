from google.appengine.ext import ndb

# class Category(ndb.Model):
# 	name 				= ndb.StringProperty(required=True)

# class CategoryWeight(ndb.Model):
# 	category 			= ndb.KeyProperty(required=True, kind=Category)
# 	weight				= ndb.FloatProperty(required=True)

class Tag(ndb.Model):
	name 				= ndb.StringProperty(required=True, indexed=True)
	disribution_cost 	= ndb.FloatProperty(required=True, indexed=False)
	total_value 		= ndb.FloatProperty(indexed=False)
	daily_rate 			= ndb.FloatProperty(indexed=False)
	weekly_rate			= ndb.FloatProperty(indexed=False)
	semester_rate 		= ndb.FloatProperty(indexed=False)


class User(ndb.Model):
	first_name 												= ndb.StringProperty(required=True, indexed=False)
	last_name 												= ndb.StringProperty(required=True, indexed=False)
	notification_tokens										= ndb.StringProperty(repeated=True, indexed=False)
	phone_number 											= ndb.StringProperty(indexed=True)
	is_phone_number_verified 								= ndb.BooleanProperty(default=False, indexed=False)
	email 													= ndb.StringProperty(required=True)
	is_email_verified 										= ndb.BooleanProperty(default=False, indexed=False)
	password 												= ndb.StringProperty(indexed=True)
	facebook_id												= ndb.StringProperty(indexed=True)
	signup_method 											= ndb.StringProperty(required=True, choices=['Facebook', 'Phone Number'], indexed=False)
	credit 													= ndb.FloatProperty(default=0.0, indexed=False) # How much money the user owes at the end of the week
	debit 													= ndb.FloatProperty(default=0.0, indexed=False) # How much money the user has credited to their account (i.e. $15 from signing up or promotions)
	status													= ndb.StringProperty(default='Active', choices=['Active', 'Inactive', 'Deactivated'], indexed=False)
	profile_picture_path									= ndb.StringProperty()


class Delivery_Address(ndb.Model):
	user 			= ndb.KeyProperty(required=True, kind=User)
	address_line_1 	= ndb.StringProperty(required=True, indexed=False)
	adderss_line_2 	= ndb.StringProperty(indexed=False)
	city 			= ndb.StringProperty(indexed=False)
	state 			= ndb.StringProperty(indexed=False)
	country 		= ndb.StringProperty(indexed=False)
	zip_code 		= ndb.StringProperty(indexed=False)
	geo_point 		= ndb.GeoPtProperty(indexed=False)


class Verification(ndb.Model):
	user									= ndb.KeyProperty(required=True, kind=User)
	phone_number_verification_code 			= ndb.IntegerProperty()
	email_verification_code 				= ndb.IntegerProperty()
	verification_code_distribution_datetime = ndb.DateTimeProperty(auto_now_add=True)


class Listing(ndb.Model):
	owner 				= ndb.KeyProperty(required=True, kind=User)
	renter 				= ndb.KeyProperty(kind=User)
	tag 				= ndb.KeyProperty(kind=Tag)
	status 				= ndb.StringProperty(required=True, choices=['Available', 'Reserved', 'Rented', 'Unavailable', 'Damaged', 'Unlisted', 'Deactivated', 'Deleted'])
	item_description 	= ndb.StringProperty()
	rating		 		= ndb.FloatProperty()	# Value of -1 is used to signal no rating

class Request(ndb.Model):
	user 		= ndb.KeyProperty(required=True, kind=User)
	tag 		= ndb.KeyProperty(required=True, kind=Tag)
	geo_point 	= ndb.GeoPtProperty(indexed=False)


'''
class Meeting_Location(ndb.Model):
	user 				= ndb.KeyProperty(required=True, kind=User)
	google_places_id 	= ndb.StringProperty(required=True)
	name 				= ndb.StringProperty(required=True)
	address 			= ndb.StringProperty(required=True)
	date_created		= ndb.DateTimeProperty(auto_now_add=True)
	date_last_modified 	= ndb.DateTimeProperty(auto_now=True)
	is_private 			= ndb.BooleanProperty(required=True) # Whether or not any user can see this address

class Meeting_Time(ndb.Model):
	time 			= ndb.DateTimeProperty(required=True) # The time of the meeting proposal
	duration		= ndb.FloatProperty(required=True, default=30.0) # Duration of the timeframe in minutes
	is_available	= ndb.BooleanProperty(required=True)

class Meeting_Event(ndb.Model):
	owner 						= ndb.KeyProperty(required=True, kind=User)
	renter 						= ndb.KeyProperty(required=True, kind=User)
	listing 					= ndb.KeyProperty(required=True, kind=Listing)
	deliverer 					= ndb.StringProperty(required=True, choices=['Owner', 'Renter']) # person who has the item
	proposed_meeting_times 		= ndb.StructuredProperty(Meeting_Time, repeated=True)
	proposed_meeting_locations 	= ndb.KeyProperty(kind=Meeting_Location, repeated=True)
	status 						= ndb.StringProperty(required=True, choices=['Proposed', 'Scheduled', 'Delayed', 'Canceled', 'Rejected', 'Concluded'])
	time 						= ndb.DateTimeProperty()
	location 					= ndb.KeyProperty(kind=Meeting_Location)

	# FIXME: Are these necessary? 
	owner_confirmation_time 	= ndb.DateTimeProperty()	# Moment that the Owner confirms the Handoff
	renter_confirmation_time 	= ndb.DateTimeProperty()	# Moment that the Renter confirms the Handoff

'''
	
class Rent_Event(ndb.Model):
	renter 						= ndb.KeyProperty(required=True, kind=User)
	listing 					= ndb.KeyProperty(required=True, kind=Listing)
	rental_rate 				= ndb.FloatProperty()
	rental_duration 			= ndb.IntegerProperty()
	rental_timeframe 			= ndb.StringProperty(choices=['Hourly', 'Daily', 'Weekly'])
	status 						= ndb.StringProperty(required=True, choices=['Inquired', 'Proposed', 'Scheduled Start', 'Ongoing', 'Scheduled End', 'Canceled', 'Rejected', 'Concluded'])


	
# class Message(ndb.Model):
# 	sender 			= ndb.KeyProperty(required=True, kind=User)
# 	receiver 		= ndb.KeyProperty(required=True, kind=User)
# 	text 			= ndb.StringProperty()
# 	date_created 	= ndb.DateTimeProperty()


# class Meeting_Message(Message):
# 	event = ndb.KeyProperty(required=True, kind=Meeting_Event)



'''
class ItemReview(ndb.Model):
	user 				= ndb.KeyProperty(required=True, indexed=True, kind=User) #, collection_name="itemReviews")
	item 				= ndb.KeyProperty(required=True, indexed=True, kind=Item) #, collection_name="reviews")
	rating 				= ndb.FloatProperty(required=True, indexed=True, default=0.0)
	comment 			= ndb.TextProperty(required=False, indexed=False)
	date 				= ndb.DateTimeProperty(required=True, indexed=True)
	# TODO: More required fields?

class RenterReview(ndb.Model):
	user 				= ndb.KeyProperty(required=True, indexed=True, kind=User) #, collection_name="renterReviews")
	renter 				= ndb.KeyProperty(required=True, indexed=True, kind=User) #, collection_name="reviews")
	rating 				= ndb.FloatProperty(required=True, indexed=True, default=0.0)
	comment 			= ndb.TextProperty(required=False, indexed=False)
	date 				= ndb.DateTimeProperty(required=True, indexed=True)
	# TODO: More required fields?

class TimeDispute(ndb.Model):
	owner 					= ndb.KeyProperty(required=True, indexed=True, kind=User) #, collection_name="time_disputes_as_owner")
	renter 					= ndb.KeyProperty(required=True, indexed=True, kind=User) #, collection_name="time_disputes_as_renter")
	rentEvent 				= ndb.KeyProperty(required=True, indexed=True, kind=RentEvent) #, collection_name="time_disputes")
	timeDifference 			= ndb.FloatProperty(required=True, indexed=True) # Time dispute in hours
	meeting 				= ndb.KeyProperty(required=True, indexed=False, kind=MeetingEvent) #, collection_name="time_dispute")

'''