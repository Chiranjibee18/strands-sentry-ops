"""
Reusable Decision Pattern: #context-memory
------------------------------------------
Pattern Name: Decider 2B Calibrated Context & Memory Relevance Scorer
Tag: #context-memory, #strands-decider-2b

Problem:
RAG and agent memory injection often dump dozens of noisy log snippets, runbook pages,
and past conversation turns into the LLM prompt. This bloats input tokens, slows down
TTFT, increases cost, and causes the LLM to get lost in the middle (context distraction).

Solution:
Strands Decider 2B scores each candidate memory/context chunk on an ordered scale
(e.g., [irrelevant, low, medium, highly_relevant]) in ~115ms. Only chunks scoring
above the calibrated relevance threshold are injected into Amazon Bedrock prompt context.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from .client import StrandsDeciderClient, ScoreQuestion


class ContextChunk(BaseModel):
    chunk_id: str
    source: str
    text: str
    metadata: Optional[Dict[str, str]] = None


class ScoredContextChunk(BaseModel):
    chunk: ContextChunk
    relevance_label: str
    score_value: float
    confidence: float
    is_injected: bool
    latency_ms: float


class DeciderContextScorer:
    """
    Sub-115ms Context and Memory Relevance Scorer powered by Strands Decider 2B.
    """

    SCALE = ["irrelevant", "low", "medium", "highly_relevant"]

    def __init__(
        self,
        client: Optional[StrandsDeciderClient] = None,
        min_score_threshold: float = 2.0,  # 'medium' or higher
    ):
        self.client = client or StrandsDeciderClient()
        self.min_score_threshold = min_score_threshold

    def score_chunks(self, user_query: str, chunks: List[ContextChunk]) -> List[ScoredContextChunk]:
        """
        Scores multiple context chunks in parallel/batched single forward passes.
        """
        results = []
        for chunk in chunks:
            state = f"Active User Query: {user_query}\nContext Candidate [{chunk.source}]: {chunk.text}"
            questions = {
                "relevance": ScoreQuestion(
                    type="score",
                    instructions="Rate the factual relevance of this context candidate to answering the user query.",
                    options=self.SCALE,
                )
            }
            decision = self.client.ask(state=state, questions=questions)
            ans = decision.answers.get("relevance")
            score_val = ans.score_value if (ans and ans.score_value is not None) else 0.0
            label = str(ans.prediction) if ans else "irrelevant"
            conf = ans.confidence if ans else 0.5
            is_injected = score_val >= self.min_score_threshold

            results.append(
                ScoredContextChunk(
                    chunk=chunk,
                    relevance_label=label,
                    score_value=score_val,
                    confidence=conf,
                    is_injected=is_injected,
                    latency_ms=decision.latency_ms,
                )
            )
        return results
