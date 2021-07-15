# oapi_builder
APISpec is a great un-opinionated framework to represent an OAPI Doc in Python. 
However, OpenAPI can have a lot of sharp edges. 
APISpec traditionally relies on plugins to manage this complexity.
Unfortunately, few of these plugins are useful for scenarios where the Doc is used as a contract, and the doc is unable to leverage an API framework like Flask or fast-api.
This is where `oapi_builder` comes in. 
`oapi_builder` offers class based representations of OpenAPI objects to provide an intuitive interface to write or extend an OpenAPI doc generated with APISpec.

To see `oapi_builder` in action check out [the provided example](example.py).

## Additional Documentation
* [API Reference](docs/API_REFERENCE.md)
* [Design Decisions](docs/DESIGN_DECISIONS.md)

