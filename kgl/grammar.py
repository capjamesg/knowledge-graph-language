grammar = """
start: query (operand query)*
query: "{" node ((relation | interrelation) node)* "}" (EXPAND | QUESTION | COUNT)?
operand: PLUS | INTERSECTION
PLUS: "+"
INTERSECTION: "INTERSECTION"
relation: "->"
interrelation: "<->"
EXPAND: "!"
QUESTION: "?"
COUNT: "#"
COMPARATOR: "=" | "!=" | ">" | "<"
CNAME: /[a-zA-Z0-9_]+/
condition: ("(" string COMPARATOR string ")"?)*
node: property condition?
property: CNAME
string: ESCAPED_STRING | int
int: /[0-9]+/
%import common.WS
%import common.ESCAPED_STRING
%ignore WS
"""
