"""
기술정보 검색 엔진 — TF-IDF 기반 키워드 검색 + 컨텍스트 추출
(RAG 개념 적용: 검색 → 관련 청크 추출 → 답변 생성 흐름)
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


DOCS_DIR = Path(__file__).parent / "docs"


def load_documents() -> List[Dict]:
    """docs 폴더의 모든 txt 파일 로드"""
    docs = []
    for path in sorted(DOCS_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        meta = _parse_meta(text, path.stem)
        docs.append({
            "id": path.stem,
            "filename": path.name,
            "text": text,
            "meta": meta,
            "chunks": _chunk_text(text),
        })
    return docs


def _parse_meta(text: str, filename: str) -> Dict:
    """헤더에서 메타 정보 추출"""
    meta = {"title": filename, "product": "전체", "category": "기술문서", "doc_no": ""}
    for line in text.splitlines()[:10]:
        if line.startswith("제목:"):
            meta["title"] = line.replace("제목:", "").strip()
        elif line.startswith("제품군:"):
            meta["product"] = line.replace("제품군:", "").strip()
        elif line.startswith("카테고리:") or line.startswith("증상:"):
            tag = "카테고리:" if "카테고리:" in line else "증상:"
            meta["category"] = line.replace(tag, "").strip()
        elif line.startswith("문서번호:"):
            meta["doc_no"] = line.replace("문서번호:", "").strip()
    return meta


def _chunk_text(text: str, size: int = 400, overlap: int = 80) -> List[str]:
    """텍스트를 overlapping 청크로 분할"""
    lines = text.splitlines()
    chunks, buf = [], []
    buf_len = 0
    for line in lines:
        buf.append(line)
        buf_len += len(line) + 1
        if buf_len >= size:
            chunks.append("\n".join(buf))
            # overlap: 마지막 몇 줄 유지
            keep = []
            keep_len = 0
            for l in reversed(buf):
                keep_len += len(l) + 1
                keep.insert(0, l)
                if keep_len >= overlap:
                    break
            buf = keep
            buf_len = keep_len
    if buf:
        chunks.append("\n".join(buf))
    return chunks


def _tokenize(text: str) -> List[str]:
    """한국어 + 영문 토큰화 (공백·특수문자 분리)"""
    text = text.lower()
    tokens = re.findall(r'[가-힣a-z0-9]+', text)
    return tokens


def _score_chunk(query_tokens: List[str], chunk: str) -> float:
    """쿼리 토큰과 청크 간 매칭 점수 계산"""
    chunk_lower = chunk.lower()
    score = 0.0
    for tok in query_tokens:
        count = chunk_lower.count(tok)
        if count > 0:
            score += 1 + 0.3 * (count - 1)  # 반복 등장 시 보너스
    return score


def search(query: str, docs: List[Dict], top_k: int = 5) -> List[Dict]:
    """키워드 검색 → 관련 청크 반환"""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    results = []
    for doc in docs:
        doc_score = _score_chunk(query_tokens, doc["text"])
        if doc_score == 0:
            continue
        # 청크별 최고 점수
        best_chunk, best_score = "", 0.0
        for chunk in doc["chunks"]:
            cs = _score_chunk(query_tokens, chunk)
            if cs > best_score:
                best_score, best_chunk = cs, chunk
        if best_score > 0:
            results.append({
                "doc_id": doc["id"],
                "title": doc["meta"]["title"],
                "product": doc["meta"]["product"],
                "category": doc["meta"]["category"],
                "doc_no": doc["meta"]["doc_no"],
                "score": best_score,
                "chunk": best_chunk,
                "full_text": doc["text"],
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def highlight(text: str, query: str) -> str:
    """검색어를 **강조** 처리"""
    tokens = _tokenize(query)
    for tok in sorted(tokens, key=len, reverse=True):
        text = re.sub(f"({re.escape(tok)})", r"**\1**", text, flags=re.IGNORECASE)
    return text
