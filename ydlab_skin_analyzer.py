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

# ── 페이지 설정 ─────────────────────────────────────────────
st.set_page_config(
    page_title="YD Lab 피부·두피 분석",
    page_icon="🔬",
    layout="centered"
)

# ── 스타일 ──────────────────────────────────────────────────
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
.result-section { border-left:3px solid #0f3460; padding-left:1rem; margin-bottom:1rem; }
.result-title { font-size:0.82rem; font-weight:700; color:#0f3460; margin-bottom:0.3rem; }
.result-text  { font-size:0.84rem; color:#444; line-height:1.7; }
.ingredient-chip { display:inline-block; background:#eef2ff; color:#3730a3;
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
.scalp-card { background:#f0faf4; border:1px solid #a5d6a7; border-radius:12px;
              padding:1.2rem; margin-bottom:1rem; }
.ref-badge { display:inline-block; background:#f1f3f4; color:#444; border-radius:4px;
             padding:0.15rem 0.5rem; font-size:0.72rem; margin-left:0.3rem;
             font-family:'DM Mono',monospace; }
</style>
""", unsafe_allow_html=True)

# ── 상수 ────────────────────────────────────────────────────
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

BODY_PARTS = [
    "이마", "눈가", "볼", "코", "턱", "입가",
    "두피 (정수리)", "두피 (측두부)", "두피 (후두부)", "목", "손등"
]

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

# ── 유틸 함수 ────────────────────────────────────────────────
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

# ── AirKorea API ─────────────────────────────────────────────
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
                            station=station, mock=False)
            except Exception:
                continue
    return dict(pm25=random.randint(12,65), pm10=random.randint(18,85),
                o3=round(random.uniform(0.01,0.08),3),
                no2=round(random.uniform(0.01,0.05),3), mock=True)

# ── 분석 프롬프트 ────────────────────────────────────────────
ANALYSIS_PROMPT = """
당신은 피부과학 전문가입니다. 업로드된 피부 또는 두피 현미경(클로즈업) 사진을 분석하여
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
  "summary": "전반적 피부 상태 종합 설명 (100자 이내)",
  "key_concerns": ["주요 고민 1", "주요 고민 2"],
  "recommended_ingredients": ["성분1", "성분2", "성분3", "성분4"],
  "care_advice": "생활 관리 조언 (80자 이내)",
  "is_scalp": true 또는 false,
  "scalp_keratin_score": 두피이면 0~100 아니면 null,
  "scalp_pore_score": 두피이면 0~100 아니면 null,
  "scalp_hair_thickness_score": 두피이면 0~100 아니면 null,
  "scalp_comment": "두피 종합 상태 설명 (50자 이내)" 또는 null
}

점수 기준: 높을수록 좋음 (100=최상, 0=매우불량)
두피 판별: 모발·모공·각질이 보이면 is_scalp=true
두피 3지표:
  scalp_keratin_score = 각질 없을수록 높음
  scalp_pore_score = 모공 깨끗할수록 높음
  scalp_hair_thickness_score = 굵고 풍성할수록 높음
사진이 불명확해도 최대한 추정하여 응답하세요.
"""

# ── LLM 비전 분석 ────────────────────────────────────────────
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
        parts_str = ""
        if body_parts:
            parts_str = f"\n\n[촬영 부위]: {', '.join(body_parts)}"
            if any("두피" in p for p in body_parts):
                parts_str += "\n두피 부위 포함 — is_scalp=true로 설정하고 두피 3지표를 반드시 채우세요."
        content.append({"type": "text", "text": ANALYSIS_PROMPT + parts_str})
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1200,
            messages=[{"role": "user", "content": content}]
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        st.error(f"분석 오류: {e}")
        return None

# ── 데이터 저장 ──────────────────────────────────────────────
DATA_FILE = Path("ydlab_skin_data.csv")
FIELDS = [
    "timestamp","name","age_group","gender","region","residence_years",
    "skin_concern","body_parts","photo_count",
    "pm25","pm10","o3","no2","ceei_score","ceei_grade",
    "overall_score","skin_type","key_concerns","recommended_ingredients",
    "wrinkle_score","pore_score","texture_score","tone_score","moisture_score",
    "is_scalp","scalp_keratin_score","scalp_pore_score","scalp_hair_thickness_score",
    "scalp_comment","consent","research_consent"
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

# ── 결과 표시 ────────────────────────────────────────────────
def show_result(result, air, region, residence_years_str,
                name, age_group, gender, selected_parts):
    pm25_avg = REGION_PM25_AVG.get(region, 22.0)
    yrs      = RESIDENCE_YEAR_MAP.get(residence_years_str, 0)
    ceei, ceei_grade, ceei_chip, ceei_msg = calc_ceei(pm25_avg, yrs)
    pm25_val  = air.get("pm25")
    alert_msg = get_pollution_alert(pm25_val, ceei)
    overall   = result.get("overall_score", 0)
    skin_type = result.get("skin_type", "")
    is_scalp  = result.get("is_scalp", False)
    sc = lambda s: "#2e7d32" if s>=70 else "#e65100" if s>=40 else "#c62828"

    st.markdown(
        "<div class='patent-banner'>"
        "🔐 본 기술은 특허 출원 중입니다 — 환경오염 연동 AI 피부·두피 분석 및 화장품 제안 시스템"
        "</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='card'>
      <div class='card-label'>종합 분석 결과</div>
      <div style='display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;'>
        <div style='text-align:center;'>
          <div style='font-size:3.5rem;font-weight:700;color:{sc(overall)};line-height:1;
                      font-family:"DM Mono",monospace;'>{overall}</div>
          <div style='font-size:0.72rem;color:#888;margin-top:0.3rem;'>종합 점수</div>
        </div>
        <div>
          <div style='font-size:1rem;font-weight:700;margin-bottom:0.4rem;'>피부 타입: {skin_type}</div>
          <div style='font-size:0.84rem;color:#555;line-height:1.7;'>{result.get("summary","")}</div>
          <div style='margin-top:0.5rem;'>{pm25_chip(pm25_val)} {ceei_chip}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if alert_msg:
        st.warning(alert_msg)

    # 피부 5지표
    metrics = [
        ("주름",   result.get("wrinkle_score",0),  result.get("wrinkle_comment","")),
        ("모공",   result.get("pore_score",0),      result.get("pore_comment","")),
        ("피부결", result.get("texture_score",0),   result.get("texture_comment","")),
        ("피부톤", result.get("tone_score",0),       result.get("tone_comment","")),
        ("수분",   result.get("moisture_score",0),  ""),
    ]
    cols = st.columns(5)
    for i, (lbl, val, cmt) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class='score-box'>
              <div class='score-num' style='color:{sc(val)};'>{val}</div>
              <div class='score-lbl'>{lbl}</div>
              <div style='font-size:0.68rem;color:#999;margin-top:0.3rem;line-height:1.3;'>{cmt}</div>
            </div>
            """, unsafe_allow_html=True)

    # 두피 3지표
    if is_scalp:
        sk = result.get("scalp_keratin_score")
        sp = result.get("scalp_pore_score")
        sh = result.get("scalp_hair_thickness_score")
        sc_comment = result.get("scalp_comment","")
        st.markdown("<div class='scalp-card'>", unsafe_allow_html=True)
        st.markdown("**🌿 두피 분석 결과 (3지표)**")
        s_cols = st.columns(3)
        for i, (lbl, val, desc) in enumerate([
            ("각질 상태", sk, "각질 분포·두께"),
            ("모공·피지", sp, "모공 상태·피지 분비"),
            ("모발 굵기·밀도", sh, "모발 굵기·풍성함"),
        ]):
            v = val if isinstance(val, int) else 0
            with s_cols[i]:
                st.markdown(f"""
                <div class='score-box' style='background:#f0faf4;border-color:#a5d6a7;'>
                  <div class='score-num' style='color:{sc(v)};'>{val if val is not None else "-"}</div>
                  <div class='score-lbl'>{lbl}</div>
                  <div style='font-size:0.68rem;color:#999;margin-top:0.3rem;'>{desc}</div>
                </div>
                """, unsafe_allow_html=True)
        if sc_comment:
            st.markdown(
                f"<div style='font-size:0.83rem;color:#2e7d32;margin-top:0.7rem;"
                f"padding:0.6rem;background:#e8f5e9;border-radius:6px;'>{sc_comment}</div>",
                unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 추천 성분
    ingredients = result.get("recommended_ingredients", [])
    ing_html = "".join([f"<span class='ingredient-chip'>{i}</span>" for i in ingredients])
    st.markdown(f"""
    <div class='card'>
      <div class='card-label'>AI 추천 화장품 성분</div>
      <div style='margin-bottom:0.8rem;'>{ing_html}</div>
      <div class='result-text'>{result.get("care_advice","")}</div>
    </div>
    """, unsafe_allow_html=True)

    # CEEI
    st.markdown(f"""
    <div class='card'>
      <div class='card-label'>CEEI — 누적 환경 노출 지수</div>
      <div style='display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.7rem;'>
        {pm25_chip(pm25_val)} {ceei_chip}
        <span class='chip chip-neu'>지역 연평균 PM2.5 {pm25_avg}㎍/m³</span>
        <span class='chip chip-neu'>거주 {yrs}년</span>
      </div>
      <div class='result-text'>{ceei_msg}</div>
    </div>
    """, unsafe_allow_html=True)

    # 우선 개선 항목
    scores_dict = {
        "주름": result.get("wrinkle_score",0),
        "모공": result.get("pore_score",0),
        "피부결": result.get("texture_score",0),
        "피부톤": result.get("tone_score",0),
        "수분": result.get("moisture_score",0),
    }
    if is_scalp:
        if result.get("scalp_keratin_score") is not None:
            scores_dict["두피 각질"] = result.get("scalp_keratin_score",0)
        if result.get("scalp_pore_score") is not None:
            scores_dict["두피 모공"] = result.get("scalp_pore_score",0)
        if result.get("scalp_hair_thickness_score") is not None:
            scores_dict["모발 굵기"] = result.get("scalp_hair_thickness_score",0)

    priority = sorted(scores_dict.items(), key=lambda x: x[1])[:3]
    priority_html = ""
    for i, (lbl, score) in enumerate(priority):
        color = "#c62828" if score<40 else "#e65100" if score<60 else "#2e7d32"
        priority_html += f"""
        <div style='display:flex;align-items:center;gap:0.8rem;padding:0.6rem 0;
                    border-bottom:1px solid #f0f0f0;'>
          <span style='background:#0f3460;color:white;border-radius:50%;width:22px;height:22px;
                       display:inline-flex;align-items:center;justify-content:center;
                       font-size:0.72rem;font-weight:700;min-width:22px;'>{i+1}</span>
          <span style='font-weight:600;flex:1;'>{lbl}</span>
          <span style='font-weight:700;color:{color};font-family:"DM Mono",monospace;'>{score}점</span>
          <span style='font-size:0.78rem;color:#888;'>
            {"집중 케어 필요" if score<40 else "개선 권장" if score<60 else "유지 관리"}
          </span>
        </div>"""
    st.markdown(f"""
    <div class='card'>
      <div class='card-label'>우선 개선 항목</div>
      {priority_html}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        pdf_html = generate_pdf_html(result, air, region, yrs, name, age_group, gender)
        st.download_button("📄 분석 리포트 다운로드",
                           data=pdf_html.encode("utf-8"),
                           file_name=f"YDLab_리포트_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                           mime="text/html", use_container_width=True, key="k_dl_report")
    with col2:
        order_html = generate_order_html(result, air, region, yrs, name, age_group, gender)
        st.download_button("🧪 공방 주문서 다운로드",
                           data=order_html.encode("utf-8"),
                           file_name=f"YDLab_주문서_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                           mime="text/html", use_container_width=True, key="k_dl_order")

# ── 공방 주문서 HTML ─────────────────────────────────────────
def generate_order_html(result, air, region, residence_years, name, age_group, gender):
    code = "YDL-" + datetime.now().strftime("%Y%m%d") + "-" + \
           ''.join(random.choices(string.ascii_uppercase+string.digits, k=4))
    overall    = result.get("overall_score",0)
    skin_type  = result.get("skin_type","")
    summary    = result.get("summary","")
    care       = result.get("care_advice","")
    ingredients= result.get("recommended_ingredients",[])
    pm25       = air.get("pm25","-")
    station    = air.get("station","인천")
    is_scalp   = result.get("is_scalp",False)

    scores = {"주름":result.get("wrinkle_score",0),"모공":result.get("pore_score",0),
              "피부결":result.get("texture_score",0),"피부톤":result.get("tone_score",0),
              "수분":result.get("moisture_score",0)}
    if is_scalp:
        if result.get("scalp_keratin_score") is not None:
            scores["두피 각질"] = result.get("scalp_keratin_score",0)
        if result.get("scalp_pore_score") is not None:
            scores["두피 모공"] = result.get("scalp_pore_score",0)
        if result.get("scalp_hair_thickness_score") is not None:
            scores["모발 굵기"] = result.get("scalp_hair_thickness_score",0)

    priority = sorted(scores.items(), key=lambda x: x[1])
    pm25_avg = REGION_PM25_AVG.get(region, 22.0)
    ceei, ceei_grade, _, ceei_msg = calc_ceei(pm25_avg, residence_years)
    alert_msg = get_pollution_alert(pm25, ceei)

    ing_purpose_map = {
        "히알루론산":"즉각 수분 공급·보습","세라마이드":"피부 장벽 강화",
        "나이아신아마이드":"피부톤 균일화·모공 관리","레티놀":"주름 개선·탄력",
        "비타민C":"항산화·피부톤 개선","비타민C 유도체":"항산화·안정형",
        "펩타이드":"탄력·항노화","판테놀":"진정·보습",
        "AHA":"각질 제거·피부결 개선","BHA":"모공 각질 용해",
        "아데노신":"주름 개선(식약처 고시)","EGF":"세포 재생·탄력",
        "징크피리치온":"두피 항균·비듬 억제","살리실산":"두피 각질 용해",
        "바이오틴":"모발 강화·성장","판테놀 (두피용)":"두피 진정·보습",
    }

    priority_rows = ""
    for i,(lbl,score) in enumerate(priority[:3]):
        color = "#c62828" if score<40 else "#e65100" if score<60 else "#2e7d32"
        priority_rows += (
            f"<tr><td style='padding:8px;border:1px solid #e4e8ee;font-weight:600;"
            f"color:#0f3460;'>{i+1}순위</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;'>{lbl}</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;font-weight:700;"
            f"color:{color};'>{score}점</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;color:#555;'>"
            f"{'집중 케어 필요' if score<40 else '개선 권장' if score<60 else '유지 관리'}"
            f"</td></tr>"
        )

    ing_rows = ""
    for i,ing in enumerate(ingredients):
        conc,note = get_concentration(ing, skin_type)
        purpose = ing_purpose_map.get(ing,"피부·두피 상태 개선")
        bg = "#f8faff" if i%2==0 else "white"
        ing_rows += (
            f"<tr style='background:{bg}'>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;text-align:center;"
            f"font-weight:600;color:#0f3460;'>{i+1}</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;font-weight:700;'>{ing}</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;color:#555;'>{purpose}</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;font-weight:600;"
            f"color:#0f3460;font-family:monospace;'>{conc}</td>"
            f"<td style='padding:8px;border:1px solid #e4e8ee;color:#888;"
            f"font-size:9px;'>{note}</td></tr>"
        )

    scalp_section = ""
    if is_scalp:
        sk=result.get("scalp_keratin_score","-")
        sp=result.get("scalp_pore_score","-")
        sh=result.get("scalp_hair_thickness_score","-")
        sc_cmt=result.get("scalp_comment","")
        scalp_section = (
            f"<div class='section'><div class='stitle'>두피 분석 결과 (3지표)</div>"
            f"<div class='score-row'>"
            f"<div class='sbox'><div class='snum'>{sk}</div><div class='slbl'>각질 상태</div></div>"
            f"<div class='sbox'><div class='snum'>{sp}</div><div class='slbl'>모공·피지</div></div>"
            f"<div class='sbox'><div class='snum'>{sh}</div><div class='slbl'>모발 굵기</div></div>"
            f"</div><div style='font-size:10px;color:#2e7d32;padding:6px 8px;"
            f"background:#e8f5e9;border-radius:4px;margin-top:6px;'>{sc_cmt}</div></div>"
        )

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>YD Lab 공방 주문서 {code}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Noto Sans KR',sans-serif;font-size:12px;color:#1a1a2e;background:white;}}
.header{{background:#0f3460;color:white;padding:20px 30px;display:flex;justify-content:space-between;align-items:center;}}
.header h1{{font-size:18px;font-weight:700;}}.header .sub{{font-size:9px;opacity:0.6;margin-top:3px;}}
.header .code{{font-size:13px;font-family:monospace;background:rgba(255,255,255,0.15);padding:4px 10px;border-radius:4px;}}
.body{{padding:22px 30px;}}.section{{margin-bottom:18px;}}
.stitle{{font-size:9px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
         color:#0f3460;margin-bottom:8px;padding-bottom:6px;border-bottom:2px solid #0f3460;}}
.infobar{{display:flex;gap:20px;font-size:10px;color:#444;padding:10px 0;
          border-bottom:1px solid #e4e8ee;margin-bottom:14px;flex-wrap:wrap;}}
.infobar span strong{{color:#0f3460;}}
table{{width:100%;border-collapse:collapse;font-size:11px;}}
th{{background:#0f3460;color:white;padding:8px;text-align:left;font-size:10px;}}
.score-row{{display:flex;gap:10px;margin-bottom:10px;flex-wrap:wrap;}}
.sbox{{flex:1;min-width:70px;background:#f8f9fa;border:1px solid #e4e8ee;
       border-radius:6px;padding:8px;text-align:center;}}
.snum{{font-size:22px;font-weight:700;line-height:1;}}
.slbl{{font-size:9px;color:#666;margin-top:2px;}}
.alert{{background:#fff3e0;border-left:3px solid #e65100;padding:8px 12px;
        font-size:10px;color:#e65100;margin-top:8px;}}
.footer{{background:#0f3460;color:rgba(255,255,255,0.6);padding:10px 30px;
         font-size:8px;display:flex;justify-content:space-between;margin-top:16px;}}
.print-btn{{position:fixed;bottom:20px;right:20px;background:#0f3460;color:white;
            border:none;padding:10px 18px;border-radius:8px;font-size:12px;cursor:pointer;}}
@media print{{.print-btn{{display:none;}}}}
</style></head><body>
<button class="print-btn" onclick="window.print()">🖨️ PDF 저장</button>
<div class="header">
  <div><h1>🧪 YD Lab 공방 주문서</h1>
  <div class="sub">AI 피부·두피 분석 기반 맞춤형 화장품 제조 요청 · 재능대학교 AI-바이오분석특화연구소</div></div>
  <div class="code">{code}</div>
</div>
<div class="body">
<div class="infobar">
  <span><strong>분석일:</strong> {datetime.now().strftime("%Y년 %m월 %d일")}</span>
  <span><strong>고객:</strong> {name} {age_group} {gender}</span>
  <span><strong>거주지:</strong> {region} 거주 {residence_years}년</span>
  <span><strong>피부 타입:</strong> {skin_type}</span>
  <span><strong>종합 점수:</strong> {overall}점</span>
</div>
<div class="section"><div class="stitle">피부 분석 점수</div>
<div class="score-row">
{"".join([f'<div class="sbox"><div class="snum">{v}</div><div class="slbl">{k}</div></div>' for k,v in list(scores.items())[:5]])}
</div>
<div style='font-size:10px;color:#555;line-height:1.7;padding:8px;
            background:#f8f9fa;border-radius:6px;'>{summary}</div></div>
{scalp_section}
<div class="section"><div class="stitle">우선 개선 항목</div>
<table><tr><th>순위</th><th>지표</th><th>점수</th><th>케어 방향</th></tr>
{priority_rows}</table></div>
<div class="section"><div class="stitle">AI 추천 화장품 성분</div>
<table>
<tr><th style='width:5%'>#</th><th style='width:18%'>성분명</th>
<th style='width:30%'>목적</th><th style='width:15%'>권장 농도</th><th>제조 참고사항</th></tr>
{ing_rows}</table></div>
<div class="section"><div class="stitle">환경 요인 (CEEI)</div>
<div style='font-size:10px;color:#555;margin-bottom:6px;'>
PM2.5 {pm25}㎍/m³ ({station}) · CEEI {ceei} [{ceei_grade}] · {region} 거주 {residence_years}년 · 연평균 {pm25_avg}㎍/m³
</div>
<div style='font-size:10px;color:#555;'>{ceei_msg}</div>
{f'<div class="alert">{alert_msg}</div>' if alert_msg else ''}
</div>
<div class="section"><div class="stitle">생활 관리 조언</div>
<div style='font-size:10px;color:#555;line-height:1.7;'>{care}</div></div>
</div>
<div class="footer">
  <span>본 주문서는 AI 분석 결과 기반이며 의료적 처방이 아닙니다. 특허 출원 중.</span>
  <span>YD Lab · 재능대학교 바이오테크과 · 개발: 남정훈 교수</span>
</div></body></html>"""


# ── PDF 리포트 HTML ──────────────────────────────────────────
def generate_pdf_html(result, air, region, residence_years, name, age_group, gender):
    overall    = result.get("overall_score",0)
    skin_type  = result.get("skin_type","")
    summary    = result.get("summary","")
    care       = result.get("care_advice","")
    ingredients= result.get("recommended_ingredients",[])
    is_scalp   = result.get("is_scalp",False)
    pm25=air.get("pm25","-"); pm10=air.get("pm10","-")
    o3=air.get("o3","-");     no2=air.get("no2","-")
    sc = lambda s: "#2e7d32" if s>=70 else "#e65100" if s>=40 else "#c62828"
    metrics = [
        ("주름",  result.get("wrinkle_score",0),  result.get("wrinkle_comment","")),
        ("모공",  result.get("pore_score",0),      result.get("pore_comment","")),
        ("피부결",result.get("texture_score",0),   result.get("texture_comment","")),
        ("피부톤",result.get("tone_score",0),       result.get("tone_comment","")),
        ("수분",  result.get("moisture_score",0),  ""),
    ]
    score_boxes = "".join([
        f"<div class='sbox'><div class='snum' style='color:{sc(v)}'>{v}</div>"
        f"<div class='slbl'>{l}</div><div class='scmt'>{c}</div></div>"
        for l,v,c in metrics
    ])
    ing_html = "".join([f"<span class='ing'>{i}</span>" for i in ingredients])

    scalp_section = ""
    if is_scalp:
        sk=result.get("scalp_keratin_score","-")
        sp=result.get("scalp_pore_score","-")
        sh=result.get("scalp_hair_thickness_score","-")
        sc_cmt=result.get("scalp_comment","")
        scalp_section = (
            f"<div class='section'><div class='stitle'>두피 분석 (3지표)</div>"
            f"<div class='score-row'>"
            f"<div class='sbox' style='background:#f0faf4;border-color:#a5d6a7;'>"
            f"<div class='snum'>{sk}</div><div class='slbl'>각질 상태</div></div>"
            f"<div class='sbox' style='background:#f0faf4;border-color:#a5d6a7;'>"
            f"<div class='snum'>{sp}</div><div class='slbl'>모공·피지</div></div>"
            f"<div class='sbox' style='background:#f0faf4;border-color:#a5d6a7;'>"
            f"<div class='snum'>{sh}</div><div class='slbl'>모발 굵기</div></div>"
            f"</div><div style='font-size:9px;color:#2e7d32;padding:5px 8px;"
            f"background:#e8f5e9;border-radius:4px;margin-top:5px;'>{sc_cmt}</div></div>"
        )

    pm25_avg = REGION_PM25_AVG.get(region, 22.0)
    ceei, ceei_grade, _, ceei_msg = calc_ceei(pm25_avg, residence_years)
    gc = {"낮음":"#2e7d32","보통":"#1565c0","높음":"#e65100","매우높음":"#c62828"}.get(ceei_grade,"#333")

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>YD Lab 피부·두피 분석 리포트</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Noto Sans KR',sans-serif;font-size:12px;color:#1a1a2e;background:white;}}
.header{{background:#0f3460;color:white;padding:22px 30px;display:flex;
         justify-content:space-between;align-items:center;}}
.header h1{{font-size:18px;font-weight:700;}}
.header .sub{{font-size:9px;opacity:0.6;margin-top:3px;}}
.header .date{{font-size:10px;opacity:0.75;}}
.body{{padding:22px 30px;}}
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
.small{{font-size:9px;color:#555;line-height:1.6;}}
.footer{{background:#0f3460;color:rgba(255,255,255,0.6);padding:10px 30px;
         font-size:8px;display:flex;justify-content:space-between;margin-top:10px;}}
.print-btn{{position:fixed;bottom:20px;right:20px;background:#0f3460;color:white;
            border:none;padding:10px 20px;border-radius:8px;font-size:13px;cursor:pointer;}}
@media print{{.print-btn{{display:none;}}}}
</style></head><body>
<button class="print-btn" onclick="window.print()">🖨️ PDF로 저장</button>
<div class="header">
  <div><h1>🔬 YD Lab 피부·두피 분석 리포트</h1>
  <div class="sub">재능대학교 바이오테크과 · AI 바이오분석특화연구소 · 특허 출원 중</div></div>
  <div class="date">{datetime.now().strftime("%Y년 %m월 %d일")}</div>
</div>
<div class="body">
<div class="infobar">
  <span>이름: {name}</span><span>연령대: {age_group}</span>
  <span>성별: {gender}</span><span>거주지: {region}</span>
  <span>거주기간: {residence_years}년</span>
</div>
<div class="section"><div class="stitle">종합 결과</div>
<div class="overall-row"><div class="big-score">{overall}</div>
<div><div class="skin-type">피부 타입: {skin_type}</div>
<div class="summary">{summary}</div></div></div></div>
<div class="section"><div class="stitle">세부 지표 (피부 5지표)</div>
<div class="score-row">{score_boxes}</div></div>
{scalp_section}
<div class="section"><div class="stitle">추천 화장품 성분</div>
<div class="ing-row">{ing_html}</div>
<div class="care">{care}</div></div>
<div class="section"><div class="stitle">환경 지수 (실시간)</div>
<div class="chip-row">
  <span class="chip">PM2.5 {pm25}㎍/m³</span>
  <span class="chip">PM10 {pm10}㎍/m³</span>
  <span class="chip">O₃ {o3}ppm</span>
  <span class="chip">NO₂ {no2}ppm</span>
</div></div>
<div class="section"><div class="stitle">CEEI 누적 환경 노출 지수</div>
<div class="chip-row">
  <span class="chip" style="background:#{'fce4ec' if ceei>=300 else 'fff3e0' if ceei>=150 else 'e8f5e9'};
        color:{gc};">CEEI {ceei} [{ceei_grade}]</span>
  <span class="chip">지역 연평균 {pm25_avg}㎍/m³</span>
  <span class="chip">거주 {residence_years}년</span>
</div>
<div class="small">{ceei_msg}</div></div>
</div>
<div class="footer">
  <span>본 리포트는 연구 참고용이며 의료적 진단을 대체하지 않습니다. 특허 출원 중.</span>
  <div style="text-align:right;">
    <div>YD Lab · 재능대학교 바이오테크과</div>
    <div style="opacity:0.7;margin-top:2px;">개발: 남정훈 교수 · Dept. of Biotechnology, Jaeneung Univ.</div>
  </div>
</div></body></html>"""


# ── 메인 앱 ─────────────────────────────────────────────────
def main():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error("⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        st.stop()

    # ── 히어로
    st.markdown("""
    <div class='hero'>
      <div class='hero-label'>YD Lab · 재능대학교 AI-바이오분석특화연구소</div>
      <h1>🔬 AI 피부·두피 분석</h1>
      <p>스마트폰 현미경 + 실시간 대기오염 데이터 + LLM 비전 AI<br>
         환경오염 연동 맞춤형 화장품 제안 시스템 (특허 출원 중)</p>
    </div>
    """, unsafe_allow_html=True)

    # ── 연구 배경 (보강된 버전)
    with st.expander("📚 연구 배경 및 과학적 근거", expanded=False):
        st.markdown("""
### 🌫️ 대기오염과 피부·두피의 과학적 연관성

세계보건기구(WHO)에 따르면 전 세계 인구의 99%가 WHO 기준을 초과하는 대기오염에 노출되어 있습니다.
피부는 인체에서 대기오염 물질과 가장 먼저 접촉하는 기관으로, 최근 국제 저명 학술지에서
PM2.5·NO₂·오존과 피부·두피 손상의 직접적 연관성이 잇따라 보고되고 있습니다.

---

#### 📄 피부 노화·주름·장벽 손상

| 연구 기관 / 저널 | 핵심 발견 | 출처 |
|---|---|---|
| **Nature Scientific Reports** | 실내 PM2.5 노출이 중국인 여성 피부 노화 징후(주름·색소침착)와 유의미한 상관관계 확인 | Ding et al., 2017 |
| **NIH / PMC (Journal of Investigative Dermatology)** | PM2.5 노출 시 경표피수분손실(TEWL) 증가 및 피부 장벽 기능 저하 직접 확인 | PMC8021104, 2021 |
| **ScienceDirect (Ecotoxicology & Environmental Safety)** | PM2.5가 세포 노화를 가속화해 피부·장기 기능 저하 유발, 산화스트레스 경로 규명 | Wang et al., 2024 |
| **NIH / PMC (Antioxidants)** | PM 노출이 아토피피부염·건선·여드름·피부 노화를 악화시키는 분자적 기전 종합 정리 | PMC11432173, 2024 |
| **Springer (Particle and Fibre Toxicology)** | 미세먼지(PM)가 피부 장벽 기능장애를 유발하고 반응성 산소종(ROS) 생성 촉진 | Springer, 2020 |

---

#### 📄 두피·탈모

| 연구 기관 / 저널 | 핵심 발견 | 출처 |
|---|---|---|
| **NIH / PMC (Int. J. Environmental Research)** | 대기오염 물질(PM·중금속·VOC)이 모낭 염증 반응 유발, 원형탈모(AA)와 연관 확인 | PMC11299971, 2024 |
| **Polish Journal of Environmental Studies** | 초미세먼지가 모발 손상·탈모·지루성 두피염·모낭 염증을 유발한다는 연구 결과 | PJOES, 2024 |
| **EurekAlert! / 국제학술발표** | 모낭 유두세포(HFDPC)를 PM2.5에 노출 시 모발 성장 관련 단백질(β-카테닌·Wnt) 현저히 감소 | EurekAlert, 2019 |
| **ResearchSquare (Preprint)** | PM2.5·PM10·NO₂ 단기 노출이 탈모 외래 방문 건수를 통계적으로 유의미하게 증가시킴 | ResearchSquare, 2025 |

---

#### 📄 NO₂·오존의 피부 산화 손상

| 연구 기관 / 저널 | 핵심 발견 | 출처 |
|---|---|---|
| **JAAD (J. of the American Academy of Dermatology)** | 오존 노출이 피부 산화스트레스를 유발하며, 항산화 세럼이 손상을 예방함을 임상 확인 | JAAD, 2020 |
| **NIH / PMC (Toxicology & Applied Pharmacology)** | O₃가 피부 세포막 지질 산화·단백질 손상을 유발하고 염증 반응을 촉진 | PMC, 2002 |
| **NIH / PMC (Dermatology Reviews)** | NO₂·SO₂·오존 복합 노출이 피부 염증성 질환(아토피·건선) 악화와 직접 연관 | PMC11965873, 2025 |

---

#### 🧮 CEEI (Cutaneous Environmental Exposure Index)

본 시스템이 독자적으로 개발한 환경 누적 노출 지수입니다.


$$CEEI = PM2.5_{지역연평균} \\times 거주년수$$

| CEEI 구간 | 등급 | 권장 케어 |
|---|---|---|
| 0 ~ 49 | 🟢 낮음 | 기본 보습·자외선 차단 |
| 50 ~ 149 | 🔵 보통 | 항산화 성분 정기 사용 |
| 150 ~ 299 | 🟠 높음 | 항산화·장벽강화 집중 케어 |
| 300 이상 | 🔴 매우높음 | 피부과 상담 + 기능성 화장품 |

> 본 연구는 공용IRB 면제심의 신청 예정이며, 수집 데이터는 학술 연구 목적으로만 활용됩니다.
        """)

    with st.expander("📷 촬영 가이드", expanded=False):
        st.markdown("""
        <div class='guide-body'>
          <div class='gstep'><span class='gnum'>1</span>
            <span>스마트폰에 클립온 현미경(50~200배)을 장착하세요.</span></div>
          <div class='gstep'><span class='gnum'>2</span>
            <span>아래 부위 선택 후, 각 부위를 밝은 곳에서 클로즈업 촬영하세요.</span></div>
          <div class='gstep'><span class='gnum'>3</span>
            <span>피부·모공이 선명하게 보이도록 초점을 맞추세요 (흔들리지 않게 고정).</span></div>
          <div class='gstep'><span class='gnum'>4</span>
            <span>두피 촬영 시: 모발을 가르마로 나누어 두피 표면이 잘 보이도록 하세요.</span></div>
          <div class='gstep'><span class='gnum'>5</span>
            <span>촬영한 사진 여러 장을 한꺼번에 업로드하시면 됩니다. 어느 부위인지 따로 표시하지 않아도 AI가 자동으로 판별합니다.</span></div>
        </div>
        """, unsafe_allow_html=True)

    # ── 기본 정보 입력
    st.markdown("<div class='card'><div class='card-label'>기본 정보 입력</div>",
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("이름 (익명 가능)", value="익명",
                             placeholder="홍길동", key="k_name")
    with c2:
        age_group = st.selectbox("연령대",
                                 ["선택","10대","20대","30대","40대","50대","60대 이상"],
                                 key="k_age")
    with c3:
        gender = st.selectbox("성별", ["선택","여성","남성","기타"], key="k_gender")

    c4, c5 = st.columns(2)
    with c4:
        region = st.selectbox("거주 지역", list(REGION_PM25_AVG.keys()), key="k_region")
    with c5:
        residence_years_str = st.selectbox("거주 기간",
                                           list(RESIDENCE_YEAR_MAP.keys()),
                                           key="k_residence")

    skin_concern = st.multiselect(
        "주요 피부·두피 고민 (복수 선택)",
        ["주름·탄력","모공","피부톤·색소침착","수분·건조",
         "민감성·홍조","여드름·트러블","탈모·두피 각질","두피 지루","기타"],
        key="k_concern"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── 촬영 부위 선택
    st.markdown("<div class='card'><div class='card-label'>촬영 부위 선택</div>",
                unsafe_allow_html=True)
    selected_parts = st.multiselect(
        "📍 촬영한 부위를 선택하세요 (복수 선택 가능)",
        BODY_PARTS, default=[], key="k_parts",
        help="두피 선택 시 두피 3지표(각질·모공·모발굵기)가 추가 분석됩니다."
    )
    if any("두피" in p for p in selected_parts):
        st.info("💡 두피 부위 선택됨 — 각질·모공·모발 굵기 3지표가 추가 분석됩니다.")
    st.markdown("</div>", unsafe_allow_html=True)

    # ── 사진 업로드 (부위 수만큼 자동 확장)
    max_photos = max(len(selected_parts), 3)
    st.markdown("<div class='card'><div class='card-label'>피부·두피 사진 업로드</div>",
                unsafe_allow_html=True)
    st.caption(f"💡 촬영한 사진을 한꺼번에 올리세요. 어느 부위인지 따로 표시하지 않아도 AI가 자동 판별합니다. (최대 {max_photos}장)")
    uploaded = st.file_uploader(
        f"사진 업로드 (최대 {max_photos}장)",
        type=["jpg","jpeg","png"],
        accept_multiple_files=True,
        key="k_upload"
    )
    if uploaded:
        show_count = min(len(uploaded), max_photos)
        cols = st.columns(min(show_count, 4))
        for i, f in enumerate(uploaded[:max_photos]):
            with cols[i % min(show_count, 4)]:
                st.image(f, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── 동의
    st.markdown("<div class='consent-box'>", unsafe_allow_html=True)
    consent = st.checkbox(
        "✅ [필수] 개인정보 수집·이용 동의: 분석 결과 및 환경 데이터가 서비스 개선 목적으로 저장됩니다.",
        key="k_consent"
    )
    research_consent = st.checkbox(
        "🔬 [선택] 연구 참여 동의: 익명화된 피부 이미지 및 환경 데이터를 학술 연구에 활용하는 것에 동의합니다.",
        key="k_research"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("🔬 AI 피부·두피 분석 시작",
                    use_container_width=True, type="primary", key="k_run")

    if run:
        if not uploaded:
            st.error("사진을 업로드해 주세요."); st.stop()
        if not consent:
            st.error("개인정보 수집·이용 동의가 필요합니다."); st.stop()
        if age_group == "선택" or gender == "선택":
            st.warning("연령대와 성별을 선택해 주세요."); st.stop()
        if not selected_parts:
            st.warning("촬영 부위를 하나 이상 선택해 주세요."); st.stop()

        images = []
        for f in uploaded[:max_photos]:
            try:
                images.append(Image.open(f).convert("RGB"))
            except Exception:
                pass

        with st.spinner("🌡️ 실시간 대기오염 데이터 수집 중..."):
            air = fetch_air(region)
            if air.get("mock"):
                st.caption("⚠️ AirKorea API 연결 실패 — Mock 데이터 사용 중")

        with st.spinner("🔬 AI 피부·두피 분석 중... (10~20초 소요)"):
            result = analyze_skin(images, api_key, selected_parts)

        if result is None:
            st.error("분석에 실패했습니다. 사진을 확인하고 다시 시도해 주세요.")
            st.stop()

        st.success("✅ 분석 완료!")
        show_result(result, air, region, residence_years_str,
                    name, age_group, gender, selected_parts)

        yrs      = RESIDENCE_YEAR_MAP.get(residence_years_str, 0)
        pm25_avg = REGION_PM25_AVG.get(region, 22.0)
        ceei, ceei_grade, _, _ = calc_ceei(pm25_avg, yrs)

        save_record({
            "timestamp":                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name":                       name,
            "age_group":                  age_group,
            "gender":                     gender,
            "region":                     region,
            "residence_years":            yrs,
            "skin_concern":               ", ".join(skin_concern),
            "body_parts":                 ", ".join(selected_parts),
            "photo_count":                len(images),
            "pm25":                       air.get("pm25",""),
            "pm10":                       air.get("pm10",""),
            "o3":                         air.get("o3",""),
            "no2":                        air.get("no2",""),
            "ceei_score":                 ceei,
            "ceei_grade":                 ceei_grade,
            "overall_score":              result.get("overall_score",""),
            "skin_type":                  result.get("skin_type",""),
            "key_concerns":               ", ".join(result.get("key_concerns",[])),
            "recommended_ingredients":    ", ".join(result.get("recommended_ingredients",[])),
            "wrinkle_score":              result.get("wrinkle_score",""),
            "pore_score":                 result.get("pore_score",""),
            "texture_score":              result.get("texture_score",""),
            "tone_score":                 result.get("tone_score",""),
            "moisture_score":             result.get("moisture_score",""),
            "is_scalp":                   result.get("is_scalp",False),
            "scalp_keratin_score":        result.get("scalp_keratin_score",""),
            "scalp_pore_score":           result.get("scalp_pore_score",""),
            "scalp_hair_thickness_score": result.get("scalp_hair_thickness_score",""),
            "scalp_comment":              result.get("scalp_comment",""),
            "consent":                    consent,
            "research_consent":           research_consent,
        })

    # ── 관리자 사이드바
    with st.sidebar:
        st.markdown("### 🔐 관리자")
        admin_pw = st.text_input("관리자 비밀번호", type="password", key="k_admin")
        if admin_pw == st.secrets.get("ADMIN_PASSWORD", "ydlab2024"):
            st.success("✅ 관리자 모드")
            if DATA_FILE.exists():
                import pandas as pd
                df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
                st.markdown(f"**총 분석 건수:** {len(df)}건")
                if len(df) > 0:
                    st.markdown("**피부 타입 분포**")
                    st.bar_chart(df["skin_type"].value_counts())
                    if "ceei_grade" in df.columns:
                        st.markdown("**CEEI 등급 분포**")
                        st.bar_chart(df["ceei_grade"].value_counts())
                    if "is_scalp" in df.columns:
                        st.metric("두피 분석 건수", f"{df['is_scalp'].sum()}건")
                    score_cols = ["overall_score","wrinkle_score","pore_score",
                                  "texture_score","tone_score","moisture_score"]
                    available = [c for c in score_cols if c in df.columns]
                    if available:
                        st.markdown("**평균 점수**")
                        st.dataframe(df[available].mean().round(1).rename("평균"))
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
