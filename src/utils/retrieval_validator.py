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
    Validates reranker score distributions using relative/adaptive thresholds.
    Works regardless of whether scores are in [-10, 0] or [0, 10] range.
    """

    def __init__(
        self,
        # Gap between top score and the "cliff" must be this fraction of total range
        min_cliff_ratio: float = 0.3,
        # Top cluster must be clearly separated from the rest
        min_top_cluster_gap: float = 1.5,
        # At least this many candidates in the "top cluster"
        min_cluster_size: int = 1,
        # Top score must beat the mean by at least this many std devs
        min_zscore_top: float = 0.5,
    ):
        self.min_cliff_ratio = min_cliff_ratio
        self.min_top_cluster_gap = min_top_cluster_gap
        self.min_cluster_size = min_cluster_size
        self.min_zscore_top = min_zscore_top

    def _find_top_cluster(self, sorted_scores: list[float]) -> list[float]:
        """
        Find the top cluster by detecting the largest gap between consecutive scores.
        Everything before the biggest gap = top cluster.
        """
        if len(sorted_scores) < 2:
            return sorted_scores

        gaps = [
            (sorted_scores[i] - sorted_scores[i + 1], i)
            for i in range(len(sorted_scores) - 1)
        ]
        biggest_gap_idx = max(gaps, key=lambda x: x[0])[1]
        return sorted_scores[: biggest_gap_idx + 1]

    def validate(self, scores: list[float], top_k: int = 10) -> ValidationResult:
        if not scores:
            return ValidationResult(is_valid=False, reason="No candidates scored.", metrics={})

        if len(scores) < 2:
            return ValidationResult(is_valid=False, reason="Only one candidate.", metrics={"count": 1})

        sorted_scores = sorted(scores, reverse=True)
        top_score = sorted_scores[0]
        score_range = sorted_scores[0] - sorted_scores[-1]
        mean_score = statistics.mean(sorted_scores)
        std_dev = statistics.stdev(sorted_scores)

        top_cluster = self._find_top_cluster(sorted_scores)
        cluster_size = len(top_cluster)

        # Gap between the bottom of the top cluster and the next score
        cliff_gap = (
            top_cluster[-1] - sorted_scores[cluster_size]
            if cluster_size < len(sorted_scores)
            else score_range
        )
        cliff_ratio = cliff_gap / max(score_range, 1e-6)

        # Z-score of the top result
        top_zscore = (top_score - mean_score) / max(std_dev, 1e-6)

        metrics = {
            "count": len(scores),
            "top_score": round(top_score, 4),
            "score_range": round(score_range, 4),
            "mean": round(mean_score, 4),
            "std_dev": round(std_dev, 4),
            "top_cluster": [round(s, 4) for s in top_cluster],
            "cluster_size": cluster_size,
            "cliff_gap": round(cliff_gap, 4),
            "cliff_ratio": round(cliff_ratio, 4),
            "top_zscore": round(top_zscore, 4),
        }

        failures = []

        if cluster_size < self.min_cluster_size:
            failures.append(f"top cluster too small ({cluster_size})")

        if cliff_ratio < self.min_cliff_ratio:
            failures.append(
                f"cliff ratio {cliff_ratio:.2f} < {self.min_cliff_ratio} (no clear separation)"
            )

        if cliff_gap < self.min_top_cluster_gap:
            failures.append(
                f"cliff gap {cliff_gap:.2f} < {self.min_top_cluster_gap} (top cluster not distinct)"
            )

        if top_zscore < self.min_zscore_top:
            failures.append(
                f"top z-score {top_zscore:.2f} < {self.min_zscore_top} (top score not outstanding)"
            )

        if failures:
            return ValidationResult(is_valid=False, reason="; ".join(failures), metrics=metrics)

        return ValidationResult(is_valid=True, reason="Score distribution looks healthy.", metrics=metrics)