"""
Lightweight shim for web3 to speed tests and avoid heavy optional deps during pytest run.
This is intentionally minimal and only intended for test runs where full blockchain features are mocked.
"""

class Web3:
    def __init__(self, *args, **kwargs):
        pass

__all__ = ["Web3"]
