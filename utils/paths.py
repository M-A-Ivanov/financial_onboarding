"""
Path management, that centralizes all path operations to ensure consistency across the application.
"""

import os
import re
import json
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime

import names_generator

from utils import RESULTS_DIR, TEMPLATE_FILENAME, SCHEMA_FILENAME, TEMPLATE_FILENAME_ABR


class ExperimentPathManager:
    """
    Path manager for a specific experiment.
    Handles all path operations for a specific experiment and its conversations.
    Also handles file saving operations for consistency.
    """

    def __init__(self, experiment_name: str = None):
        """
        Initialize the experiment path manager.
        
        Args:
            experiment_name: Name of the experiment
        """
        self.experiment_name = experiment_name or names_generator.generate_name()
        self.experiment_dir = os.path.join(RESULTS_DIR, self.experiment_name)
        # Ensure experiment directory exists
        self.ensure_dir_exists(self.experiment_dir)
        self._pdf_path = None
        self._conversation_name = None

    @property
    def pdf_path(self):
        return self._pdf_path

    @pdf_path.setter
    def pdf_path(self, pdf_name):
        self._pdf_path = os.path.join(RESULTS_DIR, pdf_name)

    @property
    def conversation_name(self):
        """Get the current conversation name, initialize if not set."""
        if self._conversation_name is None:
            self.set_next_conversation()
        return self._conversation_name
    
    @conversation_name.setter
    def conversation_name(self, name):
        """Set the conversation name manually."""
        self._conversation_name = name

    @staticmethod
    def ensure_dir_exists(dir_path: str) -> None:
        """Ensure a directory exists."""
        os.makedirs(dir_path, exist_ok=True)

    def set_next_conversation(self) -> str:
        """
        Set the conversation name to the next available one and return it.
        
        Returns:
            New conversation name with incremented number
        """
        count = len(self.list_conversations()) + 1
        self._conversation_name = f"conversation_{count}"
        return self._conversation_name

    def set_conversation(self, conversation_name: str) -> str:
        """
        Set the conversation name explicitly.
        
        Args:
            conversation_name: Name of the conversation to set
            
        Returns:
            The set conversation name
        """
        self._conversation_name = conversation_name
        return self._conversation_name

    def next_conversation_name(self) -> str:
        """
        Generate the next conversation name based on the number of existing conversations.
        Assumes conversations are created sequentially.
        
        Returns:
            New conversation name with incremented number
        """
        count = len(self.list_conversations()) + 1
        return f"conversation_{count}"

    def list_conversations(self) -> List[str]:
        """
        List all conversations in this experiment.
        
        Returns:
            List of conversation names
        """
        if not os.path.exists(self.experiment_dir) or not os.listdir(self.experiment_dir):
            return []

        # Get directory listing and filter for conversation folders
        pattern = r"^conversation_\d+$"
        conversations = [
            item for item in os.listdir(self.experiment_dir)
            if re.match(pattern, item)
        ]

        # Sort by conversation number
        conversations.sort()
        return conversations

    def get_conversation_dir(self) -> str:
        """
        Get the directory path for the current conversation within this experiment.
        Creates the directory if it doesn't exist.
        
        Returns:
            Path to the conversation directory
        """
        conversation_dir = os.path.join(self.experiment_dir, self.conversation_name)
        self.ensure_dir_exists(conversation_dir)
        return conversation_dir

    def get_ground_truth_path(self) -> str:
        """
        Get the path for a ground truth file.
        
        Returns:
            Path to the ground truth file
        """
        return os.path.join(self.get_conversation_dir(), "ground_truth.json")

    def get_generated_conversation_path(self) -> str:
        """
        Get the path for a generated conversation file.
        
        Returns:
            Path to the generated conversation file
        """
        return os.path.join(self.get_conversation_dir(), "generated_conversation.txt")

    def get_extracted_data_path(self) -> str:
        """
        Get the path for an extracted data file.
        
        Returns:
            Path to the extracted data file
        """
        return os.path.join(self.get_conversation_dir(), "extracted.json")

    def get_evaluation_path(self) -> str:
        """
        Get the path for an evaluation file.
        
        Returns:
            Path to the evaluation file
        """
        return os.path.join(self.get_conversation_dir(), "evaluation.json")

    # File saving methods

    def save_ground_truth(self, ground_truth_data: Dict[str, Any]) -> str:
        """
        Save ground truth data for the current conversation.
        
        Args:
            ground_truth_data: Ground truth data to save
            
        Returns:
            Path to the saved ground truth file
        """
        return self.save_json(ground_truth_data, self.get_ground_truth_path())

    def save_conversation(self, conversation_text: str) -> str:
        """
        Save a generated conversation for the current conversation.
        
        Args:
            conversation_text: Conversation text to save
            
        Returns:
            Path to the saved conversation file
        """
        return self.save_text(conversation_text, self.get_generated_conversation_path())

    def save_extracted_data(self, extracted_data: Dict[str, Any]) -> str:
        """
        Save extracted data for the current conversation.
        
        Args:
            extracted_data: Extracted data to save
            
        Returns:
            Path to the saved extracted data file
        """
        return self.save_json(extracted_data, self.get_extracted_data_path())

    def save_evaluation(self, evaluation_data: Dict[str, Any]) -> str:
        """
        Save evaluation results for the current conversation.
        
        Args:
            evaluation_data: Evaluation data to save
            
        Returns:
            Path to the saved evaluation file
        """
        return self.save_json(evaluation_data, self.get_evaluation_path())

    # General file operation methods

    @staticmethod
    def save_json(data: Dict[str, Any], file_path: str) -> str:
        """
        Save data as JSON to a file.
        
        Args:
            data: Data to save
            file_path: Path to save the file
        Returns:
            Path to the saved file
        """
        # Ensure parent directory exists
        ExperimentPathManager.ensure_dir_exists(os.path.dirname(file_path))

        # Write the JSON data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

        return file_path

    def save_text(self, text: str, file_path: str) -> str:
        """
        Save text to a file.
        
        Args:
            text: Text to save
            file_path: Path to save the file
            
        Returns:
            Path to the saved file
        """
        # Ensure parent directory exists
        self.ensure_dir_exists(os.path.dirname(file_path))

        # Write the text
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)

        return file_path

    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """
        Load JSON data from a file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            The loaded JSON data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def load_text(file_path: str) -> str:
        """
        Load text from a file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            The content of the text file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the file exists, False otherwise
        """
        return os.path.isfile(file_path)

    @staticmethod
    def create_backup(file_path: str) -> str:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, ext = os.path.splitext(file_path)
        backup_path = f"{filename}_backup_{timestamp}{ext}"

        # Copy the file
        shutil.copy2(file_path, backup_path)

        return backup_path

    def has_conversation(self, conversation_name: str) -> bool:
        """
        Check if a specific conversation exists within this experiment.
        
        Args:
            conversation_name: Name of the conversation to check
            
        Returns:
            True if the conversation exists, False otherwise
        """
        conversation_dir = os.path.join(self.experiment_dir, conversation_name)
        return os.path.isdir(conversation_dir)

    def has_ground_truth(self) -> bool:
        """
        Check if ground truth exists for the current conversation.
        
        Returns:
            True if ground truth exists, False otherwise
        """
        return self.file_exists(self.get_ground_truth_path())

    def has_extracted_data(self) -> bool:
        """
        Check if extracted data exists for the current conversation.
        
        Returns:
            True if extracted data exists, False otherwise
        """
        return self.file_exists(self.get_extracted_data_path())

    def conversation_count(self) -> int:
        """
        Count the number of conversations in this experiment.
        
        Returns:
            Number of conversations
        """
        return len(self.list_conversations())

    def create_conversation(self) -> str:
        """
        Create a new conversation directory and set it as the current conversation.
        
        Returns:
            Path to the created conversation directory
        """
        # Generate name
        self.set_next_conversation()

        # Create the directory
        conversation_dir = self.get_conversation_dir()
        
        return conversation_dir

    def delete_conversation(self, backup: bool = True) -> bool:
        """
        Delete the current conversation and all its files.
        
        Args:
            backup: Whether to create a backup before deletion
            
        Returns:
            True if deletion was successful, False otherwise
        """
        conversation_dir = os.path.join(self.experiment_dir, self.conversation_name)

        # Check if the conversation exists
        if not os.path.isdir(conversation_dir):
            return False

        # Create backup if requested
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"{conversation_dir}_backup_{timestamp}"
            shutil.copytree(conversation_dir, backup_dir)

        # Delete the conversation directory
        shutil.rmtree(conversation_dir)

        return True

    @property
    # Function to get the global template path
    def template_path(self) -> str:
        """Get the path for the global template file in results."""
        return str(os.path.join(RESULTS_DIR, TEMPLATE_FILENAME))

    @property
    def abridged_template_path(self) -> str:
        """Get the path for the global template file in results."""
        return str(os.path.join(RESULTS_DIR, TEMPLATE_FILENAME_ABR))

    @property
    def schema_path(self) -> str:
        """Get the path for the global schema file in results."""
        return str(os.path.join(RESULTS_DIR, SCHEMA_FILENAME))

    def save_template(self, template_data: Dict[str, Any]) -> str:
        return ExperimentPathManager.save_json(template_data, self.template_path)

    def save_abridged_template(self, template_data: Dict[str, Any]) -> str:
        return ExperimentPathManager.save_json(template_data, self.abridged_template_path)

    def load_template(self) -> Dict[str, Any]:
        return ExperimentPathManager.load_json(self.template_path)

    def load_abridged_template(self) -> Dict[str, Any]:
        return ExperimentPathManager.load_json(self.abridged_template_path)

    def save_schema(self, schema_data: Dict[str, Any]) -> str:
        return ExperimentPathManager.save_json(schema_data, self.schema_path)

    def load_schema(self) -> Dict[str, Any]:
        return ExperimentPathManager.load_json(self.schema_path)


# Function to get an experiment path manager
def get_experiment(experiment_name: str = None) -> ExperimentPathManager:
    """
    Get a path manager for a specific experiment.

    Args:
        experiment_name: Name of the experiment

    Returns:
        ExperimentPathManager instance for the experiment
    """
    return ExperimentPathManager(experiment_name)


# Function to list all experiments
def list_experiments() -> List[str]:
    """
    List all available experiments.

    Returns:
        List of experiment names
    """
    if not os.path.exists(RESULTS_DIR):
        return []

    # Get directories that aren't __pycache__
    return [
        d for d in os.listdir(RESULTS_DIR)
        if os.path.isdir(os.path.join(RESULTS_DIR, d)) and d != "__pycache__"
    ]
