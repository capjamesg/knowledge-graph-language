# Knowledge Graph Language

This repository stores my experiment in making a knowledge graph language.

## Syntax

This project allows you to index triples of data like:

```
("James", "Enjoys", "Coffee")
("James", "Hobbies", "Making coffee")
("James", "WorksFor", "Roboflow")
("Roboflow", "Makes", "Computer Vision")
("Roboflow", "EntityType", "Company")
```

### Query a Single Item

You can query a single item:

```
{ James }
```

This will return all items associated with the `James` entry:

```
[add code]
```

### Sequential Queries

The Knowledge Graph Language flows from left to right. You can make a statement, then use an arrow (`->`) to query an attribute related to the result:

Consider the following query:

```
{ James -> WorksFor -> Makes }
```

This query gets the `James` item, retrieves for whom James works, then reports the `Makes` attribute for the employer.

The query returns:

```
[add code]
```

### Filter Queries

You can filter queries so that the flow of data is constrained to only work with results that match a condition.

Consider this query:

```
{ Roboflow ("EntityType" = "Company") -> WorksFor ("Enjoys" = "Coffee") -> Hobbies }
```

This query gets the instance of `Roboflow` that has the `EntityType` property `Company`. This could be used for disambiguation.

Then, the query gets everyone who owns Roboflow who enjoys coffee. The query then finds who everyone works for, and returns their hobbies.

## License

This project is licensed under an [MIT license](LICENSE).
