import pytest
import os

test_dir = os.path.dirname(os.path.abspath(__file__))

@pytest.fixture
def kg():
    from kgl import KnowledgeGraph
    kg = KnowledgeGraph()
    kg.load_from_csv(os.path.join(test_dir, "data", "example.csv"))
    return kg

def test_evaluate(kg):
    assert kg.evaluate("{ James }") == [{'Likes': ['Coffee']}]
    assert kg.evaluate("{ James -> Likes }") == [['Coffee']]
    assert kg.evaluate("{ James -> Likes }#") == 1
    assert kg.evaluate("{ James -> Likes }?") == True
    assert kg.evaluate("{ James <-> Coffee }?") == True

def test_add_triple(kg):
    kg.add_node(("James", "Likes", "Tea"))
    assert kg.evaluate("{ James }") == [{'Likes': ['Coffee', 'Tea']}]

def test_get_nodes(kg):
    assert kg.get_nodes("James") == {'Likes': ['Coffee']}

def test_get_nodes_by_connection(kg):
    assert kg.get_nodes_by_connection("James", "Likes") == ['Coffee']

def test_export_to_csv(kg):
    kg.export_to_csv("test.csv")
    with open("test.csv") as f:
        assert "James,Likes,Coffee" in f.read()

    assert os.path.exists("test.csv")
    os.remove("test.csv")

def test_export_to_tsv(kg):
    kg.export_to_tsv("test.tsv")
    with open("test.tsv") as f:
        assert "James\tLikes\tCoffee" in f.read()

    assert os.path.exists("test.tsv")
    os.remove("test.tsv")