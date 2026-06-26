"""
YD Lab 피부·두피 분석 앱 (특허 출원 중)
설치: pip install streamlit anthropic pillow requests pandas gspread google-auth
실행: streamlit run ydlab_skin_analyzer.py
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import anthropic
import base64
import json
import re
import requests
import csv
import random
import string
from datetime import datetime
from pathlib import Path
from PIL import Image
import io

st.set_page_config(
    page_title="YD Lab 피부·두피 분석",
    page_icon="🔬",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.hero {
    background: linear-gradient(135deg, #0f3460 0%, #1a5276 100%);
    color: white; border-radius: 16px; padding: 2rem 1.8rem 1.6rem;
    margin-bottom: 1.4rem;
}
.hero-label { font-size:0.7rem; letter-spacing:0.18em; text-transform:uppercase;
              opacity:0.55; margin-bottom:0.5rem; font-family:'DM Mono',monospace; }
.hero h1 { font-size:1.55rem; font-weight:700; margin-bottom:0.4rem; }
.hero p  { font-size:0.82rem; opacity:0.65; line-height:1.7; }
.card { background:white; border-radius:12px; padding:1.4rem;
        margin-bottom:1rem; border:1px solid #e4e8ee;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.card-label { font-size:0.68rem; letter-spacing:0.14em; text-transform:uppercase;
              color:#0f3460; font-weight:700; font-family:'DM Mono',monospace;
              margin-bottom:1rem; padding-bottom:0.6rem; border-bottom:1.5px solid #e4e8ee; }
.chip { display:inline-flex; align-items:center; gap:0.3rem;
        padding:0.32rem 0.75rem; border-radius:20px; font-size:0.78rem;
        font-weight:500; font-family:'DM Mono',monospace; margin:0.2rem; }
.chip-good { background:#e8f5e9; color:#2e7d32; }
.chip-mid  { background:#e8f4fd; color:#1565c0; }
.chip-warn { background:#fff3e0; color:#e65100; }
.chip-bad  { background:#fce4ec; color:#c62828; }
.chip-neu  { background:#f1f3f4; color:#5f6368; }
.score-box { text-align:center; padding:0.8rem 0.5rem; border-radius:10px;
             background:#f8f9fa; border:1px solid #e4e8ee; }
.score-num { font-size:2rem; font-weight:700; font-family:'DM Mono',monospace; line-height:1; }
.score-lbl { font-size:0.72rem; color:#888; margin-top:0.3rem; }
.result-text { font-size:0.84rem; color:#444; line-height:1.7; }
.ingredient-chip { display:inline-block; background:#eef2ff; color:#3730a3;
                   border-radius:6px; padding:0.25rem 0.65rem; font-size:0.78rem;
                   margin:0.2rem; font-weight:500; }
.scalp-ingredient-chip { display:inline-block; background:#f0faf4; color:#2e7d32;
                   border-radius:6px; padding:0.25rem 0.65rem; font-size:0.78rem;
                   margin:0.2rem; font-weight:500; }
.consent-box { background:#f7f8fa; border-left:3px solid #0f3460;
               border-radius:0 8px 8px 0; padding:0.9rem 1rem;
               font-size:0.78rem; color:#555; line-height:1.75; }
.guide-body { background:#f0f4fa; border-radius:8px; padding:1rem;
              font-size:0.81rem; line-height:1.8; }
.gstep { display:flex; align-items:flex-start; gap:0.6rem; margin-bottom:0.35rem; }
.gnum  { background:#0f3460; color:white; border-radius:50%;
         width:20px; height:20px; min-width:20px;
         display:inline-flex; align-items:center; justify-content:center;
         font-size:0.7rem; font-weight:700; }
.patent-banner { background:#e8f4fd; border:1px solid #1565c0; border-radius:8px;
                 padding:0.6rem 1rem; font-size:0.78rem; color:#1565c0;
                 margin-bottom:1rem; text-align:center; font-weight:600; }
.medical-disclaimer { background:#fdecea; border:1px solid #c62828; border-radius:8px;
                 padding:0.6rem 1rem; font-size:0.78rem; color:#c62828;
                 margin-bottom:1rem; text-align:center; font-weight:600; }
.scalp-card { background:#f0faf4; border:1px solid #a5d6a7; border-radius:12px;
              padding:1.2rem; margin-bottom:1rem; }
.priority-item { display:flex; align-items:center; gap:0.8rem; padding:0.6rem 0;
                 border-bottom:1px solid #f0f0f0; }
.priority-num { background:#0f3460; color:white; border-radius:50%;
                width:22px; height:22px; min-width:22px;
                display:inline-flex; align-items:center; justify-content:center;
                font-size:0.72rem; font-weight:700; }
.priority-label { font-weight:600; flex:1; font-size:0.85rem; }
.priority-score { font-weight:700; font-family:'DM Mono',monospace; font-size:0.85rem; }
.priority-msg { font-size:0.78rem; color:#888; }
.air-real { background:#e8f5e9; border:1px solid #a5d6a7; border-radius:8px;
            padding:0.5rem 1rem; font-size:0.78rem; color:#2e7d32;
            margin-bottom:0.8rem; font-weight:600; }
.air-mock { background:#fff3e0; border:1px solid #ffcc80; border-radius:8px;
            padding:0.5rem 1rem; font-size:0.78rem; color:#e65100;
            margin-bottom:0.8rem; font-weight:600; }
.mixing-card { background: linear-gradient(135deg, #f0faf4, #e8f4fd);
               border: 1px solid #a5d6a7; border-radius: 12px;
               padding: 1.4rem; margin-bottom: 1rem; }
.mixing-row { display:flex; align-items:center; gap:0.8rem; padding:0.5rem 0;
              border-bottom:1px solid rgba(0,0,0,0.06); }
.mixing-ing { font-weight:600; flex:1; font-size:0.85rem; color:#0f3460; }
.mixing-pct { font-weight:700; font-family:'DM Mono',monospace;
              font-size:0.9rem; color:#2e7d32; min-width:50px; }
.mixing-ml  { font-size:0.8rem; color:#888; min-width:50px; }
.mixing-bar-wrap { flex:2; background:#e4e8ee; border-radius:4px; height:8px; }
.mixing-bar { height:8px; border-radius:4px;
              background: linear-gradient(90deg, #2e7d32, #4CAF50); }
.scalp-mixing-bar { height:8px; border-radius:4px;
              background: linear-gradient(90deg, #1565c0, #42a5f5); }
.step-badge { display:inline-flex; align-items:center; justify-content:center;
              width:24px; height:24px; border-radius:50%;
              background:#0f3460; color:white; font-size:0.72rem;
              font-weight:700; margin-right:0.5rem; flex-shrink:0; }
.coupang-btn { display:inline-block; background:#ff6b35; color:white;
               padding:0.3rem 0.8rem; border-radius:6px; font-size:0.75rem;
               font-weight:600; text-decoration:none; margin-left:0.5rem; }
.partners-notice { background:#fff8f0; border:1px solid #ffcc80; border-radius:8px;
                   padding:0.6rem 1rem; font-size:0.72rem; color:#e65100;
                   margin-top:0.8rem; line-height:1.6; }
.mode-card { border-radius:16px; padding:2rem; text-align:center; cursor:pointer;
             transition: all 0.2s; border:3px solid transparent; }
.mode-card-skin { background: linear-gradient(135deg, #e8f4fd, #f0f7ff);
                  border-color: #1565c0; }
.mode-card-scalp { background: linear-gradient(135deg, #f0faf4, #e8f5e9);
                   border-color: #2e7d32; }
.mode-title { font-size:1.1rem; font-weight:700; margin:0.8rem 0 0.4rem; }
.mode-desc  { font-size:0.82rem; color:#666; line-height:1.6; }
.mode-tags  { display:flex; flex-wrap:wrap; gap:0.3rem;
              justify-content:center; margin-top:0.8rem; }
.mode-tag   { font-size:0.72rem; padding:0.2rem 0.6rem; border-radius:12px;
              background:rgba(0,0,0,0.06); color:#444; }
</style>
""", unsafe_allow_html=True)

# ── 상수 ──────────────────────────────────────────────
PM25_ALERT_THRESHOLD       = 35
CEEI_ANTIOXIDANT_THRESHOLD = 150

REGION_PM25_AVG = {
    "인천 (중구)":      24.2,
    "서구 (청라·검단)": 23.5,
    "부평구":           22.8,
    "계양구":           22.1,
    "연수구":           21.9,
    "남동구":           23.0,
    "안산":             25.3,
    "시흥":             24.0,
    "서울":             22.0,
    "기타":             22.0,
}

RESIDENCE_YEAR_MAP = {
    "선택": 0, "1년 미만": 0, "1~2년": 1,
    "3~5년": 4, "5~10년": 7, "10년 이상": 12
}

SKIN_BODY_PARTS  = ["이마", "눈가", "볼", "코", "턱", "입가", "목", "손등"]
SCALP_BODY_PARTS = ["두피 (정수리)", "두피 (측두부)", "두피 (후두부)"]

STATION_CANDIDATES = {
    "인천 (중구)":      ["신흥", "중구", "항동"],
    "서구 (청라·검단)": ["청라", "서구", "검단"],
    "부평구":           ["부평", "갈산", "산곡"],
    "계양구":           ["계산", "계양", "효성"],
    "연수구":           ["연수", "송도", "동춘", "옥련"],
    "남동구":           ["구월", "남동", "논현", "구월동"],
    "안산":             ["본오동", "고잔동", "부곡동1", "선부동"],
    "시흥":             ["정왕동", "대야동", "배곧동", "목감동"],
    "서울":             ["중구", "종로구"],
    "기타":             ["중구"],
}

# ── 쿠팡 파트너스 링크 ────────────────────────────────
COUPANG_LINKS = {
    # 피부 전용
    "히알루론산":       {"url": "https://link.coupang.com/a/eTyrjnNNN6", "name": "히알루론산 원액"},
    "세라마이드":       {"url": "https://link.coupang.com/a/eTyBwMM8l2", "name": "세라마이드 원액"},
    "나이아신아마이드": {"url": "https://link.coupang.com/a/eTyFrMsrAa", "name": "나이아신아마이드 원액"},
    "레티놀":           {"url": "https://link.coupang.com/a/eTyKZaEF5g", "name": "레티놀 원액"},
    "비타민C":          {"url": "https://link.coupang.com/a/eTyNlOaXbE", "name": "비타민C 원액"},
    "비타민C 유도체":   {"url": "https://link.coupang.com/a/eTyNlOaXbE", "name": "비타민C 원액"},
    "펩타이드":         {"url": "https://link.coupang.com/a/eTyORAWtK8", "name": "펩타이드 원액"},
    "판테놀":           {"url": "https://link.coupang.com/a/eTyRoPRJ6W", "name": "판테놀 원액"},
    "아데노신":         {"url": "https://link.coupang.com/a/eTySFtlt0K", "name": "아데노신 원액"},
    # 두피 전용
    "징크피리치온":     {"url": "https://link.coupang.com/a/eUnNCpma4G", "name": "징크피리치온 원액"},
    "살리실산":         {"url": "https://link.coupang.com/a/eUnRNCfwpo", "name": "살리실산 원액"},
    "바이오틴":         {"url": "https://link.coupang.com/a/eUnT1cHfSm", "name": "바이오틴 원액"},
    "판테놀 (두피용)":  {"url": "https://link.coupang.com/a/eUnVWdetMW", "name": "판테놀 원액(두피용)"},
}

