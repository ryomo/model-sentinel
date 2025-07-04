"""
Inference using the uploaded model from Hugging Face Hub.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from model_sentinel import check


def main():
    REPO_NAME = "ryomo/malicious-code-test"
    REVISION = "main"
    print(f"Using repository: {REPO_NAME} at revision: {REVISION}")

    if not check(REPO_NAME, REVISION):
        print(f"Repository {REPO_NAME} at revision {REVISION} is not verified.")
        print("Please verify all remote files in the repository before proceeding.")
        return

    # Load model and tokenizer from Hub
    print("Loading model from Hugging Face Hub...")
    model = AutoModelForCausalLM.from_pretrained(
        REPO_NAME,
        revision=REVISION,
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(REPO_NAME)
    tokenizer.pad_token = tokenizer.eos_token

    # Set device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    print(f"Model loaded successfully on {device}")

    # Test generation
    print("\n=== Generation Test ===")
    prompt = "Hello, how are"
    print(f"\nPrompt: '{prompt}'\n")
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(device)
    generated_ids = model.generate(
        input_ids=input_ids,
        max_new_tokens=20,
        temperature=0.7,
        eos_token_id=tokenizer.eos_token_id,
        do_sample=True,
    )

    # Decode and print the result
    generated_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    print(f"\nGenerated: '{generated_text}'")


if __name__ == "__main__":
    main()
