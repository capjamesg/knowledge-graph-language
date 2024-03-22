import csv
import json
import random
from typing import Any, Dict, List, Union

import lark

from .grammar import grammar

parser = lark.Lark(grammar)


def value_error(error_type, message):
    if error_type == "error":
        print("\033[91mError:\033[0m", message)
    elif error_type == "warning":
        print("\033[93mKGL Warning:\033[0m", message)


def serialize_shortest_path_as_str(shortest_path) -> None:
    print(shortest_path[0], end="")

    for i in range(1, len(shortest_path)):
        print(" ->", shortest_path[i][1], "->", shortest_path[i][0], end="")

    print()


def eval_conditional(comparator, evaluated_term, term_to_match) -> list:
    """
    Evaluate a conditional on a term.
    """
    if comparator == "=" and evaluated_term == term_to_match:
        return True
    elif comparator == "!=" and evaluated_term != term_to_match:
        return True
    elif comparator == ">" and evaluated_term > term_to_match:
        return True
    elif comparator == "<" and evaluated_term < term_to_match:
        return True

    return False


def eval_condition(condition, node, kg) -> list:
    """
    Evaluate a condition on a node.
    """

    result = []

    term1 = condition.children[0].children[0].value.strip().strip('"')
    comparator = condition.children[1].value.strip()
    term2 = condition.children[2].children[0].value.strip().strip('"')

    if isinstance(node, list):
        for item in node:
            if not kg.get_nodes(item).get(term1):
                # print("Node", item, "does not have property", term1)
                continue

            evaluated_term = kg.get_nodes(item)[term1][0]

            if eval_conditional(comparator, evaluated_term, term2):
                result.append(item)
    else:
        if not kg.get_nodes_by_connection(node, term1):
            # print("Node", node, "does not have property", term1)
            return []

        evaluated_term = kg.get_nodes(node)[term1][0]

        if eval_conditional(comparator, evaluated_term, term2):
            result.append(node)

    return result


