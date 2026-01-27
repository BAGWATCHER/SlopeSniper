"""
RugCheck API Client for token risk assessment.

Fetches token risk scores and reports from rugcheck.xyz API.
"""

from __future__ import annotations

from typing import Any

import aiohttp

from .utils import Utils


class RugCheckClient:
    """Client for the RugCheck API to assess token risk."""

    def __init__(self, timeout: int = 10) -> None:
        """
        Initialize RugCheck client.

        Args:
            timeout: Request timeout in seconds
        """
        self.logger = Utils.setup_logger("RugCheckClient")
        self.base_url = "https://api.rugcheck.xyz/v1"
        self.timeout = timeout

    async def get_report_summary(
        self, contract_address: str
    ) -> dict[str, Any] | None:
        """
        Fetch report summary from RugCheck API.

        Args:
            contract_address: Token contract address

        Returns:
            Summary dict with score and risk info, or None if error
        """
        try:
            summary_url = f"{self.base_url}/tokens/{contract_address}/report/summary"
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(summary_url) as response:
                    response.raise_for_status()
                    summary = await response.json()

                    self.logger.info(
                        f"[get_report_summary] Score: {summary.get('score')}, "
                        f"Risks: {len(summary.get('risks', []))}"
                    )

                    return summary

        except aiohttp.ClientError as e:
            self.logger.error(f"[get_report_summary] Failed: {e}")
            return None
        except Exception as e:
            self.logger.exception(f"[get_report_summary] Unexpected error: {e}")
            return None

    async def check_token(
        self, contract_address: str, max_score: int = 2000
    ) -> dict[str, Any]:
        """
        Check token and return risk assessment.

        Args:
            contract_address: Token contract address
            max_score: Maximum acceptable risk score (lower = safer)

        Returns:
            Dict with keys:
            - score: Risk score
            - summary: Summary report dict
            - risks: List of risk factors
            - is_safe: Boolean recommendation
            - reason: Human-readable reason
        """
        summary = await self.get_report_summary(contract_address)

        if not summary:
            return {
                "score": None,
                "summary": None,
                "risks": [],
                "is_safe": False,
                "reason": "Failed to fetch rugcheck report",
            }

        score = summary.get("score", 9999)
        risks = summary.get("risks", [])

        # Analyze risks
        critical_risks: list[str] = []
        for risk in risks:
            risk_level = risk.get("level", "")
            risk_name = risk.get("name", "")
            risk_description = risk.get("description", "")

            if risk_level in ["danger", "critical"]:
                critical_risks.append(f"{risk_name}: {risk_description}")

        # Determine if safe
        is_safe = True
        reason = "Token passed rugcheck"

        if score is None or score > max_score:
            is_safe = False
            reason = f"High risk score: {score} (max: {max_score})"
        elif len(critical_risks) > 0:
            is_safe = False
            reason = f"Critical risks found: {critical_risks[0]}"

        self.logger.info(
            f"[check_token] {contract_address[:8]}... - "
            f"Score: {score}, Risks: {len(risks)}, Safe: {is_safe}"
        )

        return {
            "score": score,
            "summary": summary,
            "risks": risks,
            "critical_risks": critical_risks,
            "is_safe": is_safe,
            "reason": reason,
        }