COUPANG_DISCLAIMER = (
    "※ 이 페이지의 일부 구매 링크는 쿠팡 파트너스 활동의 일환으로, "
    "구매 시 일정 수수료가 YD Lab에 제공될 수 있습니다. "
    "이는 구매자에게 추가 비용을 발생시키지 않습니다."
)

# ── AI 분석 프롬프트 ──────────────────────────────────
SKIN_ANALYSIS_PROMPT = """
당신은 피부과학 전문가입니다. 업로드된 피부 현미경(클로즈업) 사진을 분석하여
아래 JSON 형식으로만 응답하세요. JSON 외 다른 텍스트는 절대 포함하지 마세요.

{
  "wrinkle_score": 0~100,
  "pore_score": 0~100,
  "texture_score": 0~100,
  "tone_score": 0~100,
  "moisture_score": 0~100,
  "overall_score": 0~100,
  "skin_type": "건성|지성|복합성|중성|민감성",
  "wrinkle_comment": "주름 상태 한 줄 설명 (30자 이내)",
  "pore_comment": "모공 상태 한 줄 설명 (30자 이내)",
  "texture_comment": "피부결 상태 한 줄 설명 (30자 이내)",
  "tone_comment": "피부톤 상태 한 줄 설명 (30자 이내)",
  "moisture_comment": "수분 상태 한 줄 설명 (30자 이내)",
  "summary": "전반적 피부 상태 종합 설명 (100자 이내)",
  "key_concerns": ["주요 고민 1", "주요 고민 2"],
  "recommended_ingredients": ["성분1", "성분2", "성분3", "성분4"],
  "care_advice": "생활 관리 조언 (80자 이내)"
}
점수 기준: 높을수록 좋음 (100=최상, 0=매우불량)
사진이 불명확해도 최대한 추정하여 응답하세요.
"""

SCALP_ANALYSIS_PROMPT = """
당신은 두피·모발 전문가입니다. 업로드된 두피 현미경(클로즈업) 사진을 분석하여
아래 JSON 형식으로만 응답하세요. JSON 외 다른 텍스트는 절대 포함하지 마세요.

{
  "overall_score": 0~100,
  "scalp_type": "지성|건성|민감성|정상|복합성",
  "keratin_score": 0~100,
  "pore_score": 0~100,
  "hair_thickness_score": 0~100,
  "scalp_color_score": 0~100,
  "moisture_balance_score": 0~100,
  "hair_damage_score": 0~100,
  "hair_loss_risk_score": 0~100,
  "keratin_comment": "각질 상태 한 줄 설명 (30자 이내)",
  "pore_comment": "모공·피지 상태 한 줄 설명 (30자 이내)",
  "hair_thickness_comment": "모발 굵기·밀도 한 줄 설명 (30자 이내)",
  "scalp_color_comment": "두피 색상·염증 상태 한 줄 설명 (30자 이내)",
  "moisture_balance_comment": "두피 수분·유분 상태 한 줄 설명 (30자 이내)",
  "hair_damage_comment": "모발 손상도 한 줄 설명 (30자 이내)",
  "hair_loss_risk_comment": "탈모 진행도 한 줄 설명 (30자 이내)",
  "summary": "전반적 두피·모발 상태 종합 설명 (100자 이내)",
  "key_concerns": ["주요 고민 1", "주요 고민 2"],
  "recommended_ingredients": ["성분1", "성분2", "성분3", "성분4"],
  "care_advice": "두피·모발 생활 관리 조언 (80자 이내)"
}

점수 기준: 높을수록 좋음 (100=최상, 0=매우불량)
각 지표 설명:
  keratin_score           = 각질 없을수록 높음
  pore_score              = 모공 깨끗·피지 적을수록 높음
  hair_thickness_score    = 모발 굵고 풍성할수록 높음
  scalp_color_score       = 정상(흰색·살색)일수록 높음, 홍조·염증일수록 낮음
  moisture_balance_score  = 수분·유분 균형 좋을수록 높음
  hair_damage_score       = 큐티클 손상 없을수록 높음
  hair_loss_risk_score    = 탈모 위험 낮을수록 높음 (참고용)
사진이 불명확해도 최대한 추정하여 응답하세요.
"""

# ── 헬퍼 함수 ─────────────────────────────────────────
def img_to_b64(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode()

def pm25_chip(v):
    if v is None:
        return "<span class='chip chip-neu'>PM2.5 -</span>"
    v = int(v)
    if v <= 15:  return f"<span class='chip chip-good'>PM2.5 좋음 {v}㎍/m³</span>"
    if v <= 35:  return f"<span class='chip chip-mid'>PM2.5 보통 {v}㎍/m³</span>"
    if v <= 75:  return f"<span class='chip chip-warn'>PM2.5 나쁨 {v}㎍/m³</span>"
    return f"<span class='chip chip-bad'>PM2.5 매우나쁨 {v}㎍/m³</span>"

def score_color(s):
    if s >= 70: return "#2e7d32"
    if s >= 40: return "#e65100"
    return "#c62828"

def get_concentration(ingredient, skin_type):
    is_sensitive = skin_type in ["민감성", "건성"]
    ING_DATA = {
        "히알루론산":      ("1~2%" if not is_sensitive else "0.5~1%",    "저·고분자 혼합 권장"),
        "세라마이드":      ("1~3%" if not is_sensitive else "0.5~1%",    "NP·AP·EOP 3종 혼합"),
        "나이아신아마이드":("5~10%" if not is_sensitive else "2~5%",     "10% 초과 시 자극 가능"),
        "레티놀":          ("0.1~0.3%" if not is_sensitive else "0.05%", "야간 전용·서서히 농도↑"),
        "비타민C":         ("10~15%" if not is_sensitive else "5~10%",   "pH 3.5 이하 유지"),
        "비타민C 유도체":  ("3~5%",   "아스코빌글루코사이드"),
        "펩타이드":        ("2~5%" if not is_sensitive else "1~3%",      "아세틸헥사펩타이드-3"),
        "판테놀":          ("1~5%" if not is_sensitive else "1~2%",      "Pro-비타민B5"),
        "AHA":             ("5~10%",  "pH 3.5~4.0·주 2~3회"),
        "BHA":             ("0.5~2%", "지성·복합성 권장"),
        "아데노신":        ("0.04%",  "기능성 화장품 기준"),
        "EGF":             ("0.0001~0.001%", "냉장 보관 필요"),
        "징크피리치온":    ("0.5~1%", "두피 항균·비듬 억제"),
        "살리실산":        ("0.5~2%", "두피 각질 용해"),
        "바이오틴":        ("0.01~0.1%", "모발 강화·성장"),
        "판테놀 (두피용)": ("2~5%",   "두피 진정·보습"),
    }
    d = ING_DATA.get(ingredient)
    return d if d else ("공방 재량", "")

def get_pollution_alert(pm25, ceei):
    if isinstance(pm25, (int, float)) and float(pm25) > PM25_ALERT_THRESHOLD:
        return "⚠️ 오늘 PM2.5 나쁨 — 항산화 성분(비타민C·나이아신아마이드) 강화 권장"
    elif ceei >= CEEI_ANTIOXIDANT_THRESHOLD:
        return "⚠️ 장기 오염 누적 노출 — 피부 광노화 대응 성분(레티놀·펩타이드) 권장"
    return ""

def calc_ceei(pm25_avg, residence_years):
    ceei = round(pm25_avg * residence_years, 1)
    if ceei < 50:
        return (ceei, "낮음",
                f"<span class='chip chip-good'>CEEI {ceei} [낮음]</span>",
                "환경 노출 영향 낮음 — 기본 보습·자외선 차단 유지")
    elif ceei < 150:
        return (ceei, "보통",
                f"<span class='chip chip-mid'>CEEI {ceei} [보통]</span>",
                "중간 수준 환경 노출 — 항산화 성분 정기적 사용 권장")
    elif ceei < 300:
        return (ceei, "높음",
                f"<span class='chip chip-warn'>CEEI {ceei} [높음]</span>",
                "높은 환경 노출 누적 — 항산화·장벽강화 집중 케어 필요")
    else:
        return (ceei, "매우높음",
                f"<span class='chip chip-bad'>CEEI {ceei} [매우높음]</span>",
                "매우 높은 누적 노출 — 피부과 상담 및 기능성 화장품 집중 케어 권장")

def fetch_air(region):
    key = st.secrets.get("AIRKOREA_API_KEY", "")
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
    candidates = STATION_CANDIDATES.get(region, ["중구"])
    if key:
        for station in candidates:
            try:
                params = dict(serviceKey=key, stationName=station,
                              dataTerm="DAILY", pageNo=1, numOfRows=1,
                              returnType="json", ver="1.3")
                r = requests.get(url, params=params, timeout=8)
                items = r.json()["response"]["body"]["items"]
                if items and isinstance(items, list):
                    item = items[0]
                    pm25 = item.get("pm25Value", "")
                    pm10 = item.get("pm10Value", "")
                    if pm25 and str(pm25).strip() not in ["-", "", "None"]:
                        return dict(
                            pm25=float(pm25),
                            pm10=float(pm10) if pm10 and str(pm10).strip() not in ["-",""] else 0,
                            o3=float(item.get("o3Value") or 0),
                            no2=float(item.get("no2Value") or 0),
                            station=station,
                            fetch_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
                            mock=False)
            except Exception:
                continue
    return dict(
        pm25=random.randint(12,65), pm10=random.randint(18,85),
        o3=round(random.uniform(0.01,0.08),3),
        no2=round(random.uniform(0.01,0.05),3),
        station="모의데이터",
        fetch_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        mock=True)

# ── AI 분석 함수 ──────────────────────────────────────
def analyze_skin(images, api_key, body_parts=None):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        content = []
        for img in images:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg",
                           "data": img_to_b64(img)}
            })
        parts_str = f"\n\n[촬영 부위]: {', '.join(body_parts)}" if body_parts else ""
        content.append({"type": "text", "text": SKIN_ANALYSIS_PROMPT + parts_str})
        msg = client.messages.create(
            model="claude-haiku-4-5", max_tokens=1200,
            messages=[{"role": "user", "content": content}]
        )
        raw = re.sub(r"```json|```", "", msg.content[0].text.strip()).strip()
        return json.loads(raw)
    except Exception as e:
        st.error(f"피부 분석 오류: {e}")
        return None

def analyze_scalp(images, api_key, body_parts=None):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        content = []
        for img in images:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg",
                           "data": img_to_b64(img)}
            })
        parts_str = f"\n\n[촬영 부위]: {', '.join(body_parts)}" if body_parts else ""
        content.append({"type": "text", "text": SCALP_ANALYSIS_PROMPT + parts_str})
        msg = client.messages.create(
            model="claude-haiku-4-5", max_tokens=1200,
            messages=[{"role": "user", "content": content}]
        )
        raw = re.sub(r"```json|```", "", msg.content[0].text.strip()).strip()
        return json.loads(raw)
    except Exception as e:
        st.error(f"두피 분석 오류: {e}")
        return None

