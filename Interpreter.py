from AstObjects import *
from Errors import *
import copy

class States:
	Normal = 0
	Breaking = 1
	Returning = 2
	Continueing = 3 #loop continue

def printSpell(id, props):
	#helper function for debugging
	print(f"casting spell {id} with properties {props}")

class Interpreter():
	def __init__(self):
		self.labels = {}#registers callable labels
		self.events = {}#registers events
		self.parent = None
		self.state = States.Normal
		self.stack = []
		self.returnValue = None
	
	def interpret(self, tree):
		for node in tree.nodes:
			if self.state == States.Returning and (type(tree)==EventNode or (type(tree)==LabelNode and not (type(tree.id)==WordNode and tree.id.id=="loop"))):
				self.state = States.Normal
				return self.returnValue
			ret = self.interpretNode(node)
		#check for returning if last node is return
		if self.state == States.Returning and (type(tree)==EventNode or (type(tree)==LabelNode and not (type(tree.id)==WordNode and tree.id.id=="loop"))):
				self.state = States.Normal
				return self.returnValue
	
	#at this point no brackets should exist anymore
	def interpretNode(self, node):
		if self.state!=States.Normal:
			return
		# endpoint entries(value, var, etc) have return values
		if type(node) in [ValueNode, VariableNode, WordNode, LiteralNode]:
			return self.interpretValue(node)
		elif type(node)==PropertyNode:
			return self.interpretProperty(node)
		elif type(node)==LabelNode:
			self.interpretLabel(node)
		elif type(node)==SpellNode:
			self.interpretSpell(node)
		elif type(node)==BranchNode:
			self.interpretBranch(node)
		elif type(node)==CallNode:
			return self.interpretCall(node)
		elif type(node)==EventNode:
			self.interpretEvent(node)
		elif type(node)==OperatorNode:
			return self.interpretOperator(node)
		else:
			print("interpreting node", type(node))#mostly debug purposes
	
	def interpretValue(self, value):
		if type(value) in [ValueNode, LiteralNode]:
			return value.id
		elif type(value) == VariableNode:
			return self.interpretVariable(value)
		elif type(value) == WordNode:
			if value.id == "true":
				return True
			elif value.id == "false":
				return False
			elif value.id == "null":
				return None
			else:
				return value.id
	
	def interpretSpell(self, spell):
		id = self.interpretNode(spell.id)
		props = {}
		for node in spell.nodes:
			propID, propVal = self.interpretNode(node)
			props[propID] = propVal
		if id==1:
			for varname, value in props.items():
				if varname=="push":#value interpreted as varname to read from
					#val = spell.findVar(value)
					self.stack.append(propVal)
				elif varname=="pop": #value interpreted as varname to write to
					val = self.stack.pop()
					spell.setVar(value,val)#does not matter if var exists or not
				elif varname=="del":#value interpreted as varname to delete
					spell.delVar(value)
				else:
					spell.setVar(varname, value)
		elif id==2:
			if list(props.keys())[0] not in list(range(1,4)):
				raise RuntimeError("invalid control flow modifying statement")
			#check if state valid
			presentedState = list(props.keys())[0]
			if presentedState == States.Breaking or presentedState==States.Continueing:
				if not spell.nodeTypeInParents(LabelNode, checkLoop=True):
					raise RuntimeError(f"invalid {'break' if presentedState == States.Breaking else 'continue'} statement")
			elif presentedState == States.Returning:
				if not spell.nodeTypeInParents(LabelNode, checkLoop=False) or spell.nodeTypeInParents(EventNode):
					raise RuntimeError("invalid return statement")
				self.returnValue = list(props.values())[0]
			self.state = presentedState
		else:
			printSpell(id, props)
	
	def interpretProperty(self, property):
		id = self.interpretNode(property.id)
		# property should only contain 1 value
		value = self.interpretNode(property.nodes[0])
		return (id, value)
	
	def interpretVariable(self, variable):
		# variable should only contain 1 value
		varid = self.interpretValue(variable.nodes[0])
		try:
			return variable.findVar(varid)
		except Exception as e:# temp
			print(f"raising exception, variable {varid} referenced before assignment")
			return -1
	
	def interpretBranch(self, branch):
		condition = self.interpretNode(branch.condition[0])
		subAst = AST()
		if condition:
			branch.BranchingState = False #set branchingState for variables
			subAst.nodes = branch.branchIf
		else:
			branch.BranchingState = True
			subAst.nodes = branch.branchElse
		self.interpret(subAst)
	
	def interpretCall(self, call):
		id = self.interpretNode(call.id)
		l=call.findLabel(id)
		print(f"interpreting for id {id}")#debug
		temp = self.interpret(l)
		self.returnValue = None
		return temp
	
	def interpretEvent(self, event):
		#register event, some external action should trigger event; therefore events don't need to be scope callable
		id = self.interpretNode(event.id)
		self.events[id] = event
	
	def interpretLabel(self, label):
		# needs some scoping work
		id = self.interpretNode(label.id)
		if id == "loop" and type(label.id)==WordNode: #non wordnode loop is not a valid loop
			while True:
				self.interpret(label)
				if self.state == States.Breaking:
					self.state = States.Normal
					break
				elif self.state == States.Continueing:
					self.state = States.Normal
		else:
			label.parent.setLabel(id, label)
			#self.labels[f"{id}"] = label
			# self.interpret(label) #testing
			
	
	def interpretOperator(self, operator):
		if operator.op != "not":
			left = self.interpretNode(operator.left[0])
		else:
			right = self.interpretNode(operator.right[0])
			return not right
		if operator.op not in ['and','or']:
			right = self.interpretNode(operator.right[0])
		if operator.op == "+":
			return left + right
		elif operator.op == "-":
			return left - right
		elif operator.op == "*":
			return left * right
		elif operator.op == "/":
			return left / right
		elif operator.op == "//":
			return left // right
		
		elif operator.op == "<":
			return left < right
		elif operator.op == ">":
			return left > right
		elif operator.op == "==":
			return left == right
		elif operator.op == ">=":
			return left >= right
		elif operator.op == "<=":
			return left <= right
		elif operator.op == "!=":
			return left != right
		
		elif operator.op == "and":
			if left:
				return self.interpretNode(operator.right[0])
		elif operaot.op == "or":
			if not left:
				return self.interpretNode(operator.right[0])
		else:
			raise Error("operator not supported (how did you even get your code to raise this exception?)")
