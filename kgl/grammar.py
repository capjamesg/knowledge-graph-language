grammar = """
start: comma_separated_list | most_connected | COUNT | QUESTION | query (operand query)*
query: "{}" | "{" (graph "|")? node ((relation | interrelation) node)* "}" (EXPAND | QUESTION | COUNT)?
operand: PLUS | INTERSECTION
PLUS: "+"
INTERSECTION: "INTERSECTION"
relation: "->"
comma_separated_list: "{" CNAME "," CNAME "," CNAME "}"
interrelation: "<->"
EXPAND: "!"
QUESTION: "?"
COUNT: "#"
COMPARATOR: "=" | "!=" | ">" | "<"
CNAME: /[a-zA-Z0-9_ ]+/
condition: ("(" string COMPARATOR string ")"?)*
node: property (enumerate_options | subsequence_operator | near)? condition?
subsequence_operator: "++"
enumerate_options: "+"
most_connected: "*"
near: "~"
graph: /[a-zA-Z0-9_]+/
property: /[a-zA-Z0-9_ ]+/
string: ESCAPED_STRING | int
int: /[0-9]+/
%import common.WS
%import common.ESCAPED_STRING
%ignore WS
"""
