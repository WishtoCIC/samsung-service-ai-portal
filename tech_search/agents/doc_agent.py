"""
DocAgent — PDF/텍스트 기술 문서 분석 에이전트
역할: PDF 업로드 → 텍스트 추출 → 구조화 → 검색 인덱스 등록
"""
import re
import json
import pdfplumber
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

DOCS_DIR   = Path(__file__).parent.parent / "docs"
DATA_DIR   = Path(__file__).parent.parent / "data"
INDEX_FILE = DATA_DIR / "doc_index.json"

PRODUCT_KEYWORDS = {
    "HAC": ["가정용", "가정용에어컨", "무풍", "벽걸이", "스탠드", "HAC"],
    "SRA": ["시스템에어컨", "시스템", "카세트", "덕트형", "SRA", "4way", "1way"],
    "CAC": ["상업용", "패키지", "DVM", "CAC", "중형냉방"],
}

SYMPTOM_KEYWORDS = ["냉방불량", "소음", "누수", "전원불량", "이상한냄새", "동작안됨",
                    "결빙", "진동", "알람", "error", "과부하", "누설", "충전불량"]

REPAIR_KEYWORDS  = ["부품교체", "가스충전", "청소", "세척", "전기수리", "점검",
                    "설정변경", "교체", "진공", "재충전", "재설치"]


class DocAgent:
    """PDF/TXT 문서 분석 에이전트"""

    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        DOCS_DIR.mkdir(exist_ok=True)
        self._load_index()

    def _load_index(self):
        if INDEX_FILE.exists():
            with INDEX_FILE.open(encoding="utf-8") as f:
                self.index: List[Dict] = json.load(f)
        else:
            self.index = []

    def _save_index(self):
        with INDEX_FILE.open("w", encoding="utf-8") as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    # ── 텍스트 추출 ──────────────────────────────────
    def extract_from_pdf(self, file_bytes: bytes, filename: str) -> str:
        """PDF 바이트에서 전체 텍스트 추출"""
        import io
        text_pages = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_pages.append(t)
        return "\n\n".join(text_pages)

    def extract_from_txt(self, file_bytes: bytes) -> str:
        """TXT/CSV 바이트에서 텍스트 추출"""
        for enc in ("utf-8", "euc-kr", "cp949"):
            try:
                return file_bytes.decode(enc)
            except UnicodeDecodeError:
                continue
        return file_bytes.decode("utf-8", errors="replace")

    # ── 구조화 추출 ──────────────────────────────────
    def analyze(self, text: str, filename: str) -> Dict:
        """텍스트에서 구조화 정보 자동 추출"""
        meta = {
            "filename": filename,
            "product_code": self._detect_product(text),
            "model_name":   self._extract_model(text),
            "release_date": self._extract_date(text),
            "symptoms":     self._extract_keywords(text, SYMPTOM_KEYWORDS),
            "repair_types": self._extract_keywords(text, REPAIR_KEYWORDS),
            "doc_no":       self._extract_doc_no(text),
            "title":        self._extract_title(text, filename),
            "summary":      self._make_summary(text),
            "char_count":   len(text),
        }
        return meta

    def _detect_product(self, text: str) -> str:
        text_u = text.upper()
        scores = {}
        for code, kws in PRODUCT_KEYWORDS.items():
            scores[code] = sum(text_u.count(kw.upper()) for kw in kws)
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "전체"

    def _extract_model(self, text: str) -> str:
        # 삼성 모델 패턴: 영숫자 조합 (예: AF17B6574WGN, DVM-S2-200)
        patterns = [
            r'모델[명\s:：]+([A-Z0-9\-]{5,20})',
            r'Model[:\s]+([A-Z0-9\-]{5,20})',
            r'\b([A-Z]{2,4}[0-9]{2,4}[A-Z0-9]{2,10})\b',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return "—"

    def _extract_date(self, text: str) -> str:
        patterns = [
            r'출시[일월년\s:：]+(\d{4}[./년\s]\d{1,2}[./월]?)',
            r'작성일[:\s：]+(\d{4}[-./]\d{1,2}[-./]\d{0,2})',
            r'(\d{4})[./년](\d{1,2})[./월]',
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(0).replace("작성일:", "").replace("출시일:", "").strip()
        return "—"

    def _extract_keywords(self, text: str, keywords: List[str]) -> List[str]:
        text_l = text.lower().replace(" ", "")
        found = [kw for kw in keywords if kw.lower().replace(" ", "") in text_l]
        return found[:6]

    def _extract_doc_no(self, text: str) -> str:
        m = re.search(r'문서번호[:\s：]+([A-Z0-9\-]+)', text)
        return m.group(1) if m else "—"

    def _extract_title(self, text: str, filename: str) -> str:
        for line in text.splitlines()[:8]:
            line = line.strip()
            if line.startswith("제목:"):
                return line.replace("제목:", "").strip()
            if len(line) > 8 and len(line) < 60 and not line.startswith("#"):
                return line
        return Path(filename).stem

    def _make_summary(self, text: str) -> str:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return " ".join(lines[:3])[:200] + "..."

    # ── 인덱스 등록 ──────────────────────────────────
    def register(self, text: str, meta: Dict) -> Dict:
        """분석 결과를 인덱스에 등록하고 docs 폴더에 저장"""
        doc_id = f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        safe_name = re.sub(r'[^\w가-힣\-]', '_', meta["filename"])
        txt_path = DOCS_DIR / f"{doc_id}_{safe_name}.txt"
        txt_path.write_text(text, encoding="utf-8")

        entry = {
            "id": doc_id,
            "path": str(txt_path),
            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            **meta,
        }
        self.index.append(entry)
        self._save_index()
        return entry

    def process_upload(self, file_bytes: bytes, filename: str) -> Dict:
        """업로드 파일 전체 처리 파이프라인"""
        # 1) 텍스트 추출
        ext = Path(filename).suffix.lower()
        if ext == ".pdf":
            text = self.extract_from_pdf(file_bytes, filename)
        else:
            text = self.extract_from_txt(file_bytes)

        if not text.strip():
            return {"error": "텍스트를 추출할 수 없습니다. 스캔 이미지 PDF는 지원되지 않습니다."}

        # 2) 구조화 분석
        meta = self.analyze(text, filename)

        # 3) 인덱스 등록
        entry = self.register(text, meta)
        return entry

    def get_stats(self) -> Dict:
        total = len(self.index)
        by_product = {}
        for d in self.index:
            pc = d.get("product_code", "전체")
            by_product[pc] = by_product.get(pc, 0) + 1
        return {"total": total, "by_product": by_product}
