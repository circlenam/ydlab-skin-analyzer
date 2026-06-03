"""
YD Lab 피부분석 앱
─────────────────────────────────────────────────────────
설치: pip install streamlit anthropic pillow requests pandas
실행: streamlit run ydlab_skin_analyzer.py

secrets.toml (.streamlit/secrets.toml):
  ANTHROPIC_API_KEY = "sk-ant-..."
  AIRKOREA_API_KEY  = "..."   # 없으면 mock 데이터 사용
─────────────────────────────────────────────────────────
"""

import streamlit as st
import io as _io
import anthropic
import base64
import json
import re
import requests
import csv
import random
from datetime import datetime
from pathlib import Path
from PIL import Image
import io

# ── 페이지 설정 ─────────────────────────────────────────────
st.set_page_config(
    page_title="YD Lab 피부분석",
    page_icon="🔬",
    layout="centered"
)

# ── 스타일 ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

.hero {
    background: #0f3460; color: white;
    border-radius: 16px; padding: 2rem 1.8rem 1.6rem;
    margin-bottom: 1.4rem;
}
.hero-label { font-size:0.7rem; letter-spacing:0.18em; text-transform:uppercase;
              opacity:0.55; margin-bottom:0.5rem; font-family:'DM Mono',monospace; }
.hero h1 { font-size:1.55rem; font-weight:700; margin-bottom:0.4rem; }
.hero p  { font-size:0.82rem; opacity:0.6; }

