"""
SlopeSniper SDK - Multi-source Solana Token Data

Bundled SDK for Solana token operations:
- JupiterUltraClient: Swap quotes and execution
- JupiterDataClient: Price and token data
- RugCheckClient: Token safety analysis
- DexScreenerClient: Trending tokens, new pairs, volume data
- PumpFunClient: Pump.fun graduated/new tokens
"""

__version__ = "0.1.0"

from .jupiter_ultra_client import JupiterUltraClient
from .jupiter_data_client import JupiterDataClient
from .rugcheck_client import RugCheckClient
from .dexscreener_client import DexScreenerClient
from .pumpfun_client import PumpFunClient
from .utils import Utils

__all__ = [
    "__version__",
    "JupiterUltraClient",
    "JupiterDataClient",
    "RugCheckClient",
    "DexScreenerClient",
    "PumpFunClient",
    "Utils",
]
