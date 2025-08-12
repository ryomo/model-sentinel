"""
Inference using the downloaded model
"""

from transformers import AutoModelForCausalLM, AutoTokenizer

from model_sentinel import verify_local_model


def main():
    MODEL_DIR = "path/to/your/local/model/directory"  # Replace with your local model directory path
    REVISION = None

    device = "cuda"

    verify_local_model(MODEL_DIR, gui=True)

    # Load model and tokenizer from Hub
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR,
        revision=REVISION,
        trust_remote_code=True,
    ).to(device)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    tokenizer.pad_token = tokenizer.eos_token

    # Encode a prompt
    prompt = "Hello, how are"
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(device)

    # Generate output tokens
    generated_ids = model.generate(
        input_ids=input_ids,
        eos_token_id=tokenizer.eos_token_id,
        do_sample=True,
    )

    # Decode and print the result
    generated_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    print(f"\n  Generated: '{generated_text}'")


if __name__ == "__main__":
    main()