.card { background:white; border-radius:12px; padding:1.4rem;
        margin-bottom:1rem; border:1px solid #e4e8ee; }
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

.cta-btn { display:block; text-align:center; background:#0f3460; color:white;
           padding:0.85rem; border-radius:10px; font-weight:700; font-size:0.9rem;
           text-decoration:none; margin-top:0.5rem; }

.consent-box { background:#f7f8fa; border-left:3px solid #0f3460;
               border-radius:0 8px 8px 0; padding:0.9rem 1rem;
               font-size:0.78rem; color:#555; line-height:1.75; }
.consent-box strong { color:#0f3460; }

.guide-body { background:#f0f4fa; border-radius:8px; padding:1rem;
              font-size:0.81rem; line-height:1.8; }
.gstep { display:flex; align-items:flex-start; gap:0.6rem; margin-bottom:0.35rem; }
.gnum  { background:#0f3460; color:white; border-radius:50%;
         width:20px; height:20px; min-width:20px;
         display:inline-flex; align-items:center; justify-content:center;
         font-size:0.7rem; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ── 유틸 ────────────────────────────────────────────────────
def img_to_b64(pil_img: Image.Image) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode()

def pm25_chip(v):
    if v is None: return "<span class='chip chip-neu'>PM2.5 -</span>"
    v = int(v)
    if v <= 15:  return f"<span class='chip chip-good'>PM2.5 좋음 {v}㎍/m³</span>"
    if v <= 35:  return f"<span class='chip chip-mid'>PM2.5 보통 {v}㎍/m³</span>"
    if v <= 75:  return f"<span class='chip chip-warn'>PM2.5 나쁨 {v}㎍/m³</span>"
    return f"<span class='chip chip-bad'>PM2.5 매우나쁨 {v}㎍/m³</span>"

STATION_MAP = {
    "인천": "인천", "부평구": "부평", "연수구": "연수", "남동구": "남동",
    "안산": "안산", "시흥": "시흥", "서울": "중구", "기타": None
}

@st.cache_data(ttl=3600)
def fetch_air(station: str) -> dict:
    """AirKorea API 또는 mock 반환"""
    try:
        key = st.secrets.get("AIRKOREA_API_KEY", "")
        if key:
            url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
            params = dict(serviceKey=key, stationName=station,
                          dataTerm="DAILY", pageNo=1, numOfRows=1,
                          returnType="json", ver="1.3")
            r = requests.get(url, params=params, timeout=5)
            item = r.json()["response"]["body"]["items"][0]
            return dict(pm25=item["pm25Value"], pm10=item["pm10Value"],
                        o3=item["o3Value"],   no2=item["no2Value"], mock=False)
    except Exception:
        pass
    return dict(pm25=random.randint(12, 65), pm10=random.randint(18, 85),
                o3=round(random.uniform(0.01, 0.08), 3),
                no2=round(random.uniform(0.01, 0.05), 3), mock=True)

# ── 분석 프롬프트 ────────────────────────────────────────────
ANALYSIS_PROMPT = """
당신은 피부과학 전문가입니다. 업로드된 피부 현미경(또는 클로즈업) 사진을 분석하여
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
  "recommended_ingredients": ["추천 성분 1", "추천 성분 2", "추천 성분 3", "추천 성분 4"],
  "care_advice": "생활 관리 조언 (80자 이내)"
}

점수 기준: 높을수록 좋음 (100 = 최상, 0 = 매우 불량)
사진이 불명확하거나 피부 사진이 아닌 경우에도 최대한 추정하여 응답하세요.
"""

def analyze_skin(images: list, api_key: str) -> dict | None:
    """Claude Vision으로 피부 분석"""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        content = []
        for img in images[:3]:  # 최대 3장
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg",
                           "data": img_to_b64(img)}
            })
        content.append({"type": "text", "text": ANALYSIS_PROMPT})

        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": content}]
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception as e:
        st.error(f"분석 오류: {e}")
        return None



def generate_pdf_html(result: dict, air: dict, region: str,
                      residence_years: int, name: str,
                      age_group: str, gender: str) -> str:
    """PDF 대신 인쇄용 HTML 반환 (브라우저 Ctrl+P → PDF 저장)"""
    from datetime import datetime as _dt

    overall    = result.get("overall_score", 0)
    skin_type  = result.get("skin_type", "")
    summary    = result.get("summary", "")
    care       = result.get("care_advice", "")
    ingredients= result.get("recommended_ingredients", [])
    metrics = [
        ("주름",   result.get("wrinkle_score",0),  result.get("wrinkle_comment","")),
        ("모공",   result.get("pore_score",0),      result.get("pore_comment","")),
        ("피부결", result.get("texture_score",0),   result.get("texture_comment","")),
        ("피부톤", result.get("tone_score",0),       result.get("tone_comment","")),
        ("수분",   result.get("moisture_score",0),  ""),
    ]
    pm25 = air.get("pm25","-"); pm10=air.get("pm10","-")
    o3   = air.get("o3","-");   no2 =air.get("no2","-")

    sc = lambda s: "#2e7d32" if s>=70 else "#e65100" if s>=40 else "#c62828"

    score_boxes = ""
    for lbl, val, cmt in metrics:
        score_boxes += f"""
        <div class="sbox">
          <div class="snum" style="color:{sc(val)}">{val}</div>
          <div class="slbl">{lbl}</div>
          <div class="scmt">{cmt}</div>
        </div>"""

    ing_html = "".join(f'<span class="ing">{i}</span>' for i in ingredients)

    exp_html = ""
    if residence_years > 0:
        avg = REGION_PM25_AVG.get(region, 22.0)
        idx, grade, _, msg = calc_exposure_index(avg, residence_years)
        gc = {"낮음":"#2e7d32","보통":"#1565c0","높음":"#e65100","매우높음":"#c62828"}.get(grade,"#333")
        exp_html = f"""
        <div class="section">
          <div class="stitle">누적 환경 노출 지수</div>
          <div class="chip-row">
            <span class="chip" style="background:#fff3e0;color:{gc}">누적 노출 {grade}</span>
            <span class="chip">지역 3년 평균 PM2.5 {avg}㎍/m³</span>
            <span class="chip">거주 {residence_years}년</span>
            <span class="chip">지수 {idx}</span>
          </div>
          <div class="small">{msg}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>YD Lab 피부분석 리포트</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Noto Sans KR',sans-serif;font-size:12px;color:#1a1a2e;background:white;padding:0;}}
.header{{background:#0f3460;color:white;padding:22px 30px;display:flex;justify-content:space-between;align-items:center;}}
.header h1{{font-size:18px;font-weight:700;}}
.header .sub{{font-size:9px;opacity:0.6;margin-top:3px;}}
.header .date{{font-size:10px;opacity:0.75;}}
.body{{padding:22px 30px;}}
.infobar{{font-size:10px;color:#555;padding-bottom:12px;margin-bottom:14px;border-bottom:1px solid #e4e8ee;}}
.infobar span{{margin-right:14px;}}
.section{{margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid #f0f0f0;}}
.stitle{{font-size:8px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#0f3460;margin-bottom:10px;}}
.overall-row{{display:flex;align-items:center;gap:18px;}}
.big-score{{font-size:44px;font-weight:700;color:{sc(overall)};line-height:1;}}
.skin-type{{font-size:13px;font-weight:600;margin-bottom:5px;}}
.summary{{font-size:9px;color:#555;line-height:1.65;}}
.score-row{{display:flex;gap:7px;}}
.sbox{{flex:1;background:#f8f9fa;border:1px solid #e4e8ee;border-radius:7px;padding:9px 5px;text-align:center;}}
.snum{{font-size:22px;font-weight:700;line-height:1.1;}}
.slbl{{font-size:8px;color:#666;margin-top:2px;}}
.scmt{{font-size:7px;color:#999;margin-top:3px;line-height:1.3;}}
.ing-row{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:7px;}}
.ing{{background:#eef2ff;color:#3730a3;border-radius:4px;padding:3px 9px;font-size:9px;font-weight:500;}}
.care{{font-size:9px;color:#555;line-height:1.6;}}
.chip-row{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:7px;}}
.chip{{background:#f1f3f4;color:#444;border-radius:12px;padding:2px 9px;font-size:9px;}}
.small{{font-size:9px;color:#555;line-height:1.6;}}
.footer{{background:#0f3460;color:rgba(255,255,255,0.6);padding:10px 30px;
         font-size:8px;display:flex;justify-content:space-between;margin-top:10px;}}
.print-btn{{position:fixed;bottom:20px;right:20px;background:#0f3460;color:white;
            border:none;padding:10px 20px;border-radius:8px;font-size:13px;
            font-family:'Noto Sans KR',sans-serif;cursor:pointer;z-index:999;}}
@media print{{ .print-btn{{display:none;}} }}
</style>
</head><body>
<button class="print-btn" onclick="window.print()">🖨️ PDF로 저장</button>
<script>window.onload=function(){{setTimeout(function(){{window.print();}},800);}}</script>
<div class="header">
  <div><h1>🔬 YD Lab 피부분석 리포트</h1>
  <div class="sub">재능대학교 바이오테크과 · AI 바이오분석특화연구소</div></div>
  <div class="date">{_dt.now().strftime("%Y년 %m월 %d일")}</div>
</div>
<div class="body">
  <div class="infobar">
    <span>이름: {name}</span><span>연령대: {age_group}</span>
    <span>성별: {gender}</span><span>거주지: {region}</span>
    <span>거주기간: {residence_years}년</span>
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
    <div class="stitle">세부 지표</div>
    <div class="score-row">{score_boxes}</div>
  </div>
  <div class="section">
    <div class="stitle">추천 화장품 성분</div>
    <div class="ing-row">{ing_html}</div>
    <div class="care">{care}</div>
  </div>
  <div class="section">
    <div class="stitle">환경 지수</div>
    <div class="chip-row">
      <span class="chip">PM2.5 {pm25}㎍/m³</span>
      <span class="chip">PM10 {pm10}㎍/m³</span>
      <span class="chip">O₃ {o3}ppm</span>
      <span class="chip">NO₂ {no2}ppm</span>
    </div>
  </div>
  {exp_html}
</div>
<div class="footer">
  <span>본 리포트는 연구 참고용이며 의료적 진단을 대체하지 않습니다.</span>
  <div style="text-align:right;"><div>YD Lab · 재능대학교 바이오테크과</div><div style="opacity:0.7;margin-top:2px;">개발: 남정훈 교수 · Dept. of Biotechnology, Jaeneung Univ.</div></div>
</div>
</body></html>"""


# ── 데이터 저장 ──────────────────────────────────────────────
DATA_FILE = Path("ydlab_skin_data.csv")
FIELDS = ["timestamp","name","age_group","gender","region","residence_years","skin_concern",
          "photo_count","pm25","pm10","o3","no2","exposure_index",
          "overall_score","skin_type","key_concerns","recommended_ingredients","consent"]

def save_record(r: dict):
    header = not DATA_FILE.exists()
    with open(DATA_FILE, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if header: w.writeheader()
        w.writerow({k: r.get(k, "") for k in FIELDS})

# ── 결과 화면 ────────────────────────────────────────────────
def calc_exposure_index(pm25_avg: float, years: int) -> tuple:
    index = round(pm25_avg * years, 1)
    if index < 50:   return index, "낮음",    "chip-good", "현재까지 환경 노출 영향은 낮은 편입니다."
    if index < 150:  return index, "보통",    "chip-mid",  "중등도의 누적 노출입니다. 항산화 관리를 권장합니다."
    if index < 300:  return index, "높음",    "chip-warn", "장기 노출로 피부 광노화 가속 가능성이 있습니다."
    return index, "매우높음", "chip-bad", "장기 고농도 노출입니다. 피부 장벽 강화와 정기 모니터링을 권장합니다."

REGION_PM25_AVG = {
    "인천": 22.4, "부평구": 23.1, "연수구": 21.8, "남동구": 24.2,
    "안산": 25.3, "시흥": 24.7, "서울": 20.1, "기타": 22.0
}

def show_result(result: dict, air: dict, region: str, pm25_val, residence_years: int = 0):
    st.markdown("---")
    st.markdown('<div class="card"><div class="card-label">분석 결과</div>', unsafe_allow_html=True)

    # 종합 점수 + 피부 타입
    col0, col1 = st.columns([1, 2])
    with col0:
        overall = result.get("overall_score", 0)
        color = "#2e7d32" if overall >= 70 else "#e65100" if overall >= 40 else "#c62828"
        st.markdown(f"""
        <div class='score-box'>
          <div class='score-num' style='color:{color}'>{overall}</div>
          <div class='score-lbl'>종합 점수</div>
        </div>
        <div style='text-align:center;margin-top:0.5rem;'>
          <span class='chip chip-mid'>{result.get("skin_type","")}</span>
        </div>
        """, unsafe_allow_html=True)
    with col1:
        st.markdown(f"""
        <div class='result-section'>
          <div class='result-title'>종합 소견</div>
          <div class='result-text'>{result.get("summary","")}</div>
        </div>
        """, unsafe_allow_html=True)

    # 5개 지표 점수
    st.markdown("<br>", unsafe_allow_html=True)
    metrics = [
        ("주름", "wrinkle_score", "wrinkle_comment"),
        ("모공", "pore_score",    "pore_comment"),
        ("피부결", "texture_score","texture_comment"),
        ("피부톤", "tone_score",   "tone_comment"),
        ("수분", "moisture_score", None),
    ]
    cols = st.columns(5)
    for i, (lbl, sk, ck) in enumerate(metrics):
        v = result.get(sk, 0)
        c = "#2e7d32" if v >= 70 else "#e65100" if v >= 40 else "#c62828"
        comment = result.get(ck, "") if ck else ""
        cols[i].markdown(f"""
        <div class='score-box'>
          <div class='score-num' style='color:{c};font-size:1.4rem'>{v}</div>
          <div class='score-lbl'>{lbl}</div>
          <div style='font-size:0.65rem;color:#999;margin-top:0.2rem;line-height:1.3'>{comment}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 추천 성분
    st.markdown('<div class="card"><div class="card-label">추천 화장품 성분</div>', unsafe_allow_html=True)
    ingredients = result.get("recommended_ingredients", [])
    chips = "".join(f"<span class='ingredient-chip'>{i}</span>" for i in ingredients)
    st.markdown(chips, unsafe_allow_html=True)
    st.markdown(f"""
    <div style='margin-top:0.8rem;font-size:0.82rem;color:#555;line-height:1.7;'>
      {result.get("care_advice","")}
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 환경 지수 연결 (방향 B)
    st.markdown('<div class="card"><div class="card-label">오늘의 환경 지수 × 피부</div>', unsafe_allow_html=True)
    pm25 = pm25_val
    env_msg = ""
    if pm25:
        pv = int(pm25)
        if pv > 75:
            env_msg = f"오늘 {region} PM2.5가 <b>{pv}㎍/m³(매우나쁨)</b>입니다. 외출 후 클렌징과 피부 장벽 강화에 특히 신경 쓰세요."
        elif pv > 35:
            env_msg = f"오늘 {region} PM2.5가 <b>{pv}㎍/m³(나쁨)</b>입니다. 항산화 성분이 포함된 제품 사용을 권장합니다."
        else:
            env_msg = f"오늘 {region} PM2.5가 <b>{pv}㎍/m³(보통~좋음)</b>입니다. 평소대로 관리하세요."

    chips_html = "".join([
        pm25_chip(air.get("pm25")),
        f"<span class='chip chip-neu'>PM10 {air.get('pm10')}㎍/m³</span>",
        f"<span class='chip chip-neu'>O₃ {air.get('o3')}ppm</span>",
        f"<span class='chip chip-neu'>NO₂ {air.get('no2')}ppm</span>",
    ])
    st.markdown(chips_html, unsafe_allow_html=True)
    if env_msg:
        st.markdown(f"<div style='margin-top:0.7rem;font-size:0.83rem;color:#444;line-height:1.7'>{env_msg}</div>",
                    unsafe_allow_html=True)
    if air.get("mock"):
        st.caption("※ 현재 샘플 데이터입니다. AirKorea API 키 연결 시 실수치로 업데이트됩니다.")


    # 누적 노출 지수 카드
    if residence_years > 0:
        pm25_avg = REGION_PM25_AVG.get(region, 22.0)
        exp_idx, exp_grade, exp_cls, exp_msg = calc_exposure_index(pm25_avg, residence_years)
        st.markdown(f"""
        <div style='margin-top:0.8rem;background:#f8f9fa;border-radius:10px;padding:1rem;border:1px solid #e4e8ee;'>
          <div style='font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;color:#0f3460;font-weight:700;margin-bottom:0.6rem;'>누적 환경 노출 지수</div>
          <div style='display:flex;align-items:center;gap:0.8rem;flex-wrap:wrap;'>
            <span class='chip {exp_cls}'>누적 노출 {exp_grade}</span>
            <span class='chip chip-neu'>지역 3년 평균 PM2.5 {pm25_avg}㎍/m³</span>
            <span class='chip chip-neu'>거주 {residence_years}년</span>
          </div>
          <div style='margin-top:0.6rem;font-size:0.82rem;color:#444;line-height:1.7;'>{exp_msg}</div>
        </div>
        """, unsafe_allow_html=True)


    # 리포트 HTML 다운로드 버튼
    from datetime import datetime as _dt2
    html_report = generate_pdf_html(
        result, air, region, residence_years,
        st.session_state.get("pdf_name", ""),
        st.session_state.get("pdf_age", ""),
        st.session_state.get("pdf_gender", "")
    )
    st.download_button(
        label="📄 PDF 리포트 저장",
        data=html_report.encode("utf-8"),
        file_name=f"YDLab_피부분석_{_dt2.now().strftime('%Y%m%d_%H%M')}.html",
        mime="text/html",
        use_container_width=True
    )
    st.caption("💡 다운로드된 파일을 크롬으로 열면 PDF 저장 창이 자동으로 열립니다.")

    # 대시보드 CTA
    st.markdown("""
    <a class='cta-btn' href='https://ydlabbio.com' target='_blank'>
      🌍 인천·안산·시흥 환경 현황 대시보드 보기 →
    </a>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  메인 UI
# ════════════════════════════════════════════════════════════

st.markdown("""
<div class='hero'>
  <div class='hero-label'>YD Lab · 재능대학교 바이오테크과</div>
  <h1>🔬 피부분석</h1>
  <p>현미경 사진 업로드 → AI 즉시 분석 → 맞춤 성분 추천</p>
</div>
""", unsafe_allow_html=True)

# API 키 확인
api_key = ""
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    api_key = ""

if not api_key:
    st.warning("⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다. `.streamlit/secrets.toml`에 키를 추가하세요.")
    st.code('[secrets]\nANTHROPIC_API_KEY = "sk-ant-..."', language="toml")
    st.stop()

# ── 촬영 가이드 ──────────────────────────────────────────────
with st.expander("📷 촬영 가이드"):
    st.markdown("""
<div class='guide-body'>
<div class='gstep'><span class='gnum'>1</span><span>세안 후 30분 뒤, 화장 제거 상태에서 촬영하세요.</span></div>
<div class='gstep'><span class='gnum'>2</span><span>자연광 또는 흰 조명 아래, 흰 배경 앞에서 촬영하세요.</span></div>
<div class='gstep'><span class='gnum'>3</span><span>촬영 부위: <b>눈가(좌우), 뺨, 이마</b> — 총 3~4장 권장</span></div>
<div class='gstep'><span class='gnum'>4</span><span>현미경을 피부에 살짝 밀착한 뒤 초점을 맞춰 촬영하세요.</span></div>
</div>
""", unsafe_allow_html=True)

# ── 기본 정보 ────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-label">기본 정보</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    name      = st.text_input("이름 (이니셜 가능)", placeholder="예: 김○○")
    age_group = st.selectbox("연령대", ["선택","10대","20대","30대","40대","50대","60대 이상"])
with c2:
    gender = st.selectbox("성별", ["선택","여성","남성","기타/무응답"])
    region = st.selectbox("거주 지역", list(STATION_MAP.keys()))
with c1:
    residence_years = st.selectbox("거주 기간",
        ["선택","1년 미만","1~2년","3~5년","5~10년","10년 이상"],
        help="해당 지역 거주 기간 (누적 환경 노출 지수 계산에 사용됩니다)")
st.markdown('</div>', unsafe_allow_html=True)

# ── 피부 고민 ────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-label">피부 고민 (복수 선택)</div>', unsafe_allow_html=True)
concerns = st.multiselect("해당 항목 선택",
    ["주름·탄력 저하","모공 확장","건조·각질","홍조·민감",
     "색소·기미","피지·번들거림","여드름·트러블","특별한 고민 없음"],
    label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# ── 사진 업로드 ──────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-label">피부 사진 업로드</div>', unsafe_allow_html=True)
uploaded = st.file_uploader("현미경 촬영 사진 (3~4장 권장)",
    type=["jpg","jpeg","png"], accept_multiple_files=True,
    label_visibility="collapsed")
images = []
if uploaded:
    cols = st.columns(min(len(uploaded), 4))
    for i, f in enumerate(uploaded[:4]):
        img = Image.open(f).convert("RGB")
        images.append(img)
        cols[i].image(img, caption=f"사진 {i+1}", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── 동의 ─────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-label">개인정보 수집·이용 동의</div>', unsafe_allow_html=True)
st.markdown("""
<div class='consent-box'>
  <strong>수집 항목:</strong> 이름(이니셜), 연령대, 성별, 거주 지역, 피부 사진, 피부 고민<br>
  <strong>수집 목적:</strong> 환경오염과 피부 상태 상관관계 연구 (재능대학교 YD Lab)<br>
  <strong>보유 기간:</strong> 연구 종료 후 3년 · <strong>제3자 제공:</strong> 없음
</div>
""", unsafe_allow_html=True)
consent = st.checkbox("위 내용을 읽고 개인정보 수집·이용에 동의합니다.")
st.markdown('</div>', unsafe_allow_html=True)

# ── 분석 버튼 ────────────────────────────────────────────────
if st.button("🔬 피부 분석 시작", type="primary", use_container_width=True):
    errors = []
    if not name.strip():      errors.append("이름을 입력해주세요.")
    if age_group == "선택":   errors.append("연령대를 선택해주세요.")
    if gender == "선택":      errors.append("성별을 선택해주세요.")
    if not concerns:          errors.append("피부 고민을 하나 이상 선택해주세요.")
    if not images:            errors.append("사진을 1장 이상 업로드해주세요.")
    if not consent:           errors.append("개인정보 수집·이용에 동의해주세요.")

    for e in errors:
        st.error(e)

    if not errors:
        # 환경 지수 조회
        station = STATION_MAP.get(region)
        air = fetch_air(station) if station else \
              dict(pm25=None, pm10=None, o3=None, no2=None, mock=True)

        # Claude Vision 분석
        with st.spinner("🔬 AI가 피부를 분석하고 있습니다... (10~20초)"):
            result = analyze_skin(images, api_key)

        if result:
            # 데이터 저장
            st.session_state["pdf_name"]   = name.strip()
            st.session_state["pdf_age"]    = age_group
            st.session_state["pdf_gender"] = gender
            save_record({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "name": name.strip(), "age_group": age_group,
                "gender": gender, "region": region, "residence_years": residence_years,
                "skin_concern": ", ".join(concerns),
                "photo_count": len(images),
                "pm25": air.get("pm25"), "pm10": air.get("pm10"),
                "exposure_index": f"{REGION_PM25_AVG.get(region,22.0)*({'1년 미만':0.5,'1~2년':1.5,'3~5년':4,'5~10년':7.5,'10년 이상':12}.get(residence_years,0)):.1f}",
                "o3":   air.get("o3"),   "no2":  air.get("no2"),
                "overall_score":          result.get("overall_score"),
                "skin_type":              result.get("skin_type"),
                "key_concerns":           ", ".join(result.get("key_concerns",[])),
                "recommended_ingredients":
                    ", ".join(result.get("recommended_ingredients",[])),
                "consent": "Y"
            })
            # 결과 표시
            res_yr_map = {"1년 미만":0,"1~2년":1,"3~5년":4,"5~10년":7,"10년 이상":12,"선택":0}
            show_result(result, air, region, air.get("pm25"),
                        residence_years=res_yr_map.get(residence_years, 0))

# ── 관리자 사이드바 ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔒 관리자")
    pwd = st.text_input("비밀번호", type="password")
    if pwd == "ydlab2025":
        st.success("관리자 모드")
        if DATA_FILE.exists():
            import pandas as pd
            df = pd.read_csv(DATA_FILE)
            st.metric("총 분석 건수", len(df))
            if "overall_score" in df.columns:
                st.metric("평균 종합 점수", round(df["overall_score"].mean(), 1))
            st.dataframe(df, use_container_width=True)
            csv_b = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("📥 CSV 다운로드", csv_b,
                               "ydlab_skin_data.csv", "text/csv")
        else:
            st.info("아직 분석 데이터가 없습니다.")
