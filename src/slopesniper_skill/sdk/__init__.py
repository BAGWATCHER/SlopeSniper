"""
SlopeSniper SDK - Jupiter and Rugcheck API Clients

Bundled SDK for Solana token operations:
- JupiterUltraClient: Swap quotes and execution
- JupiterDataClient: Price and token data
- RugCheckClient: Token safety analysis
"""

__version__ = "0.1.0"

from .jupiter_data_client import JupiterDataClient
from .jupiter_ultra_client import JupiterUltraClient
from .rugcheck_client import RugCheckClient
from .utils import Utils

__all__ = [
    "__version__",
    "JupiterUltraClient",
    "JupiterDataClient",
    "RugCheckClient",
    "Utils",
]
