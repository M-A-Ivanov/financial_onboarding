# Financial Onboarding Data Extraction

A system for extracting structured data from free-form conversational transcripts in financial onboarding scenarios using LLM-powered text processing.

## Overview

This project provides a robust, expandable framework for:

1. **Template Generation**: Analyzing documents to generate structured JSON templates that define what data to extract
2. **Ground Truth Generation**: Basis for conversation generation and for evaluation
   * Generate fully filled jsons based on the template.
   * Perform validity checks that fields have remained the same. 
3. **Conversation Generation**: Creating realistic financial onboarding conversations based on ground truths.
      * Obfuscate some fields, indicating that the information is missed in the conversation, to ensure that we can catch that and alert the advisor.
      * Ensure some field information can be inferred rather than stated directly, to test the extraction based on reasoning
4. **Transcript Processing**: Extracting structured data from conversations. Two possible basic approaches:
   * Either make use of the large context capacities (up to >1M tokens in Gemini), which no longer suffer from needle-in-heystack issues.
   * Or create a simple RAG by chunking the conversation on a client reply basis, embedding into a vectorDB and fetching relevant replies.
5. **Evaluation**: Compare with ground truth to see accuracy of extractions.

Results are stored in the 'results' folder with the following structure:
```
results/
├── experiment_1/
│   ├── conversation_1/
│   │    ├── ground_truth.json
│   │    ├── generated_conversation.txt
│   │    ├── extracted.json
│   │    ├── evaluation.json
│   ├── conversation_2/
│   │    ├── ...
├── experiment_2/
│   ├── ...
├── template.json
├── template_short.json
```
## Architecture

The project follows a modular architecture:

```
financial_onboarding/
├── core/                 # Core business logic components
├── utils/                # Utility functions and settings
├── results/              # Output data storage
```

### Core Components

- **Template Generator**: Creates JSON schemas based on document analysis
- **Schema Generator**: Converts templates to JSON schema for validation
- **Example Form Generator**: Creates ground truth data with controlled field omission
- **Conversation Generator**: Produces realistic financial conversations based on ground truth
- **Data Extractor**: Extracts structured data from conversations
- **Evaluator**: Compares extracted data with ground truth and calculates accuracy

### Key Features

- Centralized path management for data consistency
- Configurable settings via environment variables
- Support for multiple experiments and conversations
- Field obfuscation to test extraction robustness
- Detailed evaluation metrics

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/financial-onboarding.git
   cd financial-onboarding
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On Unix/MacOS
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a .env file with your OpenAI API key:
   ```
   # .env
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

The project provides a flexible command-line interface through the main.py script, allowing you to run the entire pipeline or specific components.

### Command Line Options

```bash
python main.py [OPTIONS]
```

**Arguments:**

- `--conversations INT`  Number of conversations to generate (default: 5)
- `--experiment TEXT`    Custom experiment name (auto-generated if not specified)
- `--create-template`    Flag to create a template from PDF
- `--setup-schema`       Flag to generate schema from template
- `--pdf-name TEXT`      PDF file to use for template creation (must be in the results folder)

### Examples

**Run the full pipeline:**
```bash
python main.py
```

**Run with custom settings:**
```bash
python main.py --conversations 3 --pdf-name "Custom_Template.pdf" --experiment "test_run_1"
```

**Run full pipeline:**
```bash
python main.py --create-template --setup-schema --conversations 1

```

**Run only the conversation pipeline (using existing template and schema):**
```bash
python main.py --experiment "existing_experiment"
```

### Workflow Steps

When run with default settings, the pipeline:
1. Generates a JSON template from the provided PDF
2. Creates a schema for validation from the template
3. Generates ground truth data with randomly omitted fields
4. Creates simulated conversations based on the ground truth
5. Extracts structured data from the conversations
6. Evaluates extraction accuracy against ground truth

## Potential Enhancements

1. **Multi-turn Extraction**: Implement progressive extraction over multiple conversation turns
2. **Entity Recognition**: Integrate specialized financial entity recognition for improved accuracy
3. **Validation Rules**: Add domain-specific validation for extracted fields
4. **Multi-language Support**: Extend capabilities to handle conversations in different languages
5. **Confidence Scores**: Implement confidence scoring for extracted fields
6. **Web Interface**: Create a dashboard for monitoring and managing extractions
7. **Export Formats**: Add support for exporting to various formats (CSV, Excel, etc.)
8. **Webhook Integration**: Enable integration with external systems

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.