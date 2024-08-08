import os

import pytest

test_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def kg():
    from kgl import KnowledgeGraph

    kg = KnowledgeGraph().load_from_csv(os.path.join(test_dir, "data", "example.csv"))
    return kg

@pytest.fixture
def unicode_kg():
    from kgl import KnowledgeGraph

    kg = KnowledgeGraph().load_from_csv(os.path.join(test_dir, "data", "unicode_example.csv"))
    return kg


def test_evaluate(kg):
    assert kg.evaluate("{ James }")[0] == [{"Likes": ["Coffee"]}]
    assert kg.evaluate("{ James -> Likes }")[0] == [["Coffee"]]
    assert kg.evaluate("{ James <-> Coffee }")[0] == [["James", ("Coffee", "Likes")]]

def test_unicode_query(unicode_kg):
    assert unicode_kg.evaluate("{ Jamés }")[0] == [{"Likes": ["Coffee"]}]
    assert unicode_kg.evaluate("{ Анна -> Likes }")[0] == [["Tea"]]
    assert unicode_kg.evaluate("{ Анна <-> Tea }")[0] == [["Анна", ("Tea", "Likes")]]
    

def test_returns_query_time(kg):
    _, time_taken = kg.evaluate("{ James }")

    assert time_taken > 0


def test_evaluate_operations(kg):
    assert kg.evaluate("{ James -> Likes }#")[0] == 1
    assert kg.evaluate("{ James -> Likes }?")[0] == True
    assert kg.evaluate("{ James <-> Coffee }?")[0] == True


def test_add_node_with_query(kg):
    assert kg.evaluate("{evermore, is, amazing}")[0] == {"is": ["amazing"]}


def test_adding_valid_triple_with_list_value(kg):
    kg.add_node(("James", "Likes", ["Terraria", "Cats"]))
    result = kg.evaluate("{ James -> Likes }")[0]
    assert set(result[0]) == {"Coffee", "Terraria", "Cats"}


def test_adding_invalid_triple(kg):
    with pytest.raises(ValueError):
        kg.add_node(("James", "Dislikes"), strict_load=True)
        kg.add_node(("James", "Dislikes", 1), strict_load=True)
        kg.add_node(("James", "Dislikes", ("Coffee", "Tea")), strict_load=True)


def test_evaluate_introspection(kg):
    assert kg.evaluate("{ James -> Likes }!")[0] == [{"Coffee": {"Likes": ["James"]}}]


def test_querying_root_property_that_does_not_exist(kg):
    assert kg.evaluate("{ Test }")[0] == []


def test_querying_leaf_property_that_does_not_exist(kg):
    with pytest.raises(ValueError):
        kg.evaluate("{ James -> Dislikes }")[0]


def test_evaluate_union(kg):
    union = kg.evaluate("{ James -> Likes } + { Anna -> Likes }")
    assert len(union[0]) == 2
    assert "Coffee" in union[0]
    assert "Tea" in union[0]


def test_evaluate_intersection(kg):
    union = kg.evaluate("{ James -> Likes } INTERSECTION { Anna -> Likes }")[0]
    assert len(union[0]) == 0


def test_add_triple(kg):
    kg.add_node(("James", "Likes", "Tea"))
    assert kg.evaluate("{ James }")[0] == [{"Likes": ["Coffee", "Tea"]}]


def test_get_nodes(kg):
    assert kg.get_nodes("James") == {"Likes": ["Coffee"]}


def test_get_nodes_by_connection(kg):
    assert kg.get_nodes_by_connection("James", "Likes") == ["Coffee"]


def test_export_to_csv(kg):
    kg.export_to_csv("test.csv")
    with open("test.csv") as f:
        file_contents = f.read()
        assert "James,Likes,Coffee\n" in file_contents
        assert "Anna,Likes,Tea" in file_contents

    assert os.path.exists("test.csv")
    os.remove("test.csv")


def test_export_to_tsv(kg):
    kg.export_to_tsv("test.tsv")
    with open("test.tsv") as f:
        file_contents = f.read()
        assert "James\tLikes\tCoffee" in file_contents
        assert "Anna\tLikes\tTea" in file_contents

    assert os.path.exists("test.tsv")
    os.remove("test.tsv")


def test_read_from_tsv(kg):
    from kgl import KnowledgeGraph

    kg = KnowledgeGraph().load_from_tsv(os.path.join(test_dir, "data", "example.tsv"))
    assert kg.evaluate("{ James }")[0] == [{"Likes": ["Coffee"]}]
    assert kg.evaluate("{ Anna }")[0] == [{"Likes": ["Tea"]}]


def test_read_from_json(kg):
    from kgl import KnowledgeGraph

    kg = KnowledgeGraph().load_from_json_file(
        os.path.join(test_dir, "data", "example.json")
    )
    assert kg.evaluate("{ James }")[0] == [{"Likes": ["Coffee"]}]
    assert kg.evaluate("{ Anna }")[0] == [{"Likes": ["Tea"]}]


def test_max_query_call_invocation_error(kg):
    from kgl import QueryDepthExceededError

    # length of this will be 150 calls, over default max of 50
    query = "{" + ("coffee -> is -> coffee" * 50) + "}"

    with pytest.raises(QueryDepthExceededError):
        kg.evaluate(query)

def test_empty_queries(kg):
    assert kg.evaluate("") == []
    assert kg.evaluate("{}") == []

def test_malformed_queries(kg):
    with pytest.raises(ValueError):
        kg.evaluate("{ James")
        kg.evaluate("{ James -> Likes")
        kg.evaluate("{ James -> Likes + Coffee -> is }")
        kg.evaluate("{{")
        kg.evaluate("{")
        kg.evaluate("}")
        kg.evaluate("}}")
        kg.evaluate("{{ James -> Likes }")
        kg.evaluate("{ James -> Likes }}")
        kg.evaluate("{ James -> Likes }{")
        kg.evaluate("{ James -> Likes } + ")
