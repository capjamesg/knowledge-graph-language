import os

import pytest

test_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def kg():
    from kgl import KnowledgeGraph

    kg = KnowledgeGraph().load_from_csv(os.path.join(test_dir, "data", "example.csv"))
    return kg


def test_evaluate(kg):
    assert kg.evaluate("{ James }") == [{"Likes": ["Coffee"]}]
    assert kg.evaluate("{ James -> Likes }") == [["Coffee"]]
    assert kg.evaluate("{ James <-> Coffee }") == [["James", ("Coffee", "Likes")]]


def test_evaluate_operations(kg):
    assert kg.evaluate("{ James -> Likes }#") == 1
    assert kg.evaluate("{ James -> Likes }?") == True
    assert kg.evaluate("{ James <-> Coffee }?") == True


def test_evaluate_introspection(kg):
    assert kg.evaluate("{ James -> Likes }!") == [{"Coffee": {"Likes": ["James"]}}]


def test_evaluate_union(kg):
    union = kg.evaluate("{ James -> Likes } + { Anna -> Likes }")
    assert len(union[0]) == 2
    assert "Coffee" in union[0]
    assert "Tea" in union[0]


def test_evaluate_intersection(kg):
    union = kg.evaluate("{ James -> Likes } INTERSECTION { Anna -> Likes }")
    assert len(union[0]) == 0


def test_add_triple(kg):
    kg.add_node(("James", "Likes", "Tea"))
    assert kg.evaluate("{ James }") == [{"Likes": ["Coffee", "Tea"]}]


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
    assert kg.evaluate("{ James }") == [{"Likes": ["Coffee"]}]
    assert kg.evaluate("{ Anna }") == [{"Likes": ["Tea"]}]


def test_read_from_json(kg):
    from kgl import KnowledgeGraph

    kg = KnowledgeGraph().load_from_json_file(
        os.path.join(test_dir, "data", "example.json")
    )
    assert kg.evaluate("{ James }") == [{"Likes": ["Coffee"]}]
    assert kg.evaluate("{ Anna }") == [{"Likes": ["Tea"]}]
