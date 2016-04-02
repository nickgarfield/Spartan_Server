from flask import Flask,request,json,jsonify,Response,abort
import datetime, time
# import requests
from google.appengine.ext import ndb
from google.appengine.api import search
from gcloud import storage
from models import User,Listing,Meeting_Time,Meeting_Location,Meeting_Event,Rent_Event 
from error_handlers import InvalidUsage

app = Flask(__name__)


@app.route('/rent_event/propose/listing_id=<int:listing_id>/renter_id=<int:renter_id>', methods=['POST'])
def propose_rent_request(listing_id,renter_id):
	json_data 						= request.get_json()
	rental_rate 					= float(json_data.get('rental_rate',''))
	rental_time 					= int(json_data.get('rental_time',''))
	rental_time_frame 				= json_data.get('rental_time_frame','')
	message 						= json_data.get('message','')
	proposed_meeting_times_data 	= json_data.get('proposed_meeting_times','')
	proposed_meeting_location_ids 	= json_data.get('proposed_meeting_location','')

	# Check to see if the listing exists
	l = Listing.get_by_id(listing_id)
	if l is None:
		raise InvalidUsage('ListingID does not match any existing listing', status_code=400)	

	o_key = l.owner
	r_key = ndb.Key('User', renter_id)

	# Check to see if owner == renter
	if o_key == r_key:
		raise InvalidUsage("Cannot request to an item that you own", 400)

	# Check to see if owner and renter exists
	o = o_key.get()
	if o is None:
		raise InvalidUsage('OwnerID does not match any existing user', status_code=400)
	r = r_key.get()
	if r is None:
		raise InvalidUsage('RenterID does not match any existing user', status_code=400)


	# Check that a proposed Rent_Event does not already exist with this listing_id and this renter_id
	rent_events = Rent_Event.query(Rent_Event.listing == l.key).fetch()
	# rent_events = qry.fetch(projection=[Rent_Event.renter,Rent_Event.status])
	# qry1 = qry.filter(Rent_Event.renter == r_key)
	# qry2 = qry1.filter(Rent_Event.status == 'Proposed')
	# re = qry2.fetch()
	for re in rent_events:
		if re.renter == r_key and re.status == 'Proposed':
			raise InvalidUsage('Rent request already proposed!', status_code=400)


	re = Rent_Event(owner=o.key, renter=r.key, listing=l.key, rental_rate=rental_rate, rental_time=rental_time, rental_time_frame=rental_time_frame, message=message, status='Proposed')


	proposed_meeting_times = []
	for proposed_meeting_time_data in proposed_meeting_times_data:
		time_str 				= proposed_meeting_time_data['time']
		time 					= datetime.datetime.strptime(time_str, '%Y %m %d %H:%M:%S')
		duration 				= float(proposed_meeting_time_data['duration'])
		is_available 			= bool(proposed_meeting_time_data['is_available'])
		proposed_meeting_time 	= Proposed_Meeting_Time(time=time, duration=duration, is_available=is_available)
		proposed_meeting_times.append(proposed_meeting_time)

	proposed_meeting_locations = []
	for location_id in proposed_meeting_location_ids:
		location_key = ndb.Key('Meeting_Location', int(location_id))
		proposed_meeting_locations.append(location_key)

	# Create start_meeting_event
	sme = Meeting_Event(owner=o.key, renter=r.key, listing=l.key, deliverer='Owner', status='Proposed', proposed_meeting_times=proposed_meeting_times, proposed_meeting_locations=proposed_meeting_locations)

	start_meeting_event_key 	= sme.put()
	re.start_meeting_event 		= start_meeting_event_key
	rent_event_key 				= re.put()


	# TODO: Ask Nick how push notification stuff works..
	# Send Push Notification to the Owner informing them of the new Rent Request
	# if owner.notification_tokens is not None:
	# if len(o.notification_tokens) > 0:
		# message_url 		= 'http://gcm-http.googleapis.com/gcm/send'
		# message_headers 	= {'Authorization':'key=AIzaSyBca5FNN9IUIwZuZFECDWL-jEkgMRQofW0', 'Content-Type':'application/json'}
		# message_title 		= 'New Rent Request'
		# message_body 		= renter.first_name + ' wants to borrow your ' + listing.name
		# message_sound 		= 'default'
		# m_data 				= {'type':'Rent_Request_Proposed', 'meeting_id':start_meeting_event_key.id(), 'event_id':str(event_id)}
		# message_note		= {'title':message_title, 'body':message_body, 'sound':message_sound, 'badge':1}
		# message_data		= {'data':m_data, 'content_available':True, 'priority':'high', 'to':owner.notification_tokens[0], 'notification':message_note}
    	# message_response 	= requests.post(message_url, headers=message_headers, json=message_data)

	data = {'event_id':rent_event_key.id(), 'start_meeting_id':start_meeting_event_key.id(), 'date_created':re.date_created}
	resp 				= jsonify(data)
	resp.status_code 	= 201
	return resp




