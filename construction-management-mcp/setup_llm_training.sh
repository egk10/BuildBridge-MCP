#!/bin/bash
"""
Construction Management LLM Fine-tuning Setup Script

This script sets up the environment for fine-tuning a local LLM
specifically for construction management tasks.
"""

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/construction_llm_env"
DATA_DIR="$PROJECT_ROOT/data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_system_requirements() {
    log_info "Checking system requirements..."

    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        log_success "Python $PYTHON_VERSION is compatible"
    else
        log_error "Python $PYTHON_VERSION is not supported. Please upgrade to Python 3.8+"
        exit 1
    fi

    # Check available memory
    if command -v free &> /dev/null; then
        TOTAL_MEM=$(free -g | awk 'NR==2{printf "%.0f", $2}')
        if [ "$TOTAL_MEM" -lt 16 ]; then
            log_warning "System has ${TOTAL_MEM}GB RAM. Fine-tuning Llama 3.1 8B requires at least 16GB RAM."
            log_warning "Consider using a smaller model or cloud resources."
        else
            log_success "System has ${TOTAL_MEM}GB RAM - sufficient for fine-tuning"
        fi
    fi

    # Check available disk space
    if command -v df &> /dev/null; then
        AVAILABLE_SPACE=$(df "$PROJECT_ROOT" | tail -1 | awk '{print int($4/1024/1024)}')  # GB
        if [ "$AVAILABLE_SPACE" -lt 50 ]; then
            log_warning "Only ${AVAILABLE_SPACE}GB available. Fine-tuning requires ~50GB free space."
        else
            log_success "${AVAILABLE_SPACE}GB available - sufficient disk space"
        fi
    fi
}

setup_virtual_environment() {
    log_info "Setting up Python virtual environment..."

    if [ -d "$VENV_DIR" ]; then
        log_warning "Virtual environment already exists at $VENV_DIR"
        read -p "Remove and recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            log_info "Using existing virtual environment"
            return
        fi
    fi

    python3 -m venv "$VENV_DIR"
    log_success "Created virtual environment at $VENV_DIR"

    # Activate and upgrade pip
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip

    log_success "Virtual environment setup complete"
}

install_dependencies() {
    log_info "Installing Python dependencies..."

    source "$VENV_DIR/bin/activate"

    # Core ML dependencies
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    pip install transformers datasets accelerate peft trl bitsandbytes

    # Data processing
    pip install pandas numpy scikit-learn

    # Utilities
    pip install tqdm wandb huggingface_hub

    log_success "Dependencies installed successfully"
}

setup_huggingface() {
    log_info "Setting up Hugging Face access..."

    if [ -z "$HF_TOKEN" ]; then
        log_warning "HF_TOKEN environment variable not set"
        echo "Please get your Hugging Face token from: https://huggingface.co/settings/tokens"
        echo "Then set it with: export HF_TOKEN=your_token_here"
        echo ""
        read -p "Enter your Hugging Face token (or press Enter to skip): " -r
        if [ -n "$REPLY" ]; then
            export HF_TOKEN="$REPLY"
            echo "export HF_TOKEN=$REPLY" >> ~/.bashrc
            log_success "Hugging Face token configured"
        else
            log_warning "Skipping Hugging Face setup. You'll need to configure it manually."
        fi
    else
        log_success "Hugging Face token already configured"
    fi
}

download_base_model() {
    log_info "Downloading base Llama model..."

    source "$VENV_DIR/bin/activate"

    cat << 'EOF' > download_model.py
import os
from huggingface_hub import snapshot_download

# Download Llama 3.1 8B model
model_path = "./models/llama-3.1-8b"
os.makedirs(model_path, exist_ok=True)

print("Downloading Llama 3.1 8B base model...")
snapshot_download(
    repo_id="meta-llama/Llama-3.1-8B",
    local_dir=model_path,
    local_dir_use_symlinks=False
)
print(f"Model downloaded to {model_path}")
EOF

    python download_model.py
    log_success "Base model downloaded"
}

create_training_script() {
    log_info "Creating fine-tuning training script..."

    cat << 'EOF' > train_construction_llm.py
#!/usr/bin/env python3
"""
Fine-tuning script for Construction Management LLM

Fine-tunes Llama 3.1 8B on construction-specific datasets.
"""

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
import json
import os
from pathlib import Path

def load_construction_dataset(data_path):
    """Load the construction fine-tuning dataset"""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]

    # Convert to instruction format
    formatted_data = []
    for item in data:
        instruction = item['instruction']
        output = item['output']

        # Format as instruction-response pair
        text = f"<s>[INST] {instruction} [/INST] {output} </s>"
        formatted_data.append({"text": text})

    return formatted_data

