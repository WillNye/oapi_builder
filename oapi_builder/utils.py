def add_schemas(api_spec, schemas):
    for schema in schemas:
        api_spec.components.schema(schema.__name__)
