"""
Evaluator module.
Compares extracted data with ground truth and calculates accuracy metrics.
"""

import json
import copy
import os
from typing import Dict, Any, List, Union

from openai import OpenAI

from core.base import BaseGenerator
from utils import MISSING_FIELD, settings


class Evaluator(BaseGenerator):
    """
    Evaluates extracted data against ground truth.
    This class compares the extracted data from conversations with the ground truth
    and calculates various accuracy metrics.
    """
    model_name = "gpt-4o-mini"
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate(self) -> Dict[str, Any]:
        """
        Generate evaluation metrics by comparing extracted data with ground truth.
        
        Returns:
            Evaluation metrics as a dictionary
        """
        # Load the ground truth and extracted data
        ground_truth_path = self.path_manager.get_ground_truth_path()
        extracted_path = self.path_manager.get_extracted_data_path()
        
        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            ground_truth = json.load(f)
            
        with open(extracted_path, 'r', encoding='utf-8') as f:
            extracted = json.load(f)
        
        # Process ground truth to identify missing fields
        # We need to find fields that were marked as MISSING_FIELD
        # and remove them from consideration in our evaluation
        missing_fields = []
        processed_ground_truth = self._find_missing_fields(ground_truth, missing_fields=missing_fields)
        
        # Calculate metrics
        evaluation = self._evaluate_data(
            ground_truth=processed_ground_truth,
            extracted=extracted,
            missing_fields=missing_fields
        )
        
        return evaluation

    def save(self, evaluation: Dict[str, Any]) -> str:
        """
        Save evaluation results for a conversation.
        
        Args:
            evaluation: Evaluation data to save
            
        Returns:
            Path to the saved evaluation file
        """
        return self.path_manager.save_evaluation(evaluation)

    def get_prompt(self) -> str:
        """
        Not applicable for this evaluator as it doesn't use prompts.
        """
        raise NotImplementedError("This evaluator doesn't use prompts")

    def _find_missing_fields(self, data, path="", missing_fields=None):
        """
        Recursively find fields marked as MISSING_FIELD in the data.
        
        Args:
            data: The data structure to process
            path: Current path in the data structure
            missing_fields: List to collect paths to missing fields
            
        Returns:
            Modified data with MISSING_FIELD markers removed
        """
        # Make a deep copy to avoid modifying the original
        if missing_fields is None:
            missing_fields = []
            data = copy.deepcopy(data)
        
        if isinstance(data, dict):
            keys_to_delete = []
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, (dict, list)):
                    data[key] = self._find_missing_fields(value, current_path, missing_fields)
                elif value == MISSING_FIELD:
                    missing_fields.append(current_path)
                    keys_to_delete.append(key)
            
            # Remove MISSING_FIELD entries
            for key in keys_to_delete:
                del data[key]
                
        elif isinstance(data, list):
            indices_to_delete = []
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                if isinstance(item, (dict, list)):
                    data[i] = self._find_missing_fields(item, current_path, missing_fields)
                elif item == MISSING_FIELD:
                    missing_fields.append(current_path)
                    indices_to_delete.append(i)
            
            # Remove MISSING_FIELD entries (in reverse to avoid index shifting)
            for index in sorted(indices_to_delete, reverse=True):
                del data[index]
                
        return data
        
    def _evaluate_data(
        self, 
        ground_truth: Dict[str, Any],
        extracted: Dict[str, Any],
        missing_fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Compare extracted data with ground truth and calculate metrics.
        
        Args:
            ground_truth: Ground truth data with MISSING_FIELD values removed
            extracted: Extracted data
            missing_fields: List of fields that were marked as missing in the ground truth
            
        Returns:
            Evaluation metrics
        """
        # Set default empty list if None
        missing_fields = missing_fields or []
        
        # Flatten both dictionaries for comparison
        flat_ground_truth = self._flatten_dict(ground_truth)
        flat_extracted = self._flatten_dict(extracted)
        
        # Collect field-level results
        field_results = {}
        
        # Calculate field-level metrics
        for field, truth_value in flat_ground_truth.items():
            # Check if field exists in extracted data
            if field in flat_extracted:
                extracted_value = flat_extracted[field]
                
                # Compare values
                is_match = self._compare_values(truth_value, extracted_value)
                
                field_results[field] = {
                    "ground_truth": truth_value,
                    "extracted": extracted_value,
                    "match": is_match,
                    "category": "present"
                }
            else:
                # Field was not extracted
                field_results[field] = {
                    "ground_truth": truth_value,
                    "extracted": None,
                    "match": False,
                    "category": "present",
                    "error": "missing_field"
                }
        
        # Check for extra fields in extracted data
        for field in flat_extracted:
            if field not in flat_ground_truth:
                # If the field is marked as MISSING_INFORMATION in the extracted data,
                # it likely was removed from ground truth during processing, so it's not really an error
                if flat_extracted[field] == MISSING_FIELD:
                    field_results[field] = {
                        "ground_truth": MISSING_FIELD,  # Set ground truth to MISSING_FIELD for consistency
                        "extracted": flat_extracted[field],
                        "match": True,  # This is a correct extraction of a missing field
                        "category": "missing"
                    }
                else:
                    field_results[field] = {
                        "ground_truth": None,
                        "extracted": flat_extracted[field],
                        "match": False,
                        "category": "extra",
                        "error": "extra_field"
                    }
        
        # Calculate summary metrics
        metrics = self._calculate_metrics(field_results, missing_fields)
        
        # Build the evaluation response
        evaluation = {
            "metrics": metrics,
            "field_results": field_results,
            "missing_fields": missing_fields
        }
        
        return evaluation

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten a nested dictionary.
        
        Args:
            d: The dictionary to flatten
            parent_key: The parent key for nested values
            sep: Separator for keys in the flattened dictionary
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))
                
        return dict(items)

    def _semantic_match(self, value1: str, value2: str) -> bool:
        """
        Check if two values are semantically equivalent using GPT.
        
        Args:
            value1: First value as string
            value2: Second value as string
            
        Returns:
            True if values are semantically equivalent, False otherwise
        """
        try:
            # Skip semantic matching for very different length strings or very short strings
            if abs(len(value1) - len(value2)) > 20 or min(len(value1), len(value2)) < 3:
                return False
                
            prompt = f"""Compare these two values and determine if they convey the same, or very similar, 
            client information in a financial context.
            Value 1: "{value1}"
            Value 2: "{value2}"
            
            Only respond with YES if they convey the same, or very similar, client information
            (ignoring formatting, spelling variations, and minor wording differences), or NO if they have different 
            meanings. Just respond with YES or NO."""
            
            response = self.client.responses.create(
                model=self.model_name,
                input=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0  # Use deterministic output for consistency
            )
            
            result = response.output_text.strip()
            return "yes" in result.lower()
        except Exception as e:
            # Log the error but fall back to exact matching in case of API failure
            print(f"Error in semantic matching: {e}")
            return False
    
    def _compare_values(self, value1: Any, value2: Any) -> bool:
        """
        Compare two values, handling different types and formats.
        First tries exact matching, then falls back to semantic matching for non-matching strings.
        
        Args:
            value1: First value
            value2: Second value
            
        Returns:
            True if values match (exactly or semantically), False otherwise
        """
        # Handle None values
        if value1 is None and value2 is None:
            return True
        if value1 is None or value2 is None:
            return False
        if MISSING_FIELD in value1 and MISSING_FIELD in value2:
            return True
        if MISSING_FIELD in value1 or MISSING_FIELD in value2:
            return False
        
        # Convert to strings for comparison, handling different formats
        str1 = str(value1).lower().strip()
        str2 = str(value2).lower().strip()
        
        # First try exact matching
        if str1 == str2:
            return True
            
        # If exact match fails, try semantic matching for potential equivalence
        return self._semantic_match(str1, str2)

    def _calculate_metrics(
        self, 
        field_results: Dict[str, Dict[str, Any]],
        missing_fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate summary metrics from field-level results including precision and recall.
        
        Args:
            field_results: Field-level evaluation results
            missing_fields: Fields that were marked as missing in the ground truth
            
        Returns:
            Summary metrics including precision and recall
        """
        # Initialize counters for precision and recall calculation
        true_positives = 0  # Correctly extracted and matched fields
        false_positives = 0  # Extracted fields that are incorrect or shouldn't be extracted
        false_negatives = 0  # Fields that should have been extracted but weren't
        
        # Count fields by category for reporting
        categories = {
            "present": {"total": 0, "matched": 0},
            "extra": {"total": 0, "matched": 0},
            "missing": {"total": 0, "matched": 0}
        }
        
        # Analyze each field result
        for field, result in field_results.items():
            category = result["category"]
            is_match = result.get("match", False)
            
            # Update category counters
            if category in categories:
                categories[category]["total"] += 1
                if is_match:
                    categories[category]["matched"] += 1
            
            # Update precision/recall counters
            if category == "present":
                if "error" in result and result["error"] == "missing_field":
                    # Field not extracted but should have been
                    false_negatives += 1
                elif is_match:
                    # Correctly extracted field
                    true_positives += 1
                else:
                    # Extracted but incorrect value
                    false_positives += 1
            elif category == "extra":
                # Extracted field that doesn't exist in ground truth
                false_positives += 1
        
        # Calculate precision and recall
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        # Calculate F1 score
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Calculate overall accuracy
        total_judgments = true_positives + false_positives + false_negatives
        accuracy = true_positives / total_judgments if total_judgments > 0 else 0
        
        # Calculate category accuracies
        category_metrics = {}
        for category, counts in categories.items():
            category_metrics[category] = {
                "total": counts["total"],
                "matched": counts["matched"],
                "accuracy": counts["matched"] / counts["total"] if counts["total"] > 0 else 0
            }
        
        # Build metrics dictionary
        metrics = {
            "overall_accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "total_fields": sum(cat["total"] for cat in categories.values()),
            "missing_fields_count": len(missing_fields) if missing_fields else 0,
            "categories": category_metrics
        }
        
        return metrics


class EvaluationAggregator(BaseGenerator):
    def generate(self):
        """
        Aggregate evaluation metrics (accuracy, precision, recall, etc.) across conversations
        within a specific experiment.
        Returns:
            Dictionary containing aggregated metrics for the experiment
        """
        # Get the path manager for the specified experiment
        # Get conversations for this experiment
        conversations = self.path_manager.list_conversations()
        if not conversations:
            print(f"No conversations found in experiment: {self.path_manager.experiment_name}")
            return

        # Initialize aggregation variables
        total_conversations = 0
        metrics_sum = {
            'overall_accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0
        }

        # Process each conversation's evaluation file
        for conversation in conversations:
            self.path_manager.set_conversation(conversation)
            try:
                # Load the evaluation file
                evaluation = self.path_manager.load_json(self.path_manager.get_evaluation_path())

                # Get metrics from the evaluation
                metrics = evaluation.get('metrics', {})
                if metrics:
                    total_conversations += 1

                    # Add to our running totals
                    for key in metrics_sum.keys():
                        if key in metrics:
                            metrics_sum[key] += metrics[key]

            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error processing {self.path_manager.get_evaluation_path()}: {e}")

        # Calculate averages
        aggregated_metrics = {}
        if total_conversations > 0:
            aggregated_metrics = {
                key: value / total_conversations
                for key, value in metrics_sum.items()
            }

        # Prepare the aggregated results
        aggregated_results = {
            'experiment': self.path_manager.experiment_name,
            'total_conversations': total_conversations,
            'aggregated_metrics': aggregated_metrics
        }

        return aggregated_results

    def save(self, output: Union[str, Dict[str, Any]]) -> str:
        return self.path_manager.save_json(output, os.path.join(self.path_manager.experiment_dir,
                                                                "aggregated_results.json"))

    def get_prompt(self, *args) -> str:
        return ""
