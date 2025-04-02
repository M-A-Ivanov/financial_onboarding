from typing import Dict, Any

from genson import SchemaBuilder

from core.base import BaseGenerator


class SchemaGenerator(BaseGenerator):
    def generate(self) -> Dict[str, Any]:
        # Create a schema builder instance

        template = self.path_manager.load_abridged_template()
        return self.generate_schema_from_json(template)

    def save(self, file_path: str) -> str:
        schema = self.generate()
        return self.path_manager.save_schema(schema)

    def get_prompt(self) -> str:
        raise NotImplementedError

    @staticmethod
    def generate_schema_from_json(json_data):

        builder = SchemaBuilder(None)
        # Feed your data into the builder
        builder.add_object(json_data)

        # Get the generated schema
        generated_schema = builder.to_schema()
        SchemaGenerator.enforce_additional_properties_false(generated_schema)
        output_schema = {
            "format": {
                "type": "json_schema",
                "name": "client_data",  # You can choose an appropriate name
                "schema": generated_schema,
                "strict": True
            }
        }
        return output_schema

    @staticmethod
    def enforce_additional_properties_false(schema):
        """
        Recursively traverse the schema and add "additionalProperties": False to all objects.
        """
        if isinstance(schema, dict):
            # If the current schema represents an object, enforce additionalProperties to be False.
            if schema.get("type") == "object":
                schema["additionalProperties"] = False
                # Recursively process all properties.
                if "properties" in schema:
                    for prop in schema["properties"].values():
                        SchemaGenerator.enforce_additional_properties_false(prop)
            # If the schema defines an array, process its "items".
            if "items" in schema:
                SchemaGenerator.enforce_additional_properties_false(schema["items"])
        elif isinstance(schema, list):
            for item in schema:
                SchemaGenerator.enforce_additional_properties_false(item)