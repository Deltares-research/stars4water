# STAC API

## Search endpoint

The search endpoint implements the [STAC API Item Search](https://api.stacspec.org/v1.0.0/item-search/) operation.

```
GET  /api/search
POST /api/search
```

Interactive documentation is available at `http://localhost:8000/api/api.html` (Swagger UI) when the backend is running.

### Example — unfiltered search

To retrieve Items without applying a filter, omit both `filter` and `filter-lang`.
This is the frontend's default request when the user has not selected any search
criteria.

```json
{
  "limit": 500
}
```

## CQL2 filter extension

For advanced filtering, this implementation supports the [STAC Filter Extension](https://github.com/stac-api-extensions/filter) with `filter-lang: cql2-json`.

Use a CQL2 filter only when a search criterion is selected. A `like` expression
such as `%%` must not be used as a substitute for an unfiltered search.

The request body can include a `filter` object written in CQL2 JSON. Filter
properties must be advertised by the API's `/api/queryables` endpoint. The
operators used in this implementation are:

| Operator | Description |
|----------|-------------|
| `and` | Combines multiple conditions |
| `or` | Matches any of several conditions |
| `like` | Matches text values |
| `>=` | Compares values such as dates |
| `s_intersects` | Checks whether an Item geometry intersects a GeoJSON geometry |
| `a_overlaps` | Checks whether an array property shares any value with the given list |

Array-valued properties such as `properties.keywords.id` must be filtered with
`a_overlaps` rather than `in`: `in` compares a single scalar and never matches
a list of keyword objects.

In this syntax, `op` and `args` come from the Filter Extension and CQL2 JSON expression structure, not from the core STAC Item Search parameters.

### Example — spatial filter

```json
{
  "filter-lang": "cql2-json",
  "filter": {
    "op": "s_intersects",
    "args": [
      { "property": "geometry" },
      {
        "type": "Polygon",
        "coordinates": [[[4.0, 51.0], [5.0, 51.0], [5.0, 52.0], [4.0, 52.0], [4.0, 51.0]]]
      }
    ]
  }
}
```

### Example — combined filter

```json
{
  "filter-lang": "cql2-json",
  "filter": {
    "op": "and",
    "args": [
      {
        "op": "like",
        "args": [{ "property": "properties.title" }, "%water%"]
      },
      {
        "op": ">=",
        "args": [{ "property": "properties.datetime" }, "2020-01-01T00:00:00Z"]
      }
    ]
  }
}
```

### Example — keyword filter

```json
{
  "filter-lang": "cql2-json",
  "filter": {
    "op": "a_overlaps",
    "args": [
      { "property": "properties.keywords.id" },
      ["0898e009-a91d-4589-8adc-837178859c73"]
    ]
  }
}
```
