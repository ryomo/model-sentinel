from model_sentinel import Verify, verify_hf_model, verify_local_model


def main():
    import argparse

    # Default values for backward compatibility
    DEFAULT_REPO_NAME = "ryomo/malicious-code-test"
    DEFAULT_REVISION = "main"

    parser = argparse.ArgumentParser(description="Model Sentinel CLI")
    parser.add_argument("--delete", action="store_true", help="Delete the hash file")
    parser.add_argument(
        "--list-verified", action="store_true", help="List all verified hashes"
    )
    parser.add_argument("--gui", action="store_true", help="Launch GUI interface")
    parser.add_argument(
        "--repo",
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
            if args.repo:
                launch_verification_gui(repo_id=args.repo, revision=args.revision)
            elif args.local:
                launch_verification_gui(model_dir=args.local)
            else:
                launch_verification_gui()
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
        # Default behavior: check model hash then files
        if args.local:
            # Verify local model
            print(f"Verifying local model: {args.local}")
            if not verify_local_model(args.local):
                print(f"Local model {args.local} is not verified.")
                print(
                    "Please verify all files in the model directory before proceeding."
                )
        else:
            # Verify Hugging Face model
            repo_name = args.repo or DEFAULT_REPO_NAME
            revision = args.revision
            print(f"Using repository: {repo_name} at revision: {revision}")

            if not verify_hf_model(repo_name, revision):
                print(f"Repository {repo_name} at revision {revision} is not verified.")
                print(
                    "Please verify all remote files in the repository before proceeding."
                )
