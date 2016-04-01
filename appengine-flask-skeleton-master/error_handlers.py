### InvalidUsage class used to report user errors
class InvalidUsage(Exception):
	status_code = 400
	
	def __init__(self, message, status_code=None, payload=None):
		Exception.__init__(self)
		self.message = message
		if status_code is not None:
			self.status_code = status_code
		self.payload = payload

	def to_dict(self):
		rv = dict(self.payload or ())
		rv['message'] = self.message
		return rv

### ServerError class used to report server errors
class ServerError(Exception):
	status_code = 500

	def __init__(self, message, status_code=None, payload=None):
		Exception.__init__(self)
		self.message = message
		self.status_code = status_code
		self.payload = payload

	def to_dict(self):
		rv = dict(self.payload or ())
		rv['message'] = self.message
		return rv