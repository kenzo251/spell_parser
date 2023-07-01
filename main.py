from Interpreter import Interpreter
from Lexer import lexer
from Parser import parser

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
	chain = "1!br%true 1_ if°(br$) 1!1%1 : 1!2%2 3!1%1$ : : 1. 1!br%false 1."
	lexerTokens = lexer(chain)
	ast = parser(lexerTokens)
	ast.simplify()
	ast.setParentRelations()
	print(ast)
	interpreter = Interpreter()
	interpreter.interpret(ast)
	print(ast.vars)
	print(ast.nodes[1].nodes[0].varsIf)
	print(ast.nodes[1].nodes[0].varsElse)
	print(interpreter.stack)