class Token():
	pass

class Spell (Token):
	def __str__(self):
		return "Spell"
	def __repr__(self):
		return self.__str__()

class Property (Token):
	def __str__(self):
		return "Property"
	def __repr__(self):
		return self.__str__()

class Condition (Token):
	def __str__(self):
		return "Condition"
	def __repr__(self):
		return self.__str__()

class Chain_end (Token):
	def __str__(self):
		return "Chain_end"
	def __repr__(self):
		return self.__str__()

class Event (Token):
	def __str__(self):
		return "Event"
	def __repr__(self):
		return self.__str__()

class Label (Token):
	def __str__(self):
		return "Label"
	def __repr__(self):
		return self.__str__()

class Call (Token):
	def __str__(self):
		return "Call"
	def __repr__(self):
		return self.__str__()

class Variable (Token):
	def __str__(self):
		return "Variable"
	def __repr__(self):
		return self.__str__()

class Value (Token):
	def __init__(self):
		self.value = 0
	def __str__(self):
		return "Value" + ": " + str(self.value)
	def __repr__(self):
		return self.__str__()

class Bracket (Token):
	def __init__(self):
		self.open = None
	def __str__(self):
		return "Bracket" + ": " + str(self.open)
	def __repr__(self):
		return self.__str__()

class Literal(Token):
	def __init__(self):
		self.value = ""
	def __str__(self):
		return "Literal" + ": " + str(self.value)
	def __repr__(self):
		return self.__str__()

class Comment(Token):
	def __init__(self):
		self.open = None
		self.value = ""
	def __str__(self):
		return "Comment" + ": " + str(self.value)
	def __repr__(self):
		return self.__str__()

class Operator(Token):
	def __init__(self):
		self.value = ""
	def __str__(self):
		return "Operator" + ": " + str(self.value)
	def __repr__(self):
		return self.__str__()

class Word(Token):
	def __init__(self):
		self.value = ""
		self.completed=False
	def __str__(self):
		return "Word" + ": " + str(self.value)
	def __repr__(self):
		return self.__str__()
