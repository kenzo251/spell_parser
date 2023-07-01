from Errors import *

class AST():
	def __init__(self):
		self.nodes = []
		self.parent = None
	
	def __str__(self):
		return self.printNode()
		return "AST: "+str(self.nodes)
	
	def __repr__(self):
		return "AST: "# + str(self.nodes)
	
	def printNode(self, indent=0):
		return ' '*indent*4 + self.__repr__() + "\n"+\
			'\n'.join([i.printNode(indent+1) for i in self.nodes])
	
	def addNode(self, node):
		self.nodes.append(node)
		node.parent = self
	
	def simplify(self):
		for index, node in enumerate(self.nodes):
			self.nodes[index] = node.simplify()
		return self
	
	def setParentRelations(self):
		for node in self.nodes:
			node.parent = self
			node.setParentRelations()
	
	def findVar(self, varname):#only request var in scopeable items
		if self.parent == None:
			raise RuntimeError(f"variable referenced before assignment: {varname}")
		return self.parent.findVar(varname)
	
	def setVar(self, varname, value, canSet=True):
		return self.parent.setVar(varname, value, canSet)
	
	def delVar(self, varname):
		self.parent.delVar(varname)
	
	def findLabel(self, labelname):
		if self.parent == None:
			raise RuntimeError(f"'{labelname}' is not defined")
		return self.parent.findLabel(labelname)
	
	def setLabel(self, labelname, target):
		self.parent.setLabel(labelname, target)
	
	def nodeTypeInParents(self, nodetype, checkLoop=False):
		if self.parent==None:
			return False
		elif type(self)==nodetype and not checkLoop:
			if type(self.id)==WordNode and self.id.id == "loop":
				#actually don't return true but return parent's test
				return self.parent.nodeTypeInParents(nodetype, checkLoop)
			return True
		elif checkLoop and type(self)==LabelNode and type(self.id) == WordNode and self.id.id == "loop": #evaluated label names don't get interpreted as loops
			return True
		return self.parent.nodeTypeInParents(nodetype, checkLoop)

class ScopedAST(AST):
	def __init__(self):
		super().__init__()
		self.vars = {}
		self.labels = {}
	
	def findVar(self, varname):
		if varname in self.vars:
			return self.vars[varname]
		if self.parent == None:
			raise RuntimeError(f"variable referenced before assignment: {varname}")
		return self.parent.findVar(varname)
	
	def setVar(self, varname, value, canSet=True):
		#first find if earlier occurence exists
		if varname in self.vars:
			self.vars[varname]=value
			return True
		if self.parent==None:
			if canSet:#has not found a better scope candidate
				self.vars[varname]=value
				return True
			return False #has found better scope candidate, not setting var here
		
		earlier_occurence = self.parent.setVar(varname, value, False)
		if not earlier_occurence and canSet:
			self.vars[varname]=value
			return True
		else:
			return earlier_occurence
	
	def delVar(self,varname):
		if varname in self.vars:
			del self.vars['varname']
	
	def findLabel(self,labelname):
		if labelname in self.labels:
			return self.labels[labelname]
		if self.parent == None:
			raise RuntimeError(f"'{labelname}' is not defined")
		return self.parent.findLabel(labelname)
	
	def setLabel(self, labelname, target):
		self.labels[labelname]=target

class PropertyNode(AST):
	def __init__(self, id):
		super().__init__()
		self.id = id
	
	def __repr__(self):
		return f"Property({self.id.id}): "
	
	def simplify(self):
		self. id = self.id.simplify()
		for index, node in enumerate(self.nodes):
			self.nodes[index] = node.simplify()
		return self

class SpellNode(AST):
	def __init__(self, id):
		super().__init__()
		self.id = id
	
	def addProperty(self, property):
		self.nodes.append(property)
	
	def __repr__(self):
		try:
			return f"Spell({self.id.id}): "
		except:
			if type(self.id)==VariableNode:
				return f"Spell(Variable: {self.id.nodes[0]})"
			return f"Spell({self.id.nodes})"
		
	def verifySpecial(self):
		if type(self.id)!=VariableNode and self.id.id==2 and len(self.nodes)!=1:
			#can't do shit if you're working with self modifying code: aka variable spell id
			raise SyntaxError("Cannot set multiple control flow states")
	
	def simplify(self):
		self.id = self.id.simplify()
		self.verifySpecial()
		for index,node in enumerate(self.nodes):
			self.nodes[index] = node.simplify()
		return self

