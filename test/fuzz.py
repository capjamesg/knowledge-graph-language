import random
from kgl.graph import KnowledgeGraph
import os
import lark
from nltk.corpus import stopwords
from nltk import download as nltk_download
import emoji
import string

print("Downloading stopwords...")
nltk_download("stopwords")

print("Running tests...")

test_dir = os.path.dirname(os.path.abspath(__file__))

kg = KnowledgeGraph().load_from_csv(os.path.join(test_dir, "data", "example.csv"))

seeds = [
    "{ coffee -> is }",
    "{ coffee -> is -> coffee }",
    "{ tea -> type-of }",
    "{ James -> favourite-songs } + { Taylor -> favourite-songs }",
    "{ coffee } INTERSECTION { tea }",
    "{ coffee } - { tea }",
    "{ coffee -> is } - { tea -> is }",
]

seed_templates = {
    # query structure, number of words to generate
    "single_query": ("{ %s }", 1),
    "single_query_with_two_word_clause": ("{ %s %s -> %s }", 3),
    "set_union": ("{ %s } + { %s }", 2),
    "set_intersection": ("{ %s } INTERSECTION { %s }", 2),
    "set_difference": ("{ %s } - { %s }", 2),
}

supported_languages = stopwords.fileids()

character_ranges = {
    file_id: list(stopwords.words(file_id)) for file_id in supported_languages
}

character_ranges["alphanumeric"] = string.ascii_letters + string.digits
character_ranges["unicode"] = [chr(i) for i in range(0x0000, 0x10FFFF)]
character_ranges["numbers"] = [str(random.randint(1, 10_000_000)) for _ in range(1000)]
character_ranges["long_numbers"] = [
    str(random.randint(10_000_000_000_000, 10_000_000_000_000_000)) for _ in range(1000)
]
character_ranges["emojis"] = list(emoji.EMOJI_DATA.keys())

supported_languages.append("unicode")

CHANGE_RATE = 0.1
ITERATIONS_PER_SEED = 100


def change():
    return (
        random.choices(
            population=[["do not change"], ["change"]],
            weights=[1 - CHANGE_RATE, CHANGE_RATE],
            k=1,
        )[0][0]
        == "change"
    )


def mutate(
    seed, characters_to_skip=["{", "}", "-", ">", "<"], character_range="unicode"
):
    seed = list(seed)

    for i in range(len(seed)):
        if change() and seed[i] not in characters_to_skip:
            seed[i] = random.choice(character_ranges[character_range])

    return "".join(seed)


def get_random_word_from_random_language():
    return random.choice(character_ranges[random.choice(supported_languages)])


def generate_query_from_scratch(template, num_words_to_generate):
    return template % tuple(
        get_random_word_from_random_language() for _ in range(num_words_to_generate)
    )


def execute_query(query):
    try:
        kg.evaluate(query)
    except (lark.exceptions.UnexpectedCharacters, ValueError):
        # In this case, the program has successfully detected an invalid input.
        return "pass"
    except Exception as e:
        # In this case, an unknown error has been raised.
        return "fail"


def test_fuzzer():
    failed_tests = []

    tests = []

    tests.extend([mutate(seed) for seed in seeds for _ in range(ITERATIONS_PER_SEED)])

    tests.extend(
        [mutate(seed, []) for seed in seeds for _ in range(ITERATIONS_PER_SEED)]
    )

    for character_range in character_ranges:
        tests.extend(
            [
                mutate(seed, [], character_range)
                for seed in seeds
                for _ in range(ITERATIONS_PER_SEED)
            ]
        )

    tests.extend(
        [
            generate_query_from_scratch(template, num_words)
            for template, num_words in seed_templates.values()
            for _ in range(ITERATIONS_PER_SEED)
        ]
    )

    test_count = len(tests)

    for test in tests:
        if execute_query(test) == "fail":
            failed_tests.append(test)
            if __name__ != "__main__":
                print(test)
                assert False

    failed_tests_count = len(failed_tests)

    print(
        f"Ran {test_count} tests with {failed_tests_count} failures ({(test_count - failed_tests_count) / test_count * 100}% success rate)"
    )


if __name__ == "__main__":
    test_fuzzer()
