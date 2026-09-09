"""AI platform foundation and Phase 14 user-facing features.

This package keeps the execution boundary strict:
- authenticated backend user context only
- canonical financial tools as the source of truth
- payload validation before provider execution
- no direct provider or database bypass from feature code
"""

from app.ai.categorization import CategoryClassification, categorize_transaction
from app.ai.chat import ConversationMessage, ConversationStore
from app.ai.nl_query import NLQueryResult, execute_nl_query
from app.ai.receipt import ReceiptDraft, ReceiptExtractionResult, extract_receipt
from app.ai.recommendations import explain_recommendation
from app.ai.spending_analysis import SpendingAnalysisResult, analyze_spending

__all__ = [
    "CategoryClassification",
    "ConversationMessage",
    "ConversationStore",
    "NLQueryResult",
    "ReceiptDraft",
    "ReceiptExtractionResult",
    "SpendingAnalysisResult",
    "analyze_spending",
    "categorize_transaction",
    "explain_recommendation",
    "execute_nl_query",
    "extract_receipt",
]
