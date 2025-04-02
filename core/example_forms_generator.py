import json
from typing import Dict, Any

from openai import OpenAI

from core.base import BaseGenerator
from utils import settings, MISSING_FIELD


class ExampleFormGenerator(BaseGenerator):
    """
    Generates example forms with realistic financial data for testing.
    This class creates realistic financial data based on the JSON schema,
    with options to randomly remove fields for testing extraction robustness.
    Of course, we can also obfuscate fields programmatically, but we want to be quick and dirty,
    so the LLM does it for us.
    """
    model_name = "gpt-4.5-preview"
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate(self) -> Dict[str, Any]:
        """
        Generate an example form with realistic financial data.
        Returns:
            Generated form data as a dictionary
        """
        # Get the schema for guidance
        schema = self.path_manager.load_schema()

        # Generate form data using the LLM
        response = self.client.responses.create(
            model=self.model_name,
            input=[
                {"role": "user", "content": self.get_prompt()}
            ],
            text=schema,
        )

        # Parse the response to get the form data
        form_data = json.loads(self.strip_markdown_code_block(response.output_text))
        return form_data

    def save(self, form_data: Dict[str, Any]) -> str:
        """
        Save the generated form data as ground truth.
        
        Args:
            form_data: The generated form data
            
        Returns:
            Path to the saved form data file
        """
        return self.path_manager.save_ground_truth(form_data)

    def get_prompt(self) -> str:
        """
        Not directly used in this implementation.
        """
        return ("You are a financial advisor that has had an interview with a client "
                "and needs to fill in the 'Fact Find' form."
                "Please fill in the form as given in the JSON schema with varied and random, but plausible "
                "financial client information that is likely to occur in a real-life "
                f"scenario. Be creative. Please, when quoting money, don't put currencies, "
                f"but just provide the numbers as a string."
                f" Please mark some of the fields (between 10-30 % of all fields) "
                f"for filling in as '{MISSING_FIELD}' at random and avoid adding {MISSING_FIELD} in list item fields. "
                f"Please only output the JSON dictionary.")
                
    def create(self) -> str:
        """
        Generate and save an example form with missing fields.
        Returns:
            Path to the saved form data file
        """
        form_data = self.generate()
        return self.save(form_data)
