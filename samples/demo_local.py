"""
Inference using the downloaded model from a ZIP file.
"""

from pathlib import Path

from transformers import AutoModelForCausalLM, AutoTokenizer

from model_sentinel import verify_local_model


def main():
    ZIP_URL = "https://guinea-pig.co/temp/model.zip"
    REVISION = None
    LOCAL_PATH = "./downloaded_models"

    device = "cuda"

    MODEL_DIR = download_and_extract_zip(ZIP_URL, LOCAL_PATH)

    verify_local_model(MODEL_DIR, gui=True)

    # Load model and tokenizer from Hub
    print("Loading model from Hugging Face Hub...")
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


def download_and_extract_zip(url: str, extract_to: str | Path) -> Path:
    """Download a ZIP from the given URL and extract it under extract_to.

    Naming rules for the created directory under extract_to:
    - If the ZIP has a single top-level directory, use that directory name.
    - Otherwise, use the ZIP file name without extension.

    Always ensures files are placed under a subdirectory of extract_to.
    Returns the path to that directory.
    """
    import io
    import shutil
    import time
    import urllib.parse
    import zipfile

    import requests

    extract_root = Path(extract_to)
    extract_root.mkdir(parents=True, exist_ok=True)

    print(f"Downloading and extracting from {url}...")
    ts = int(time.time())
    url_with_ts = f"{url}{'&' if '?' in url else '?'}_ts={ts}"

    with requests.get(url_with_ts, stream=True) as r:
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as zip_ref:
            names = [n for n in zip_ref.namelist() if n]
            top_levels = {n.split("/")[0] for n in names}
            only = (
                next(iter(top_levels))
                if (len(top_levels) == 1 and any("/" in n for n in names))
                else None
            )

            # Decide target directory name
            stem = Path(urllib.parse.urlparse(url).path).stem or "extracted"
            target_dir = extract_root / (only if only else stem)

            # Clean existing target path
            if target_dir.exists():
                (
                    shutil.rmtree(target_dir)
                    if target_dir.is_dir()
                    else target_dir.unlink()
                )

            # Extract
            if only:
                # For single-root archives, extract into extract_root so the top-level dir is created
                zip_ref.extractall(extract_root)
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                zip_ref.extractall(target_dir)

            result_path = target_dir

    print(f"Complete. Extracted to: {result_path}")
    return result_path


if __name__ == "__main__":
    main()
