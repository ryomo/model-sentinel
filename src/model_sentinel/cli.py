from model_sentinel import Verify, TargetHF, verify_hf_model


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Model Sentinel CLI")
    parser.add_argument("--delete", action="store_true", help="Delete the hash file")
    parser.add_argument(
        "--check-files-only", action="store_true", help="Only check remote files"
    )
    parser.add_argument(
        "--list-verified", action="store_true", help="List all verified hashes"
    )
    args = parser.parse_args()

    REPO_NAME = "ryomo/malicious-code-test"
    REVISION = "main"

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

    elif args.check_files_only:
        # Check remote files only without checking model hash
        verify = Verify()
        result = verify.check_remote_files(REPO_NAME, revision=REVISION)
        print(f"File check result: {result}")

    else:
        # Default behavior: check model hash then files
        print(f"Using repository: {REPO_NAME} at revision: {REVISION}")

        if not verify_hf_model(REPO_NAME, REVISION):
            print(f"Repository {REPO_NAME} at revision {REVISION} is not verified.")
            print("Please verify all remote files in the repository before proceeding.")
