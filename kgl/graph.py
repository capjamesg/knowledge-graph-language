import csv
import json
from typing import Any, Dict, List, Union

import lark

from .grammar import grammar

parser = lark.Lark(grammar)


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
                print("Node", item, "does not have property", term1)
                continue

            evaluated_term = kg.get_nodes(item)[term1][0]

            if eval_conditional(comparator, evaluated_term, term2):
                result.append(item)
    else:
        if not kg.get_nodes_by_connection(node, term1):
            print("Node", node, "does not have property", term1)
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

    def __init__(self):
        self.index_by_connection = []
        self.reverse_index_by_connection = {}

    def add_node(self, triple) -> None:
        """
        Given a triple, add it to the graph.
        """
        item = triple[0]
        relates_to = triple[1]
        value = triple[2]

        self._validate_triple(triple)

        if isinstance(value, list):
            for val in value:
                if val not in self.reverse_index_by_connection:
                    self.reverse_index_by_connection[val] = {}

                if relates_to not in self.reverse_index_by_connection[val]:
                    self.reverse_index_by_connection[val][relates_to] = []

                self.reverse_index_by_connection[val][relates_to].append(item)

                self.reverse_index_by_connection[val][relates_to] = list(
                    set(self.reverse_index_by_connection[val][relates_to])
                )

                self.index_by_connection.append((item, relates_to, val))
        else:
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
        current_node = item1
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

        shortest_path = min(paths, key=len)

        return shortest_path

    def evaluate(self, text) -> Union[int, bool, List[Dict[str, Any]]]:
        """
        Evaluate a query on the graph.
        """

        l = parser.parse(text)

        parent_tree = l.children

        final_results = []
        expand = False
        operand = None
        count = False
        question = False
        intersection = False

        is_evaluating_relation = False
        relation_terms = []

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
                        print("Getting", property, "of", node)
                        if isinstance(node, list):
                            result = [
                                self.get_nodes_by_connection(n, property) for n in node
                            ]
                            result = [item for sublist in result for item in sublist]
                        else:
                            result = self.get_nodes_by_connection(node, property)
                        node = result
                    elif children[i].data == "node":
                        if is_evaluating_relation:
                            relation_terms.append(
                                children[i].children[0].children[0].value
                            )
                            if len(relation_terms) == 2:
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
                                print(result)
                                all_items.append(result)
                            # flatten list
                            result = [item for sublist in all_items for item in sublist]
                        else:
                            # if no result, get all properties
                            if not result:
                                result = self.get_nodes(node)
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
                                result = result[node]

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
                    if children[i].type == "operand":
                        operand = children[i].value
                        continue
                    if children[i].type == "INTERSECTION":
                        intersection = True
                        continue

            final_results.append(result if result else [])

        # remove all false values
        final_results = [item for item in final_results if item]

        if intersection:
            print("Final results", final_results)
            final_result = set(final_results[0]).intersection(set(final_results[1]))
            return [list(final_result)]
        else:
            try:
                print("Final results", final_results)
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
            print("Final result", final_result)

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

                    print("Adding", entity, key, value)
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
