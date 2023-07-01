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

class Lexer:
	def lexIncompleteWord(self, token, tokens):
		if token in '!%°:#_.$=<>)' or re.match(r"\s", token):
			tokens[-1].completed = True
			if tokens[-1].value in ["and","or","not"]:
				# on complete, if operator keyword replace to operator node
				temp = tokens[-1].value
				tokens.pop()
				Token = Operator()
				Token.value = temp
				tokens.append(Token)
			# don't continue to next loop yet
		elif not re.match(r'[a-zA-Z0-9_]',token):
			raise SyntaxError(f"Invalid character '{token}'")
		else:
			#add token to word
			tokens[-1].value += token
			return True
		return False
	
	def lexNumber(self, token, tokens):
		if type(tokens[-1])!=Value:
			Token = Value()
			Token.value = int(token)
			tokens.append(Token)
		else:
			tokens[-1].value=tokens[-1].value*10 + int(token)
	
	def lexForwardSlash(self, token, tokens):
		if type(tokens[-1]) == Comment and tokens[-1].value.endswith("*/"):
			tokens[-1].value = tokens[-1].value[:-2]
			tokens[-1].open = False
		elif type(tokens[-1]) == Operator and tokens[-1].value == "/":
			tokens[-1].value += "/"
		else:
			Token = Operator()
			Token.value = "/"
			tokens.append(Token)
	
	def lexAsterisk(self, token, tokens):
		if type(tokens[-1]) == Operator and tokens[-1].value == "/":
			Token = Comment()
			Token.open = True
			tokens[-1] = Token
		else:
			Token = Operator()
			Token.value = "*"
			tokens.append(Token)
	
	def lexEqualSign(self, token, tokens):
		if type(tokens[-1])==Spell:
			Token = Operator()
			Token.value = "!="
			tokens[-1] = Token
		elif type(tokens[-1])==Operator and tokens[-1].value in "<>=":
			tokens[-1].value += token
		else:
			Token = Operator()
			Token.value = token
			tokens.append(Token)
	
	def addTokenWithValue(self, tokentype, value, tokens):
		# wordnodes cannot start with a number
		if type(tokens[-1])==Value and tokentype==Word:
			raise SyntaxError("word cannot start with number")
		Token = tokentype()
		Token.value = value
		tokens.append(Token)
	
	def addBracket(self, isOpen, tokens):
		Token = Bracket()
		Token.open = isOpen
		tokens.append(Token)
	
	def lexerSubStep1(self, token, tokens):
		#set of long multistring operations
		if type(tokens[-1]) == Comment and tokens[-1].open:
			tokens[-1].value += token
			if token!="/":
				return True
			#add to comment
		elif type(tokens[-1]) == Literal and (tokens[-1].value[0]!=tokens[-1].value[-1] or len(tokens[-1].value)==1):
			tokens[-1].value+=token
			return True
		elif type(tokens[-1]) == Word and not tokens[-1].completed:
			if self.lexIncompleteWord(token, tokens):
				return True
		return False
	
	def lexerSubStep2(self, token, tokens):
		if token in simple and type(tokens[-1])!=Comment:#ignores any special(simple) symbols in comments
			tokens.append(simple[token]())
		elif re.match(r'[0-9]',token):
			self.lexNumber(token, tokens)
		elif re.match(r'\s',token):#whitespace
			if(tokens[-1]!=None):
				tokens.append(None)
		elif token=='(':
			self.addBracket(True, tokens)
		elif token==')':
			self.addBracket(False, tokens)
		elif token in "+-<>":
			self.addTokenWithValue(Operator, token, tokens)
		elif token == "/":
			self.lexForwardSlash(token, tokens)
		elif token == "*":
			self.lexAsterisk(token, tokens)
		elif token == "=":
			self.lexEqualSign(token, tokens)
		elif token in "\'\"":
			self.addTokenWithValue(Literal, token, tokens)
		elif re.match(r"[a-zA-Z]",token): 
			self.addTokenWithValue(Word, token, tokens)
	
	def lex(self, string):
		tokens = [None]
		for token in string:
			if self.lexerSubStep1(token, tokens):
				continue
			self.lexerSubStep2(token, tokens)
		return tokens #None values get ignored in parser