from Tokens import *
from AstObjects import *
from Errors import *
from Interpreter import Interpreter
import re

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

def findClosestBranchIndex(stack):
	index = len(stack)-1
	for item in stack[::-1]:
		if type(item) not in [EventNode, BranchNode, LabelNode]:
			index-=1
		else:
			break
	return index

def findMatchingBracketIndex(stack):
	index = len(stack)-1
	for item in stack[::-1]:
		if type(item)!=EvaluationNode:
			index -= 1
		else:
			break
	return index

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

def parseVariable(index, tokens, stack):
	node = VariableNode()
	value = stack.pop()
	if type(value) not in [EvaluationNode, ValueNode, LiteralNode]:
		raise SyntaxError(f"cannot interpret {node} as variable")
	node.addNode(value)
	if type(stack[-1])==PropertyNode:
		# add to property under special positional condition
		# if next token is not an operator
		if type(tokens[index+1])!=Operator:
			stack[-1].addNode(node)
			stack.pop()
	else:
		stack.append(node)

def parseLabel(stack):
	if type(stack[-1]) in [EvaluationNode, ValueNode, VariableNode, LiteralNode, WordNode]:
		value = stack.pop()
	else:
		raise SyntaxError(f"{stack[-1]} is not a valid label")
	while type(stack[-1]) in [PropertyNode, SpellNode]:
		stack.pop()
	node = LabelNode(value)
	stack[-1].addNode(node)
	stack.append(node)

def parseSpell(stack):
	if type(stack[-1]) in [EvaluationNode, ValueNode, VariableNode, WordNode]:
		value = stack.pop()
	else:
		raise SyntaxError(f"invalid value for spell node {type(stack[-1])}")
	
	if type(stack[-1])==SpellNode:
		stack.pop()
	
	node = SpellNode(value)
	stack[-1].addNode(node)
	stack.append(node)

def parseProperty(stack):
	if type(stack[-1]) in [EvaluationNode, ValueNode, VariableNode, WordNode]:
		value = stack.pop()
	else:
		raise SyntaxError(f"{stack[-1]} is not a valid type of property")
	if type(stack[-1])!=SpellNode: # expand later
		raise SyntaxError(f"property cannot be assigned to {type(stack[-1])}")
	node = PropertyNode(value)
	stack[-1].addProperty(node)
	stack.append(node)

def parseCall(stack):
	if type(stack[-1]) in [EvaluationNode, ValueNode, VariableNode, WordNode]:
		value = stack.pop()
	else:
		raise SyntaxError(f"{stack[-1]} is not a valid callable label")
	if type(stack[-1])==SpellNode: #close spell node
		stack.pop()
	node = CallNode(value)
	stack[-1].addNode(node)

def parseValue(index, token, tokens, stack):
	skipVar = False
	if index+1==len(tokens) or type(tokens[index+1])!=Variable:
		# last token or not var
		node = ValueNode(token.value)
	else:
		value = ValueNode(token.value)
		node = VariableNode()
		node.addNode(value)
		skipVar = True
	if type(stack[-1])==PropertyNode:
		# add to property under special positional condition
		# if next token is not an operator
		if index+1==len(tokens) or type(tokens[index+1])!=Operator:
			stack[-1].addNode(node)
			stack.pop()
	else:
		stack.append(node)
	return skipVar

def parseLiteral(index, token, tokens, stack):
	node = LiteralNode(token.value)
	if type(stack[-1])==PropertyNode:
		if type(tokens[index+1])!=Operator:
			stack[-1].addNode(node)
			stack.pop()
	else:
		stack.append(node)

def parseWord(index, token, tokens, stack):
	skipVar = False
	if index+1==len(tokens) or type(tokens[index+1])!=Variable:
		# last token or not var
		node = WordNode(token.value)
	else:
		value = WordNode(token.value)
		node = VariableNode()
		node.addNode(value)
		skipVar = True
	if type(stack[-1])==PropertyNode:
		# add to property under special positional condition
		# if next token is not an operator
		if type(tokens[index+1])!=Operator:
			stack[-1].addNode(node)
			stack.pop()
	else:
		stack.append(node)
	return skipVar

def parseEvent(stack):
	if type(stack[-1]) in [EvaluationNode, ValueNode, VariableNode, WordNode]:
		value = stack.pop()
	else:
		raise SyntaxError(f"{stack[-1]} is not a valid type of property")
	
	if type(stack[-1])==SpellNode: #close spell node
		stack.pop()
	node = EventNode(value)
	stack[-1].addNode(node)
	stack.append(node)

def parseCondition(stack):
	if type(stack[-1]) in [EvaluationNode, ValueNode, VariableNode, WordNode]:
		value = stack.pop()
	else:
		raise SyntaxError(f"{stack[-1]} is not a valid type of property")
	
	if type(stack[-1])==SpellNode: #close spell node
		stack.pop()
	node = BranchNode(value.id)
	stack[-1].addNode(node)
	stack.append(node)

