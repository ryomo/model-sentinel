import argparse

from model_sentinel import __version__, verify_hf_model, verify_local_model
from model_sentinel.verify.verify import Verify


def main():
    DEFAULT_REVISION = "main"

    parser = argparse.ArgumentParser(description="Model Sentinel CLI")
    parser.add_argument(
        "--version", action="version", version=f"model-sentinel {__version__}"
    )
    parser.add_argument(
        "--hf",
        type=str,
        help="Hugging Face repository ID (e.g., ryomo/malicious-code-test)",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default=DEFAULT_REVISION,
        help=f"Model revision/branch (default: {DEFAULT_REVISION})",
    )
    parser.add_argument("--local", type=str, help="Path to local model directory")
    parser.add_argument("--gui", action="store_true", help="Launch GUI interface")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="GUI server host address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="GUI server port (default: 7860)",
    )
    parser.add_argument(
        "--list-verified", action="store_true", help="List all verified hashes"
    )
    parser.add_argument("--delete", action="store_true", help="Delete the hash file")
    args = parser.parse_args()

    if args.delete:
        # Delete the hash file (the list of verified files)
        verify = Verify()
        result = verify.delete_hash_file()
        if result:
            print("Hash file deleted.")
        else:
            print("Failed to delete hash file.")

    elif args.list_verified:
        # List all verified hashes
        verify = Verify()
        verify.list_verified_hashes()

    else:
        # Verify local model
        if args.local:
            _local_verification(args)

        # Verify Hugging Face model
        elif args.hf:
            _hf_verification(args)

        # No model specified - show help
        else:
            parser.print_help()


def _local_verification(args):
    """Handle verification flow for a local model based on parsed args."""
    print(f"Verifying local model: {args.local}")
    result = verify_local_model(
        args.local,
        gui=args.gui,
        exit_on_reject=False,
        host=args.host,
        port=args.port,
    )
    if not result:
        print(f"Local model {args.local} is not verified.")
        print("Please verify all files in the model directory before proceeding.")


def _hf_verification(args):
    """Handle verification flow for a Hugging Face model based on parsed args."""
    repo_name = args.hf
    revision = args.revision
    print(f"Using repository: {repo_name} at revision: {revision}")

    result = verify_hf_model(
        repo_name,
        revision,
        gui=args.gui,
        exit_on_reject=False,
        host=args.host,
        port=args.port,
    )
    if not result:
        print(f"Repository {repo_name} at revision {revision} is not verified.")
        print("Please verify all remote files in the repository before proceeding.")
