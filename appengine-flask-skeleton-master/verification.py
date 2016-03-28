from flask import Flask
from flask import request
from flask import json
from flask import jsonify
from random import randint
from twilio.rest import TwilioRestClient
from google.appengine.ext import ndb
from models import User, Verification
from main import InvalidUsage
import datetime


app = Flask(__name__)


# Configure Twilio keys 
# FIXME: These are TEST API Keys. Production version of the code will require different keys
TWILIO_ACCOUNT_SID = "AC6072db26faf5d50711552e99dfa61a72" 
TWILIO_AUTH_TOKEN = "51dafc97f504b143551f096a74eebba2"

# If the user doesn't verify within 30 minutes, the verification code will expire
VERIFICATION_TIMEOUT_LIMIT = 1800

# Required number of digits in the verification code
VERIFICATION_CODE_SIZE = 6


# Generate a random n digit number
def generate_verification_code(n):
	lower = 10**(n-1)
	upper = 10**n - 1
	return randint(lower,upper)


# Send a verification code to the user's phone number
@app.route('/verification/phone_number/send_code/user_id=<int:user_id>')
def send_code(user_id):
	# Check if the user_id is valid
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('UserID does not match any existing user', status_code=401)

	# Check if the user has a phone number
	if u.phone_number is None:
		u.phone_number_verification = None
		u.put()
		raise InvalidUsage('Phone number is missing', status_code=412)

	# Check if the user's phone number is already verified
	if u.phone_number_verification is not None:
		if u.phone_number_verification.is_verified:
			raise InvalidUsage('Phone number is already verified', status_code=400)

	# Generate the verification code
	verification_code = generate_verification_code(VERIFICATION_CODE_SIZE)

	# Mark the expected verification code and send time
	u.phone_number_verification = Verification(code=verification_code)
	u.put()

	# Send the verification code to the user's phone number
	twilio_client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
	message = twilio_client.messages.create(to=u.phone_number, from_="+13093870021", body="Your Bygo verification code is {}".format(verification_code))

	return 200



# Check that the verification code the user has entered matches the expected verification code
@app.route('/verification/phone_number/check_code', methods=['POST'])
def check_code():
	# Get the request data
	json_data = request.get_json()
	verification_code = int(json_data.get('verification_code',''))
	user_id = int(json_data.get('user_id',''))

	# Check if the user_id is valid
	u = User.get_by_id(user_id)
	if u is None:
		raise InvalidUsage('UserID does not match any existing user', status_code=400)

	# Check is there is a valid distribution time
	if u.phone_number_verification is None:
		raise InvalidUsage('No verification code has been sent', status_code=400)

	# Check to make sure the user has not removed their phone number
	if u.phone_number is None:
		u.phone_number_verification = None
		u.put()
		raise InvalidUsage('Phone number is missing', status_code=412)

	# Check if the user's phone number is already verified
	if u.phone_number_verification.is_verified:
		raise InvalidUsage('Phone number is already verified', status_code=400)

	# Check if the verification code has timed out
	elapsed_time = datetime.datetime.now() - u.phone_number_verification.distribution_datetime
	if elapsed_time.total_seconds() > VERIFICATION_TIMEOUT_LIMIT:
		raise InvalidUsage('Verification code is no longer valid', status_code=419)

	# Check if the verification code matches the expected code
	if u.phone_number_verification.code != verification_code:
		u.phone_number_verification = None
		u.put()
		raise InvalidUsage('Verification code did not match', status_code=400)

	# Mark the user's phone number as verified
	u.phone_number_verification.is_verified = True
	u.put()
	return 'Success', 200


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