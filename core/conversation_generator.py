"""
Conversation Generator module.
Takes a ground truth JSON and generates a natural free-form conversation.
"""

import json
import copy
from typing import Dict, Any, List, Tuple

from openai import OpenAI

from utils import settings, MISSING_FIELD
from core.base import BaseGenerator


class ConversationGenerator(BaseGenerator):
    """
    Generates natural free-form conversations based on ground truth data.
    This class creates realistic financial onboarding conversations based on
    the provided ground truth data, considering fields marked as missing.
    """
    model_name = "gpt-4.5-preview"
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate(self) -> str:
        """
        Generate a natural conversation based on ground truth data.
        Returns:
            Generated conversation text
        """
        # Load the ground truth data
        ground_truth_path = self.path_manager.get_ground_truth_path()
        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            ground_truth = json.load(f)
        
        # Process ground truth to identify missing fields
        processed_ground_truth, missing_fields = self.process_ground_truth(ground_truth)
        # Build the prompt for conversation generation
        prompt = self.get_prompt(
            ground_truth=processed_ground_truth,
            missing_fields=missing_fields
        )
        
        # Generate the conversation using the LLM
        response = self.client.responses.create(
            model=self.model_name,
            input=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        
        # Extract the conversation text from the response
        conversation_text = response.output_text
        
        return conversation_text

    def save(self, conversation_text: str) -> str:
        """
        Save a generated conversation.
        
        Args:
            conversation_text: Conversation text to save
            
        Returns:
            Path to the saved conversation file
        """
        return self.path_manager.save_conversation(conversation_text)

    def process_ground_truth(self, ground_truth: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Process the ground truth to extract information about missing fields.
        
        Args:
            ground_truth: The ground truth data with MISSING_FIELD markers
            
        Returns:
            Tuple of (processed_ground_truth, missing_fields)
        """
        # Create a deep copy to avoid modifying the original
        processed_gt = copy.deepcopy(ground_truth)
        
        # Find all missing fields
        missing_fields = self._find_missing_fields(processed_gt)
        
        return processed_gt, missing_fields
    
    def _find_missing_fields(self, data, path="", missing_fields=None):
        """
        Recursively process the ground truth data to find missing fields.
        
        Args:
            data: The ground truth data to process
            path: Current JSON path
            missing_fields: List to store paths to missing fields
            
        Returns:
            List of paths to missing fields
        """
        if missing_fields is None:
            missing_fields = []
            
        if isinstance(data, dict):
            # Track keys to delete to avoid modifying the dictionary during iteration
            keys_to_delete = []
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, (dict, list)):
                    self._find_missing_fields(value, current_path, missing_fields)
                elif value == MISSING_FIELD:
                    missing_fields.append(current_path)
                    keys_to_delete.append(key)
            
            # Delete the keys after iteration is complete
            for key in keys_to_delete:
                del data[key]
                
        elif isinstance(data, list):
            # Process the list in reverse to avoid index shifting issues when deleting
            # First identify indices to remove
            indices_to_delete = []
            
            # First pass: identify and process
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                if isinstance(item, (dict, list)):
                    self._find_missing_fields(item, current_path, missing_fields)
                elif item == MISSING_FIELD:
                    missing_fields.append(current_path)
                    indices_to_delete.append(i)
            
            # Second pass: delete in reverse order to avoid index shifting
            for index in sorted(indices_to_delete, reverse=True):
                del data[index]

        return missing_fields

    def get_prompt(
        self, 
        ground_truth: Dict[str, Any],
        missing_fields: List[str]
    ) -> str:
        """
        Build a prompt for conversation generation.
        
        Args:
            ground_truth: The processed ground truth data (with None for missing fields)
            missing_fields: List of paths to fields that are missing or need to be inferred
            
        Returns:
            Prompt for the LLM
        """
        # Format the ground truth and missing fields for the prompt
        ground_truth_str = json.dumps(ground_truth, indent=2)
        missing_fields_str = "\n- ".join(missing_fields) if missing_fields else "None"
        
        return (
            "You are a virtual assistant that simulates realistic financial onboarding Fact Find conversations "
            "between a financial advisor and a single client. Your task is to generate "
            "a long natural conversation based on the provided ground truth data.\n\n"
            f"Ground Truth Data:\n{ground_truth_str}\n\n"
            "Please note the following:\n"
            f"The following fields are missing and should NOT be mentioned in the conversation:\n- {missing_fields_str}\n\n"
            "Guidelines:\n"
            "- Create a natural, realistic dialogue between a financial advisor and a client\n"
            "- Include casual conversation elements and small talk to make it realistic\n"
            "- The conversation should focus on gathering financial information for onboarding\n"
            "- Please make sure to include all the information from the ground truth data\n"
            "- Please include other data that is not present in the ground truth data, "
            " making noise in the conversation with respect to the ground truth\n"
            
            "- Format the conversation clearly with 'Advisor:' and 'Client:' prefixes\n"
            "- Include typical clarifications, follow-up questions, and corrections\n"
            "Make some small bits of the conversation less straightforward by "
            "using tricks such as:\n"
            "   -  having some of the details inferred through reasoning\n"
            "   -  having some of the details suggested by the advisor and confirmed or denied by the client\n"
            "   - having some of the details stated wrong and corrected subsequently\n"
            "Do not include any explanations or notes outside the conversation format. "
            "Please make sure that all the information from the Ground Truth data can be found in the conversation.\n\n"
            "Generate the conversation now:"
        )
        
    def create(self) -> str:
        """
        Create a conversation for the current path manager conversation.
        
        Returns:
            Path to the saved conversation file
        """
        conversation_text = self.generate()
        return self.save(conversation_text)