def parseChainEnd(stack):
	idx = findClosestBranchIndex(stack)
	if idx!=-1:
		for _ in range(len(stack)-(idx+1)): #delete everything until closest index
			stack.pop()
		if type(stack[-1]) in [EventNode, LabelNode]:
			stack.pop()
		elif type(stack[-1])==BranchNode: #BranchNode
			if not stack[-1].parserBranchingState:
				stack[-1].parserBranchingState = True
			else:
				stack.pop()
	else:
		raise SyntaxError("unmatched close branch")

def parseBracket(index, token, tokens, stack):
	if token.open:
		node = EvaluationNode()
		stack.append(node)
		return 1
	else:
		idx = findMatchingBracketIndex(stack)
		if idx == -1:
			raise SyntaxError("unmatched bracket close")
		for _ in range(len(stack)-(idx+1)):
			popped = stack.pop()
			stack[-1].addNode(popped)
		evaluation = stack.pop()
		if type(stack[-1])==BranchNode and len(stack[-1].condition)==0:
			stack[-1].condition.append(evaluation)
		elif index+1==len(tokens) or type(tokens[index+1]) not in [Operator, Variable]:
			stack[-1].addNode(evaluation)
		else:
			stack.append(evaluation)
		return -1

def parseOperator(token, stack):
	if token.value in ['*', "/", "//"]:
		parse_operator_order_3(token, stack)
	if token.value in ["+", "-"]:
		parse_operator_order_2(token, stack)
	if token.value in ['>=', '<=', '>', '<', '!=', '==']:
		parse_operator_order_1(token, stack)
	if token.value == "not":
		parse_operator_not(token, stack)
	if token.value == "and":
		parse_operator_and(token, stack)
	if token.value == "or":
		parse_operator_or(token, stack)

def CollapseOperatorsUntil(operators, stack):
	while type(stack[-2])==OperatorNode and stack[-2].op not in operators:
		lastOp = stack.pop()
		stack[-1].right.append(lastOp)

def parse_operator_order_3(token, stack): # * / //
	if type(stack[-2])==OperatorNode:# and stack[-2].op in ['*','/', "//"]:
		#consume left operand and attach to previous operator
		value = stack.pop()
		stack[-1].addNode(value)
		node = OperatorNode(token.value)
		CollapseOperatorsUntil(['*','/', "//",'+', '-', '==', ">=", "<=", "!=", ">", "<","and","or"],stack)
		if type(stack[-1])==OperatorNode:
			lastOp = stack.pop()
			node.left.append(lastOp)
		stack.append(node)
	else:
		#consume left operand, do nothing
		node = OperatorNode(token.value)
		left = stack.pop()
		node.left.append(left)
		stack.append(node)

def parse_operator_order_2(token, stack): # + -
	if type(stack[-2])==OperatorNode and stack[-2].op in ['*','/', "//", '+', '-']:
		#yield value to other operator (precedence or left to right)
		value = stack.pop()
		stack[-1].addNode(value)
		node = OperatorNode(token.value)
		CollapseOperatorsUntil(['+', '-', '==', ">=", "<=", "!=", ">", "<","and","or"],stack)
		if type(stack[-1])==OperatorNode:
			lastOp = stack.pop()
			node.left.append(lastOp)
		stack.append(node)
	else:
		#consume left operand
		node = OperatorNode(token.value)
		left = stack.pop()
		node.left.append(left)
		stack.append(node)

def parse_operator_order_1(token, stack):# == >= <= != > <
	if type(stack[-2])==OperatorNode and stack[-2].op in ['==', ">=", "<=", "!=", ">", "<"]:
		raise SyntaxError("cannot parse comparison of comparison")
	if type(stack[-2])==OperatorNode and stack[-2].op in ['*','/', "//",'+','-']:
		#yield left operand to other operator (precedence)
		value = stack.pop()
		stack[-1].addNode(value)
		node = OperatorNode(token.value)
		CollapseOperatorsUntil(['==', ">=", "<=", "!=", ">", "<","and","or"],stack)
		if type(stack[-1])==OperatorNode:
			lastOp = stack.pop()
			node.left.append(lastOp)
		stack.append(node)
	else:
		#consume left operand
		node = OperatorNode(token.value)
		left = stack.pop()
		node.left.append(left)
		stack.append(node)

#WIP
def parse_operator_not(token, stack):
	if token.value == "not":
		# no need to process left operand, adding to value type node causes syntax error anyway
		# collapsing of chain will fill in this node
		node = OperatorNode(token.value)
		stack.append(node)

