# spell_parser
spellparser (hopefully) compatible with codespells's rune design

## what is this project
this project is made with codespells's design of programmable magic based on a (custom) rune system, therefore this project is my attempt at an underlying parser for such a rune based system  
read more on https://codespells.org/

## symbols
`'text'` text item  

`{id}!` defines a spell, the interpreter prints it out for now  

`{id}%{value}` defines a property spells  

`{id}_ {inner code} :` defines a label (callable function)  

`{id}.` calls a label  

`{id}° ({condition}) {if branch} : {else branch} :` defines an if statement (certain conditionals may contain extra variables, eg an implementation may have status° may contain variables for a target's status conditions; currently none implemented)  

`{id}# {inner code} :` defines an event, triggered by external sources  

`{id}$` variable reference  

`({evaluation})` brackets... you know how this works  
previously mentioned `{id}` may be numbers, words or expressions
whitespace is ignored

## valid operators

| symbols | type |
| --- | --- |
| `+`,`-`,`/`,`//`,`*` | math |
| `==`,`!=`,`<=`,`>=`,`<`,`>` | comparison |
| `and`,`or`,`not` | logic |

## special "spells"

`1!{set of properties}` assigns variables with name being property id and value being property value
variables are scoped

`2!{state, see table}%{unused value}`

|state|action|
|---|---|
|1|break|
|2|return|
|3|continue|

currently numbers, will make this words later

## loops
loops can be defined with `loop_`
creates a while true loop, use break to end

## inserting spells
see main.py at the bottom, examples listed (varname "chain")

## running
`python main.py`
t is 
