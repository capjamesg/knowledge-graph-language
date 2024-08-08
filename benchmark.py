import os
from kgl import KnowledgeGraph
import cProfile

TEST_ITERATIONS = 1_000_000

test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test")

kg = KnowledgeGraph().load_from_csv(os.path.join(test_dir, "data", "example.csv"))

def main():
    for i in range(TEST_ITERATIONS):
        kg.evaluate("{ James -> Likes }")

# save the profile results
cProfile.run("main()", sort="cumtime", filename="profile_results")