# Accept a rent request
@app.route('/rent_event/accept/rent_event_id=<int:rent_event_id>', methods=['POST'])
def accept_rent_request(rent_event_id):
	json_data 	= request.get_json()
	time_str 	= json_data.get('time','')
	location_id = int(json_data.get('location_id',''))

	# Get the Rent_Event, starting Meeting_Event, and Listing
	re 		= Rent_Event.get_by_id(rent_event_id)
	sme 	= re.start_meeting_event.get()
	l 		= re.listing.get()
	r 		= re.renter.get()
	o 		= re.owner.get()

	# Create end_meeting_event exactly rental_time*rental_time_frame away
	if re.rental_time_frame == 'Hourly':
		return_time = sme.time + datetime.timedelta(hours=re.rental_time)
	if re.rental_time_frame == 'Daily':
		return_time = sme.time + datetime.timedelta(days=re.rental_time)
	if re.rental_time_frame == 'Weekly':
		return_time = sme.time + datetime.timedelta(days=7*re.rental_time)

	eme = Meeting_Event(owner=o.key, renter=r.key, listing=l.key, deliverer='Renter', status='Scheduled', time=return_time, location=sme.location)
	end_meeting_event_key = eme.put()

	# Mark the response time
	re.date_responded = datetime.datetime.now()

	# Update the Meeting_Event to Scheduled and add the time and location
	time 			= datetime.datetime.strptime(time_str, '%Y %m %d %H:%M:%S')
	sme.time 		= time
	sme.location 	= ndb.Key('Meeting_Location', location_id)
	sme.status 		= 'Scheduled'
	sme.put()

	# Set Rent_Event status to 'Scheduled Start'	
	re.status 		= 'Scheduled Start'
	re.end_meeting_event = end_meeting_event_key
	re.put()

	# Set Listing status to 'reserved'
	l.status 		= 'Reserved'
	l.renter 		= re.renter
	l.put()


	# Send Push Notification to the Renter that their request was accepted
	# if renter.notification_tokens is not None:
	# if len(renter.notification_tokens) > 0:
		# message_url 		= 'http://gcm-http.googleapis.com/gcm/send'
		# message_headers 	= {'Authorization':'key=AIzaSyBca5FNN9IUIwZuZFECDWL-jEkgMRQofW0', 'Content-Type':'application/json'}
		# message_title 		= 'Rent Request Accepted'
		# message_body 		= owner.first_name + ' accepted your request'
		# message_sound 		= 'default'
		# m_data 				= {'type':'Rent_Request_Accepted', 'event_id':str(event_id), 'status':'Scheduled Start', 'meeting_id':str(m.key.id()), 'meeting_status':'Scheduled', 'listing_id':str(l.key.id()), 'listing_status':'Reserved'}
		# message_note		= {'title':message_title, 'body':message_body, 'sound':message_sound, 'badge':1}
		# message_data		= {'data':m_data, 'content_available':True, 'priority':'high', 'to':renter.notification_tokens[0], 'notification':message_note}
   		# message_response 	= requests.post(message_url, headers=message_headers, json=message_data)
	
	# Create response 
	data = {'event_id':rent_event_id, 'rent_event_status':re.status, 'start_meeting_id':sme.key.id(), 'end_meeting_id':end_meeting_event_key.id(), 'listing_id':l.key.id()}
	resp 				= jsonify(data)
	resp.status_code 	= 200
	return resp

