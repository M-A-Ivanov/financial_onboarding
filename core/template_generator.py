"""
Template Generator module.
Takes in documents and prompts an LLM to generate JSON templates.
"""

import json
from typing import Dict, Any
from openai import OpenAI

from utils import settings
from core.base import BaseGenerator


class TemplateGenerator(BaseGenerator):
    """
    Generates JSON templates from documents using LLM.
    This class is responsible for analyzing documents and creating structured
    JSON templates that represent the data fields to be extracted.

    Note:
    Ways to extend this functionality:
        - for simplicity, we just generate a template in the results directory, this can easily be scaled to
    produce another level in the results folder structure.
        - for now, we are just using OpenAI for brevity, but we can extend this to use other LLM providers.
        - to confirm template, we can open the PDF manually and find that every generated key exists as text
        in the PDF
    """
    model_name = "gpt-4o-mini"
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate(self,
    ) -> Dict[str, Any]:
        """
        Generate a JSON template from a document.
        Returns:
            Generated JSON template as a dictionary
        """
        # Build the prompt for template generation
        prompt = self.get_prompt()

        file = self.client.files.create(
            file=open(self.path_manager.pdf_path, "rb"),
            purpose="user_data"
        )

        response = self.client.responses.create(
            model=self.model_name,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "file_id": file.id,
                        },
                        {
                            "type": "input_text",
                            "text": prompt,
                        },
                    ]
                }
            ]
        )

        return json.loads(self.strip_markdown_code_block(response.output_text))

    def save(self, file_path):
        template = self.generate()
        return self.path_manager.save_template(template)

    def get_prompt(self) -> str:
        return f"""You are a useful helper that takes a table structure used for recording client data in a financial onboarding process. 
         Your task is to take a PDF file and transfer the found forms into a JSON template accurately, 
         nesting fields when necessary. If the field is a list, please indicate it with a list with an empty string - [""].
         If the file contains multiple instances of the same form, please only capture a single instance of it.
        Please only output the JSON dictionary template. 
    """
