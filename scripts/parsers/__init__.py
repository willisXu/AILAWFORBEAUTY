"""Parsers for converting raw regulation data to structured format

Version 2.0 - Multi-Table Model Architecture
"""

from .base_parser_v2 import BaseParserV2
from .eu_parser_v2 import EUParserV2
from .jp_parser_v2 import JPParserV2
from .cn_parser_v2 import CNParserV2
from .ca_parser_v2 import CAParserV2
from .asean_parser_v2 import ASEANParserV2

__all__ = [
    "BaseParserV2",
    "EUParserV2",
    "JPParserV2",
    "CNParserV2",
    "CAParserV2",
    "ASEANParserV2",
]
