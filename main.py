"""Main script for the financial onboarding data extraction pipeline."""

import argparse
import json
import os
from typing import Optional

from core.conversation_generator import ConversationGenerator
from core.data_extractor import DataExtractor
from core.evaluation_generator import Evaluator, EvaluationAggregator
from core.example_forms_generator import ExampleFormGenerator
from core.schema_generator import SchemaGenerator
from core.template_generator import TemplateGenerator
from core.template_shortener import TemplateShortener
from utils.paths import get_experiment


def create_template(pdf_name: Optional[str] = "General Fact Find Template.pdf"):
    """Create JSON template from PDF document and an abridged version."""
    path_manager = get_experiment()
    path_manager.pdf_path = pdf_name
    template_gen = TemplateGenerator(path_manager)
    template_gen.create()
    
    shortener = TemplateShortener(path_manager)
    shortener.create()


def setup_experiment():
    """Set up a new experiment, generating template, schema, and form."""
    path_manager = get_experiment()
    # Generate JSON schema from the template
    schema_gen = SchemaGenerator(path_manager)
    schema_gen.create()
    return path_manager


def run_conversation_pipeline(experiment_name: Optional[str] = None,
                              num_conversations: int = 1):
    """Run the full pipeline including ground truth, conversation, extraction, and evaluation."""
    # Set up the experiment
    path_manager = get_experiment(experiment_name)

    # Loop through the number of conversations to generate
    for _ in range(num_conversations):
        # Create a new conversation
        path_manager.create_conversation()
        print(f"Processing conversation: {path_manager.conversation_name}")

        # Generate ground truth with randomly removed fields
        form_gen = ExampleFormGenerator(path_manager)
        form_gen.create()
        print("Generated ground truth data with removed fields")

        # Generate conversation based on ground truth
        conv_gen = ConversationGenerator(path_manager)
        conv_gen.create()
        print("Generated simulated conversation")

        # Extract data from conversation
        extractor = DataExtractor(path_manager)
        extractor.create()
        print("Extracted structured data from conversation")

        # Evaluate extraction against ground truth
        evaluator = Evaluator(path_manager)
        eval_path = evaluator.create()
        print(f"Evaluation complete and saved to {eval_path}")
        print("---")

    aggregator = EvaluationAggregator(path_manager)
    agg_path = aggregator.create()
    print(f"Evaluation metrics aggregated and saved to {agg_path}")
    print("---")


def main():
    parser = argparse.ArgumentParser(description="Financial Onboarding Data Extraction")
    parser.add_argument("--conversations", type=int, default=5, help="Number of conversations to generate")
    parser.add_argument("--experiment", type=str, default=None, help="Experiment name")
    parser.add_argument("--create-template", action="store_true", help="Create template from PDF")
    parser.add_argument("--setup-schema", action="store_true", help="Generate schema from template")
    parser.add_argument("--pdf-name", type=str, default="General Fact Find Template.pdf", 
                      help="PDF file to use for template creation. Please put it in the results folder.")
    args = parser.parse_args()
    
    if args.create_template:
        create_template(pdf_name=args.pdf_name)
    
    if args.setup_schema:
        setup_experiment()
    
    run_conversation_pipeline(experiment_name=args.experiment, num_conversations=5)


if __name__ == '__main__':
    main()
