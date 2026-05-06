import statistics
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    is_valid: bool
    reason: str
    metrics: dict[str, Any]


class RetrievalValidator:
    """
    Validates reranker score distributions to detect weak/irrelevant retrievals.

    Cross-encoder scores (ms-marco-MiniLM-L-6-v2) are ranking logits, NOT
    calibrated probabilities. They can look like [5.8, 2.8, 1.5, -1.4, -3.0]
    even when nothing truly matches. This validator detects those patterns.
    """

    def __init__(
        self,
        min_top_score: float = 4.0,
        strong_threshold: float = 3.0,
        min_strong_count: int = 2,
        min_dropoff_ratio: float = 0.4,
        min_top_mean_gap: float = 1.5,
    ):
        self.min_top_score = min_top_score
        self.strong_threshold = strong_threshold
        self.min_strong_count = min_strong_count
        self.min_dropoff_ratio = min_dropoff_ratio
        self.min_top_mean_gap = min_top_mean_gap

    def validate(self, scores: list[float], top_k: int = 10) -> ValidationResult:
        """
        scores: ALL reranker scores for candidates (before slicing to top_k).
        top_k: how many the user asked for.
        """
        if not scores:
            return ValidationResult(
                is_valid=False,
                reason="No candidates scored.",
                metrics={},
            )

        if len(scores) < 2:
            return ValidationResult(
                is_valid=False,
                reason="Only one candidate available.",
                metrics={"count": 1},
            )

        sorted_scores = sorted(scores, reverse=True)
        top_score = sorted_scores[0]
        bottom_score = sorted_scores[-1]
        mean_score = statistics.mean(sorted_scores)
        median_score = statistics.median(sorted_scores)
        strong_count = sum(1 for s in sorted_scores if s >= self.strong_threshold)
        top_k_scores = sorted_scores[:top_k]
        avg_top_k = statistics.mean(top_k_scores)
        score_range = top_score - bottom_score
        dropoff_ratio = score_range / max(abs(mean_score), 0.1)
        top_mean_gap = top_score - mean_score
        std_dev = statistics.stdev(sorted_scores) if len(sorted_scores) > 1 else 0.0

        metrics = {
            "count": len(scores),
            "top_score": round(top_score, 4),
            "bottom_score": round(bottom_score, 4),
            "mean": round(mean_score, 4),
            "median": round(median_score, 4),
            "std_dev": round(std_dev, 4),
            "strong_count": strong_count,
            "avg_top_k": round(avg_top_k, 4),
            "dropoff_ratio": round(dropoff_ratio, 4),
            "top_mean_gap": round(top_mean_gap, 4),
        }

        failures = []

        # 1. Absolute threshold: the best score must be reasonably high
        if top_score < self.min_top_score:
            failures.append(
                f"top score {top_score:.2f} < min {self.min_top_score}"
            )

        # 2. Strong count: at least a few candidates look good
        if strong_count < self.min_strong_count:
            failures.append(
                f"only {strong_count} strong match(es) (need >= {self.min_strong_count})"
            )

        # 3. Dropoff ratio: scores must spread out (not all similar noise)
        if dropoff_ratio < self.min_dropoff_ratio:
            failures.append(
                f"dropoff ratio {dropoff_ratio:.2f} < min {self.min_dropoff_ratio} (scores too similar)"
            )

        # 4. Top-mean gap: the winner must stand out from the pack
        if top_mean_gap < self.min_top_mean_gap:
            failures.append(
                f"top-mean gap {top_mean_gap:.2f} < min {self.min_top_mean_gap} (no clear winner)"
            )

        if failures:
            return ValidationResult(
                is_valid=False,
                reason="; ".join(failures),
                metrics=metrics,
            )

        return ValidationResult(
            is_valid=True,
            reason="Score distribution looks healthy.",
            metrics=metrics,
        )
