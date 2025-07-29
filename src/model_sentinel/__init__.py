from .target.hf import TargetHF, verify_hf_model
from .target.local import TargetLocal, verify_local_model
from .verify.verify import Verify

__version__ = "0.2.0"

# GUI functionality (optional dependency)
try:
    from .gui import launch_verification_gui as launch_gui

    __all__ = [
        "TargetHF",
        "verify_hf_model",
        "TargetLocal",
        "verify_local_model",
        "Verify",
        "launch_gui",
    ]
except ImportError:
    # Gradio not installed
    __all__ = [
        "TargetHF",
        "verify_hf_model",
        "TargetLocal",
        "verify_local_model",
        "Verify",
    ]
