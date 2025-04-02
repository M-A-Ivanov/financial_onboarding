"""
Data Extractor module.
Takes in conversation transcripts and extracts structured data in JSON format.
"""

import json
from typing import Dict, Any

from openai import OpenAI

from utils import settings, MISSING_FIELD
from core.base import BaseGenerator


class DataExtractor(BaseGenerator):
    """
    Extracts structured data from conversation transcripts.
    This class is responsible for processing conversation transcripts and
    extracting structured data according to a specified schema format.
    """
    model_name = "gpt-4o-mini"
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate(self) -> Dict[str, Any]:
        """
        Extract structured data from a conversation transcript.
        Returns:
            Extracted structured data as a dictionary
        """
        # Get the schema for validation
        schema = self.path_manager.load_schema()
        
        # Load the conversation text
        conversation_path = self.path_manager.get_generated_conversation_path()
        with open(conversation_path, 'r', encoding='utf-8') as f:
            conversation_text = f.read()
        
        # Build the prompt for data extraction
        prompt = self.get_prompt(conversation_text)
        
        # Generate the structured data using the LLM
        response = self.client.responses.create(
            model=self.model_name,
            text=schema,
            input=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract the JSON content from the response
        extracted_data = json.loads(self.strip_markdown_code_block(response.output_text))
        
        return extracted_data

    def save(self, extracted_data: Dict[str, Any]) -> str:
        """
        Save extracted data for a conversation.
        
        Args:
            extracted_data: Extracted data to save

        Returns:
            Path to the saved extracted data file
        """
        return self.path_manager.save_extracted_data(extracted_data)

    def get_prompt(self, conversation_text: str) -> str:
        """
        Build a prompt for data extraction from a conversation.
        
        Args:
            conversation_text: The conversation transcript

        Returns:
            Prompt for the LLM
        """
        return (
            "You are a data extraction expert. Your task is to extract structured data from "
            "a financial onboarding conversation transcript according to a provided schema. "
            "Only include information that is explicitly mentioned or can be confidently inferred "
            f"from the conversation. If information is missing or unclear, mark the field with {MISSING_FIELD}.\n\n"
            f"Here is the conversation transcript:\n\n{conversation_text}\n\n"
            "Please extract all relevant information from this conversation and format it "
            "according to the provided JSON schema. "
            "Do not include currency signs, just provide the numbers as a string. "
            "Output only the valid JSON data without any "
            "additional explanations."
        )
        
    def create(self) -> str:
        """
        Process the current conversation to extract structured data.
        
        Returns:
            Path to the saved extracted data file
        """
        extracted_data = self.generate()
        return self.save(extracted_data)