class LabelNode(ScopedAST):
	def __init__(self, id):
		super().__init__()
		self.id = id
	
	def __repr__(self):
		return f"Label({self.id.id})"
	
	def simplify(self):
		self.id = self.id.simplify()
		for index, node in enumerate(self.nodes):
			self.nodes[index] = node.simplify()
		return self
	
class CallNode(AST):
	def __init__(self, id):
		super().__init__()
		self.id = id
	
	def __repr__(self):
		return f"Call({self.id.id}): "
	
	def simplify(self):
		self.id = self.id.simplify()
		for index, node in enumerate(self.nodes):
			self.nodes[index] = node.simplify()
		return self

class EventNode(ScopedAST):
	def __init__(self, id):
		super().__init__()
		self.id = id
	
	def __repr__(self):
		return f"Event({self.id.id}): "
	
	def simplify(self):
		self.id = self.id.simplify()
		for index, node in enumerate(self.nodes):
			self.nodes[index] = node.simplify()
		return self

class BranchNode(ScopedAST): #note: has 2 scopes, needs to change later
	def __init__(self, id):
		super().__init__()
		self.id = id
		self.condition = []
		self.branchIf = []
		self.branchElse = []
		self.parserBranchingState = False
	
	def addNode(self, node):
		if not self.parserBranchingState:
			self.branchIf.append(node)
		else:
			self.branchElse.append(node)
	
	def printNode(self, indent=0):
		return ' '*indent*4 + self.__class__.__name__ + f"({self.id if hasattr(self, 'id') else ''}):\n" \
			+ '\n'.join([i.printNode(indent+1) for i in self.condition])+f"\n{' '*(indent+1)*4}---\n" \
			+ '\n'.join([i.printNode(indent+1) for i in self.branchIf])+f"{' '*(indent+1)*4}---\n" \
			+ '\n'.join([i.printNode(indent+1) for i in self.branchElse])
	
	def __repr__(self):
		return f"Condition({self.id}): "#+str(self.nodes)
	
	def simplify(self):
		for index, node in enumerate(self.condition):
			self.condition[index] = node.simplify()
		for index, node in enumerate(self.branchIf):
			self.branchIf[index] = node.simplify()
		for index, node in enumerate(self.branchElse):
			self.branchElse[index] = node.simplify()
		return self
	
	def setParentRelations(self):
		for nodelist in [self.condition, self.branchIf, self.branchElse]:
			for node in nodelist:
				node.parent = self
				node.setParentRelations()

class LiteralNode(AST):
	def __init__(self, id):
		super().__init__()
		self.id = id
	
	def printNode(self, indent=0):
		return " "*indent*4 + self.__repr__()
	
	def addNode(self, node):
		raise SyntaxError("cannot add node to LiteralNode")
		
	def __repr__(self):
		return f"Literal({self.id})"
	
	def simplify(self):
		if len(self.nodes):
			raise SyntaxError("literal cannot have children nodes")
		return self

class ValueNode(AST):
	def __init__(self, id):
		super().__init__()
		self.id = id
	
	def printNode(self, indent=0):
		return " "*indent*4 + self.__repr__()
	
	def addNode(self, node):
		raise SyntaxError("cannot add node to ValueNode")
	
	def __repr__(self):
		return f"Value({self.id})"
	
	def simplify(self):
		if len(self.nodes):
			raise SyntaxError("value cannot have children nodes")
		return self

class WordNode(AST):
	def __init__(self, id):
		super().__init__()
		self.id = id
	
	def printNode(self, indent=0):
		return " "*indent*4 + self.__repr__()
	
	def addNode(self, node):
		raise SyntaxError("cannot add node to WordNode")
	
	def __repr__(self):
		return f"WordNode({self.id})"
	
	def simplify(self):
		if len(self.nodes):
			raise SyntaxError("word cannot have children nodes")
		return self

class VariableNode(AST):
	def __init__(self, _=None):
		super().__init__()
	
	def __repr__(self):
		return f"Variable: "
	
	# default simplify