# ── 혼합 비율 생성 (피부) ─────────────────────────────
def generate_mixing_guide(ingredients, skin_type, ceei_grade, total_ml=20):
    BASE_WEIGHT = {
        "히알루론산": 35, "세라마이드": 20, "나이아신아마이드": 20,
        "판테놀": 15, "비타민C": 15, "비타민C 유도체": 15,
        "펩타이드": 15, "아데노신": 10, "레티놀": 8,
        "AHA": 10, "BHA": 8, "EGF": 5,
    }
    boost = {"낮음": 1.0, "보통": 1.2, "높음": 1.5, "매우높음": 1.8}.get(ceei_grade, 1.0)
    antioxidants  = {"비타민C", "비타민C 유도체", "나이아신아마이드", "펩타이드", "레티놀"}
    sensitive_red = {"레티놀", "AHA", "BHA"}
    is_sensitive  = skin_type in ["민감성", "건성"]

    weights = {}
    for ing in ingredients:
        w = BASE_WEIGHT.get(ing, 10)
        if ing in antioxidants: w = round(w * boost)
        if is_sensitive and ing in sensitive_red: w = max(3, round(w * 0.5))
        weights[ing] = w

    total_w = sum(weights.values())
    ratios  = {ing: round(w / total_w * 100) for ing, w in weights.items()}
    diff    = 100 - sum(ratios.values())
    if diff != 0 and ratios:
        ratios[max(ratios, key=ratios.get)] += diff

    ml_dict = {ing: round(total_ml * pct / 100, 1) for ing, pct in ratios.items()}

    order_group = {
        1: {"히알루론산", "판테놀"},
        2: {"나이아신아마이드", "비타민C", "비타민C 유도체", "펩타이드"},
        3: {"아데노신", "EGF", "레티놀"},
        4: {"세라마이드", "AHA", "BHA"},
    }
    steps = {}
    for ing in ingredients:
        g = next((k for k, s in order_group.items() if ing in s), 5)
        steps.setdefault(g, []).append(ing)

    step_labels = {
        1: "수용성 베이스 혼합 (기초 보습층)",
        2: "기능성 성분 첨가 (항산화·미백·탄력)",
        3: "유효 성분 첨가 (고기능 활성 성분)",
        4: "지용성·특수 성분 첨가 (장벽·각질 관리)",
        5: "기타 성분 첨가",
    }
    ordered_steps = [
        {"step": g, "label": step_labels.get(g, "성분 첨가"), "items": steps[g]}
        for g in sorted(steps)
    ]
    return {"ratios": ratios, "ml": ml_dict, "steps": ordered_steps, "total_ml": total_ml}

# ── 혼합 비율 생성 (두피) ─────────────────────────────
def generate_scalp_mixing_guide(ingredients, scalp_result, ceei_grade, total_ml=20):
    BASE_WEIGHT = {
        "징크피리치온":    25,
        "살리실산":        20,
        "바이오틴":        20,
        "판테놀 (두피용)": 25,
        "나이아신아마이드":15,
        "비타민C":         10,
        "비타민C 유도체":  10,
        "히알루론산":      15,
        "세라마이드":      10,
    }

    keratin_score = scalp_result.get("keratin_score", 70)
    pore_score    = scalp_result.get("pore_score", 70)
    thickness     = scalp_result.get("hair_thickness_score", 70)
    color_score   = scalp_result.get("scalp_color_score", 70)
    moisture      = scalp_result.get("moisture_balance_score", 70)
    damage        = scalp_result.get("hair_damage_score", 70)

    env_boost = {"낮음": 1.0, "보통": 1.2, "높음": 1.5, "매우높음": 1.8}.get(ceei_grade, 1.0)

    weights = {}
    for ing in ingredients:
        w = BASE_WEIGHT.get(ing, 10)
        if ing in {"살리실산", "징크피리치온"} and keratin_score < 50:
            w = round(w * 1.5)
        if ing == "살리실산" and pore_score < 50:
            w = round(w * 1.3)
        if ing in {"바이오틴", "판테놀 (두피용)"} and thickness < 50:
            w = round(w * 1.5)
        if ing in {"판테놀 (두피용)", "히알루론산"} and color_score < 50:
            w = round(w * 1.4)
        if ing in {"판테놀 (두피용)", "히알루론산"} and moisture < 50:
            w = round(w * 1.3)
        if ing in {"바이오틴", "판테놀 (두피용)"} and damage < 50:
            w = round(w * 1.3)
        if ing in {"나이아신아마이드", "비타민C", "비타민C 유도체"}:
            w = round(w * env_boost)
        weights[ing] = max(w, 5)

    total_w = sum(weights.values())
    ratios  = {ing: round(w / total_w * 100) for ing, w in weights.items()}
    diff    = 100 - sum(ratios.values())
    if diff != 0 and ratios:
        ratios[max(ratios, key=ratios.get)] += diff

    ml_dict = {ing: round(total_ml * pct / 100, 1) for ing, pct in ratios.items()}

    order_group = {
        1: {"히알루론산", "판테놀 (두피용)"},
        2: {"나이아신아마이드", "비타민C", "비타민C 유도체"},
        3: {"바이오틴"},
        4: {"징크피리치온", "살리실산", "세라마이드"},
    }
    steps = {}
    for ing in ingredients:
        g = next((k for k, s in order_group.items() if ing in s), 5)
        steps.setdefault(g, []).append(ing)

    step_labels = {
        1: "두피 베이스 혼합 (보습·진정층)",
        2: "기능성 성분 첨가 (항산화·피지 조절)",
        3: "모발 강화 성분 첨가 (성장·강화)",
        4: "특수 성분 첨가 (항균·각질·장벽)",
        5: "기타 성분 첨가",
    }
    ordered_steps = [
        {"step": g, "label": step_labels.get(g, "성분 첨가"), "items": steps[g]}
        for g in sorted(steps)
    ]
    return {"ratios": ratios, "ml": ml_dict, "steps": ordered_steps, "total_ml": total_ml}

