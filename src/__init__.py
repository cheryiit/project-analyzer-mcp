"""
Project Analyzer MCP Server
A modular Python-based MCP server for comprehensive project analysis
"""

__version__ = "2.0.0"
__author__ = "Claude"
__description__ = "Enhanced Python-based MCP server for project analysis"

from .core.server import ProjectAnalyzerMCPServer
from .core.analyzer import ProjectAnalyzer
from .core.config import ProjectAnalyzerConfig

__all__ = [
    "ProjectAnalyzerMCPServer",
    "ProjectAnalyzer", 
    "ProjectAnalyzerConfig"
]