class EvaluationNode(AST): #mostly used for grouping while parsing
	def __init__(self, _=None):
		super().__init__()
	def __repr__(self):
		return f"Eval(): "
	
	def simplify(self):
		if len(self.nodes)!=1:
			raise SyntaxError("invalid evaluation node")
		self.nodes[0]=self.nodes[0].simplify()
		return self.nodes[0]

class OperatorNode(AST):
	def __init__(self, op):
		super().__init__()
		self.op = op
		self.left = []
		self.right = []
		
	def addNode(self, node):
		self.right.append(node)
		
	def __repr__(self):
		return f'Operator({self.op})'
	
	def printNode(self, indent=0):
		return ' '*indent*4 + self.__class__.__name__ + f"({self.op}):\n" \
			+ '\n'.join([i.printNode(indent+1) for i in self.left])+f"\n{' '*(indent+1)*4}---\n" \
			+ '\n'.join([i.printNode(indent+1) for i in self.right])
	
	def __convertLiteralTrueFalse(self, toBoolean = True):
		if toBoolean:
			try:
				if type(self.left[0])==WordNode and self.left[0].id == "true":
					self.left[0].id = True
				if type(self.left[0])==WordNode and self.left[0].id == "false":
					self.left[0].id = False
				if type(self.right[0])==WordNode and self.right[0].id == "true":
					self.right[0].id = True
				if type(self.right[0])==WordNode and self.right[0].id == "false":
					self.right[0].id = False
			except:
				pass
		else:
			try:
				if type(self.left[0])==WordNode and self.left[0].id:
					self.left[0].id = "true"
				if type(self.left[0])==WordNode and not self.left[0].id:
					self.left[0].id = "false"
				if type(self.right[0])==WordNode and self.right[0].id:
					self.right[0].id = "true"
				if type(self.right[0])==WordNode and not self.right[0].id:
					self.right[0].id = "false"
			except:
				pass
	
	def __generateLogicOperatorResult(self):
		res = None
		if self.op == "not" and type(self.right[0]) in [ValueNode, LiteralNode, WordNode]:
			res = "true" if not self.right[0].id else "false"
		elif type(self.left[0]) in [ValueNode, LiteralNode, WordNode] and type(self.right[0]) in [ValueNode, LiteralNode, WordNode]:
			if self.op == "==":
				res = "true" if self.left[0].id==self.right[0].id else "false"
			elif self.op == ">=":
				res = "true" if self.left[0].id>=self.right[0].id else "false"
			elif self.op == "<=":
				res = "true" if self.left[0].id<=self.right[0].id else "false"
			elif self.op == "!=":
				res = "true" if self.left[0].id!=self.right[0].id else "false"
			elif self.op == ">":
				res = "true" if self.left[0].id>self.right[0].id else "false"
			elif self.op == "<":
				res = "true" if self.left[0].id<self.right[0].id else "false"
			elif self.op == "and":
				res = "true" if self.left[0].id and self.right[0].id else "false"
			elif self.op == "or":
				res = "true" if self.left[0].id or self.right[0].id else "false"
		return res
	
	def __generateMathOperatorResult(self):
		if self.op=="+":
			res = self.left[0].id + self.right[0].id
		elif self.op=="-":
			res = self.left[0].id - self.right[0].id
		elif self.op=="*":
			res = self.left[0].id * self.right[0].id
		elif self.op=="/":
			res = self.left[0].id / self.right[0].id
		elif self.op=="//":
			res = self.left[0].id // self.right[0].id
		return ValueNode(res)
	
	def simplify(self):
		for index,node in enumerate(self.left):
			self.left[index] = node.simplify()
		for index,node in enumerate(self.right):
			self.right[index] = node.simplify()
		if self.op in ["+","-","*","/","//"]:
			#operate here, return if simplifyable
			if type(self.left[0])==ValueNode and type(self.right[0])==ValueNode:
				return self.__generateMathOperatorResult()
		else:
			#temp conversion to True/False
			self.__convertLiteralTrueFalse()
			res=self.__generateLogicOperatorResult()
			self.__convertLiteralTrueFalse()
			if res!=None:
				return WordNode(res)
		return self
	
	def setParentRelations(self):
		for nodelist in [self.left, self.right]:
			for node in nodelist:
				node.parent = self
				node.setParentRelations()
