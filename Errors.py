#WIP, more coming
class SyntaxError(Exception):
	# base class for Exception raised in parser
	def __init__(self, message):
		super().__init__(message)

class RuntimeError(Exception):
	# base class for Exception raised in parser
	def __init__(self, message):
		super().__init__(message)