#WIP
def parse_operator_and(token, stack):
	if type(stack[-2])==OperatorNode and stack[-2] != "or": # or = only operator with lower precedence
		#yield left operand to other operator (precedence)
		value = stack.pop()
		stack[-1].addNode(value)
		node = OperatorNode(token.value)
		CollapseOperatorsUntil(["and","or"],stack)
		if type(stack[-1])==OperatorNode:
			lastOp = stack.pop()
			node.left.append(lastOp)
		stack.append(node)
	else:
		#consume left operand
		node = OperatorNode(token.value)
		left = stack.pop()
		node.left.append(left)
		stack.append(node)
	pass

#WIP
def parse_operator_or(token, stack):
	if type(stack[-2])==OperatorNode: #lowest precedence, always yield if not only operator
		#yield left operand to other operator (precedence)
		value = stack.pop()
		stack[-1].addNode(value)
		node = OperatorNode(token.value)
		CollapseOperatorsUntil(["or"],stack)
		if type(stack[-1])==OperatorNode:
			lastOp = stack.pop()
			node.left.append(lastOp)
		stack.append(node)
	else:
		#consume left operand
		node = OperatorNode(token.value)
		left = stack.pop()
		node.left.append(left)
		stack.append(node)


def parser(tokens):
	stack = []
	ast = ScopedAST()
	scopeOpen = 0
	bracketOpen = 0
	stack.append(ast)
	skipVar = False #used to skip variable token
	
	if type(tokens[-1]) == Literal and tokens[-1].value[0]!=tokens[-1].value[-1]:
		raise SyntaxError("unclosed Literal")
	for index, token in enumerate(tokens):
		if skipVar:
			skipVar = False
		elif type(token)==Variable:# already processed in token type value
			parseVariable(index, tokens, stack)
		elif type(token)==Label:
			scopeOpen+=1
			parseLabel(stack)
		elif type(token)==Spell:
			parseSpell(stack)
		elif type(token)==Property:
			parseProperty(stack)
		elif type(token)==Call:
			parseCall(stack)
		elif type(token)==Value:
			skipVar = parseValue(index, token, tokens, stack)
		elif type(token)==Literal:
			parseLiteral(index, token, tokens, stack)
		elif type(token)==Word:
			skipVar = parseWord(index, token, tokens, stack)
		elif type(token)==Event:
			scopeOpen +=1
			parseEvent(stack)
		elif type(token)==Condition:
			scopeOpen +=2
			parseCondition(stack)
		elif type(token)==Chain_end:
			scopeOpen -= 1
			parseChainEnd(stack)
		elif type(token)==Bracket:
			bracketOpen += parseBracket(index, token, tokens, stack)
		elif type(token)==Operator:
			parseOperator(token, stack)
	while(len(stack)>1):
		#collapse stack
		node=stack.pop()
		if type(node) not in [SpellNode, PropertyNode]: #certain linger but are already attached
			stack[-1].addNode(node)
	if scopeOpen!=0:
		raise SyntaxError(f"unmatched scope open {scopeOpen}")
	if bracketOpen!=0:
		raise SyntaxError("unmatched bracket open")
	return ast

if __name__=='__main__':
	chain = "8_ 1!15%27 2!14%26 cond°(3//2==2) call.: event# 3!3%test$ 4!5%'test' : 5!5%(6$)$: :" #dev (debug version)
	chain = """
	/*this is a comment; the parser mostly ignores whitespace, this just makes it a bit more readable*/

	8_ /*creates a label, comparable to a function, note: labels do currently run by default*/
	1!15%27 /*spell with id 1*/
	2!14%26 /*also a spell; properties (property type 15, value 27)*/
	cond°(true!=1) /*conditional with id "cond" and condition true!=1*/
		call. /*if branch; only contains call node, calls label named "call"*/
	: /*end of if branch, followed by else branch*/
		event# /*event, specific events not implemented yet, event id = "event"*/
			3!3%test$ /*spell with variable as property value (test$); $ represents variable*/
			4!5%'test' /*literal as property value, see quotes, "test" also valid*/
		: /*end of event scope*/
		5!5%(6+6)$ /* evaluation between brackets possible, can be used as variable*/
		5!5%(6$)$ /*nested variable reference possible, brackets required*/
	: /*end of else branch*/
:/*end of label scope*/
	"""# explained version (see "parsable spell.txt"); comments do not appear in syntax tree
	chain = "8_1!15%27 2!14%26cond°(true==false)call.:event#3!3%test$4!5%'test':5!5%(6$)$::" #version with minimal whitespace
	chain = "1_ 2_ 4! : 2. : 1."
	lexerTokens = lexer(chain)
	ast = parser(lexerTokens)
	ast.simplify()
	ast.setParentRelations()
	print(ast)
	interpreter = Interpreter()
	interpreter.interpret(ast)