def tokenize_function(examples, tokenizer):
    """Tokenize the dataset"""
    return tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=512,
    )

def main():
    # Configuration
    model_name = "meta-llama/Llama-3.1-8B"
    output_dir = "./models/construction-llama-3.1-8b"
    dataset_path = "./data/construction_instruction_dataset.jsonl"

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # Load dataset
    dataset = load_construction_dataset(dataset_path)

    # Tokenize dataset
    tokenized_dataset = [tokenize_function(item, tokenizer) for item in dataset]

    # Load model with quantization
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        load_in_8bit=True,
        device_map="auto",
        torch_dtype=torch.float16
    )

    # Prepare model for training
    model = prepare_model_for_kbit_training(model)

    # LoRA configuration
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, lora_config)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=2,
        learning_rate=2e-4,
        fp16=True,
        save_total_limit=3,
        logging_steps=10,
        save_steps=500,
        evaluation_strategy="steps",
        eval_steps=500,
        load_best_model_at_end=True,
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )

    # Train the model
    trainer.train()

    # Save the fine-tuned model
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    print(f"Fine-tuned model saved to {output_dir}")

if __name__ == "__main__":
    main()
EOF

    chmod +x train_construction_llm.py
    log_success "Training script created"
}

create_inference_script() {
    log_info "Creating model inference script..."

    cat << 'EOF' > inference_construction_llm.py
#!/usr/bin/env python3
"""
Inference script for Construction Management LLM

Loads the fine-tuned model and provides construction-specific responses.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import sys

class ConstructionLLM:
    def __init__(self, model_path="./models/construction-llama-3.1-8b"):
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Llama-3.1-8B",
            torch_dtype=torch.float16,
            device_map="auto"
        )

        # Load fine-tuned adapters
        self.model = PeftModel.from_pretrained(base_model, model_path)
        self.model.eval()

    def generate_response(self, instruction, max_length=512, temperature=0.7):
        """Generate a response to a construction-related instruction"""

        # Construction-specific system prompt
        system_prompt = """You are a construction project management expert. You have extensive knowledge of:
- Construction project lifecycle and methodologies
- Industry standards (OSHA, PMI, AGC guidelines)
- Project management best practices
- Construction terminology and jargon
- Risk management and safety protocols
- Budget and cost control principles

When responding:
1. Use accurate construction terminology
2. Reference industry standards when relevant
3. Consider project phases, safety requirements, and budget constraints
4. Provide actionable insights based on data provided
5. Be specific about construction processes and requirements
6. Highlight potential risks and mitigation strategies

"""

        # Format the prompt
        prompt = f"<s>[INST] {system_prompt}\n\n{instruction} [/INST]"

        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        # Generate response
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        # Decode response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract just the response part (after the instruction)
        response = response.split("[/INST]")[-1].strip()

        return response

def main():
    if len(sys.argv) < 2:
        print("Usage: python inference_construction_llm.py 'Your construction question here'")
        sys.exit(1)

    question = sys.argv[1]

    # Initialize model
    llm = ConstructionLLM()

    # Generate response
    response = llm.generate_response(question)

    print(f"Question: {question}")
    print(f"Response: {response}")

if __name__ == "__main__":
    main()
EOF

    chmod +x inference_construction_llm.py
    log_success "Inference script created"
}

create_requirements_file() {
    log_info "Creating requirements file..."

    cat << 'EOF' > requirements_llm.txt
# Core ML libraries
torch>=2.0.0
transformers>=4.30.0
datasets>=2.10.0
accelerate>=0.20.0

# PEFT for efficient fine-tuning
peft>=0.4.0
bitsandbytes>=0.41.0
trl>=0.7.0

# Data processing
pandas>=1.5.0
numpy>=1.21.0
scikit-learn>=1.0.0

# Utilities
tqdm>=4.64.0
wandb>=0.15.0
huggingface-hub>=0.16.0

# Optional: for monitoring and visualization
matplotlib>=3.5.0
seaborn>=0.11.0
EOF

    log_success "Requirements file created"
}

create_readme() {
    log_info "Creating training README..."

    cat << 'EOF' > LLM_TRAINING_README.md
# Construction Management LLM Fine-tuning Guide

This guide walks you through fine-tuning a Llama 3.1 model specifically for construction management tasks.

## Prerequisites

- Python 3.8+
- At least 16GB RAM (32GB recommended)
- NVIDIA GPU with 8GB+ VRAM (for efficient training)
- 50GB+ free disk space
- Hugging Face account and token

## Quick Start

1. **Setup Environment:**
   ```bash
   ./setup_llm_training.sh
   source construction_llm_env/bin/activate
   ```

2. **Download Base Model:**
   ```bash
   python download_model.py
   ```

3. **Generate Training Data:**
   ```bash
   python src/dataset_generator.py
   ```

4. **Fine-tune Model:**
   ```bash
   python train_construction_llm.py
   ```

5. **Test Model:**
   ```bash
   python inference_construction_llm.py "What's the status of the Downtown Office Building?"
   ```

## Training Configuration

### Model: Llama 3.1 8B
- **Base Model:** meta-llama/Llama-3.1-8B
- **Fine-tuning Method:** LoRA (Low-Rank Adaptation)
- **Training Epochs:** 3
- **Batch Size:** 4 (with gradient accumulation)
- **Learning Rate:** 2e-4

### Dataset
- **Source:** Generated from your construction project data
- **Format:** Instruction-response pairs
- **Size:** ~500 samples (expandable)
- **Focus:** Construction terminology, project management, safety, budgeting

## Expected Training Time

- **Hardware:** RTX 3080 (10GB VRAM) + 32GB RAM
- **Time:** ~2-4 hours for 3 epochs
- **Memory Usage:** ~12GB GPU VRAM, ~16GB system RAM

## Model Capabilities After Fine-tuning

✅ **Construction Terminology:** Understands industry jargon and abbreviations
✅ **Project Management:** Provides PM-specific insights and recommendations
✅ **Safety Compliance:** References OSHA standards and safety protocols
✅ **Budget Analysis:** Offers construction-specific financial analysis
✅ **Schedule Management:** Understands CPM, delays, and recovery planning
✅ **Risk Assessment:** Identifies construction-specific risks and mitigations

## Integration with MCP

After fine-tuning, integrate the model with your MCP server:

```python
# In your MCP server
from inference_construction_llm import ConstructionLLM

llm = ConstructionLLM()

def enhance_response_with_llm(query, data):
    prompt = f"Analyze this construction data and answer: {query}\nData: {data}"
    return llm.generate_response(prompt)
```

## Troubleshooting

### Common Issues:

1. **Out of Memory:**
   - Reduce batch size in training arguments
   - Use smaller model (Llama 3.1 7B instead of 8B)
   - Enable gradient checkpointing

2. **Slow Training:**
   - Ensure GPU is being used (`nvidia-smi` to check)
   - Reduce model max length
   - Use mixed precision training

3. **Poor Results:**
   - Increase dataset size
   - Fine-tune for more epochs
   - Improve data quality and diversity

### Performance Optimization:

- Use `bitsandbytes` for 8-bit quantization
- Implement gradient accumulation
- Use `torch.compile()` for faster inference
- Cache tokenized datasets

## Next Steps

1. **Expand Dataset:** Add more construction-specific examples
2. **Domain Adaptation:** Fine-tune on additional construction documents
3. **Evaluation:** Create comprehensive test suite
4. **Deployment:** Set up model serving infrastructure
5. **Monitoring:** Track model performance and accuracy

## Resources

- [Llama Fine-tuning Guide](https://huggingface.co/docs/transformers/training)
- [PEFT Documentation](https://huggingface.co/docs/peft/index)
- [Construction Management Standards](https://www.osha.gov/construction)

---

Happy building! 🏗️🤖
EOF

    log_success "Training README created"
}

main() {
    echo "🏗️ Construction Management LLM Fine-tuning Setup"
    echo "=" * 60

    check_system_requirements
    setup_virtual_environment
    install_dependencies
    setup_huggingface
    create_training_script
    create_inference_script
    create_requirements_file
    create_readme

    echo ""
    log_success "Setup complete! 🎉"
    echo ""
    echo "📋 Next steps:"
    echo "1. Activate environment: source construction_llm_env/bin/activate"
    echo "2. Download model: python download_model.py"
    echo "3. Generate data: python src/dataset_generator.py"
    echo "4. Train model: python train_construction_llm.py"
    echo "5. Test model: python inference_construction_llm.py 'your question'"
    echo ""
    echo "📖 See LLM_TRAINING_README.md for detailed instructions"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi</content>
<parameter name="filePath">/home/egk/buildbridge-MCP/BuildBridge-MCP/construction-management-mcp/setup_llm_training.sh