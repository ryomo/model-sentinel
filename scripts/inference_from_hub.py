"""
Inference using the uploaded model from Hugging Face Hub.
"""

from transformers import AutoModelForCausalLM, AutoTokenizer

from model_sentinel import verify_hf_model


def main():
    REPO_NAME = "ryomo/malicious-code-test"
    REVISION = "main"

    device = "cuda"

    verify_hf_model(REPO_NAME, REVISION, gui=True)

    # Load model and tokenizer from Hub
    model = AutoModelForCausalLM.from_pretrained(
        REPO_NAME,
        revision=REVISION,
        trust_remote_code=True,
    ).to(device)
    tokenizer = AutoTokenizer.from_pretrained(REPO_NAME)
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
