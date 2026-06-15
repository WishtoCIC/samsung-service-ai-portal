"""
FeedbackAgent — 엔지니어 요청·피드백 에이전트
역할: 사진/동영상 포함 요청 접수 → 담당자 피드백 댓글 스레드 관리
"""
import json
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

DATA_DIR    = Path(__file__).parent.parent / "data"
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
REQ_FILE    = DATA_DIR / "requests.json"

STATUS_FLOW = ["접수완료", "검토중", "피드백완료", "처리중", "해결완료", "보류"]

CATEGORY_MAP = {
    "수리방법 문의":     "🔧",
    "부품코드 확인":     "🔩",
    "사양변경 이력":     "📋",
    "알람코드 해석":     "⚠️",
    "자료추가 요청":     "📄",
    "현장지원 요청":     "🚨",
    "기타":             "💬",
}


class FeedbackAgent:
    """요청 접수 및 피드백 스레드 관리 에이전트"""

    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        UPLOADS_DIR.mkdir(exist_ok=True)
        self._load()

    def _load(self):
        if REQ_FILE.exists():
            with REQ_FILE.open(encoding="utf-8") as f:
                self.requests: List[Dict] = json.load(f)
        else:
            self.requests = []

    def _save(self):
        with REQ_FILE.open("w", encoding="utf-8") as f:
            json.dump(self.requests, f, ensure_ascii=False, indent=2)

    # ── 요청 접수 ─────────────────────────────────────
    def create_request(
        self,
        name: str,
        region: str,
        product: str,
        category: str,
        priority: str,
        model: str,
        content: str,
        image_files: Optional[List] = None,
    ) -> Dict:
        req_id = f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        attachments = []

        if image_files:
            for img in image_files:
                att_path = UPLOADS_DIR / f"{req_id}_{img.name}"
                att_path.write_bytes(img.read())
                attachments.append({
                    "filename": img.name,
                    "path": str(att_path),
                    "type": "image" if img.name.lower().endswith(
                        ('.png', '.jpg', '.jpeg', '.gif', '.webp')) else "video",
                })

        req = {
            "id": req_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "name": name,
            "region": region,
            "product": product,
            "category": category,
            "priority": priority,
            "model": model or "—",
            "content": content,
            "status": "접수완료",
            "attachments": attachments,
            "feedback_thread": [],  # 댓글 스레드
            "history": [
                {"at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                 "action": "접수완료", "by": name}
            ],
        }
        self.requests.append(req)
        self._save()
        return req

    # ── 피드백 추가 ───────────────────────────────────
    def add_feedback(self, req_id: str, author: str, role: str, message: str) -> bool:
        req = self._find(req_id)
        if not req:
            return False
        comment = {
            "id": f"FB-{datetime.now().strftime('%H%M%S')}",
            "at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "author": author,
            "role": role,  # "엔지니어" or "담당자"
            "message": message,
        }
        req["feedback_thread"].append(comment)
        if role == "담당자" and req["status"] == "접수완료":
            req["status"] = "피드백완료"
        req["history"].append({
            "at": comment["at"], "action": f"피드백 추가 ({role})", "by": author
        })
        self._save()
        return True

    # ── 상태 변경 ─────────────────────────────────────
    def update_status(self, req_id: str, new_status: str, by: str = "담당자") -> bool:
        req = self._find(req_id)
        if not req or new_status not in STATUS_FLOW:
            return False
        req["status"] = new_status
        req["history"].append({
            "at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "action": f"상태변경 → {new_status}", "by": by
        })
        self._save()
        return True

    # ── 조회 헬퍼 ─────────────────────────────────────
    def _find(self, req_id: str) -> Optional[Dict]:
        return next((r for r in self.requests if r["id"] == req_id), None)

    def get_all(self, status_filter: str = "전체", product_filter: str = "전체") -> List[Dict]:
        result = self.requests
        if status_filter != "전체":
            result = [r for r in result if r["status"] == status_filter]
        if product_filter != "전체":
            result = [r for r in result if product_filter[:3] in r["product"]]
        return list(reversed(result))

    def get_stats(self) -> Dict:
        total = len(self.requests)
        by_status = {}
        by_product = {}
        urgent = 0
        for r in self.requests:
            s = r["status"]
            by_status[s] = by_status.get(s, 0) + 1
            p = r["product"][:3]
            by_product[p] = by_product.get(p, 0) + 1
            if "긴급" in r["priority"]:
                urgent += 1
        return {
            "total": total,
            "urgent": urgent,
            "by_status": by_status,
            "by_product": by_product,
            "unresolved": total - by_status.get("해결완료", 0),
        }

    def get_category_icon(self, category: str) -> str:
        return CATEGORY_MAP.get(category, "💬")
