import json
from typing import Dict, Any

from openai import OpenAI

from utils import settings
from core.base import BaseGenerator


class TemplateShortener(BaseGenerator):
    model_name = "gpt-4o-mini"
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate(self) -> Dict[str, Any]:
        template = self.path_manager.load_template()
        response = self.client.responses.create(model=self.model_name,
                                                input=self.get_prompt(template))
        return json.loads(self.strip_markdown_code_block(response.output_text))

    def get_prompt(self, template):
        return ("I am creating a JSON form for Fact Finding used by financial "
                "advisors. I am aiming to showcase a solution for automatic "
                "filling of that form. Please extract fields that are "
                "representative of the variation of the client data in order to "
                "best showcase the solution. Please aim to remove around 20% to 30% of the fields."
                "Please create a shortened JSON variant from the JSON template "
                "below: \n"
                f"{json.dumps(template, indent=4)} \n"
                f"Please only output the JSON dictionary template.")

    def save(self, file_path: str) -> str:
        template = self.generate()
        return self.path_manager.save_abridged_template(template)
