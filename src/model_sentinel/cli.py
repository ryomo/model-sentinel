from model_sentinel import Verify, verify_hf_model, verify_local_model, __version__


def main():
    import argparse

    DEFAULT_REVISION = "main"

    parser = argparse.ArgumentParser(description="Model Sentinel CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=f"model-sentinel {__version__}"
    )
    parser.add_argument("--delete", action="store_true", help="Delete the hash file")
    parser.add_argument(
        "--list-verified", action="store_true", help="List all verified hashes"
    )
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
    args = parser.parse_args()

    if args.gui:
        # Launch GUI interface
        try:
            from model_sentinel.gui import launch_verification_gui

            print("Starting Model Sentinel GUI...")
            if args.hf:
                launch_verification_gui(
                    repo_id=args.hf,
                    revision=args.revision,
                    host=args.host,
                    port=args.port
                )
            elif args.local:
                launch_verification_gui(
                    model_dir=args.local,
                    host=args.host,
                    port=args.port
                )
            else:
                launch_verification_gui(host=args.host, port=args.port)
        except ImportError:
            print("GUI functionality requires gradio. Install with:")
            print("pip install 'model-sentinel[gui]'")
            return

    elif args.delete:
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
        # Check if any model-related arguments are provided
        if args.local:
            # Verify local model
            print(f"Verifying local model: {args.local}")
            if not verify_local_model(args.local):
                print(f"Local model {args.local} is not verified.")
                print(
                    "Please verify all files in the model directory before proceeding."
                )
        elif args.hf:
            # Verify Hugging Face model
            repo_name = args.hf
            revision = args.revision
            print(f"Using repository: {repo_name} at revision: {revision}")

            if not verify_hf_model(repo_name, revision):
                print(f"Repository {repo_name} at revision {revision} is not verified.")
                print(
                    "Please verify all remote files in the repository before proceeding."
                )
        else:
            # No model specified - show help
            parser.print_help()