# ── 혼합 비율 카드 렌더링 ─────────────────────────────
def show_mixing_card(mixing, title, is_scalp=False):
    bar_class = "scalp-mixing-bar" if is_scalp else "mixing-bar"
    st.markdown("<div class='mixing-card'>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='card-label' style='color:#1a5276;'>{title}</div>",
        unsafe_allow_html=True
    )
    rows_html = ""
    for ing, pct in sorted(mixing["ratios"].items(), key=lambda x: -x[1]):
        ml_val = mixing["ml"].get(ing, 0)
        cp     = COUPANG_LINKS.get(ing, {})
        cp_url = cp.get("url", "") if cp else ""
        cp_btn = (
            f"<a href='{cp_url}' target='_blank' class='coupang-btn'>🛒 구매</a>"
            if cp_url else ""
        )
        rows_html += f"""
<div class='mixing-row'>
  <span class='mixing-ing'>{ing}{cp_btn}</span>
  <div class='mixing-bar-wrap'>
    <div class='{bar_class}' style='width:{pct}%;'></div>
  </div>
  <span class='mixing-pct'>{pct}%</span>
  <span class='mixing-ml'>{ml_val}ml</span>
</div>"""
    st.markdown(rows_html, unsafe_allow_html=True)

    st.markdown(
        "<div style='margin-top:1rem;font-size:0.82rem;font-weight:700;"
        "color:#0f3460;margin-bottom:0.5rem;'>📋 제조 순서</div>",
        unsafe_allow_html=True
    )
    for s in mixing["steps"]:
        items_str = " + ".join(s["items"])
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.5rem;"
            f"padding:0.4rem 0;font-size:0.83rem;color:#333;'>"
            f"<span class='step-badge'>{s['step']}</span>"
            f"<span><b>{s['label']}</b> — {items_str}</span></div>",
            unsafe_allow_html=True
        )
    st.markdown(
        f"<div class='partners-notice'>{COUPANG_DISCLAIMER}</div>",
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ── 데이터 저장 ───────────────────────────────────────
DATA_FILE = Path("ydlab_skin_data.csv")
FIELDS = [
    "timestamp","participant_id","age_group","gender","region","residence_years",
    "skin_concern","body_parts","photo_count","analysis_mode",
    "pm25","pm10","o3","no2","air_station","air_source","ceei_score","ceei_grade",
    "overall_score","skin_type",
    "key_concerns","recommended_ingredients",
    "wrinkle_score","pore_score","texture_score","tone_score","moisture_score",
    "scalp_keratin_score","scalp_pore_score","scalp_hair_thickness_score",
    "scalp_color_score","scalp_moisture_balance_score",
    "scalp_hair_damage_score","scalp_hair_loss_risk_score",
    "scalp_comment","consent","research_consent","marketing_opt_in"
]

def get_sheet():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scopes = ["https://spreadsheets.google.com/feeds",
                  "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets.get("GOOGLE_SHEETS_ID","")).sheet1
    except Exception:
        return None

def get_marketing_sheet():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scopes = ["https://spreadsheets.google.com/feeds",
                  "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets.get("GOOGLE_SHEETS_ID",""))
        try:
            ws = sh.worksheet("marketing_opt")
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet("marketing_opt", rows=200, cols=4)
            ws.append_row(["participant_id","email","opt_in_date","region"])
        return ws
    except Exception:
        return None

def save_marketing_opt(participant_id, email, region):
    try:
        ws = get_marketing_sheet()
        if ws:
            ws.append_row([participant_id, email,
                           datetime.now().strftime("%Y-%m-%d %H:%M:%S"), region])
    except Exception:
        pass

def ensure_header(sheet):
    try:
        if sheet.row_values(1) == []:
            sheet.append_row(FIELDS)
    except Exception:
        pass

def save_record(r):
    try:
        sheet = get_sheet()
        if sheet:
            ensure_header(sheet)
            sheet.append_row([r.get(k,"") for k in FIELDS])
    except Exception:
        pass
    header = not DATA_FILE.exists()
    with open(DATA_FILE, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if header: w.writeheader()
        w.writerow({k: r.get(k,"") for k in FIELDS})

def show_air_status(air):
    if air.get("mock"):
        st.markdown(
            "<div class='air-mock'>⚠️ 대기오염 데이터: <b>모의(Mock) 데이터</b> 사용 중</div>",
            unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='air-real'>✅ 에어코리아 실시간 측정값 — "
            f"측정소: {air.get('station','')} · {air.get('fetch_time','')}</div>",
            unsafe_allow_html=True)

# ── 피부 결과 렌더링 ──────────────────────────────────
def show_skin_result(result, air, region, residence_years_str,
                     participant_id, age_group, gender, selected_parts):
    pm25_avg = REGION_PM25_AVG.get(region, 22.0)
    yrs      = RESIDENCE_YEAR_MAP.get(residence_years_str, 0)
    ceei, ceei_grade, ceei_chip, ceei_msg = calc_ceei(pm25_avg, yrs)
    pm25_val    = air.get("pm25")
    alert_msg   = get_pollution_alert(pm25_val, ceei)
    overall     = result.get("overall_score", 0)
    skin_type   = result.get("skin_type", "")
    ingredients = result.get("recommended_ingredients", [])

    st.markdown("<div class='patent-banner'>🔐 본 기술은 특허 출원 중입니다</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<div class='medical-disclaimer'>⚠️ 본 분석 결과는 AI 기반 참고용 정보이며 "
        "의학적 진단이 아닙니다.</div>", unsafe_allow_html=True)
    show_air_status(air)

    st.markdown(f"""
<div class='card'>
  <div class='card-label'>🧴 피부 분석 종합 결과</div>
  <div style='display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;'>
    <div style='text-align:center;'>
      <div style='font-size:3.5rem;font-weight:700;color:{score_color(overall)};
                  line-height:1;font-family:"DM Mono",monospace;'>{overall}</div>
      <div style='font-size:0.72rem;color:#888;margin-top:0.3rem;'>종합 점수</div>
    </div>
    <div>
      <div style='font-size:1rem;font-weight:700;margin-bottom:0.4rem;'>
        피부 타입: {skin_type}</div>
      <div style='font-size:0.84rem;color:#555;line-height:1.7;'>
        {result.get("summary","")}</div>
      <div style='margin-top:0.5rem;'>{pm25_chip(pm25_val)} {ceei_chip}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    if alert_msg: st.warning(alert_msg)

    metrics = [
        ("주름",   result.get("wrinkle_score",0),  result.get("wrinkle_comment","")),
        ("모공",   result.get("pore_score",0),      result.get("pore_comment","")),
        ("피부결", result.get("texture_score",0),   result.get("texture_comment","")),
        ("피부톤", result.get("tone_score",0),       result.get("tone_comment","")),
        ("수분",   result.get("moisture_score",0),  result.get("moisture_comment","")),
    ]
    cols = st.columns(5)
    for i, (lbl, val, cmt) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
<div class='score-box'>
  <div class='score-num' style='color:{score_color(val)};'>{val}</div>
  <div class='score-lbl'>{lbl}</div>
  <div style='font-size:0.68rem;color:#999;margin-top:0.3rem;line-height:1.3;'>{cmt}</div>
</div>""", unsafe_allow_html=True)

    # ✅ 수정 1: 추천 성분 + 쿠팡 링크 (show_skin_result)
    ing_html = ""
    for ing in ingredients:
        cp = COUPANG_LINKS.get(ing, {})
        cp_url = cp.get("url", "") if cp else ""
        link = (
            f"<a href='{cp_url}' target='_blank' "
            f"style='color:#ff6b35;font-size:0.7rem;text-decoration:none;'>🛒</a>"
            if cp_url else ""
        )
        ing_html += f"<span class='ingredient-chip'>{ing} {link}</span>"

    st.markdown(f"""
<div class='card'>
  <div class='card-label'>AI 추천 화장품 성분</div>
  <div style='margin-bottom:0.8rem;'>{ing_html}</div>
  <div class='result-text'>{result.get("care_advice","")}</div>
</div>""", unsafe_allow_html=True)

    if ingredients:
        mixing = generate_mixing_guide(ingredients, skin_type, ceei_grade)
        show_mixing_card(
            mixing,
            f"🧪 피부 맞춤 혼합 비율 — 총 {mixing['total_ml']}ml · {skin_type}",
            is_scalp=False
        )

    st.markdown(f"""
<div class='card'>
  <div class='card-label'>CEEI — 누적 환경 노출 지수</div>
  <div style='display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.7rem;'>
    {pm25_chip(pm25_val)} {ceei_chip}
    <span class='chip chip-neu'>지역 연평균 {pm25_avg}㎍/m³</span>
    <span class='chip chip-neu'>거주 {yrs}년</span>
  </div>
  <div class='result-text'>{ceei_msg}</div>
</div>""", unsafe_allow_html=True)

    scores_dict = {
        "주름": result.get("wrinkle_score",0),
        "모공": result.get("pore_score",0),
        "피부결": result.get("texture_score",0),
        "피부톤": result.get("tone_score",0),
        "수분": result.get("moisture_score",0),
    }
    priority = sorted(scores_dict.items(), key=lambda x: x[1])[:3]
    st.markdown("<div class='card'><div class='card-label'>우선 개선 항목</div>",
                unsafe_allow_html=True)
    for i, (lbl, score) in enumerate(priority):
        color    = score_color(score)
        care_msg = "집중 케어 필요" if score < 40 else "개선 권장" if score < 60 else "유지 관리"
        st.markdown(f"""
<div class='priority-item'>
  <span class='priority-num'>{i+1}</span>
  <span class='priority-label'>{lbl}</span>
  <span class='priority-score' style='color:{color};'>{score}점</span>
  <span class='priority-msg'>{care_msg}</span>
</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    mixing = generate_mixing_guide(ingredients, skin_type, ceei_grade)
    col1, col2 = st.columns(2)
    with col1:
        pdf_html = generate_skin_report_html(
            result, air, region, yrs, participant_id, age_group, gender, mixing)
        st.download_button("📄 피부 분석 리포트",
                           data=pdf_html.encode("utf-8"),
                           file_name=f"YDLab_피부리포트_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                           mime="text/html", use_container_width=True, key="k_skin_report")
    with col2:
        order_html = generate_skin_order_html(
            result, air, region, yrs, participant_id, age_group, gender, mixing)
        st.download_button("🧪 피부 공방 주문서",
                           data=order_html.encode("utf-8"),
                           file_name=f"YDLab_피부주문서_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                           mime="text/html", use_container_width=True, key="k_skin_order")


# ── 두피 결과 렌더링 ──────────────────────────────────
def show_scalp_result(result, air, region, residence_years_str,
                      participant_id, age_group, gender, selected_parts):
    pm25_avg = REGION_PM25_AVG.get(region, 22.0)
    yrs      = RESIDENCE_YEAR_MAP.get(residence_years_str, 0)
    ceei, ceei_grade, ceei_chip, ceei_msg = calc_ceei(pm25_avg, yrs)
    pm25_val    = air.get("pm25")
    overall     = result.get("overall_score", 0)
    scalp_type  = result.get("scalp_type", "")
    ingredients = result.get("recommended_ingredients", [])

    st.markdown("<div class='patent-banner'>🔐 본 기술은 특허 출원 중입니다</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<div class='medical-disclaimer'>⚠️ 본 분석 결과는 AI 기반 참고용 정보이며 "
        "의학적 진단이 아닙니다. 탈모 진행도는 참고용입니다.</div>",
        unsafe_allow_html=True)
    show_air_status(air)

    st.markdown(f"""
<div class='card' style='border-color:#a5d6a7;'>
  <div class='card-label'>💆 두피 분석 종합 결과</div>
  <div style='display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;'>
    <div style='text-align:center;'>
      <div style='font-size:3.5rem;font-weight:700;color:{score_color(overall)};
                  line-height:1;font-family:"DM Mono",monospace;'>{overall}</div>
      <div style='font-size:0.72rem;color:#888;margin-top:0.3rem;'>종합 점수</div>
    </div>
    <div>
      <div style='font-size:1rem;font-weight:700;margin-bottom:0.4rem;'>
        두피 타입: {scalp_type}</div>
      <div style='font-size:0.84rem;color:#555;line-height:1.7;'>
        {result.get("summary","")}</div>
      <div style='margin-top:0.5rem;'>{pm25_chip(pm25_val)} {ceei_chip}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    scalp_metrics = [
        ("각질 상태",      result.get("keratin_score", 0),
         result.get("keratin_comment", "")),
        ("모공·피지",      result.get("pore_score", 0),
         result.get("pore_comment", "")),
        ("모발 굵기",      result.get("hair_thickness_score", 0),
         result.get("hair_thickness_comment", "")),
        ("두피 색상·염증", result.get("scalp_color_score", 0),
         result.get("scalp_color_comment", "")),
        ("수분·유분 밸런스", result.get("moisture_balance_score", 0),
         result.get("moisture_balance_comment", "")),
        ("모발 손상도",    result.get("hair_damage_score", 0),
         result.get("hair_damage_comment", "")),
    ]

    st.markdown("<div class='scalp-card'>", unsafe_allow_html=True)
    st.markdown("**💆 두피 분석 6지표**")
    cols = st.columns(3)
    for i, (lbl, val, cmt) in enumerate(scalp_metrics):
        with cols[i % 3]:
            st.markdown(f"""
<div class='score-box' style='background:#f0faf4;border-color:#a5d6a7;'>
  <div class='score-num' style='color:{score_color(val)};'>{val}</div>
  <div class='score-lbl'>{lbl}</div>
  <div style='font-size:0.68rem;color:#999;margin-top:0.3rem;line-height:1.3;'>{cmt}</div>
</div>""", unsafe_allow_html=True)

    hair_loss     = result.get("hair_loss_risk_score", 0)
    hair_loss_cmt = result.get("hair_loss_risk_comment", "")
    st.markdown(
        f"<div style='margin-top:0.8rem;background:#fff8f0;border:1px solid #ffcc80;"
        f"border-radius:8px;padding:0.7rem 1rem;font-size:0.82rem;'>"
        f"<b>⚠️ 탈모 진행도 (참고용)</b>: "
        f"<span style='font-weight:700;color:{score_color(hair_loss)};'>{hair_loss}점</span> "
        f"— {hair_loss_cmt}</div>",
        unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ✅ 수정 2: 추천 성분 + 쿠팡 링크 (show_scalp_result)
    ing_html = ""
    for ing in ingredients:
        cp = COUPANG_LINKS.get(ing, {})
        cp_url = cp.get("url", "") if cp else ""
        link = (
            f"<a href='{cp_url}' target='_blank' "
            f"style='color:#ff6b35;font-size:0.7rem;text-decoration:none;'>🛒</a>"
            if cp_url else ""
        )
        ing_html += f"<span class='scalp-ingredient-chip'>{ing} {link}</span>"

    st.markdown(f"""
<div class='card' style='border-color:#a5d6a7;'>
  <div class='card-label'>AI 추천 두피·모발 성분</div>
  <div style='margin-bottom:0.8rem;'>{ing_html}</div>
  <div class='result-text'>{result.get("care_advice","")}</div>
</div>""", unsafe_allow_html=True)

    if ingredients:
        mixing = generate_scalp_mixing_guide(ingredients, result, ceei_grade)
        show_mixing_card(
            mixing,
            f"🧪 두피 맞춤 혼합 비율 — 총 {mixing['total_ml']}ml · {scalp_type}",
            is_scalp=True
        )

    st.markdown(f"""
<div class='card'>
  <div class='card-label'>CEEI — 누적 환경 노출 지수 (두피 영향)</div>
  <div style='display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.7rem;'>
    {pm25_chip(pm25_val)} {ceei_chip}
  </div>
  <div class='result-text'>{ceei_msg}</div>
</div>""", unsafe_allow_html=True)

    priority_scores = {
        "각질 상태":        result.get("keratin_score", 0),
        "모공·피지":        result.get("pore_score", 0),
        "모발 굵기":        result.get("hair_thickness_score", 0),
        "두피 색상·염증":   result.get("scalp_color_score", 0),
        "수분·유분 밸런스": result.get("moisture_balance_score", 0),
        "모발 손상도":      result.get("hair_damage_score", 0),
    }
    priority = sorted(priority_scores.items(), key=lambda x: x[1])[:3]
    st.markdown("<div class='card'><div class='card-label'>우선 개선 항목 (두피)</div>",
                unsafe_allow_html=True)
    for i, (lbl, score) in enumerate(priority):
        color    = score_color(score)
        care_msg = "집중 케어 필요" if score < 40 else "개선 권장" if score < 60 else "유지 관리"
        st.markdown(f"""
<div class='priority-item'>
  <span class='priority-num'>{i+1}</span>
  <span class='priority-label'>{lbl}</span>
  <span class='priority-score' style='color:{color};'>{score}점</span>
  <span class='priority-msg'>{care_msg}</span>
</div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    mixing = generate_scalp_mixing_guide(ingredients, result, ceei_grade)
    col1, col2 = st.columns(2)
    with col1:
        pdf_html = generate_scalp_report_html(
            result, air, region, yrs, participant_id, age_group, gender, mixing)
        st.download_button("📄 두피 분석 리포트",
                           data=pdf_html.encode("utf-8"),
                           file_name=f"YDLab_두피리포트_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                           mime="text/html", use_container_width=True, key="k_scalp_report")
    with col2:
        order_html = generate_scalp_order_html(
            result, air, region, yrs, participant_id, age_group, gender, mixing)
        st.download_button("🧪 두피 공방 주문서",
                           data=order_html.encode("utf-8"),
                           file_name=f"YDLab_두피주문서_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                           mime="text/html", use_container_width=True, key="k_scalp_order")


# ── HTML 생성 헬퍼: 쿠팡 링크 태그 ──────────────────
def _cp_link_tag(ing, font_size="8px"):
    """성분명으로 쿠팡 링크 <a> 태그를 반환. 없으면 빈 문자열."""
    cp = COUPANG_LINKS.get(ing, {})
    url = cp.get("url", "") if cp else ""
    if not url:
        return ""
    return f'<a href="{url}" target="_blank" style="color:#ff6b35;font-size:{font_size};">🛒</a>'

def _cp_buy_btn(ing):
    """성분명으로 쿠팡 구매 버튼 <a> 태그를 반환. 없으면 "-"."""
    cp = COUPANG_LINKS.get(ing, {})
    url = cp.get("url", "") if cp else ""
    if not url:
        return "-"
    return (
        f'<a href="{url}" target="_blank" '
        f'style="display:inline-block;background:#ff6b35;color:white;'
        f'padding:3px 8px;border-radius:4px;font-size:9px;text-decoration:none;">🛒 구매</a>'
    )

def _cp_mix_link(ing):
    """혼합비율 테이블용 쿠팡 링크 태그. 없으면 빈 문자열."""
    cp = COUPANG_LINKS.get(ing, {})
    url = cp.get("url", "") if cp else ""
    if not url:
        return ""
    return f'<a href="{url}" target="_blank" style="color:#ff6b35;">🛒</a>'


# ── HTML 생성 (피부 리포트) ───────────────────────────
def generate_skin_report_html(result, air, region, residence_years,
                               participant_id, age_group, gender, mixing=None):
    overall   = result.get("overall_score", 0)
    skin_type = result.get("skin_type", "")
    summary   = result.get("summary", "")
    care      = result.get("care_advice", "")
    ings      = result.get("recommended_ingredients", [])
    pm25_avg  = REGION_PM25_AVG.get(region, 22.0)
    ceei, ceei_grade, _, ceei_msg = calc_ceei(pm25_avg, residence_years)
    is_mock   = air.get("mock", True)
    air_color = "#2e7d32" if not is_mock else "#e65100"
    air_bg    = "#e8f5e9" if not is_mock else "#fff3e0"
    air_txt   = (f"📡 에어코리아 실시간 · {air.get('station','')} · {air.get('fetch_time','')}"
                 if not is_mock else "⚠️ 모의 데이터")

    def sc(s):
        if s >= 70: return "#2e7d32"
        if s >= 40: return "#e65100"
        return "#c62828"

    metrics = [
        ("주름",   result.get("wrinkle_score",0),  result.get("wrinkle_comment","")),
        ("모공",   result.get("pore_score",0),      result.get("pore_comment","")),
        ("피부결", result.get("texture_score",0),   result.get("texture_comment","")),
        ("피부톤", result.get("tone_score",0),       result.get("tone_comment","")),
        ("수분",   result.get("moisture_score",0),  result.get("moisture_comment","")),
    ]
    score_boxes = "".join([
        f"<div class='sbox'><div class='snum' style='color:{sc(v)}'>{v}</div>"
        f"<div class='slbl'>{l}</div><div class='scmt'>{c}</div></div>"
        for l, v, c in metrics
    ])

    # ✅ 수정 3: 피부 리포트 성분 링크
    ing_parts = []
    for i in ings:
        link_tag = _cp_link_tag(i)
        ing_parts.append(f"<span class='ing'>{i} {link_tag}</span>")
    ing_html = "".join(ing_parts)

    mixing_section = ""
    if mixing:
        mix_rows_parts = []
        for ing, pct in sorted(mixing["ratios"].items(), key=lambda x: -x[1]):
            ml_val   = mixing["ml"].get(ing, 0)
            link_tag = _cp_mix_link(ing)
            mix_rows_parts.append(
                f"<div style='display:flex;align-items:center;gap:6px;"
                f"padding:4px 0;border-bottom:1px solid #f0f0f0;font-size:9px;'>"
                f"<span style='flex:1;font-weight:600;'>{ing} {link_tag}</span>"
                f"<span style='font-weight:700;color:#2e7d32;min-width:35px;'>{pct}%</span>"
                f"<span style='color:#888;min-width:40px;'>{ml_val}ml</span>"
                f"<div style='flex:2;background:#e4e8ee;border-radius:3px;height:6px;'>"
                f"<div style='width:{pct}%;height:6px;border-radius:3px;"
                f"background:linear-gradient(90deg,#2e7d32,#4CAF50);'></div></div></div>"
            )
        mix_rows = "".join(mix_rows_parts)
        mixing_section = (
            f"<div class='section'><div class='stitle'>맞춤 혼합 비율 (총 {mixing['total_ml']}ml)</div>"
            f"{mix_rows}"
            f"<div style='font-size:7px;color:#e65100;padding:5px 8px;"
            f"background:#fff8f0;border-radius:4px;margin-top:6px;'>{COUPANG_DISCLAIMER}</div></div>"
        )

    gc = {"낮음":"#2e7d32","보통":"#1565c0","높음":"#e65100","매우높음":"#c62828"}.get(ceei_grade,"#333")
    ceei_bg = "fce4ec" if ceei>=300 else "fff3e0" if ceei>=150 else "e8f5e9"

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>YD Lab 피부 분석 리포트</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Noto Sans KR',sans-serif;font-size:12px;color:#1a1a2e;background:white;}}
.header{{background:#0f3460;color:white;padding:20px 30px;display:flex;justify-content:space-between;align-items:center;}}
.header h1{{font-size:18px;font-weight:700;}}
.header .sub{{font-size:9px;opacity:0.6;margin-top:3px;}}
.body{{padding:22px 30px;}}
.air-bar{{font-size:9px;font-weight:600;padding:5px 10px;border-radius:4px;
          margin-bottom:12px;background:{air_bg};color:{air_color};}}
.infobar{{font-size:10px;color:#555;padding-bottom:12px;margin-bottom:14px;
          border-bottom:1px solid #e4e8ee;}}
.infobar span{{margin-right:14px;}}
.section{{margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid #f0f0f0;}}
.stitle{{font-size:8px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
         color:#0f3460;margin-bottom:10px;}}
.overall-row{{display:flex;align-items:center;gap:18px;}}
.big-score{{font-size:44px;font-weight:700;color:{sc(overall)};line-height:1;}}
.skin-type{{font-size:13px;font-weight:600;margin-bottom:5px;}}
.summary{{font-size:9px;color:#555;line-height:1.65;}}
.score-row{{display:flex;gap:7px;}}
.sbox{{flex:1;background:#f8f9fa;border:1px solid #e4e8ee;border-radius:7px;
       padding:9px 5px;text-align:center;}}
.snum{{font-size:22px;font-weight:700;line-height:1.1;}}
.slbl{{font-size:8px;color:#666;margin-top:2px;}}
.scmt{{font-size:7px;color:#999;margin-top:3px;line-height:1.3;}}
.ing-row{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:7px;}}
.ing{{background:#eef2ff;color:#3730a3;border-radius:4px;padding:3px 9px;
      font-size:9px;font-weight:500;}}
.care{{font-size:9px;color:#555;line-height:1.6;}}
.chip-row{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:7px;}}
.chip{{background:#f1f3f4;color:#444;border-radius:12px;padding:2px 9px;font-size:9px;}}
.footer{{background:#0f3460;color:rgba(255,255,255,0.6);padding:10px 30px;
         font-size:8px;display:flex;justify-content:space-between;margin-top:10px;}}
.print-btn{{position:fixed;bottom:20px;right:20px;background:#0f3460;color:white;
            border:none;padding:10px 20px;border-radius:8px;font-size:13px;cursor:pointer;}}
@media print{{.print-btn{{display:none;}}}}
</style></head><body>
<button class="print-btn" onclick="window.print()">🖨️ PDF로 저장</button>
<div class="header">
  <div><h1>🧴 YD Lab 피부 분석 리포트</h1>
  <div class="sub">재능대학교 바이오테크과 · AI 바이오분석특화연구소 · 특허 출원 중</div></div>
  <div style="font-size:10px;opacity:0.75;">{datetime.now().strftime("%Y년 %m월 %d일")}</div>
</div>
<div class="body">
<div class="air-bar">{air_txt}</div>
<div class="infobar">
  <span>코드: {participant_id}</span><span>{age_group}</span>
  <span>{gender}</span><span>{region}</span><span>거주 {residence_years}년</span>
</div>
<div class="section">
  <div class="stitle">종합 결과</div>
  <div class="overall-row">
    <div class="big-score">{overall}</div>
    <div><div class="skin-type">피부 타입: {skin_type}</div>
    <div class="summary">{summary}</div></div>
  </div>
</div>
<div class="section">
  <div class="stitle">피부 5지표</div>
  <div class="score-row">{score_boxes}</div>
</div>
<div class="section">
  <div class="stitle">추천 성분</div>
  <div class="ing-row">{ing_html}</div>
  <div class="care">{care}</div>
</div>
{mixing_section}
<div class="section">
  <div class="stitle">환경 지수</div>
  <div class="chip-row">
    <span class="chip">PM2.5 {air.get('pm25','-')}㎍/m³</span>
    <span class="chip">PM10 {air.get('pm10','-')}㎍/m³</span>
    <span class="chip">O₃ {air.get('o3','-')}ppm</span>
    <span class="chip">NO₂ {air.get('no2','-')}ppm</span>
  </div>
  <div class="chip-row">
    <span class="chip" style="background:#{ceei_bg};color:{gc};">CEEI {ceei} [{ceei_grade}]</span>
  </div>
  <div style="font-size:9px;color:#555;">{ceei_msg}</div>
</div>
</div>
<div class="footer">
  <span>본 리포트는 참고용이며 의료적 진단을 대체하지 않습니다. 특허 출원 중.</span>
  <span>YD Lab · 재능대학교 · 남정훈 교수</span>
</div>
</body></html>"""


# ── HTML 생성 (두피 리포트) ───────────────────────────
def generate_scalp_report_html(result, air, region, residence_years,
                                participant_id, age_group, gender, mixing=None):
    overall    = result.get("overall_score", 0)
    scalp_type = result.get("scalp_type", "")
    summary    = result.get("summary", "")
    care       = result.get("care_advice", "")
    ings       = result.get("recommended_ingredients", [])
    pm25_avg   = REGION_PM25_AVG.get(region, 22.0)
    ceei, ceei_grade, _, ceei_msg = calc_ceei(pm25_avg, residence_years)
    is_mock    = air.get("mock", True)
    air_color  = "#2e7d32" if not is_mock else "#e65100"
    air_bg     = "#e8f5e9" if not is_mock else "#fff3e0"
    air_txt    = (f"📡 에어코리아 실시간 · {air.get('station','')} · {air.get('fetch_time','')}"
                  if not is_mock else "⚠️ 모의 데이터")

    def sc(s):
        if s >= 70: return "#2e7d32"
        if s >= 40: return "#e65100"
        return "#c62828"

    scalp_metrics = [
        ("각질 상태",        result.get("keratin_score",0),         result.get("keratin_comment","")),
        ("모공·피지",        result.get("pore_score",0),             result.get("pore_comment","")),
        ("모발 굵기",        result.get("hair_thickness_score",0),   result.get("hair_thickness_comment","")),
        ("두피 색상·염증",   result.get("scalp_color_score",0),      result.get("scalp_color_comment","")),
        ("수분·유분 밸런스", result.get("moisture_balance_score",0), result.get("moisture_balance_comment","")),
        ("모발 손상도",      result.get("hair_damage_score",0),      result.get("hair_damage_comment","")),
    ]
    score_boxes = "".join([
        f"<div class='sbox' style='background:#f0faf4;border-color:#a5d6a7;'>"
        f"<div class='snum' style='color:{sc(v)}'>{v}</div>"
        f"<div class='slbl'>{l}</div><div class='scmt'>{c}</div></div>"
        for l, v, c in scalp_metrics
    ])
    hair_loss     = result.get("hair_loss_risk_score", 0)
    hair_loss_cmt = result.get("hair_loss_risk_comment", "")

    # ✅ 수정 4: 두피 리포트 성분 링크
    ing_parts = []
    for i in ings:
        link_tag = _cp_link_tag(i)
        ing_parts.append(
            f"<span class='ing' style='background:#f0faf4;color:#2e7d32;'>{i} {link_tag}</span>"
        )
    ing_html = "".join(ing_parts)

    mixing_section = ""
    if mixing:
        mix_rows_parts = []
        for ing, pct in sorted(mixing["ratios"].items(), key=lambda x: -x[1]):
            ml_val   = mixing["ml"].get(ing, 0)
            link_tag = _cp_mix_link(ing)
            mix_rows_parts.append(
                f"<div style='display:flex;align-items:center;gap:6px;"
                f"padding:4px 0;border-bottom:1px solid #f0f0f0;font-size:9px;'>"
                f"<span style='flex:1;font-weight:600;'>{ing} {link_tag}</span>"
                f"<span style='font-weight:700;color:#1565c0;min-width:35px;'>{pct}%</span>"
                f"<span style='color:#888;min-width:40px;'>{ml_val}ml</span>"
                f"<div style='flex:2;background:#e4e8ee;border-radius:3px;height:6px;'>"
                f"<div style='width:{pct}%;height:6px;border-radius:3px;"
                f"background:linear-gradient(90deg,#1565c0,#42a5f5);'></div></div></div>"
            )
        mix_rows = "".join(mix_rows_parts)
        mixing_section = (
            f"<div class='section'><div class='stitle'>두피 맞춤 혼합 비율 (총 {mixing['total_ml']}ml)</div>"
            f"{mix_rows}"
            f"<div style='font-size:7px;color:#e65100;padding:5px 8px;"
            f"background:#fff8f0;border-radius:4px;margin-top:6px;'>{COUPANG_DISCLAIMER}</div></div>"
        )

    gc = {"낮음":"#2e7d32","보통":"#1565c0","높음":"#e65100","매우높음":"#c62828"}.get(ceei_grade,"#333")
    ceei_bg = "fce4ec" if ceei>=300 else "fff3e0" if ceei>=150 else "e8f5e9"

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>YD Lab 두피 분석 리포트</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Noto Sans KR',sans-serif;font-size:12px;color:#1a1a2e;background:white;}}
.header{{background:#1b5e20;color:white;padding:20px 30px;display:flex;justify-content:space-between;align-items:center;}}
.header h1{{font-size:18px;font-weight:700;}}
.header .sub{{font-size:9px;opacity:0.6;margin-top:3px;}}
.body{{padding:22px 30px;}}
.air-bar{{font-size:9px;font-weight:600;padding:5px 10px;border-radius:4px;
          margin-bottom:12px;background:{air_bg};color:{air_color};}}
.infobar{{font-size:10px;color:#555;padding-bottom:12px;margin-bottom:14px;
          border-bottom:1px solid #e4e8ee;}}
.infobar span{{margin-right:14px;}}
.section{{margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid #f0f0f0;}}
.stitle{{font-size:8px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
         color:#1b5e20;margin-bottom:10px;}}
.overall-row{{display:flex;align-items:center;gap:18px;}}
.big-score{{font-size:44px;font-weight:700;color:{sc(overall)};line-height:1;}}
.scalp-type{{font-size:13px;font-weight:600;margin-bottom:5px;}}
.summary{{font-size:9px;color:#555;line-height:1.65;}}
.score-row{{display:flex;gap:7px;flex-wrap:wrap;}}
.sbox{{flex:1;min-width:80px;background:#f0faf4;border:1px solid #a5d6a7;
       border-radius:7px;padding:9px 5px;text-align:center;}}
.snum{{font-size:22px;font-weight:700;line-height:1.1;}}
.slbl{{font-size:8px;color:#666;margin-top:2px;}}
.scmt{{font-size:7px;color:#999;margin-top:3px;line-height:1.3;}}
.ing-row{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:7px;}}
.ing{{background:#f0faf4;color:#2e7d32;border-radius:4px;padding:3px 9px;
      font-size:9px;font-weight:500;}}
.care{{font-size:9px;color:#555;line-height:1.6;}}
.chip-row{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:7px;}}
.chip{{background:#f1f3f4;color:#444;border-radius:12px;padding:2px 9px;font-size:9px;}}
.footer{{background:#1b5e20;color:rgba(255,255,255,0.6);padding:10px 30px;
         font-size:8px;display:flex;justify-content:space-between;margin-top:10px;}}
.print-btn{{position:fixed;bottom:20px;right:20px;background:#1b5e20;color:white;
            border:none;padding:10px 20px;border-radius:8px;font-size:13px;cursor:pointer;}}
@media print{{.print-btn{{display:none;}}}}
</style></head><body>
<button class="print-btn" onclick="window.print()">🖨️ PDF로 저장</button>
<div class="header">
  <div><h1>💆 YD Lab 두피 분석 리포트</h1>
  <div class="sub">재능대학교 바이오테크과 · AI 바이오분석특화연구소 · 특허 출원 중</div></div>
  <div style="font-size:10px;opacity:0.75;">{datetime.now().strftime("%Y년 %m월 %d일")}</div>
</div>
<div class="body">
<div class="air-bar">{air_txt}</div>
<div class="infobar">
  <span>코드: {participant_id}</span><span>{age_group}</span>
  <span>{gender}</span><span>{region}</span><span>거주 {residence_years}년</span>
</div>
<div class="section">
  <div class="stitle">종합 결과</div>
  <div class="overall-row">
    <div class="big-score">{overall}</div>
    <div><div class="scalp-type">두피 타입: {scalp_type}</div>
    <div class="summary">{summary}</div></div>
  </div>
</div>
<div class="section">
  <div class="stitle">두피 6지표</div>
  <div class="score-row">{score_boxes}</div>
  <div style="margin-top:8px;background:#fff8f0;border:1px solid #ffcc80;
              border-radius:6px;padding:6px 10px;font-size:9px;">
    <b>⚠️ 탈모 진행도 (참고용):</b>
    <span style="font-weight:700;color:{sc(hair_loss)};">{hair_loss}점</span>
    — {hair_loss_cmt}
  </div>
</div>
<div class="section">
  <div class="stitle">추천 두피·모발 성분</div>
  <div class="ing-row">{ing_html}</div>
  <div class="care">{care}</div>
</div>
{mixing_section}
<div class="section">
  <div class="stitle">환경 지수 (두피 영향)</div>
  <div class="chip-row">
    <span class="chip">PM2.5 {air.get('pm25','-')}㎍/m³</span>
    <span class="chip" style="background:#{ceei_bg};color:{gc};">CEEI {ceei} [{ceei_grade}]</span>
  </div>
  <div style="font-size:9px;color:#555;">{ceei_msg}</div>
</div>
</div>
<div class="footer">
  <span>본 리포트는 참고용이며 의료적 진단을 대체하지 않습니다. 특허 출원 중.</span>
  <span>YD Lab · 재능대학교 · 남정훈 교수</span>
</div>
</body></html>"""


# ── HTML 생성 (피부 주문서) ───────────────────────────
def generate_skin_order_html(result, air, region, residence_years,
                              participant_id, age_group, gender, mixing=None):
    code      = "YDL-SKIN-" + datetime.now().strftime("%Y%m%d") + "-" + \
                ''.join(random.choices(string.ascii_uppercase+string.digits, k=4))
    overall   = result.get("overall_score", 0)
    skin_type = result.get("skin_type", "")
    ings      = result.get("recommended_ingredients", [])
    pm25_avg  = REGION_PM25_AVG.get(region, 22.0)
    ceei, ceei_grade, _, ceei_msg = calc_ceei(pm25_avg, residence_years)
    is_mock   = air.get("mock", True)
    total_ml  = mixing["total_ml"] if mixing else 20

    ing_purpose_map = {
        "히알루론산":     "즉각 수분 공급·보습",
        "세라마이드":     "피부 장벽 강화",
        "나이아신아마이드":"피부톤·모공 관리",
        "레티놀":         "주름 개선·탄력",
        "비타민C":        "항산화·피부톤",
        "비타민C 유도체": "항산화·안정형",
        "펩타이드":       "탄력·항노화",
        "판테놀":         "진정·보습",
        "AHA":            "각질 제거",
        "BHA":            "모공 각질 용해",
        "아데노신":       "주름 개선(식약처)",
        "EGF":            "세포 재생·탄력",
    }

    # ✅ 수정 5: 피부 주문서 성분 테이블 행
    ing_rows_parts = []
    for idx, ing in enumerate(ings):
        conc, note = get_concentration(ing, skin_type)
        purpose    = ing_purpose_map.get(ing, "피부 상태 개선")
        cp_btn     = _cp_buy_btn(ing)
        ratio_val  = mixing["ratios"].get(ing, "-") if mixing else "-"
        ml_val     = mixing["ml"].get(ing, "-") if mixing else "-"
        bg = "#f8faff" if idx % 2 == 0 else "white"
        ing_rows_parts.append(
            f"<tr style='background:{bg}'>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;text-align:center;"
            f"font-weight:600;color:#0f3460;'>{idx+1}</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;font-weight:700;'>{ing}</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;color:#555;'>{purpose}</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;font-weight:600;"
            f"color:#2e7d32;'>{ratio_val}% ({ml_val}ml)</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;color:#0f3460;"
            f"font-family:monospace;'>{conc}</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;'>{cp_btn}</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;color:#888;"
            f"font-size:9px;'>{note}</td></tr>"
        )
    ing_rows = "".join(ing_rows_parts)

    steps_html_parts = []
    if mixing:
        for s in mixing["steps"]:
            items_str = " + ".join(s["items"])
            steps_html_parts.append(
                f"<div style='display:flex;align-items:center;gap:8px;"
                f"padding:5px 0;font-size:10px;border-bottom:1px solid #f0f0f0;'>"
                f"<span style='background:#0f3460;color:white;border-radius:50%;"
                f"width:20px;height:20px;display:inline-flex;align-items:center;"
                f"justify-content:center;font-size:9px;font-weight:700;flex-shrink:0;'>"
                f"{s['step']}</span>"
                f"<span><b>{s['label']}</b> — {items_str}</span></div>"
            )
    steps_html = "".join(steps_html_parts)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>YD Lab 피부 공방 주문서 {code}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Noto Sans KR',sans-serif;font-size:12px;color:#1a1a2e;background:white;}}
.header{{background:#0f3460;color:white;padding:20px 30px;display:flex;
         justify-content:space-between;align-items:center;}}
.header h1{{font-size:18px;font-weight:700;}}
.body{{padding:22px 30px;}}
table{{width:100%;border-collapse:collapse;font-size:11px;}}
th{{background:#0f3460;color:white;padding:8px;text-align:left;font-size:10px;}}
.footer{{background:#0f3460;color:rgba(255,255,255,0.6);padding:10px 30px;
         font-size:8px;display:flex;justify-content:space-between;margin-top:16px;}}
.print-btn{{position:fixed;bottom:20px;right:20px;background:#0f3460;color:white;
            border:none;padding:10px 18px;border-radius:8px;font-size:12px;cursor:pointer;}}
@media print{{.print-btn{{display:none;}}}}
</style></head><body>
<button class="print-btn" onclick="window.print()">🖨️ PDF 저장</button>
<div class="header">
  <div><h1>🧴 YD Lab 피부 공방 주문서</h1>
  <div style="font-size:9px;opacity:0.6;margin-top:3px;">
    AI 피부 분석 기반 맞춤형 화장품 제조 요청 · 재능대학교 AI-바이오분석특화연구소</div></div>
  <div style="font-family:monospace;background:rgba(255,255,255,0.15);
              padding:4px 10px;border-radius:4px;">{code}</div>
</div>
<div class="body">
  <div style="font-size:10px;color:#555;padding:10px 0;margin-bottom:14px;
              border-bottom:1px solid #e4e8ee;display:flex;gap:20px;flex-wrap:wrap;">
    <span><b>분석일:</b> {datetime.now().strftime("%Y년 %m월 %d일")}</span>
    <span><b>참여자:</b> {participant_id} {age_group} {gender}</span>
    <span><b>거주지:</b> {region} {residence_years}년</span>
    <span><b>피부타입:</b> {skin_type}</span>
    <span><b>종합점수:</b> {overall}점</span>
    <span><b>총 제조량:</b> {total_ml}ml</span>
  </div>
  <div style="margin-bottom:16px;">
    <div style="font-size:9px;font-weight:700;letter-spacing:0.1em;color:#0f3460;
                margin-bottom:8px;padding-bottom:5px;border-bottom:2px solid #0f3460;">
      성분 처방 · 혼합 비율 · 구매 링크</div>
    <table>
      <tr><th>#</th><th>성분명</th><th>목적</th><th>혼합비율</th>
          <th>권장농도</th><th>구매링크</th><th>제조참고</th></tr>
      {ing_rows}
    </table>
  </div>
  <div style="margin-bottom:16px;">
    <div style="font-size:9px;font-weight:700;letter-spacing:0.1em;color:#0f3460;
                margin-bottom:8px;padding-bottom:5px;border-bottom:2px solid #0f3460;">
      제조 순서</div>
    {steps_html}
    <div style="font-size:8px;color:#e65100;padding:6px 8px;background:#fff8f0;
                border-radius:4px;margin-top:8px;">{COUPANG_DISCLAIMER}</div>
  </div>
  <div style="font-size:10px;color:#555;">
    <b>CEEI {ceei} [{ceei_grade}]</b> · PM2.5 {air.get('pm25','-')}㎍/m³ ·
    {'에어코리아 실측' if not is_mock else '모의데이터'} · {ceei_msg}
  </div>
</div>
<div class="footer">
  <span>본 주문서는 AI 분석 기반이며 의료적 처방이 아닙니다. 특허 출원 중.</span>
  <span>YD Lab · 재능대학교 · 남정훈 교수</span>
</div>
</body></html>"""


# ── HTML 생성 (두피 주문서) ───────────────────────────
def generate_scalp_order_html(result, air, region, residence_years,
                               participant_id, age_group, gender, mixing=None):
    code       = "YDL-SCALP-" + datetime.now().strftime("%Y%m%d") + "-" + \
                 ''.join(random.choices(string.ascii_uppercase+string.digits, k=4))
    overall    = result.get("overall_score", 0)
    scalp_type = result.get("scalp_type", "")
    ings       = result.get("recommended_ingredients", [])
    pm25_avg   = REGION_PM25_AVG.get(region, 22.0)
    ceei, ceei_grade, _, ceei_msg = calc_ceei(pm25_avg, residence_years)
    is_mock    = air.get("mock", True)
    total_ml   = mixing["total_ml"] if mixing else 20

    scalp_purpose_map = {
        "징크피리치온":    "두피 항균·비듬 억제",
        "살리실산":        "두피 각질 용해",
        "바이오틴":        "모발 강화·성장 촉진",
        "판테놀 (두피용)": "두피 진정·보습",
        "나이아신아마이드":"두피 피지 조절·진정",
        "비타민C":         "두피 항산화",
        "비타민C 유도체":  "두피 항산화·안정형",
        "히알루론산":      "두피 수분 공급",
        "세라마이드":      "두피 장벽 강화",
    }

    # ✅ 수정 6: 두피 주문서 성분 테이블 행
    ing_rows_parts = []
    for idx, ing in enumerate(ings):
        conc, note = get_concentration(ing, scalp_type)
        purpose    = scalp_purpose_map.get(ing, "두피·모발 상태 개선")
        cp_btn     = _cp_buy_btn(ing)
        ratio_val  = mixing["ratios"].get(ing, "-") if mixing else "-"
        ml_val     = mixing["ml"].get(ing, "-") if mixing else "-"
        bg = "#f0faf4" if idx % 2 == 0 else "white"
        ing_rows_parts.append(
            f"<tr style='background:{bg}'>"
            f"<td style='padding:8px;border:1px solid #a5d6a7;text-align:center;"
            f"font-weight:600;color:#1b5e20;'>{idx+1}</td>"
            f"<td style='padding:8px;border:1px solid #a5d6a7;font-weight:700;'>{ing}</td>"
            f"<td style='padding:8px;border:1px solid #a5d6a7;color:#555;'>{purpose}</td>"
            f"<td style='padding:8px;border:1px solid #a5d6a7;font-weight:600;"
            f"color:#1565c0;'>{ratio_val}% ({ml_val}ml)</td>"
            f"<td style='padding:8px;border:1px solid #a5d6a7;color:#1b5e20;"
            f"font-family:monospace;'>{conc}</td>"
            f"<td style='padding:8px;border:1px solid #a5d6a7;'>{cp_btn}</td>"
            f"<td style='padding:8px;border:1px solid #a5d6a7;color:#888;"
            f"font-size:9px;'>{note}</td></tr>"
        )
    ing_rows = "".join(ing_rows_parts)

    steps_html_parts = []
    if mixing:
        for s in mixing["steps"]:
            items_str = " + ".join(s["items"])
            steps_html_parts.append(
                f"<div style='display:flex;align-items:center;gap:8px;"
                f"padding:5px 0;font-size:10px;border-bottom:1px solid #f0f0f0;'>"
                f"<span style='background:#1b5e20;color:white;border-radius:50%;"
                f"width:20px;height:20px;display:inline-flex;align-items:center;"
                f"justify-content:center;font-size:9px;font-weight:700;flex-shrink:0;'>"
                f"{s['step']}</span>"
                f"<span><b>{s['label']}</b> — {items_str}</span></div>"
            )
    steps_html = "".join(steps_html_parts)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>YD Lab 두피 공방 주문서 {code}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Noto Sans KR',sans-serif;font-size:12px;color:#1a1a2e;background:white;}}
.header{{background:#1b5e20;color:white;padding:20px 30px;display:flex;
         justify-content:space-between;align-items:center;}}
.header h1{{font-size:18px;font-weight:700;}}
.body{{padding:22px 30px;}}
table{{width:100%;border-collapse:collapse;font-size:11px;}}
th{{background:#1b5e20;color:white;padding:8px;text-align:left;font-size:10px;}}
.footer{{background:#1b5e20;color:rgba(255,255,255,0.6);padding:10px 30px;
         font-size:8px;display:flex;justify-content:space-between;margin-top:16px;}}
.print-btn{{position:fixed;bottom:20px;right:20px;background:#1b5e20;color:white;
            border:none;padding:10px 18px;border-radius:8px;font-size:12px;cursor:pointer;}}
@media print{{.print-btn{{display:none;}}}}
</style></head><body>
<button class="print-btn" onclick="window.print()">🖨️ PDF 저장</button>
<div class="header">
  <div><h1>💆 YD Lab 두피 공방 주문서</h1>
  <div style="font-size:9px;opacity:0.6;margin-top:3px;">
    AI 두피 분석 기반 맞춤형 두피케어 제조 요청 · 재능대학교 AI-바이오분석특화연구소</div></div>
  <div style="font-family:monospace;background:rgba(255,255,255,0.15);
              padding:4px 10px;border-radius:4px;">{code}</div>
</div>
<div class="body">
  <div style="font-size:10px;color:#555;padding:10px 0;margin-bottom:14px;
              border-bottom:1px solid #a5d6a7;display:flex;gap:20px;flex-wrap:wrap;">
    <span><b>분석일:</b> {datetime.now().strftime("%Y년 %m월 %d일")}</span>
    <span><b>참여자:</b> {participant_id} {age_group} {gender}</span>
    <span><b>거주지:</b> {region} {residence_years}년</span>
    <span><b>두피타입:</b> {scalp_type}</span>
    <span><b>종합점수:</b> {overall}점</span>
    <span><b>총 제조량:</b> {total_ml}ml</span>
  </div>
  <div style="margin-bottom:16px;">
    <div style="font-size:9px;font-weight:700;letter-spacing:0.1em;color:#1b5e20;
                margin-bottom:8px;padding-bottom:5px;border-bottom:2px solid #1b5e20;">
      두피 성분 처방 · 혼합 비율 · 구매 링크</div>
    <table>
      <tr><th>#</th><th>성분명</th><th>목적</th><th>혼합비율</th>
          <th>권장농도</th><th>구매링크</th><th>제조참고</th></tr>
      {ing_rows}
    </table>
  </div>
  <div style="margin-bottom:16px;">
    <div style="font-size:9px;font-weight:700;letter-spacing:0.1em;color:#1b5e20;
                margin-bottom:8px;padding-bottom:5px;border-bottom:2px solid #1b5e20;">
      두피 제조 순서</div>
    {steps_html}
    <div style="font-size:8px;color:#e65100;padding:6px 8px;background:#fff8f0;
                border-radius:4px;margin-top:8px;">{COUPANG_DISCLAIMER}</div>
  </div>
  <div style="font-size:10px;color:#555;">
    <b>CEEI {ceei} [{ceei_grade}]</b> · PM2.5 {air.get('pm25','-')}㎍/m³ ·
    {'에어코리아 실측' if not is_mock else '모의데이터'} · {ceei_msg}
  </div>
</div>
<div class="footer">
  <span>본 주문서는 AI 분석 기반이며 의료적 처방이 아닙니다. 특허 출원 중.</span>
  <span>YD Lab · 재능대학교 · 남정훈 교수</span>
</div>
</body></html>"""


# ── 메인 ──────────────────────────────────────────────
def main():
    valid_codes = st.secrets.get("ACCESS_CODES",
                                  [st.secrets.get("ACCESS_PASSWORD", "YDLAB2025")])
    if isinstance(valid_codes, str):
        valid_codes = [valid_codes]

    if "authed" not in st.session_state:
        st.session_state["authed"] = False

    if not st.session_state["authed"]:
        url_code = st.query_params.get("code", "")
        if url_code and url_code in valid_codes:
            st.session_state["authed"] = True

    if not st.session_state["authed"]:
        st.markdown("""
<div class='hero'>
  <div class='hero-label'>YD Lab · 재능대학교 AI-바이오분석특화연구소</div>
  <h1>🔬 AI 피부·두피 분석</h1>
  <p>본 페이지는 접근 코드가 필요합니다.</p>
</div>""", unsafe_allow_html=True)
        gate_pw = st.text_input("접근 코드", type="password", key="k_gate")
        if st.button("입장", type="primary"):
            if gate_pw in valid_codes:
                st.session_state["authed"] = True
                st.rerun()
            else:
                st.error("접근 코드가 올바르지 않습니다.")
        st.stop()

    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        st.stop()

    st.markdown("""
<div class='hero'>
  <div class='hero-label'>YD Lab · 재능대학교 AI-바이오분석특화연구소</div>
  <h1>🔬 AI 피부·두피 분석</h1>
  <p>스마트폰 현미경 + 실시간 대기오염 데이터 + LLM 비전 AI<br>
     환경오염 연동 맞춤형 화장품 제안 시스템 (특허 출원 중)</p>
</div>""", unsafe_allow_html=True)

    st.markdown("<div class='card'><div class='card-label'>🎯 분석 모드 선택</div>",
                unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        skin_selected = st.button(
            "🧴 피부 분석\n\n피부 5지표\n주름·모공·피부결·피부톤·수분",
            use_container_width=True, key="k_mode_skin"
        )
    with col2:
        scalp_selected = st.button(
            "💆 두피 분석\n\n두피 6지표\n각질·모공·모발굵기·염증·수분밸런스·손상도",
            use_container_width=True, key="k_mode_scalp"
        )

    if skin_selected:
        st.session_state["analysis_mode"] = "skin"
    if scalp_selected:
        st.session_state["analysis_mode"] = "scalp"

    mode = st.session_state.get("analysis_mode", None)

    if mode == "skin":
        st.info("🧴 **피부 분석 모드** — 피부 5지표 분석 + 맞춤 혼합 비율 처방")
    elif mode == "scalp":
        st.info("💆 **두피 분석 모드** — 두피 6지표 분석 + 탈모 진행도 + 맞춤 혼합 비율 처방")
    else:
        st.warning("⬆️ 위에서 분석 모드를 먼저 선택해 주세요.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'><div class='card-label'>기본 정보 입력</div>",
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        participant_id = st.text_input("익명 참여 코드", placeholder="YD-001", key="k_pid")
    with c2:
        age_group = st.selectbox("연령대",
            ["선택","10대","20대","30대","40대","50대","60대 이상"], key="k_age")
    with c3:
        gender = st.selectbox("성별", ["선택","여성","남성","기타"], key="k_gender")
    c4, c5 = st.columns(2)
    with c4:
        region = st.selectbox("거주 지역", list(REGION_PM25_AVG.keys()), key="k_region")
    with c5:
        residence_years_str = st.selectbox("거주 기간",
            list(RESIDENCE_YEAR_MAP.keys()), key="k_residence")

    if mode == "skin":
        skin_concern = st.multiselect(
            "주요 피부 고민",
            ["주름·탄력","모공","피부톤·색소침착","수분·건조",
             "민감성·홍조","여드름·트러블","기타"], key="k_concern")
    else:
        skin_concern = st.multiselect(
            "주요 두피·모발 고민",
            ["두피 각질","두피 지루·피지","탈모·모발 가늘어짐",
             "두피 염증·홍조","비듬","두피 건조","모발 손상·끊김","기타"],
            key="k_concern")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'><div class='card-label'>촬영 부위 선택</div>",
                unsafe_allow_html=True)
    if mode == "skin":
        selected_parts = st.multiselect(
            "📍 촬영한 피부 부위 선택 (복수 가능)",
            SKIN_BODY_PARTS, key="k_parts")
    else:
        selected_parts = st.multiselect(
            "📍 촬영한 두피 부위 선택 (복수 가능)",
            SCALP_BODY_PARTS, key="k_parts")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'><div class='card-label'>"
                f"{'피부' if mode=='skin' else '두피'} 사진 업로드 (최대 3장)"
                "</div>", unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "사진 업로드 (최대 3장, JPG/PNG)",
        type=["jpg","jpeg","png"],
        accept_multiple_files=True, key="k_upload"
    )
    if uploaded:
        cols = st.columns(min(len(uploaded[:3]), 3))
        for i, f in enumerate(uploaded[:3]):
            with cols[i]:
                st.image(f, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='consent-box'>", unsafe_allow_html=True)
    consent = st.checkbox(
        "✅ [필수] 본 연구는 IRB 승인 후 연구담당자를 통해 별도 동의서를 작성합니다",
        key="k_consent")
    research_consent = st.checkbox(
        "🔬 [선택] 익명화된 데이터를 학술 연구에 활용하는 것에 동의합니다.",
        key="k_research")
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("📧 결과 알림 수신 동의 (선택)", expanded=False):
        marketing_opt_in = st.checkbox(
            "SKIN-X 플랫폼 정식 출시 시 안내를 받겠습니다.", key="k_marketing")
        marketing_email = ""
        if marketing_opt_in:
            marketing_email = st.text_input("이메일 주소", key="k_marketing_email")

    st.markdown("<br>", unsafe_allow_html=True)
    btn_label = ("🧴 피부 AI 분석 시작" if mode == "skin" else "💆 두피 AI 분석 시작")
    run = st.button(btn_label, use_container_width=True, type="primary", key="k_run")

    if run:
        if not uploaded:
            st.error("사진을 업로드해 주세요."); st.stop()
        if not consent:
            st.error("IRB 동의 확인이 필요합니다."); st.stop()
        if not participant_id.strip():
            st.error("익명 참여 코드를 입력해 주세요."); st.stop()
        if age_group == "선택" or gender == "선택":
            st.warning("연령대와 성별을 선택해 주세요."); st.stop()
        if not selected_parts:
            st.warning("촬영 부위를 하나 이상 선택해 주세요."); st.stop()

        images = []
        for f in uploaded[:3]:
            try: images.append(Image.open(f).convert("RGB"))
            except: pass

        with st.spinner("🌡️ 실시간 대기오염 데이터 수집 중..."):
            air = fetch_air(region)

        spinner_msg = ("🧴 AI 피부 분석 중..." if mode == "skin"
                       else "💆 AI 두피 분석 중...")
        with st.spinner(spinner_msg + " (10~20초 소요)"):
            if mode == "skin":
                result = analyze_skin(images, api_key, selected_parts)
            else:
                result = analyze_scalp(images, api_key, selected_parts)

        if result is None:
            st.error("분석에 실패했습니다. 사진을 확인하고 다시 시도해 주세요.")
            st.stop()

        for k, v in {
            "result": result, "air": air, "region": region,
            "residence_years_str": residence_years_str,
            "participant_id": participant_id, "age_group": age_group,
            "gender": gender, "selected_parts": selected_parts,
            "skin_concern": skin_concern, "consent": consent,
            "research_consent": research_consent,
            "current_mode": mode,
        }.items():
            st.session_state[k] = v

        yrs      = RESIDENCE_YEAR_MAP.get(residence_years_str, 0)
        pm25_avg = REGION_PM25_AVG.get(region, 22.0)
        ceei, ceei_grade, _, _ = calc_ceei(pm25_avg, yrs)

        save_record({
            "timestamp":             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "participant_id":        participant_id,
            "age_group":             age_group,
            "gender":                gender,
            "region":                region,
            "residence_years":       yrs,
            "skin_concern":          ", ".join(skin_concern),
            "body_parts":            ", ".join(selected_parts),
            "photo_count":           len(images),
            "analysis_mode":         mode,
            "pm25":                  air.get("pm25",""),
            "pm10":                  air.get("pm10",""),
            "o3":                    air.get("o3",""),
            "no2":                   air.get("no2",""),
            "air_station":           air.get("station",""),
            "air_source":            "실측" if not air.get("mock") else "모의",
            "ceei_score":            ceei,
            "ceei_grade":            ceei_grade,
            "overall_score":         result.get("overall_score",""),
            "skin_type":             result.get("skin_type", result.get("scalp_type","")),
            "key_concerns":          ", ".join(result.get("key_concerns",[])),
            "recommended_ingredients": ", ".join(result.get("recommended_ingredients",[])),
            "wrinkle_score":         result.get("wrinkle_score",""),
            "pore_score":            result.get("pore_score",""),
            "texture_score":         result.get("texture_score",""),
            "tone_score":            result.get("tone_score",""),
            "moisture_score":        result.get("moisture_score",""),
            "scalp_keratin_score":   result.get("keratin_score",""),
            "scalp_pore_score":      result.get("pore_score",""),
            "scalp_hair_thickness_score": result.get("hair_thickness_score",""),
            "scalp_color_score":     result.get("scalp_color_score",""),
            "scalp_moisture_balance_score": result.get("moisture_balance_score",""),
            "scalp_hair_damage_score": result.get("hair_damage_score",""),
            "scalp_hair_loss_risk_score": result.get("hair_loss_risk_score",""),
            "scalp_comment":         result.get("summary",""),
            "consent":               consent,
            "research_consent":      research_consent,
            "marketing_opt_in":      marketing_opt_in,
        })

        if marketing_opt_in and marketing_email.strip():
            save_marketing_opt(participant_id, marketing_email.strip(), region)

    if "result" in st.session_state:
        st.success("✅ 분석 완료!")
        current_mode = st.session_state.get("current_mode", "skin")
        if current_mode == "skin":
            show_skin_result(
                st.session_state["result"], st.session_state["air"],
                st.session_state["region"], st.session_state["residence_years_str"],
                st.session_state["participant_id"], st.session_state["age_group"],
                st.session_state["gender"], st.session_state["selected_parts"],
            )
        else:
            show_scalp_result(
                st.session_state["result"], st.session_state["air"],
                st.session_state["region"], st.session_state["residence_years_str"],
                st.session_state["participant_id"], st.session_state["age_group"],
                st.session_state["gender"], st.session_state["selected_parts"],
            )

    with st.sidebar:
        st.markdown("### 🔐 관리자")
        admin_pw = st.text_input("관리자 비밀번호", type="password", key="k_admin")
        if admin_pw == st.secrets.get("ADMIN_PASSWORD", "ydlab2024"):
            st.success("✅ 관리자 모드")
            if DATA_FILE.exists():
                import pandas as pd
                df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
                st.markdown(f"**총 분석 건수:** {len(df)}건")
                if "analysis_mode" in df.columns:
                    st.markdown("**분석 모드 분포**")
                    st.bar_chart(df["analysis_mode"].value_counts())
                if len(df) > 0:
                    st.markdown("**피부 타입 분포**")
                    st.bar_chart(df["skin_type"].value_counts())
                    if "ceei_grade" in df.columns:
                        st.markdown("**CEEI 등급 분포**")
                        st.bar_chart(df["ceei_grade"].value_counts())
                    if "air_source" in df.columns:
                        real_c = (df["air_source"]=="실측").sum()
                        mock_c = (df["air_source"]=="모의").sum()
                        st.markdown(f"**대기데이터** — 실측:{real_c} / 모의:{mock_c}")
                st.download_button(
                    "📥 전체 데이터 CSV",
                    data=open(DATA_FILE,"rb").read(),
                    file_name=f"ydlab_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv", key="k_csv"
                )
            else:
                st.info("아직 수집된 데이터가 없습니다.")


if __name__ == "__main__":
    main()
