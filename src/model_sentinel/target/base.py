from model_sentinel.verify.verify import Verify


class TargetBase:
    """
    Base class for all target implementations.
    """

    def __init__(self):
        self.verify = Verify()
