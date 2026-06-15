"""
StatusAgent — 진행사항 관리 에이전트
역할: 요청 라이프사이클 추적, 우선순위 관리, 통계 리포트, SLA 경보
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from .feedback_agent import FeedbackAgent, STATUS_FLOW

SLA_HOURS = {
    "긴급 (당일 처리 요청)": 8,
    "일반": 48,
}

STATUS_COLOR = {
    "접수완료":   ("#e8ecff", "#1428A0"),
    "검토중":     ("#fff8e1", "#f57c00"),
    "피드백완료": ("#e8f5e9", "#2e7d32"),
    "처리중":     ("#e3f2fd", "#1565c0"),
    "해결완료":   ("#f1f8e9", "#558b2f"),
    "보류":       ("#fce4ec", "#c62828"),
}

STATUS_NEXT = {
    "접수완료":   "검토중",
    "검토중":     "피드백완료",
    "피드백완료": "처리중",
    "처리중":     "해결완료",
    "해결완료":   None,
    "보류":       "검토중",
}


class StatusAgent:
    """진행 현황 관리 에이전트"""

    def __init__(self, feedback_agent: FeedbackAgent):
        self.fa = feedback_agent

    # ── SLA 초과 여부 ─────────────────────────────────
    def check_sla(self, req: Dict) -> Tuple[bool, float]:
        """SLA 초과 여부와 경과 시간(h) 반환"""
        limit_h = SLA_HOURS.get(req["priority"], 48)
        created = datetime.strptime(req["created_at"], "%Y-%m-%d %H:%M")
        elapsed = (datetime.now() - created).total_seconds() / 3600
        return elapsed > limit_h, round(elapsed, 1)

    # ── 상태 배지 스타일 ──────────────────────────────
    def status_style(self, status: str) -> Tuple[str, str]:
        return STATUS_COLOR.get(status, ("#f0f0f0", "#666"))

    # ── 다음 상태 ────────────────────────────────────
    def next_status(self, current: str) -> str | None:
        return STATUS_NEXT.get(current)

    # ── 긴급 요청 목록 ───────────────────────────────
    def get_urgent_list(self) -> List[Dict]:
        result = []
        for req in self.fa.requests:
            if req["status"] == "해결완료":
                continue
            over, elapsed = self.check_sla(req)
            if "긴급" in req["priority"] or over:
                result.append({**req, "elapsed_h": elapsed, "sla_over": over})
        result.sort(key=lambda x: (-x["sla_over"], x["created_at"]))
        return result

    # ── 전체 통계 리포트 ────────────────────────────
    def build_report(self) -> Dict:
        reqs = self.fa.requests
        if not reqs:
            return {
                "total": 0, "resolved": 0, "resolution_rate": 0,
                "avg_resolve_h": 0, "sla_breach": 0, "unresolved": 0,
                "by_status": {}, "by_product": {}, "by_category": {},
                "weekly_trend": [],
            }

        resolved = [r for r in reqs if r["status"] == "해결완료"]
        sla_breach = sum(1 for r in reqs
                         if r["status"] != "해결완료" and self.check_sla(r)[0])

        # 평균 해결 시간
        resolve_times = []
        for r in resolved:
            h = r.get("history", [])
            start = h[0]["at"] if h else r["created_at"]
            end   = h[-1]["at"] if len(h) > 1 else r["created_at"]
            try:
                dt = (datetime.strptime(end, "%Y-%m-%d %H:%M")
                      - datetime.strptime(start, "%Y-%m-%d %H:%M"))
                resolve_times.append(dt.total_seconds() / 3600)
            except Exception:
                pass
        avg_resolve_h = round(sum(resolve_times) / len(resolve_times), 1) if resolve_times else 0

        # 상태별
        by_status: Dict[str, int] = {}
        by_product: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        for r in reqs:
            by_status[r["status"]]     = by_status.get(r["status"], 0) + 1
            pc = r["product"][:3]
            by_product[pc]             = by_product.get(pc, 0) + 1
            by_category[r["category"]] = by_category.get(r["category"], 0) + 1

        # 주간 트렌드 (최근 7일)
        weekly: Dict[str, int] = {}
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%m/%d")
            weekly[d] = 0
        for r in reqs:
            d = r["created_at"][:7].replace("-", "/")[3:]  # MM/DD
            day_key = r["created_at"][5:10].replace("-", "/")
            if day_key in weekly:
                weekly[day_key] += 1

        return {
            "total": len(reqs),
            "resolved": len(resolved),
            "resolution_rate": round(len(resolved) / len(reqs) * 100, 1) if reqs else 0,
            "avg_resolve_h": avg_resolve_h,
            "sla_breach": sla_breach,
            "by_status": by_status,
            "by_product": by_product,
            "by_category": by_category,
            "weekly_trend": list(weekly.items()),
        }
