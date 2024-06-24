import click
import os
import json
from .graph import KnowledgeGraph
from . import __version__

# Create ~/.cache/kgl if it doesn't exist
if not os.path.exists(os.path.expanduser("~/.cache/kgl")):
    os.makedirs(os.path.expanduser("~/.cache/kgl"))
    with open(os.path.expanduser("~/.cache/kgl/current.json"), "w") as f:
        f.write("{}")

def get_current():
    with open(os.path.expanduser("~/.cache/kgl/current.json"), "r") as f:
        return json.load(f)
    
def set_current(graph):
    with open(os.path.expanduser("~/.cache/kgl/current.json"), "w") as f:
        json.dump(graph, f)

@click.group()
@click.version_option(version=__version__)
def cli():
    pass

@click.command()
@click.argument("query", nargs=-1)
def kgl(query):
    """Query the loaded knowledge graph with the given QUERY."""
    # if query == "use"

    if query[0] == "use":
        if len(query) < 2:
            click.echo("Please provide a knowledge graph to use")
            return
        
        set_current({"graph": query[1]})
        click.echo("Set the current knowledge graph to use to " + query[1] + ".")
        return

    current_graph = get_current()

    if not current_graph or "graph" not in current_graph:
        click.echo("No knowledge graph loaded. Use `kgl load <path>` to load a knowledge graph.")
        return
    
    kg = KnowledgeGraph(
        allow_substring_search=True, create_similarity_index=False
    ).load_from_csv(current_graph["graph"])

    # if doesn't start with {, add
    query = list(query)

    if not query[0].startswith("{"):
        query[0] = "{ " + query[0] + " }"

    result, _ = kg.evaluate(query[0])

    for item in result:
        if isinstance(item, dict):
            for key, value in item.items():
                click.echo(click.style(key, fg="blue"), nl=False)
                click.echo(": ", nl=False)
                click.echo(click.style(", ".join(value), fg="green"))
        else:
            click.echo(click.style(", ".join(item), fg="green"))


    return result

cli.add_command(kgl)
