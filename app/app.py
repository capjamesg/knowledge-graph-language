import pygtrie
from flask import Flask, jsonify, render_template, request

from kgl import KnowledgeGraph, graph_to_dot

AUTOCOMPLETE = True

kg = KnowledgeGraph(
    allow_substring_search=True, create_similarity_index=False
).load_from_csv("../../all1.csv")

node_trie = pygtrie.CharTrie()

for graph in kg.search_index.keys():
    connections = kg.reverse_index_by_connection[graph]

    for connection in connections:
        node_trie[connection] = True

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            result, time_taken = kg.evaluate(request.json["query"])

            if isinstance(result, set):
                result = [list(result)]
            if not isinstance(result, list):
                result = [result]
        except:
            return jsonify({"error": "Syntax error."})

        dot = graph_to_dot(result, request.json["query"])

        return jsonify({"result": result, "dot": dot, "time_taken": time_taken})

    return render_template("index.html")


@app.route("/autocomplete", methods=["GET", "POST"])
def autocomplete():
    if request.method == "POST" and AUTOCOMPLETE:
        prefix = request.json["query"]
        prefix = prefix.lstrip("{ ").strip()
        print(prefix)

        if len(prefix) < 2:
            return jsonify({"completions": []})

        try:
            completions = node_trie.keys(prefix)
            return jsonify({"completions": list(completions)[:5]})
        except:
            return jsonify({"completions": []})

    return jsonify({"completions": []})


if __name__ == "__main__":
    app.run(debug=True)
