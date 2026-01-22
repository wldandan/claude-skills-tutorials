"""Correlation analysis module."""

from typing import List, Dict, Any, Tuple
import numpy as np
from datetime import datetime
from scipy import stats


class CorrelationAnalyzer:
    """Analyze correlations between metrics."""

    def __init__(self):
        """Initialize correlation analyzer."""
        pass

    def calculate_pearson(
        self,
        series1: List[float],
        series2: List[float]
    ) -> Tuple[float, float]:
        """Calculate Pearson correlation coefficient.

        Args:
            series1: First time series
            series2: Second time series

        Returns:
            Tuple of (correlation coefficient, p-value)
        """
        if len(series1) != len(series2):
            raise ValueError("Series must have same length")

        if len(series1) < 2:
            return 0.0, 1.0

        correlation, p_value = stats.pearsonr(series1, series2)
        return correlation, p_value

    def find_correlations(
        self,
        metrics_data: Dict[str, List[float]],
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find correlated metric pairs.

        Args:
            metrics_data: Dictionary of metric name to values
            threshold: Correlation threshold (default: 0.7)

        Returns:
            List of correlation results
        """
        results = []
        metric_names = list(metrics_data.keys())

        for i in range(len(metric_names)):
            for j in range(i + 1, len(metric_names)):
                name1 = metric_names[i]
                name2 = metric_names[j]

                series1 = metrics_data[name1]
                series2 = metrics_data[name2]

                # Ensure same length
                min_len = min(len(series1), len(series2))
                series1 = series1[:min_len]
                series2 = series2[:min_len]

                if min_len < 2:
                    continue

                corr, p_value = self.calculate_pearson(series1, series2)

                if abs(corr) >= threshold:
                    results.append({
                        'metric1': name1,
                        'metric2': name2,
                        'correlation': corr,
                        'p_value': p_value,
                        'strength': self._get_correlation_strength(abs(corr)),
                    })

        # Sort by absolute correlation
        results.sort(key=lambda x: abs(x['correlation']), reverse=True)
        return results

    def _get_correlation_strength(self, abs_corr: float) -> str:
        """Get correlation strength label.

        Args:
            abs_corr: Absolute correlation value

        Returns:
            Strength label
        """
        if abs_corr >= 0.9:
            return 'very_strong'
        elif abs_corr >= 0.7:
            return 'strong'
        elif abs_corr >= 0.5:
            return 'moderate'
        elif abs_corr >= 0.3:
            return 'weak'
        else:
            return 'very_weak'

    def calculate_lag_correlation(
        self,
        series1: List[float],
        series2: List[float],
        max_lag: int = 10
    ) -> Dict[str, Any]:
        """Calculate lagged correlation.

        Args:
            series1: First time series
            series2: Second time series
            max_lag: Maximum lag to test

        Returns:
            Dictionary with best lag and correlation
        """
        if len(series1) < max_lag or len(series2) < max_lag:
            return {'lag': 0, 'correlation': 0.0}

        best_lag = 0
        best_corr = 0.0

        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                # series1 leads series2
                s1 = series1[:lag]
                s2 = series2[-lag:]
            elif lag > 0:
                # series2 leads series1
                s1 = series1[lag:]
                s2 = series2[:-lag]
            else:
                s1 = series1
                s2 = series2

            if len(s1) < 2:
                continue

            corr, _ = self.calculate_pearson(s1, s2)

            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag

        return {
            'lag': best_lag,
            'correlation': best_corr,
            'interpretation': self._interpret_lag(best_lag),
        }

    def _interpret_lag(self, lag: int) -> str:
        """Interpret lag value.

        Args:
            lag: Lag value

        Returns:
            Interpretation string
        """
        if lag < 0:
            return f"metric1 leads metric2 by {abs(lag)} steps"
        elif lag > 0:
            return f"metric2 leads metric1 by {lag} steps"
        else:
            return "no lag (simultaneous)"
