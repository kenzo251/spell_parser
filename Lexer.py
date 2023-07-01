import re
from Tokens import *

simple = {
	"!": Spell,
	"%": Property,
	"°": Condition,
	":": Chain_end,
	"#": Event,
	"_": Label,
	".": Call,
	"$": Variable,
}

def lexer(string):
	tokens = []
	lastToken = None
	for token in string:
		#set of long multistring operations
		if type(lastToken) == Comment and lastToken.open:
			lastToken.value += token
			if token!="/":
				continue
			#add to comment
		elif type(lastToken) == Literal and (lastToken.value[0]!=lastToken.value[-1] or len(lastToken.value)==1):
			lastToken.value+=token
			continue
		elif type(lastToken) == Word and not lastToken.completed:
			if token in '!%°:#_.$=<>)' or re.match(r"\s", token):
				lastToken.completed = True
				if lastToken.value in ["and","or","not"]:
					# on complete, if operator keyword replace to operator node
					tokens.pop()
					temp = lastToken.value
					lastToken = Operator()
					lastToken.value = temp
					tokens.append(lastToken)
				# don't continue to next loop yet
			elif not re.match(r'[a-zA-Z0-9_]',token):
				raise SyntaxError(f"Invalid character '{token}'")
			else:
				#add token to word
				lastToken.value += token
				continue
		if token in simple and type(lastToken)!=Comment:#ignores any special(simple) symbols in comments
			lastToken = simple[token]()
			tokens.append(lastToken)
		elif re.match(r'[0-9]',token):
			if type(lastToken)!=Value:
				lastToken = Value()
				lastToken.value = int(token)
				tokens.append(lastToken)
			else:
				lastToken.value=lastToken.value*10 + int(token)
		elif re.match(r'\s',token):
			if(type(lastToken)==WhiteSpace):
				continue
			else:
				lastToken = WhiteSpace()
		elif token=='(':
			lastToken = Bracket()
			lastToken.open = True
			tokens.append(lastToken)
		elif token==')':
			lastToken = Bracket()
			lastToken.open = False
			tokens.append(lastToken)
		elif token in "+-<>":
			lastToken = Operator()
			lastToken.value = token
			tokens.append(lastToken)
		elif token == "/":
			if type(lastToken) == Comment and lastToken.value.endswith("*/"):
				lastToken.value = lastToken.value[:-2]
				lastToken.open = False
				tokens[-1] = lastToken
			elif type(lastToken) == Operator and lastToken.value == "/":
				lastToken.value += "/"
			else:
				lastToken = Operator()
				lastToken.value = "/"
				tokens.append(lastToken)
		elif token == "*":
			if type(lastToken) == Operator and lastToken.value == "/":
				lastToken = Comment()
				lastToken.open = True
				tokens[-1] = lastToken
			else:
				lastToken = Operator()
				lastToken.value = "*"
				tokens.append(lastToken)
		elif token == "=":
			if type(lastToken)==Spell:
				lastToken = Operator()
				lastToken.value = "!="
				tokens[-1] = lastToken
			elif type(lastToken)==Operator and lastToken.value in "<>=":
				lastToken.value += token
			else:
				lastToken = Operator()
				lastToken.value = token
				tokens.append(lastToken)
		elif token in "\'\"":
			lastToken = Literal()
			lastToken.value = token
			tokens.append(lastToken)
		elif re.match(r"[a-zA-Z]",token):
			# start creating word; words cannot start with number
			lastToken = Word()
			lastToken.value = token
			tokens.append(lastToken)
	return tokens