'''
@app.route('/rent/reject_rent_request', methods=['POST'])
def reject_rent_request():
	json_data 	= request.get_json()
	event_id 	= int(json_data.get('event_id', ''))

	# Get the Rent_event and starting Meeting_Event
	e 		= Rent_Event.get_by_id(event_id)
	m 		= Meeting_Event.get_by_id(e.start_meeting_event.id())
	renter 	= User.get_by_id(e.renter.id())
	owner 	= User.get_by_id(e.owner.id())

	# Mark the response time
	now = datetime.datetime.now()
	e.date_responded = now

	# Update the Meeting_Event and Rent_Event to Rejected
	status 		= 'Rejected'
	e.status 	= status
	m.status 	= status
	m.put()
	e.put()

	# Send Push Notification to the Renter that their request was rejected
	if len(renter.notification_tokens) > 0:
		message_url 		= 'http://gcm-http.googleapis.com/gcm/send'
		message_headers 	= {'Authorization':'key=AIzaSyBca5FNN9IUIwZuZFECDWL-jEkgMRQofW0', 'Content-Type':'application/json'}
		message_title 		= 'Rent Request Rejected'
		message_body 		= owner.first_name + ' declined your request'
		message_sound 		= 'default'
		m_data 				= {'type':'Rent_Request_Rejected', 'event_id':str(event_id), 'status':status, 'meeting_id':str(m.key.id()), 'meeting_status':status}
		message_note		= {'title':message_title, 'body':message_body, 'sound':message_sound, 'badge':0}
		message_data		= {'data':m_data, 'content_available':True, 'priority':'high', 'to':renter.notification_tokens[0], 'notification':message_note}
		message_response 	= requests.post(message_url, headers=message_headers, json=message_data)

	# Create response
	data = {'event_id':str(event_id), 'status':status, 'meeting_id':str(m.key.id()), 'meeting_status':status}
	resp 				= jsonify(data)
	resp.status_code 	= 200
	return resp
'''


# Get a user's rent requests (other users asking to borrow an item)
@app.route('/rent_event/get_rent_events/user_id=<int:user_id>', methods=['GET'])
def get_user_rent_requests(user_id):
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('User ID does not match any existing user', 400)

	u_key = ndb.Key('User', user_id)
	# rent_requests = Rent_Event.query(Rent_Event.owner == u_key).fetch()
	rent_requests = Rent_Event.query(Rent_Event.owner == u_key, Rent_Event.status == 'Proposed').fetch()

	data = []
	for re in rent_requests:
		re_data = {'listing_id':re.listing.id(), 'date_received':re.date_created,'renter_id':re.renter.id(), 
					'rental_time':re.rental_time, 'rental_time_frame':re.rental_time_frame, 
					'rental_rate':re.rental_rate}
		data += [re_data]

	resp = jsonify({'listings':data})
	resp.status_code = 200
	return resp



# Get a specific rent event
@app.route('/rent_event/get_rent_event/rent_event_id=<int:rent_event_id>', methods=['GET'])
def get_rent_event(rent_event_id):
	# Get the rent event from Datastore
	e = Rent_Event.get_by_id(rent_event_id)

	event_id 				= str(e.key.id())
	owner_id 				= str(e.owner.id())
	renter_id 				= str(e.renter.id())
	listing_id 				= str(e.listing.id())
	rental_rate 			= float(e.rental_rate)
	rental_time 			= e.rental_time
	rental_time_frame		= e.rental_time_frame
	status 					= e.status
	start_meeting_event_id 	= None
	if e.start_meeting_event is not None:
		start_meeting_event_id 	= str(e.start_meeting_event.id())
	end_meeting_event_id 	= None
	if e.end_meeting_event is not None:
		end_meeting_event_id 	= str(e.end_meeting_event.id())

	data = { 'event_id':str(event_id), 'owner_id':owner_id, 'renter_id':renter_id, 'listing_id':listing_id, 'rental_rate':rental_rate, 'rental_time':rental_time, 'rental_time_frame':rental_time_frame, 'status':status, 'start_meeting_event_id':start_meeting_event_id, 'end_meeting_event_id':end_meeting_event_id }
	resp = jsonify(data)
	resp.status_code = 200
	return resp




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