class KnowledgeGraph:
    """
    A Knowledge Graph Language graph representation of triples.
    """

    def _validate_triple(self, triple):
        """
        Ensure that the triple is a tuple with exactly three elements.
        """
        if not isinstance(triple, tuple):
            raise ValueError("Triple must be a tuple")
        if len(triple) != 3:
            raise ValueError("Triple must have exactly 3 elements")

        if not isinstance(triple[0], str):
            raise ValueError("First element of triple must be a string")

        if not isinstance(triple[1], str):
            raise ValueError("Second element of triple must be a string")

        if not isinstance(triple[2], str) and not isinstance(triple[2], list):
            raise ValueError("Third element of triple must be a string or list")

    def __init__(self, allow_substring_search=False):
        self.index_by_connection = []
        self.reverse_index_by_connection = {}
        self.search_index = {}
        self.allow_substring_search = allow_substring_search

    def add_node(self, triple) -> None:
        """
        Given a triple, add it to the graph.
        """

        try:
            self._validate_triple(triple)
        except ValueError as e:
            return

        # don't add if first item is only 1 len, unless it is "i"
        if len(triple[0].strip()) < 1 and triple[0].strip() != "i":
            return

        item = triple[0].lower().strip()
        relates_to = triple[1].lower()
        value = triple[2].lower().strip()

        if isinstance(value, list):
            relates_to = relates_to.strip()

            for val in value:
                val = val.strip()
                if val not in self.reverse_index_by_connection:
                    self.reverse_index_by_connection[val] = {}

                if relates_to not in self.reverse_index_by_connection[val]:
                    self.reverse_index_by_connection[val][relates_to] = []

                if item not in self.reverse_index_by_connection:
                    self.reverse_index_by_connection[item] = {}

                if relates_to not in self.reverse_index_by_connection[item]:
                    self.reverse_index_by_connection[item][relates_to] = []

                self.reverse_index_by_connection[item][relates_to].append(val)

                self.reverse_index_by_connection[val][relates_to] = list(
                    set(self.reverse_index_by_connection[val][relates_to])
                )

                self.index_by_connection.append((item, relates_to, val))
        else:
            value = value.strip()
            relates_to = relates_to.strip()
            if value not in self.reverse_index_by_connection:
                self.reverse_index_by_connection[value] = {}

            if relates_to not in self.reverse_index_by_connection[value]:
                self.reverse_index_by_connection[value][relates_to] = []

            self.reverse_index_by_connection[value][relates_to].append(item)

            if item not in self.reverse_index_by_connection:
                self.reverse_index_by_connection[item] = {}

            if relates_to not in self.reverse_index_by_connection[item]:
                self.reverse_index_by_connection[item][relates_to] = []

            self.reverse_index_by_connection[item][relates_to].append(value)

            self.reverse_index_by_connection[value][relates_to] = list(
                set(self.reverse_index_by_connection[value][relates_to])
            )

            self.index_by_connection.append((item, relates_to, value))

        if self.allow_substring_search:
            for word in item.split():
                if word not in self.search_index:
                    self.search_index[word] = []

                self.search_index[word].append(item)
            ngrams = []
            for i in range(1, len(item.split())):
                ngrams.append(" ".join(item.split()[i:]))

            for ngram in ngrams:
                if ngram not in self.search_index:
                    self.search_index[ngram] = []

                self.search_index[ngram].append(item)

    def get_nodes(self, item) -> dict:
        """
        Get the nodes connected to an item.
        """
        return self.reverse_index_by_connection.get(item, {})

    def get_nodes_by_connection(self, item, connection) -> list:
        """
        Get the nodes connected to an item by a connection.
        """
        result = self.reverse_index_by_connection.get(item, {}).get(
            connection, {}
        ) or self.reverse_index_by_connection.get(item, {})
        return list(set(result))

    def get_connection_count(self, item) -> int:
        """
        Get the number of connections for an item.
        """
        return len(self.index_by_connection.get(item, {}))

    def get_connection_paths(self, item1, item2) -> list:
        """
        Get the shortest path between two items.
        """
        paths = []
        current_node = item1.strip()
        item2 = item2.strip()
        visited = set()

        def dfs(node, path):
            if node == item2:
                paths.append(path)
                return

            visited.add(node)

            for connection in self.get_nodes(node):
                for c in self.get_nodes(node)[connection]:
                    if c in visited:
                        continue

                    dfs(c, path + [(c, connection)])

                if connection in visited:
                    continue

                dfs(connection, path + [connection])

        dfs(current_node, [current_node])

        if paths == []:
            return []

        shortest_paths = min(paths, key=len)

        return shortest_paths

    def remove_node(self, item) -> None:
        """
        Remove a node from the graph.
        """
        all_relations_of_item = self.get_nodes(item)

        if item in self.reverse_index_by_connection:
            del self.reverse_index_by_connection[item]

        for relation in all_relations_of_item:
            for connected_item in all_relations_of_item[relation]:
                self.index_by_connection.remove((item, relation, connected_item))
                self.reverse_index_by_connection[connected_item][relation].remove(item)

    def evaluate(self, text) -> Union[int, bool, List[Dict[str, Any]]]:
        """
        Evaluate a query on the graph.
        """

        try:
            l = parser.parse(text)
        except:
            raise ValueError("Invalid query")

        parent_tree = l.children

        final_results = []
        expand = False
        count = False
        question = False
        intersection = False

        is_evaluating_relation = False
        relation_terms = []

        if (
            len(parent_tree) > 0
            and isinstance(parent_tree[0], lark.tree.Tree)
            and len(parent_tree[0].children) == 0
        ):
            item = self.index_by_connection[
                random.randint(0, len(self.index_by_connection) - 1)
            ][0]
            return self.evaluate("{" + item + "}")
        # Is leaf
        elif (
            len(parent_tree) > 0
            and hasattr(parent_tree[0], "type")
            and parent_tree[0].type == "QUESTION"
        ):
            # brute force up to 1000 times
            iters = 0
            while iters < 1000:
                item1 = self.index_by_connection[
                    random.randint(0, len(self.index_by_connection) - 1)
                ][0]
                item2 = self.index_by_connection[
                    random.randint(0, len(self.index_by_connection) - 1)
                ][0]
                shortest_path = self.get_connection_paths(item1, item2)
                if shortest_path:
                    serialize_shortest_path_as_str(shortest_path)
                    return True

            return False

        result_accumulator = []

        for child in parent_tree:
            children = child.children

            if len(children) == 0:
                continue

            node = None
            result = None

            for i in range(len(children)):
                if isinstance(children[i], lark.tree.Tree):
                    if children[i].data == "interrelation":
                        is_evaluating_relation = True
                        break

            for i in range(len(children)):
                if isinstance(children[i], lark.tree.Tree):
                    if children[i].data == "property":
                        property = children[i].children[0].value.strip()
                        # print("Getting", property, "of", node)
                        if isinstance(node, list):
                            result = [
                                self.get_nodes_by_connection(n, property) for n in node
                            ]
                            result = [item for sublist in result for item in sublist]
                        else:
                            result = self.get_nodes_by_connection(node, property)
                        node = result
                    elif children[i].data == "node":
                        subsequence = False
                        enumerate_options = False
                        # if node has subsequence operator
                        # search for subsequence operator in children
                        for j in range(len(children[i].children)):
                            if children[i].children[j].data == "subsequence_operator":
                                print("Subsequence operator found")
                                subsequence = True
                            elif children[i].children[j].data == "enumerate_options":
                                print("Enumerate options found")
                                enumerate_options = True

                        if is_evaluating_relation:
                            relation_terms.append(
                                children[i].children[0].children[0].value
                            )

                            # if second from last node or last node, evaluate relation
                            if i == len(children) - 2 or i == len(children) - 1:
                                print("Evaluating relation", relation_terms)
                                result = self.get_connection_paths(
                                    relation_terms[0], relation_terms[1]
                                )
                                node = result
                                is_evaluating_relation = False
                                relation_terms = []
                                continue

                        node = children[i].children[0].children[0].value.strip()
                        property = children[i].children[0].children[0].value.strip()

                        if (
                            len(children[i].children) > 1
                            and len(children[i].children[1].children) > 0
                        ):
                            print("Getting", property, "of", result)
                            all_items = []
                            if result:
                                if (
                                    len(
                                        [
                                            self.get_nodes(r)[node]
                                            for r in result
                                            if node in self.get_nodes(r)
                                        ]
                                    )
                                    == 0
                                ):
                                    result = result[property]
                                else:
                                    result = [
                                        self.get_nodes(r)[node]
                                        for r in result
                                        if node in self.get_nodes(r)
                                    ][0]
                                condition = children[i].children[1]
                                result = eval_condition(condition, result, self)
                                all_items.append(result)
                            else:
                                condition = children[i].children[1]
                                result = eval_condition(condition, node, self)
                                # print(result)
                                all_items.append(result)
                            # flatten list
                            result = [item for sublist in all_items for item in sublist]
                        else:
                            # print("Getting", property, "of", node, subsequence, enumerate_options, result)
                            # if no result, get all properties
                            # if allow substring is falase and subseqnece or enumerate is true, print warning
                            if self.allow_substring_search == False and (
                                subsequence or enumerate_options
                            ):
                                value_error(
                                    "warning",
                                    "Subsequence and enumerate options are not allowed without `allow_substring_search` set to True.",
                                )
                            if not result and not subsequence and not enumerate_options:
                                result = self.get_nodes(node)
                            elif not result and (subsequence or enumerate_options):
                                nodes_that_mention_term = self.search_index.get(
                                    node, []
                                )
                                result = []
                                for node in nodes_that_mention_term:
                                    # if enumerate options, add node name, else add dict
                                    if enumerate_options:
                                        result.append(node)
                                    else:
                                        result.append({node: self.get_nodes(node)})

                                if enumerate_options:
                                    result = list(set(result))
                            # if result is list:
                            elif isinstance(result, list):
                                result = [
                                    self.get_nodes(r)[node]
                                    for r in result
                                    if node in self.get_nodes(r)
                                ]
                                result = [
                                    item for sublist in result for item in sublist
                                ]
                            else:
                                try:
                                    result = result[node]
                                except:
                                    raise ValueError(
                                        "Node does not have property " + node + "."
                                    )

                        if result == []:
                            return []
                else:
                    if children[i].type == "EXPAND":
                        expand = True
                        continue
                    if children[i].type == "COUNT":
                        count = True
                        continue
                    if children[i].type == "QUESTION":
                        question = True
                        continue
                    if children[i].type == "INTERSECTION":
                        intersection = True
                        continue

            final_results.append(result if result else [])

        # remove all false values
        final_results = [item for item in final_results if item]

        if intersection:
            # print("Final results", final_results)
            final_result = set(final_results[0]).intersection(set(final_results[1]))
            return [list(final_result)]
        else:
            try:
                final_result = set(final_results[0]).union(set(final_results[1]))
                return [list(final_result)]
            except:
                if len(final_results) == 0:
                    final_result = []
                else:
                    final_result = final_results[0]

        if count:
            return len(final_result)
        elif question:
            return bool(final_result)
        elif expand:
            if isinstance(final_result, dict):
                return final_result

            acc = []
            # print("Final result", final_result)

            for item in final_result:
                nodes = self.get_nodes(item)
                if not nodes:
                    continue
                acc.append({item: nodes})

            acc = sorted(acc, key=lambda x: list(x.keys())[0])

            return acc

        return final_results

    def load_from_csv(self, file_name):
        """
        Load the graph from a CSV file.
        """
        with open(file_name, mode="r") as file:
            reader = csv.reader(file)
            for row in reader:
                row = tuple(row)
                self.add_node(row)

        return self

    def load_from_tsv(self, file_name):
        """
        Load the graph from a TSV file.
        """
        with open(file_name, mode="r") as file:
            reader = csv.reader(file, delimiter="\t")
            for row in reader:
                row = tuple(row)
                self.add_node(row)

        return self

    def load_from_json_file(self, file_name):
        """
        Load the graph from a JSON object.
        """
        with open(file_name, mode="r") as file:
            data = json.load(file)
            for item in data:
                entity = item.get("Entity")

                if not entity:
                    raise ValueError("JSON object must have an 'Entity' key")

                for key, value in item.items():
                    if key == "Entity":
                        continue

                    self.add_node((entity, key, value))

        return self

    def export_to_csv(self, file_name) -> None:
        """
        Export the graph to a CSV file.
        """
        with open(file_name, mode="w") as file:
            writer = csv.writer(file)
            for row in self.index_by_connection:
                writer.writerow(row)

    def export_to_tsv(self, file_name) -> None:
        """
        Export the graph to a TSV file.
        """
        with open(file_name, mode="w") as file:
            writer = csv.writer(file, delimiter="\t")
            for row in self.index_by_connection:
                writer.writerow(row)

    def export_graph_index(self, file_name) -> None:
        """
        Export the graph index.
        """

        with open(file_name, mode="w+") as f:
            index = {
                "index_by_connection": self.index_by_connection,
                "reverse_index_by_connection": self.reverse_index_by_connection,
                "search_index": self.search_index,
            }

            json.dump(index, f)
