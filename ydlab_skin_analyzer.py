"""
YD Lab 피부·두피 분석 앱 v4.4  ─ Dark Glassmorphism Edition (텍스트 가시성 완전 수정)
설치: pip install streamlit anthropic pillow requests pandas gspread google-auth
실행: streamlit run ydlab_skin_analyzer.py

secrets.toml:
  ANTHROPIC_API_KEY = "..."
  AIRKOREA_API_KEY  = "..."
  KMA_API_KEY       = "..."
  ACCESS_PASSWORD   = "YDLAB2025"
  ADMIN_PASSWORD    = "YDLAB2025"
  GOOGLE_SHEETS_ID  = "..."
  [gcp_service_account] ...
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
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image
import io

st.set_page_config(
    page_title="YD Lab 피부두피 분석",
    page_icon="🔬",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=DM+Mono:wght@400;500&family=Orbitron:wght@400;700;900&display=swap');

/* ══════════════════════════════════════
   1. 전체 배경 & 기본 폰트
══════════════════════════════════════ */
html, body, [class*="css"], .stApp {
    font-family: 'Noto Sans KR', sans-serif;
    background: linear-gradient(135deg,
        #0a0a1a 0%, #0d1b3e 30%, #1a0a2e 60%, #0a1628 100%) !important;
    min-height: 100vh;
}
.stApp {
    background: linear-gradient(135deg,
        #0a0a1a 0%, #0d1b3e 30%, #1a0a2e 60%, #0a1628 100%) !important;
}
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
        radial-gradient(ellipse at 20% 20%, rgba(99,102,241,0.15) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(16,185,129,0.10) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(139,92,246,0.08) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* ══════════════════════════════════════
   2. 모든 기본 텍스트 → 밝은 색 강제 적용
══════════════════════════════════════ */
p, span, div, li, td, th, label,
.stMarkdown, .stMarkdown p, .stMarkdown span,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] div {
    color: #e2e8f0 !important;
}
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* ══════════════════════════════════════
   3. 위젯 라벨 (selectbox·input 위 한국어 라벨)
══════════════════════════════════════ */
label,
.stTextInput label,
.stSelectbox label,
.stMultiSelect label,
.stNumberInput label,
.stTextArea label,
.stRadio label,
.stCheckbox label,
.stSlider label,
.stFileUploader label,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
[data-testid="stWidgetLabel"] div,
.stCheckbox label p,
.stRadio [data-testid="stMarkdownContainer"] p {
    color: #c4b5fd !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

/* ══════════════════════════════════════
   4. 입력 위젯 박스
══════════════════════════════════════ */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: #ffffff !important;
    border: 1px solid rgba(99,102,241,0.45) !important;
    border-radius: 10px !important;
    color: #111111 !important;
    caret-color: #6366f1 !important;
    padding: 10px 14px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.9rem !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: rgba(100,100,120,0.60) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(99,102,241,0.70) !important;
    box-shadow: none !important;
    outline: none !important;
}


/* ══════════════════════════════════════
   5. Selectbox / Multiselect
══════════════════════════════════════ */
/* 컨테이너 */
.stSelectbox > div > div,
.stMultiSelect > div > div,
[data-baseweb="select"],
[data-baseweb="select"] > div,
[data-baseweb="select"]:focus-within,
[data-baseweb="select"] > div:focus,
[data-baseweb="select"] > div:focus-within {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    outline: none !important;
}

/* 포커스 시 테두리만 변경, 블러 없음 */
[data-baseweb="select"] > div:focus,
[data-baseweb="select"] > div[aria-expanded="true"] {
    border-color: rgba(99,102,241,0.70) !important;
    box-shadow: none !important;
    outline: none !important;
}

/* 드롭다운 화살표 */
.stSelectbox svg, .stMultiSelect svg {
    fill: #a78bfa !important;
    color: #a78bfa !important;
}
/* 드롭다운 팝업 */
/* ══ 드롭다운 팝업 배경 ══ */
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="popover"] > div > div,
ul[data-baseweb="menu"],
[data-baseweb="menu"],
[data-baseweb="menu"] > div,
[role="listbox"],
[role="listbox"] > div,
[role="listbox"] > div > div {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1px solid rgba(99,102,241,0.45) !important;
    border-radius: 10px !important;
}

/* ══ 드롭다운 각 옵션 ══ */
[role="option"],
[role="option"] *,
[data-baseweb="option"],
[data-baseweb="option"] *,
li[role="option"],
li[role="option"] *,
[data-baseweb="menu"] li,
[data-baseweb="menu"] li * {
    color: #111111 !important;
    background: transparent !important;
    background-color: transparent !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.87rem !important;
}

/* ══ 호버 상태 ══ */
[role="option"]:hover,
[role="option"]:hover *,
[data-baseweb="option"]:hover,
[data-baseweb="option"]:hover * {
    background: rgba(99,102,241,0.12) !important;
    background-color: rgba(99,102,241,0.12) !important;
    color: #111111 !important;
}

/* ══ 선택된 항목 ══ */
[aria-selected="true"][role="option"],
[aria-selected="true"][role="option"] * {
    background: rgba(99,102,241,0.18) !important;
    background-color: rgba(99,102,241,0.18) !important;
    color: #111111 !important;
}



/* ══════════════════════════════════════
   6. 체크박스 & 라디오
══════════════════════════════════════ */
.stCheckbox > label > div[data-testid="stMarkdownContainer"] p,
.stCheckbox span,
.stRadio > div label span,
.stRadio span {
    color: #e2e8f0 !important;
    font-size: 0.87rem !important;
}

/* ══════════════════════════════════════
   7. 파일 업로더
══════════════════════════════════════ */
/* ══ 파일 업로더 ══ */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.08) !important;
    border: 2px dashed rgba(99,102,241,0.50) !important;
    border-radius: 14px !important;
    padding: 16px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(99,102,241,0.85) !important;
    background: rgba(99,102,241,0.10) !important;
}
[data-testid="stFileUploader"] *,
[data-testid="stFileUploadDropzone"] * {
    color: #111111 !important;
}

/* Upload 버튼 */
[data-testid="stFileUploader"] button,
[data-testid="stFileUploadDropzone"] button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    border: 1px solid rgba(99,102,241,0.80) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-weight: 500 !important;
}
[data-testid="stFileUploader"] button:hover,
[data-testid="stFileUploadDropzone"] button:hover {
    background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%) !important;
    border-color: rgba(99,102,241,1.0) !important;
    color: #d3d3d3 !important;
}



/* ══════════════════════════════════════
   8. 알림 메시지 (info / warning / success / error)
══════════════════════════════════════ */
.stAlert > div,
[data-testid="stAlert"] > div {
    border-radius: 10px !important;
}
/* info */
[data-testid="stAlert"][data-baseweb="notification"][kind="info"] > div,
.stInfo > div {
    background: rgba(59,130,246,0.12) !important;
    border: 1px solid rgba(59,130,246,0.30) !important;
}
[data-testid="stAlert"][kind="info"] p,
.stInfo p, .stInfo span {
    color: #93c5fd !important;
}
/* warning */
[data-testid="stAlert"][kind="warning"] > div,
.stWarning > div {
    background: rgba(245,158,11,0.12) !important;
    border: 1px solid rgba(245,158,11,0.30) !important;
}
[data-testid="stAlert"][kind="warning"] p,
.stWarning p, .stWarning span {
    color: #fcd34d !important;
}
/* success */
[data-testid="stAlert"][kind="success"] > div,
.stSuccess > div {
    background: rgba(16,185,129,0.12) !important;
    border: 1px solid rgba(16,185,129,0.30) !important;
}
[data-testid="stAlert"][kind="success"] p,
.stSuccess p, .stSuccess span {
    color: #6ee7b7 !important;
}
/* error */
[data-testid="stAlert"][kind="error"] > div,
.stError > div {
    background: rgba(239,68,68,0.12) !important;
    border: 1px solid rgba(239,68,68,0.30) !important;
}
[data-testid="stAlert"][kind="error"] p,
.stError p, .stError span {
    color: #fca5a5 !important;
}

/* ══════════════════════════════════════
   9. 버튼
══════════════════════════════════════ */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.35) !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99,102,241,0.55) !important;
    filter: brightness(1.1) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,
        #6366f1 0%, #8b5cf6 50%, #10b981 100%) !important;
    font-size: 1rem !important;
    padding: 0.8rem 1.5rem !important;
    box-shadow: 0 6px 25px rgba(99,102,241,0.45) !important;
}
.stDownloadButton > button {
    background: rgba(99,102,241,0.15) !important;
    border: 1px solid rgba(99,102,241,0.35) !important;
    color: #a5b4fc !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    background: rgba(99,102,241,0.28) !important;
    box-shadow: 0 0 15px rgba(99,102,241,0.35) !important;
}

/* ══════════════════════════════════════
   10. 사이드바
══════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: rgba(10,10,26,0.95) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #d4d4e8 !important;
}

/* ══════════════════════════════════════
   11. Expander
══════════════════════════════════════ */
.stExpander {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 12px !important;
}
.stExpander summary span,
.stExpander summary p {
    color: #c4b5fd !important;
    font-weight: 500 !important;
}

/* ══════════════════════════════════════
   12. 데이터프레임 / 테이블
══════════════════════════════════════ */
[data-testid="stDataFrame"] th {
    background: rgba(99,102,241,0.28) !important;
    color: #c7d2fe !important;
}
[data-testid="stDataFrame"] td {
    color: #cbd5e1 !important;
}

/* ══════════════════════════════════════
   13. Spinner
══════════════════════════════════════ */
[data-testid="stSpinner"] p,
[data-testid="stSpinner"] span {
    color: #c4b5fd !important;
}

/* ══════════════════════════════════════
   14. 기타 Streamlit 요소 정리
══════════════════════════════════════ */
hr { border-color: rgba(255,255,255,0.08) !important; }
[data-testid="stToolbar"]  { display: none !important; }
#MainMenu { visibility: hidden !important; }
footer    { visibility: hidden !important; }

/* 스크롤바 */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track  { background: rgba(255,255,255,0.03); }
::-webkit-scrollbar-thumb  { background: rgba(99,102,241,0.50); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.80); }

/* ══════════════════════════════════════
   15. 커스텀 컴포넌트 클래스들
══════════════════════════════════════ */

/* 글래스 카드 */
.glass-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 20px;
    padding: 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4),
                inset 0 1px 0 rgba(255,255,255,0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    color: #e2e8f0;
}
.glass-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 48px rgba(0,0,0,0.5),
                0 0 0 1px rgba(99,102,241,0.30),
                inset 0 1px 0 rgba(255,255,255,0.12);
}
.glass-card p, .glass-card span, .glass-card div { color: #e2e8f0 !important; }
.glass-card h1, .glass-card h2, .glass-card h3 { color: #ffffff !important; }

/* 히어로 배너 */
.hero {
    background: linear-gradient(135deg,
        rgba(99,102,241,0.25) 0%,
        rgba(139,92,246,0.20) 40%,
        rgba(16,185,129,0.15) 100%);
    backdrop-filter: blur(30px);
    -webkit-backdrop-filter: blur(30px);
    border: 1px solid rgba(99,102,241,0.30);
    border-radius: 24px;
    padding: 2.4rem 2rem 2rem;
    margin-bottom: 1.6rem;
    box-shadow: 0 20px 60px rgba(99,102,241,0.20),
                inset 0 1px 0 rgba(255,255,255,0.10);
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: conic-gradient(
        from 0deg at 50% 50%,
        transparent 0deg,
        rgba(99,102,241,0.05) 60deg,
        transparent 120deg,
        rgba(16,185,129,0.05) 180deg,
        transparent 240deg,
        rgba(139,92,246,0.05) 300deg,
        transparent 360deg);
    animation: rotate 20s linear infinite;
    pointer-events: none;
}
@keyframes rotate {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
}
.hero-label {
    font-size: 0.68rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(16,185,129,0.90) !important;
    margin-bottom: 0.6rem;
    font-family: 'DM Mono', monospace;
}
.hero h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: white !important;
    margin-bottom: 0.5rem;
    text-shadow: 0 0 30px rgba(99,102,241,0.5);
}
.hero p {
    font-size: 0.82rem;
    color: rgba(255,255,255,0.70) !important;
    line-height: 1.75;
}
.hero-version {
    font-family: 'DM Mono', monospace;
    font-size: 0.70rem;
    color: rgba(16,185,129,0.80) !important;
    margin-top: 0.5rem;
}

/* 카드 라벨 */
.card-label {
    font-size: 0.65rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: rgba(165,180,252,1) !important;
    font-weight: 700;
    font-family: 'DM Mono', monospace;
    margin-bottom: 1rem;
    padding-bottom: 0.7rem;
    border-bottom: 1px solid rgba(99,102,241,0.20);
}
.card-label-green {
    font-size: 0.65rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: rgba(110,231,183,1) !important;
    font-weight: 700;
    font-family: 'DM Mono', monospace;
    margin-bottom: 1rem;
    padding-bottom: 0.7rem;
    border-bottom: 1px solid rgba(16,185,129,0.20);
}

/* 점수 게이지 */
.gauge-wrap  { text-align: center; padding: 0.8rem 0.4rem; }
.gauge-num   { font-size: 1.9rem; font-weight: 700; font-family: 'DM Mono', monospace;
               line-height: 1; text-shadow: 0 0 20px currentColor; }
.gauge-lbl   { font-size: 0.68rem; color: rgba(255,255,255,0.55) !important; margin-top: 0.25rem; }
.gauge-cmt   { font-size: 0.64rem; color: rgba(255,255,255,0.40) !important;
               margin-top: 0.3rem; line-height: 1.3; }
.score-high  { color: #10b981 !important; }
.score-mid   { color: #f59e0b !important; }
.score-low   { color: #ef4444 !important; }

/* 빅 스코어 */
.big-score {
    font-size: 5rem;
    font-weight: 900;
    font-family: 'DM Mono', monospace;
    line-height: 1;
    text-shadow: 0 0 40px currentColor, 0 0 80px currentColor;
    letter-spacing: -2px;
}

/* 성분 칩 */
.ing-chip {
    display: inline-block;
    background: rgba(99,102,241,0.16);
    border: 1px solid rgba(99,102,241,0.38);
    color: rgba(165,180,252,1) !important;
    border-radius: 8px;
    padding: 0.28rem 0.75rem;
    font-size: 0.78rem;
    margin: 0.2rem;
    font-weight: 500;
    transition: all 0.2s ease;
    cursor: default;
}
.ing-chip:hover {
    background: rgba(99,102,241,0.32);
    border-color: rgba(99,102,241,0.72);
    box-shadow: 0 0 12px rgba(99,102,241,0.42);
    transform: translateY(-1px);
}
.scalp-chip {
    display: inline-block;
    background: rgba(16,185,129,0.16);
    border: 1px solid rgba(16,185,129,0.38);
    color: rgba(110,231,183,1) !important;
    border-radius: 8px;
    padding: 0.28rem 0.75rem;
    font-size: 0.78rem;
    margin: 0.2rem;
    font-weight: 500;
    transition: all 0.2s ease;
    cursor: default;
}
.scalp-chip:hover {
    background: rgba(16,185,129,0.32);
    border-color: rgba(16,185,129,0.72);
    box-shadow: 0 0 12px rgba(16,185,129,0.42);
    transform: translateY(-1px);
}

/* 상태 칩 */
.chip {
    display: inline-flex; align-items: center;
    padding: 0.28rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 0.2rem;
}
.chip-good { background:rgba(16,185,129,0.16); color:#6ee7b7 !important; border:1px solid rgba(16,185,129,0.32); }
.chip-mid  { background:rgba(59,130,246,0.16);  color:#93c5fd !important; border:1px solid rgba(59,130,246,0.32); }
.chip-warn { background:rgba(245,158,11,0.16);  color:#fcd34d !important; border:1px solid rgba(245,158,11,0.32); }
.chip-bad  { background:rgba(239,68,68,0.16);   color:#fca5a5 !important; border:1px solid rgba(239,68,68,0.32); }
.chip-neu  { background:rgba(255,255,255,0.07); color:rgba(210,210,235,0.80) !important;
             border:1px solid rgba(255,255,255,0.13); }

/* 혼합 카드 */
.mixing-card {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(16,185,129,0.20);
    border-radius: 20px;
    padding: 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.mixing-row {
    display: flex; align-items: center; gap: 0.8rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.mixing-ing  { font-weight: 600; flex: 1; font-size: 0.84rem; color: rgba(255,255,255,0.90) !important; }
.mixing-pct  { font-weight: 700; font-family: 'DM Mono', monospace; font-size: 0.88rem;
               color: #10b981 !important; min-width: 48px; }
.mixing-ml   { font-size: 0.78rem; color: #93c5fd !important; font-weight: 600;
               min-width: 52px; font-family: 'DM Mono', monospace; }
.mixing-bar-wrap { flex: 2; background: rgba(255,255,255,0.09); border-radius: 4px; height: 7px; }
.mixing-bar {
    height: 7px; border-radius: 4px;
    background: linear-gradient(90deg, #10b981, #6ee7b7);
    box-shadow: 0 0 8px rgba(16,185,129,0.5);
    transition: width 0.8s cubic-bezier(0.4,0,0.2,1);
}
.scalp-mixing-bar {
    height: 7px; border-radius: 4px;
    background: linear-gradient(90deg, #6366f1, #a78bfa);
    box-shadow: 0 0 8px rgba(99,102,241,0.5);
}
.mixing-conc { font-size: 0.68rem; color: rgba(200,200,230,0.45) !important; min-width: 72px; }

/* 스텝 배지 */
.step-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 22px; height: 22px; border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white !important; font-size: 0.68rem; font-weight: 700;
    margin-right: 0.5rem; flex-shrink: 0;
    box-shadow: 0 0 8px rgba(99,102,241,0.5);
}
.step-badge-green {
    display: inline-flex; align-items: center; justify-content: center;
    width: 22px; height: 22px; border-radius: 50%;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white !important; font-size: 0.68rem; font-weight: 700;
    margin-right: 0.5rem; flex-shrink: 0;
    box-shadow: 0 0 8px rgba(16,185,129,0.5);
}

/* 우선 개선 항목 */
.priority-item {
    display: flex; align-items: center; gap: 0.8rem;
    padding: 0.65rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.priority-num {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white !important; border-radius: 50%;
    width: 24px; height: 24px; min-width: 24px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.70rem; font-weight: 700;
    box-shadow: 0 0 10px rgba(99,102,241,0.4);
}
.priority-label { font-weight: 600; flex: 1; font-size: 0.84rem; color: rgba(255,255,255,0.90) !important; }
.priority-score { font-weight: 700; font-family: 'DM Mono', monospace; font-size: 0.84rem; }
.priority-msg   { font-size: 0.75rem; color: rgba(200,200,230,0.55) !important; }

/* 배너들 */
.patent-banner {
    background: rgba(59,130,246,0.12);
    border: 1px solid rgba(59,130,246,0.28);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    font-size: 0.76rem;
    color: #93c5fd !important;
    margin-bottom: 1rem;
    text-align: center;
    font-weight: 600;
}
.medical-disclaimer {
    background: rgba(239,68,68,0.10);
    border: 1px solid rgba(239,68,68,0.28);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    font-size: 0.76rem;
    color: #fca5a5 !important;
    margin-bottom: 1rem;
    text-align: center;
    font-weight: 600;
}
.air-real {
    background: rgba(16,185,129,0.10);
    border: 1px solid rgba(16,185,129,0.28);
    border-radius: 10px;
    padding: 0.5rem 1rem;
    font-size: 0.76rem;
    color: #6ee7b7 !important;
    margin-bottom: 0.8rem;
    font-weight: 600;
}
.air-mock {
    background: rgba(245,158,11,0.10);
    border: 1px solid rgba(245,158,11,0.28);
    border-radius: 10px;
    padding: 0.5rem 1rem;
    font-size: 0.76rem;
    color: #fcd34d !important;
    margin-bottom: 0.8rem;
    font-weight: 600;
}
.workshop-banner {
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.22);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin-bottom: 1rem;
    font-size: 0.80rem;
    color: #6ee7b7 !important;
    font-weight: 500;
}

/* SEEI 박스 */
.seei-box {
    background: rgba(16,185,129,0.06);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(16,185,129,0.20);
    border-radius: 20px;
    padding: 1.4rem;
    margin-bottom: 1.2rem;
}
.kma-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(245,158,11,0.22);
    border-radius: 12px;
    padding: 0.8rem;
    margin-top: 0.7rem;
}

/* 동의 박스 */
.consent-box {
    background: rgba(255,255,255,0.04);
    border-left: 3px solid rgba(99,102,241,0.65);
    border-radius: 0 10px 10px 0;
    padding: 0.9rem 1rem;
    font-size: 0.78rem;
    color: rgba(220,220,240,0.70) !important;
    line-height: 1.75;
    margin-bottom: 1rem;
}

/* 혼탁 카드 */
.confound-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 16px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    color: #e2e8f0 !important;
}
.confound-card p, .confound-card span, .confound-card div { color: #e2e8f0 !important; }

/* 두피 섹션 */
.scalp-section {
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.18);
    border-radius: 16px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}
.scalp-section p, .scalp-section span, .scalp-section div { color: #e2e8f0 !important; }

/* 결과 텍스트 */
.result-text {
    font-size: 0.84rem;
    color: rgba(220,220,245,0.80) !important;
    line-height: 1.7;
}

/* 탈모 위험 박스 */
.hair-loss-box {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.22);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    font-size: 0.82rem;
    margin-top: 0.8rem;
    color: #e2e8f0 !important;
}
.hair-loss-box span { color: inherit !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# 상수
# ══════════════════════════════════════════
PM25_ALERT_THRESHOLD       = 35
CEEI_ANTIOXIDANT_THRESHOLD = 150

SEEI_WEIGHTS     = {"pm25": 0.40, "pm10": 0.25, "no2": 0.20, "o3": 0.15}
NO2_PPM_TO_UGM3  = 1882.0
O3_PPM_TO_UGM3   = 1962.0

SEASON_CORRECTION = {
    1: 1.1, 2: 1.1, 3: 1.0, 4: 1.0, 5: 1.0,
    6: 1.2, 7: 1.3, 8: 1.3, 9: 1.0, 10: 1.0, 11: 1.1, 12: 1.1,
}

REGION_PM25_AVG = {
    "인천 중구": 24.2, "인천 서구": 23.5, "부평구": 22.8,
    "계양구": 22.1, "연수구": 21.9, "남동구": 23.0,
    "안산": 25.3, "시흥": 24.0, "서울": 22.0, "기타": 22.0,
}
RESIDENCE_YEAR_MAP = {
    "선택": 0, "1년 미만": 0, "1~2년": 1, "3~5년": 4, "5~10년": 7, "10년 이상": 12,
}

SKIN_BODY_PARTS  = ["이마", "눈가", "볼", "코", "턱", "입가", "목", "손등"]
SCALP_BODY_PARTS = ["두피 정수리", "두피 측두부", "두피 후두부"]

STATION_CANDIDATES = {
    "인천 중구": ["신흥","중구","항동"], "인천 서구": ["청라","서구","검단"],
    "부평구": ["부평","갈산","산곡"], "계양구": ["계산","계양","효성"],
    "연수구": ["연수","송도","동춘","옥련"], "남동구": ["구월","남동","논현"],
    "안산": ["본오동","고잔동","부곡동1"], "시흥": ["정왕동","대야동","배곧동"],
    "서울": ["중구","종로구"], "기타": ["중구"],
}
KMA_AREA_CODE = {
    "인천 중구": "2811000000", "인천 서구": "2815000000",
    "부평구": "2813700000", "계양구": "2814500000",
    "연수구": "2814000000", "남동구": "2814200000",
    "안산": "4126000000", "시흥": "4139000000",
    "서울": "1100000000", "기타": "2800000000",
}
KMA_GRID = {
    "인천 중구": (53,124), "인천 서구": (51,125),
    "부평구": (54,125), "계양구": (53,126),
    "연수구": (54,123), "남동구": (55,123),
    "안산": (57,119), "시흥": (57,121),
    "서울": (60,127), "기타": (54,124),
}

SAMPLE_CONC_DB = {
    "히알루론산":            {"pct": 1.0,    "note": "저분자·고분자 혼합 권장"},
    "나이아신아마이드":      {"pct": 5.0,    "note": "10% 초과 시 자극 가능"},
    "판테놀":                {"pct": 3.0,    "note": "Pro-비타민B5"},
    "아스코빌글루코사이드":  {"pct": 5.0,    "note": "비타민C유도체 / pH 5-7 안정"},
    "비타민C유도체":         {"pct": 5.0,    "note": "아스코빌글루코사이드"},
    "레티닐팔미테이트":      {"pct": 0.3,    "note": "주름개선 기능성 고시 / 차광냉장"},
    "아세틸헥사펩타이드-8":  {"pct": 0.002,  "note": "EGF 대체 펩타이드 / 냉장"},
    "피토스핑고신":          {"pct": 0.1,    "note": "세라마이드 전구체 / 수용성"},
    "펩타이드":              {"pct": 3.0,    "note": "콜라겐 펩타이드"},
    "아데노신":              {"pct": 0.04,   "note": "식약처 주름개선 기능성 기준"},
    "글리세린":              {"pct": 5.0,    "note": "기초 보습"},
    "알란토인":              {"pct": 0.3,    "note": "피부 진정·재생"},
    "스쿠알란":              {"pct": 3.0,    "note": "산화 안정적 오일"},
    "살리실산":              {"pct": 1.0,    "note": "각질 용해 / 에탄올 선용해"},
    "피록톤올아민":          {"pct": 0.5,    "note": "비듬·항균 / ZPT 대체"},
    "바이오틴":              {"pct": 0.05,   "note": "모발 강화·성장"},
    "티트리오일":            {"pct": 1.0,    "note": "항균·진정 / 가용화 필요"},
    "로즈마리오일":          {"pct": 0.5,    "note": "혈행 촉진 / 가용화 필요"},
    "멘톨":                  {"pct": 0.3,    "note": "청량감·항균 / 에탄올 선용해"},
    "소듐PCA":               {"pct": 3.0,    "note": "두피 보습"},
}

VOL_PRESETS = [
    {"label": "10ml",  "ml": 10},
    {"label": "30ml",  "ml": 30},
    {"label": "50ml",  "ml": 50},
    {"label": "100ml", "ml": 100},
]

SKIN_INGREDIENT_LIST = [
    "히알루론산","나이아신아마이드","판테놀","아스코빌글루코사이드",
    "레티닐팔미테이트","아세틸헥사펩타이드-8","피토스핑고신","펩타이드",
    "아데노신","글리세린","알란토인","스쿠알란","살리실산",
]
SCALP_INGREDIENT_LIST = [
    "피록톤올아민","살리실산","바이오틴","판테놀","나이아신아마이드",
    "히알루론산","피토스핑고신","티트리오일","로즈마리오일","멘톨","소듐PCA","아데노신",
]
SKIN_ING_STR  = ", ".join(SKIN_INGREDIENT_LIST)
SCALP_ING_STR = ", ".join(SCALP_INGREDIENT_LIST)

# ══════════════════════════════════════════
# AI 프롬프트
# ══════════════════════════════════════════
SKIN_PROMPT = (
    "당신은 피부과학 전문가입니다. 업로드된 피부 현미경 사진을 분석하여 "
    "아래 JSON 형식으로만 응답하세요. JSON 외 다른 텍스트는 절대 포함하지 마세요.\n"
    '{"wrinkle_score":0~100,"pore_score":0~100,"texture_score":0~100,'
    '"tone_score":0~100,"moisture_score":0~100,"overall_score":0~100,'
    '"skin_type":"건성|지성|복합성|중성|민감성",'
    '"wrinkle_comment":"주름 상태 한 줄 30자 이내",'
    '"pore_comment":"모공 상태 30자 이내",'
    '"texture_comment":"피부결 30자 이내",'
    '"tone_comment":"피부톤 30자 이내",'
    '"moisture_comment":"수분 30자 이내",'
    '"summary":"종합 설명 100자 이내",'
    '"key_concerns":["고민1","고민2"],'
    '"recommended_ingredients":["성분1","성분2","성분3","성분4"],'
    '"care_advice":"조언 80자 이내"}\n'
    "점수는 높을수록 좋음.\n"
    "recommended_ingredients는 반드시 아래 목록에서만 선택:\n"
)
SCALP_PROMPT = (
    "당신은 두피 모발 전문가입니다. 업로드된 두피 현미경 사진을 분석하여 "
    "아래 JSON 형식으로만 응답하세요. JSON 외 다른 텍스트는 절대 포함하지 마세요.\n"
    '{"overall_score":0~100,"scalp_type":"지성|건성|민감성|정상|복합성",'
    '"keratin_score":0~100,"pore_score":0~100,"hair_thickness_score":0~100,'
    '"scalp_color_score":0~100,"moisture_balance_score":0~100,'
    '"hair_damage_score":0~100,"hair_loss_risk_score":0~100,'
    '"keratin_comment":"각질 30자 이내",'
    '"pore_comment":"모공 피지 30자 이내",'
    '"hair_thickness_comment":"모발굵기 30자 이내",'
    '"scalp_color_comment":"색상 염증 30자 이내",'
    '"moisture_balance_comment":"수분유분 30자 이내",'
    '"hair_damage_comment":"손상도 30자 이내",'
    '"hair_loss_risk_comment":"탈모 30자 이내",'
    '"summary":"종합 100자 이내",'
    '"key_concerns":["고민1","고민2"],'
    '"recommended_ingredients":["성분1","성분2","성분3","성분4"],'
    '"care_advice":"조언 80자 이내"}\n'
    "점수는 높을수록 좋음.\n"
    "recommended_ingredients는 반드시 아래 목록에서만 선택:\n"
)

# ══════════════════════════════════════════
# 헬퍼
# ══════════════════════════════════════════
def img_to_b64(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode()

def score_color(s):
    if s >= 70: return "#10b981"
    if s >= 40: return "#f59e0b"
    return "#ef4444"

def score_class(s):
    if s >= 70: return "score-high"
    if s >= 40: return "score-mid"
    return "score-low"

def pm25_chip(v):
    if v is None: return "<span class='chip chip-neu'>PM2.5 -</span>"
    v = int(v)
    if v <= 15:  return f"<span class='chip chip-good'>PM2.5 좋음 {v}</span>"
    if v <= 35:  return f"<span class='chip chip-mid'>PM2.5 보통 {v}</span>"
    if v <= 75:  return f"<span class='chip chip-warn'>PM2.5 나쁨 {v}</span>"
    return f"<span class='chip chip-bad'>PM2.5 매우나쁨 {v}</span>"

def get_sample_conc(ingredient):
    if ingredient in SAMPLE_CONC_DB: return SAMPLE_CONC_DB[ingredient]
    for k in SAMPLE_CONC_DB:
        if k in ingredient or ingredient in k: return SAMPLE_CONC_DB[k]
    return None

def get_pollution_alert(pm25, ceei):
    if isinstance(pm25,(int,float)) and float(pm25) > PM25_ALERT_THRESHOLD:
        return "오늘 PM2.5 나쁨 — 아스코빌글루코사이드·나이아신아마이드 항산화 강화 권장"
    elif ceei >= CEEI_ANTIOXIDANT_THRESHOLD:
        return "장기 오염 누적 — 레티닐팔미테이트·펩타이드 광노화 대응 권장"
    return ""

def svg_gauge(score, label, comment="", size=100):
    c = score_color(score)
    r = 38
    circ = 2 * 3.14159 * r
    dash = circ * score / 100
    gap  = circ - dash
    return f"""
<div style="text-align:center;padding:0.5rem 0.2rem;">
  <svg width="{size}" height="{size}" viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="{r}" fill="none"
      stroke="rgba(255,255,255,0.07)" stroke-width="7"/>
    <circle cx="50" cy="50" r="{r}" fill="none"
      stroke="{c}" stroke-width="7"
      stroke-dasharray="{dash:.1f} {gap:.1f}"
      stroke-linecap="round"
      transform="rotate(-90 50 50)"
      style="filter:drop-shadow(0 0 6px {c})"/>
    <text x="50" y="46" text-anchor="middle"
      fill="{c}" font-size="18" font-weight="700"
      font-family="DM Mono,monospace"
      style="filter:drop-shadow(0 0 4px {c})">{score}</text>
    <text x="50" y="60" text-anchor="middle"
      fill="rgba(255,255,255,0.60)" font-size="8.5"
      font-family="Noto Sans KR,sans-serif">{label}</text>
  </svg>
  <div style="font-size:0.62rem;color:rgba(210,210,240,0.50);
    line-height:1.3;margin-top:0.1rem;max-width:90px;
    margin-left:auto;margin-right:auto;">
    {comment}</div>
</div>"""

# ══════════════════════════════════════════
# 환경 지수
# ══════════════════════════════════════════
def calc_ceei(pm25_avg, residence_years):
    ceei = round(pm25_avg * residence_years, 1)
    if ceei < 50:
        return (ceei,"낮음",
                "<span class='chip chip-good'>CEEI "+str(ceei)+" 낮음</span>",
                "환경 노출 영향 낮음 — 기본 보습·자외선 차단 유지")
    elif ceei < 150:
        return (ceei,"보통",
                "<span class='chip chip-mid'>CEEI "+str(ceei)+" 보통</span>",
                "중간 수준 환경 노출 — 항산화 성분 정기 사용 권장")
    elif ceei < 300:
        return (ceei,"높음",
                "<span class='chip chip-warn'>CEEI "+str(ceei)+" 높음</span>",
                "높은 환경 노출 누적 — 항산화·장벽강화 집중 케어 필요")
    else:
        return (ceei,"매우높음",
                "<span class='chip chip-bad'>CEEI "+str(ceei)+" 매우높음</span>",
                "매우 높은 누적 노출 — 피부과 상담·기능성 화장품 집중 케어 권장")

def uv_index_grade(uv):
    if uv is None: return ("알수없음",1.0,"#888888")
    uv = float(uv)
    if uv < 3:    return ("낮음",     1.0, "#10b981")
    elif uv < 6:  return ("보통",     1.1, "#3b82f6")
    elif uv < 8:  return ("높음",     1.2, "#f59e0b")
    elif uv < 11: return ("매우높음", 1.35,"#ef4444")
    else:         return ("위험",     1.5, "#8b5cf6")

def humidity_correction(hum):
    if hum is None: return 1.0
    h = float(hum)
    if h >= 80:   return 1.3
    elif h >= 70: return 1.2
    elif h >= 40: return 1.0
    elif h >= 30: return 1.1
    else:         return 1.2

def calc_seei(air, residence_years, uv_data=None, humidity_data=None):
    pm25 = float(air.get("pm25") or 0)
    pm10 = float(air.get("pm10") or 0)
    no2  = float(air.get("no2")  or 0) * NO2_PPM_TO_UGM3
    o3   = float(air.get("o3")   or 0) * O3_PPM_TO_UGM3
    month  = datetime.now().month
    season = SEASON_CORRECTION.get(month, 1.0)
    components = {
        "PM2.5": round(pm25 * SEEI_WEIGHTS["pm25"], 1),
        "PM10":  round(pm10 * SEEI_WEIGHTS["pm10"], 1),
        "NO2":   round(no2  * SEEI_WEIGHTS["no2"],  1),
        "O3":    round(o3   * SEEI_WEIGHTS["o3"],   1),
    }
    composite = sum(components.values())
    uv_val   = uv_data.get("uv_index") if uv_data else None
    uv_gstr, uv_corr, uv_color = uv_index_grade(uv_val)
    hum_val  = humidity_data.get("humidity") if humidity_data else None
    hum_corr = humidity_correction(hum_val)
    seei = round(composite * residence_years * season * uv_corr * hum_corr, 1)
    if seei < 50:
        grade,chip,msg = ("낮음",
            "<span class='chip chip-good'>SEEI "+str(seei)+" 낮음</span>",
            "복합 환경 노출 낮음 — 기본 두피 보습·청결 유지")
    elif seei < 150:
        grade,chip,msg = ("보통",
            "<span class='chip chip-mid'>SEEI "+str(seei)+" 보통</span>",
            "중간 수준 복합 오염 — 두피 항산화·항균 성분 정기 사용 권장")
    elif seei < 300:
        grade,chip,msg = ("높음",
            "<span class='chip chip-warn'>SEEI "+str(seei)+" 높음</span>",
            "높은 복합 오염 누적 — 탈모 위험 증가, 두피케어 집중 필요")
    else:
        grade,chip,msg = ("매우높음",
            "<span class='chip chip-bad'>SEEI "+str(seei)+" 매우높음</span>",
            "매우 높은 누적 — 두피 전문 케어·피부과 상담 권장")
    return (seei,grade,chip,msg,components,season,uv_val,uv_gstr,hum_val,hum_corr)

# ══════════════════════════════════════════
# 데이터 수집
# ══════════════════════════════════════════
def fetch_air(region):
    key = st.secrets.get("AIRKOREA_API_KEY","")
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
    for station in STATION_CANDIDATES.get(region,["중구"]):
        if not key: break
        try:
            params = dict(serviceKey=key,stationName=station,dataTerm="DAILY",
                          pageNo=1,numOfRows=1,returnType="json",ver="1.3")
            r     = requests.get(url,params=params,timeout=8)
            items = r.json()["response"]["body"]["items"]
            if not (items and isinstance(items,list)): continue
            item  = items[0]
            def _s(k):
                v = item.get(k,"")
                return float(v) if v and str(v).strip() not in ["-","","None"] else None
            pm25 = _s("pm25Value")
            if pm25 is None: continue
            return dict(pm25=pm25,pm10=_s("pm10Value") or 0.0,
                        o3=_s("o3Value") or 0.0,no2=_s("no2Value") or 0.0,
                        station=station,
                        fetch_time=datetime.now().strftime("%Y-%m-%d %H:%M"),mock=False)
        except Exception: continue
    return dict(pm25=float(random.randint(12,65)),pm10=float(random.randint(18,85)),
                o3=round(random.uniform(0.010,0.080),3),no2=round(random.uniform(0.010,0.050),3),
                station="시간대 추정값",
                fetch_time=datetime.now().strftime("%Y-%m-%d %H:%M"),mock=True)

def fetch_kma_uv(region):
    key     = st.secrets.get("KMA_API_KEY","")
    area_no = KMA_AREA_CODE.get(region,"2800000000")
    today   = datetime.now().strftime("%Y%m%d")
    if key:
        try:
            url    = "http://apis.data.go.kr/1360000/LivingWthrIdxServiceV4/getUVIdxV4"
            params = dict(serviceKey=key,pageNo=1,numOfRows=10,dataType="JSON",
                          areaNo=area_no,time=today+"0600")
            r      = requests.get(url,params=params,timeout=8)
            items  = (r.json().get("response",{}).get("body",{})
                               .get("items",{}).get("item",[]))
            if items:
                uv_val = items[0].get("h12") or items[0].get("h0") or 0
                return {"uv_index":float(uv_val),"mock":False}
        except Exception: pass
    hour = datetime.now().hour
    if   6  <= hour <= 8:  est=2.0
    elif 9  <= hour <= 11: est=5.0
    elif hour == 12:       est=8.0
    elif 13 <= hour <= 14: est=9.0
    elif 15 <= hour <= 17: est=5.0
    elif 18 <= hour <= 19: est=2.0
    else:                  est=0.0
    return {"uv_index":est,"mock":True}

def fetch_kma_humidity(region):
    key    = st.secrets.get("KMA_API_KEY","")
    nx, ny = KMA_GRID.get(region,(54,124))
    now    = datetime.now()
    if key:
        try:
            url      = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
            obs_time = now - timedelta(hours=1) if now.minute < 40 else now
            params   = dict(serviceKey=key,pageNo=1,numOfRows=10,dataType="JSON",
                            base_date=obs_time.strftime("%Y%m%d"),
                            base_time=obs_time.strftime("%H00"),nx=nx,ny=ny)
            r      = requests.get(url,params=params,timeout=8)
            items  = (r.json().get("response",{}).get("body",{})
                               .get("items",{}).get("item",[]))
            for item in items:
                if item.get("category")=="REH":
                    return {"humidity":float(item.get("obsrValue",50)),"mock":False}
        except Exception: pass
        try:
            base_hours = [2,5,8,11,14,17,20,23]
            candidates = [h for h in base_hours if h <= now.hour]
            if candidates: base_hour=max(candidates); base_date=now.strftime("%Y%m%d")
            else:          base_hour=23; base_date=(now-timedelta(days=1)).strftime("%Y%m%d")
            url    = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
            params = dict(serviceKey=key,pageNo=1,numOfRows=100,dataType="JSON",
                          base_date=base_date,base_time=f"{base_hour:02d}00",nx=nx,ny=ny)
            r      = requests.get(url,params=params,timeout=8)
            items  = (r.json().get("response",{}).get("body",{})
                               .get("items",{}).get("item",[]))
            now_str   = now.strftime("%Y%m%d%H%M")[:10]
            reh_items = sorted([i for i in items if i.get("category")=="REH"],
                               key=lambda x:x.get("fcstDate","")+x.get("fcstTime",""))
            for item in reh_items:
                fdt = item.get("fcstDate","")+item.get("fcstTime","")[:2]
                if fdt >= now_str:
                    return {"humidity":float(item.get("fcstValue",50)),"mock":False}
            if reh_items:
                return {"humidity":float(reh_items[-1].get("fcstValue",50)),"mock":False}
        except Exception: pass
    month = now.month
    if month in [6,7,8]:    hum=random.randint(65,85)
    elif month in [12,1,2]: hum=random.randint(30,50)
    else:                   hum=random.randint(45,65)
    return {"humidity":float(hum),"mock":True}

# ══════════════════════════════════════════
# AI 분석
# ══════════════════════════════════════════
def analyze_skin(images, api_key, body_parts=None):
    try:
        client  = anthropic.Anthropic(api_key=api_key)
        content = [{"type":"image","source":{"type":"base64","media_type":"image/jpeg",
                    "data":img_to_b64(img)}} for img in images]
        parts_str = f"\n촬영 부위: {', '.join(body_parts)}" if body_parts else ""
        content.append({"type":"text","text":SKIN_PROMPT+SKIN_ING_STR+parts_str})
        msg = client.messages.create(model="claude-haiku-4-5",max_tokens=1200,
                                     messages=[{"role":"user","content":content}])
        return json.loads(re.sub(r"```json|```","",msg.content[0].text.strip()).strip())
    except Exception as e:
        st.error(f"피부 분석 오류: {e}"); return None

def analyze_scalp(images, api_key, body_parts=None):
    try:
        client  = anthropic.Anthropic(api_key=api_key)
        content = [{"type":"image","source":{"type":"base64","media_type":"image/jpeg",
                    "data":img_to_b64(img)}} for img in images]
        parts_str = f"\n촬영 부위: {', '.join(body_parts)}" if body_parts else ""
        content.append({"type":"text","text":SCALP_PROMPT+SCALP_ING_STR+parts_str})
        msg = client.messages.create(model="claude-haiku-4-5",max_tokens=1200,
                                     messages=[{"role":"user","content":content}])
        return json.loads(re.sub(r"```json|```","",msg.content[0].text.strip()).strip())
    except Exception as e:
        st.error(f"두피 분석 오류: {e}"); return None

# ══════════════════════════════════════════
# 혼합 가이드
# ══════════════════════════════════════════
def generate_mixing_guide(ingredients, skin_type, ceei_grade, total_ml=30):
    BW = {
        "히알루론산":35,"나이아신아마이드":20,"판테놀":25,
        "아스코빌글루코사이드":15,"비타민C유도체":15,
        "레티닐팔미테이트":8,"아세틸헥사펩타이드-8":8,"피토스핑고신":12,
        "펩타이드":15,"아데노신":10,"글리세린":20,"알란토인":10,"스쿠알란":10,"살리실산":10,
    }
    boost = {"낮음":1.0,"보통":1.2,"높음":1.5,"매우높음":1.8}.get(ceei_grade,1.0)
    antioxidants  = {"아스코빌글루코사이드","비타민C유도체","나이아신아마이드","펩타이드","레티닐팔미테이트"}
    sensitive_red = {"레티닐팔미테이트","살리실산"}
    is_s = skin_type in ["민감성","건성"]
    weights = {}
    for ing in ingredients:
        w = BW.get(ing,10)
        if ing in antioxidants:           w = round(w*boost)
        if is_s and ing in sensitive_red: w = max(3,round(w*0.5))
        weights[ing] = w
    tw     = sum(weights.values())
    ratios = {ing:round(w/tw*100) for ing,w in weights.items()}
    diff   = 100-sum(ratios.values())
    if diff and ratios: ratios[max(ratios,key=ratios.get)] += diff
    ml_dict = {ing:round(total_ml*pct/100,1) for ing,pct in ratios.items()}
    OG = {
        1:{"히알루론산","판테놀","글리세린"},
        2:{"나이아신아마이드","아스코빌글루코사이드","비타민C유도체","펩타이드"},
        3:{"아데노신","아세틸헥사펩타이드-8","레티닐팔미테이트","알란토인","피토스핑고신"},
        4:{"살리실산","스쿠알란"},
    }
    steps = {}
    for ing in ingredients:
        g = next((k for k,s in OG.items() if ing in s),5)
        steps.setdefault(g,[]).append(ing)
    SL = {1:"수용성 베이스 혼합",2:"기능성 성분 첨가",3:"고기능 활성 성분 첨가",4:"특수 성분 첨가",5:"기타"}
    return {"ratios":ratios,"ml":ml_dict,
            "steps":[{"label":SL.get(g,"성분 첨가"),"items":steps[g]} for g in sorted(steps)],
            "total_ml":total_ml}

def generate_scalp_mixing_guide(ingredients, scalp_result, seei_grade, total_ml=30):
    BW = {
        "피록톤올아민":25,"살리실산":20,"바이오틴":20,"판테놀":25,
        "나이아신아마이드":15,"히알루론산":15,"피토스핑고신":12,"아데노신":10,
        "티트리오일":15,"로즈마리오일":10,"멘톨":5,"소듐PCA":15,
    }
    ks=scalp_result.get("keratin_score",70); ps=scalp_result.get("pore_score",70)
    ts=scalp_result.get("hair_thickness_score",70); cs=scalp_result.get("scalp_color_score",70)
    ms=scalp_result.get("moisture_balance_score",70); ds=scalp_result.get("hair_damage_score",70)
    eb={"낮음":1.0,"보통":1.3,"높음":1.6,"매우높음":2.0}.get(seei_grade,1.0)
    weights = {}
    for ing in ingredients:
        w = BW.get(ing,10)
        if ing in {"살리실산","피록톤올아민","티트리오일"} and ks<50: w=round(w*1.5)
        if ing=="살리실산" and ps<50: w=round(w*1.3)
        if ing in {"바이오틴","판테놀"} and ts<50: w=round(w*1.5)
        if ing in {"판테놀","피토스핑고신"} and cs<50: w=round(w*1.4)
        if ing in {"판테놀","히알루론산","소듐PCA"} and ms<50: w=round(w*1.3)
        if ing in {"바이오틴","판테놀"} and ds<50: w=round(w*1.3)
        if ing in {"나이아신아마이드","피토스핑고신"}: w=round(w*eb)
        weights[ing]=max(w,5)
    tw     = sum(weights.values())
    ratios = {ing:round(w/tw*100) for ing,w in weights.items()}
    diff   = 100-sum(ratios.values())
    if diff and ratios: ratios[max(ratios,key=ratios.get)] += diff
    ml_dict = {ing:round(total_ml*pct/100,1) for ing,pct in ratios.items()}
    OG = {
        1:{"히알루론산","판테놀","소듐PCA"},
        2:{"나이아신아마이드","아데노신"},
        3:{"바이오틴","피토스핑고신"},
        4:{"피록톤올아민","살리실산","티트리오일","로즈마리오일","멘톨"},
    }
    steps = {}
    for ing in ingredients:
        g = next((k for k,s in OG.items() if ing in s),5)
        steps.setdefault(g,[]).append(ing)
    SL = {1:"두피 베이스 혼합",2:"기능성 성분 첨가",3:"모발·장벽 강화",4:"특수 성분 첨가",5:"기타"}
    return {"ratios":ratios,"ml":ml_dict,
            "steps":[{"label":SL.get(g,"성분 첨가"),"items":steps[g]} for g in sorted(steps)],
            "total_ml":total_ml}

# ══════════════════════════════════════════
# UI 컴포넌트
# ══════════════════════════════════════════
def show_mixing_card(mixing, title, is_scalp=False):
    bar_cls = "scalp-mixing-bar" if is_scalp else "mixing-bar"
    st.markdown("<div class='mixing-card'>", unsafe_allow_html=True)
    lbl_color = "#6ee7b7" if is_scalp else "#a5b4fc"
    st.markdown(
        f"<div style='font-size:0.65rem;letter-spacing:0.16em;text-transform:uppercase;"
        f"color:{lbl_color};font-weight:700;font-family:DM Mono,monospace;"
        f"margin-bottom:1rem;padding-bottom:0.7rem;"
        f"border-bottom:1px solid rgba(255,255,255,0.08);'>{title}</div>",
        unsafe_allow_html=True)
    st.markdown(
        "<div class='workshop-banner'>"
        "사전 준비된 성분 샘플로 즉시 제조 가능 — 아래 비율·ml량 참고하여 혼합</div>",
        unsafe_allow_html=True)
    rows = ""
    for ing, pct in sorted(mixing["ratios"].items(), key=lambda x: -x[1]):
        ml   = mixing["ml"].get(ing,0)
        conc = get_sample_conc(ing)
        conc_txt = f"{conc['pct']}%" if conc else "재량"
        rows += (
            f"<div class='mixing-row'>"
            f"<span class='mixing-ing'>{ing}</span>"
            f"<div class='mixing-bar-wrap'>"
            f"<div class='{bar_cls}' style='width:{pct}%;'></div></div>"
            f"<span class='mixing-pct'>{pct}%</span>"
            f"<span class='mixing-ml'>{ml}ml</span>"
            f"<span class='mixing-conc'>샘플 {conc_txt}</span>"
            f"</div>")
    st.markdown(rows, unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align:right;font-size:0.80rem;font-weight:700;"
        f"color:rgba(220,220,240,0.65);padding:0.5rem 0;'>총 {mixing['total_ml']}ml</div>",
        unsafe_allow_html=True)
    badge = "step-badge-green" if is_scalp else "step-badge"
    st.markdown(
        "<div style='margin-top:0.8rem;font-size:0.75rem;font-weight:700;"
        "color:rgba(210,210,240,0.65);margin-bottom:0.5rem;letter-spacing:0.08em;'>"
        "MIXING ORDER</div>", unsafe_allow_html=True)
    for dn, s in enumerate(mixing["steps"], start=1):
        items_str = " + ".join(s["items"])
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.5rem;"
            f"padding:0.4rem 0;font-size:0.82rem;color:rgba(220,220,240,0.80);'>"
            f"<span class='{badge}'>{dn}</span>"
            f"<span><b style='color:rgba(255,255,255,0.92);'>{s['label']}</b>"
            f" — {items_str}</span></div>",
            unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def show_air_status(air, uv_data=None, humidity_data=None):
    is_mock = air.get("mock")
    uv_mock = (uv_data or {}).get("mock",True)
    air_txt = (f"에어코리아 실측 / {air.get('station','')} / {air.get('fetch_time','')}"
               if not is_mock else "에어코리아: 시간대 추정값")
    kma_txt = ""
    if uv_data or humidity_data:
        kma_txt = f" | {'기상청 실측' if not uv_mock else '기상청: 시간대 추정값'}"
    css = "air-real" if not is_mock else "air-mock"
    st.markdown(
        f"<div class='{css}'>{air_txt}{kma_txt} | "
        f"PM2.5 {air.get('pm25','-')} | PM10 {air.get('pm10','-')} | "
        f"NO2 {air.get('no2','-')}ppm | O3 {air.get('o3','-')}ppm</div>",
        unsafe_allow_html=True)


def vol_selector(key_prefix):
    state_key = f"{key_prefix}_total_ml"
    if state_key not in st.session_state:
        st.session_state[state_key] = 30
    st.markdown(
        "<div class='glass-card'>"
        "<div class='card-label'>제조 용량 선택</div>",
        unsafe_allow_html=True)
    cols = st.columns(len(VOL_PRESETS))
    for i, preset in enumerate(VOL_PRESETS):
        with cols[i]:
            if st.button(preset["label"], key=f"{key_prefix}_vol_{i}",
                         use_container_width=True):
                st.session_state[state_key] = preset["ml"]
                st.rerun()
    chosen = st.number_input(
        "직접 입력 (ml)", min_value=5, max_value=300,
        value=st.session_state[state_key], step=5,
        key=f"{key_prefix}_custom_ml")
    st.session_state[state_key] = int(chosen)
    st.markdown("</div>", unsafe_allow_html=True)
    return st.session_state[state_key]

# ══════════════════════════════════════════
# 결과 렌더링 — 피부
# ══════════════════════════════════════════
def show_skin_result(result, air, region, res_str, pid, age, gender, parts):
    pm25_avg = REGION_PM25_AVG.get(region,22.0)
    yrs      = RESIDENCE_YEAR_MAP.get(res_str,0)
    ceei, ceei_grade, ceei_chip, ceei_msg = calc_ceei(pm25_avg,yrs)
    pm25_val  = air.get("pm25")
    alert     = get_pollution_alert(pm25_val,ceei)
    overall   = result.get("overall_score",0)
    skin_type = result.get("skin_type","")
    ings      = result.get("recommended_ingredients",[])

    st.markdown("<div class='patent-banner'>본 기술은 특허 출원 중입니다 (CEEI·SEEI 알고리즘)</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='medical-disclaimer'>본 분석 결과는 AI 기반 참고용 정보이며 의학적 진단이 아닙니다.</div>",
                unsafe_allow_html=True)
    show_air_status(air)

    sc = score_color(overall)
    st.markdown(
        f"<div class='glass-card'>"
        f"<div class='card-label'>피부 분석 종합 결과</div>"
        f"<div style='display:flex;align-items:center;gap:2rem;flex-wrap:wrap;'>"
        f"<div style='text-align:center;'>"
        f"<div class='big-score' style='color:{sc};'>{overall}</div>"
        f"<div style='font-size:0.70rem;color:rgba(200,200,230,0.55);margin-top:0.3rem;"
        f"font-family:DM Mono,monospace;letter-spacing:0.1em;'>OVERALL SCORE</div>"
        f"</div>"
        f"<div style='flex:1;'>"
        f"<div style='font-size:1.1rem;font-weight:700;color:white;margin-bottom:0.5rem;'>"
        f"피부 타입: <span style='color:{sc};text-shadow:0 0 15px {sc};'>{skin_type}</span></div>"
        f"<div class='result-text'>{result.get('summary','')}</div>"
        f"<div style='margin-top:0.7rem;'>{pm25_chip(pm25_val)} {ceei_chip}</div>"
        f"</div></div></div>",
        unsafe_allow_html=True)

    if alert:
        st.warning(alert)

    metrics = [
        ("주름",   result.get("wrinkle_score",0),  result.get("wrinkle_comment","")),
        ("모공",   result.get("pore_score",0),      result.get("pore_comment","")),
        ("피부결", result.get("texture_score",0),   result.get("texture_comment","")),
        ("피부톤", result.get("tone_score",0),       result.get("tone_comment","")),
        ("수분",   result.get("moisture_score",0),  result.get("moisture_comment","")),
    ]
    st.markdown("<div class='glass-card'><div class='card-label'>피부 5지표</div>",
                unsafe_allow_html=True)
    cols = st.columns(5)
    for i,(lbl,val,cmt) in enumerate(metrics):
        with cols[i]:
            st.markdown(svg_gauge(val,lbl,cmt,96), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    ing_html = "".join([f"<span class='ing-chip'>{ing}</span>" for ing in ings])
    st.markdown(
        f"<div class='glass-card'><div class='card-label'>AI 추천 화장품 성분</div>"
        f"<div style='margin-bottom:0.8rem;'>{ing_html}</div>"
        f"<div class='result-text'>{result.get('care_advice','')}</div></div>",
        unsafe_allow_html=True)

    chosen_ml = vol_selector("skin")
    if ings:
        mixing = generate_mixing_guide(ings,skin_type,ceei_grade,total_ml=chosen_ml)
        show_mixing_card(mixing,
            f"피부 맞춤 혼합 — {chosen_ml}ml / {skin_type}",is_scalp=False)

    st.markdown(
        f"<div class='glass-card'><div class='card-label'>CEEI 피부 누적 환경노출지수</div>"
        f"<div style='display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.7rem;'>"
        f"{pm25_chip(pm25_val)} {ceei_chip}"
        f"<span class='chip chip-neu'>연평균 {pm25_avg}㎍/m³</span>"
        f"<span class='chip chip-neu'>거주 {yrs}년</span></div>"
        f"<div class='result-text'>{ceei_msg}</div></div>",
        unsafe_allow_html=True)

    scores = {"주름":result.get("wrinkle_score",0),"모공":result.get("pore_score",0),
              "피부결":result.get("texture_score",0),"피부톤":result.get("tone_score",0),
              "수분":result.get("moisture_score",0)}
    pri = sorted([(k,v) for k,v in scores.items() if v>0],key=lambda x:x[1])[:3]
    if not pri: pri = sorted(scores.items(),key=lambda x:x[1])[:3]
    st.markdown("<div class='glass-card'><div class='card-label'>우선 개선 항목</div>",
                unsafe_allow_html=True)
    for i,(lbl,sc_) in enumerate(pri):
        cm = "집중 케어 필요" if sc_<40 else "개선 권장" if sc_<60 else "유지 관리"
        st.markdown(
            f"<div class='priority-item'>"
            f"<span class='priority-num'>{i+1}</span>"
            f"<span class='priority-label'>{lbl}</span>"
            f"<span class='priority-score' style='color:{score_color(sc_)};"
            f"text-shadow:0 0 10px {score_color(sc_)};'>{sc_}</span>"
            f"<span class='priority-msg'>{cm}</span></div>",
            unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    mixing_final = generate_mixing_guide(ings,skin_type,ceei_grade,total_ml=chosen_ml)
    c1,c2 = st.columns(2)
    with c1:
        html = generate_skin_report_html(result,air,region,yrs,pid,age,gender,mixing_final)
        st.download_button("피부 분석 리포트 다운로드",data=html.encode("utf-8"),
            file_name=f"YDLab_피부리포트_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",use_container_width=True,key="k_skin_report")
    with c2:
        html2 = generate_skin_order_html(result,air,region,yrs,pid,age,gender,mixing_final)
        st.download_button("피부 공방 주문서 다운로드",data=html2.encode("utf-8"),
            file_name=f"YDLab_피부주문서_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",use_container_width=True,key="k_skin_order")

# ══════════════════════════════════════════
# 결과 렌더링 — 두피
# ══════════════════════════════════════════
def show_scalp_result(result, air, region, res_str, pid, age, gender, parts,
                      uv_data=None, humidity_data=None):
    pm25_avg  = REGION_PM25_AVG.get(region,22.0)
    yrs       = RESIDENCE_YEAR_MAP.get(res_str,0)
    ceei,ceei_grade,ceei_chip,_ = calc_ceei(pm25_avg,yrs)
    (seei,seei_grade,seei_chip,seei_msg,seei_comp,season_corr,
     uv_val,uv_gstr,hum_val,hum_corr) = calc_seei(air,yrs,uv_data,humidity_data)
    _,uv_corr,uv_color = uv_index_grade(uv_val)
    pm25_val   = air.get("pm25")
    overall    = result.get("overall_score",0)
    scalp_type = result.get("scalp_type","")
    ings       = result.get("recommended_ingredients",[])

    st.markdown("<div class='patent-banner'>본 기술은 특허 출원 중입니다 (CEEI·SEEI 알고리즘 / 기상청 연동)</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='medical-disclaimer'>본 분석 결과는 AI 기반 참고용 정보이며 의학적 진단이 아닙니다.</div>",
                unsafe_allow_html=True)
    show_air_status(air,uv_data,humidity_data)

    sc = score_color(overall)
    st.markdown(
        f"<div class='glass-card' style='border-color:rgba(16,185,129,0.25);'>"
        f"<div class='card-label-green'>두피 분석 종합 결과</div>"
        f"<div style='display:flex;align-items:center;gap:2rem;flex-wrap:wrap;'>"
        f"<div style='text-align:center;'>"
        f"<div class='big-score' style='color:{sc};'>{overall}</div>"
        f"<div style='font-size:0.70rem;color:rgba(200,200,230,0.55);margin-top:0.3rem;"
        f"font-family:DM Mono,monospace;letter-spacing:0.1em;'>SCALP SCORE</div>"
        f"</div>"
        f"<div style='flex:1;'>"
        f"<div style='font-size:1.1rem;font-weight:700;color:white;margin-bottom:0.5rem;'>"
        f"두피 타입: <span style='color:{sc};text-shadow:0 0 15px {sc};'>{scalp_type}</span></div>"
        f"<div class='result-text'>{result.get('summary','')}</div>"
        f"<div style='margin-top:0.7rem;'>{pm25_chip(pm25_val)} {seei_chip}</div>"
        f"</div></div></div>",
        unsafe_allow_html=True)

    scalp_metrics = [
        ("각질",     result.get("keratin_score",0),          result.get("keratin_comment","")),
        ("모공피지", result.get("pore_score",0),             result.get("pore_comment","")),
        ("모발굵기", result.get("hair_thickness_score",0),   result.get("hair_thickness_comment","")),
        ("색상염증", result.get("scalp_color_score",0),      result.get("scalp_color_comment","")),
        ("수분유분", result.get("moisture_balance_score",0), result.get("moisture_balance_comment","")),
        ("손상도",   result.get("hair_damage_score",0),      result.get("hair_damage_comment","")),
    ]
    st.markdown("<div class='scalp-section'><div class='card-label-green'>두피 분석 6지표</div>",
                unsafe_allow_html=True)
    cols = st.columns(3)
    for i,(lbl,val,cmt) in enumerate(scalp_metrics):
        with cols[i%3]:
            st.markdown(svg_gauge(val,lbl,cmt,96), unsafe_allow_html=True)
    hl  = result.get("hair_loss_risk_score",0)
    hlc = result.get("hair_loss_risk_comment","")
    st.markdown(
        f"<div class='hair-loss-box'>"
        f"<span style='color:rgba(220,220,240,0.75);font-size:0.80rem;'>"
        f"탈모 진행도 (참고용)</span> "
        f"<span style='font-weight:700;font-family:DM Mono,monospace;"
        f"color:{score_color(hl)};text-shadow:0 0 10px {score_color(hl)};'>{hl}점</span>"
        f"<span style='color:rgba(200,200,230,0.60);font-size:0.78rem;'> — {hlc}</span></div>",
        unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    ing_html = "".join([f"<span class='scalp-chip'>{ing}</span>" for ing in ings])
    st.markdown(
        f"<div class='glass-card' style='border-color:rgba(16,185,129,0.20);'>"
        f"<div class='card-label-green'>AI 추천 두피·모발 성분</div>"
        f"<div style='margin-bottom:0.8rem;'>{ing_html}</div>"
        f"<div class='result-text'>{result.get('care_advice','')}</div></div>",
        unsafe_allow_html=True)

    chosen_ml = vol_selector("scalp")
    if ings:
        mixing = generate_scalp_mixing_guide(ings,result,seei_grade,total_ml=chosen_ml)
        show_mixing_card(mixing,
            f"두피 맞춤 혼합 — {chosen_ml}ml / {scalp_type} / SEEI {seei_grade}",
            is_scalp=True)

    comp_boxes = "".join([
        f"<div style='background:rgba(255,255,255,0.05);border:1px solid rgba(16,185,129,0.16);"
        f"border-radius:10px;padding:0.6rem;text-align:center;'>"
        f"<div style='font-weight:700;color:#6ee7b7;font-size:0.88rem;"
        f"font-family:DM Mono,monospace;'>{v}</div>"
        f"<div style='color:rgba(200,200,230,0.55);font-size:0.65rem;margin-top:0.2rem;'>{k}</div></div>"
        for k,v in seei_comp.items()])
    uv_d  = f"{uv_val:.1f}" if uv_val is not None else "--"
    hum_d = f"{hum_val:.0f}%" if hum_val is not None else "--"
    uv_mt  = "" if not (uv_data  or {}).get("mock",True) else " (추정)"
    hum_mt = "" if not (humidity_data or {}).get("mock",True) else " (추정)"
    st.markdown(
        f"<div class='seei-box'>"
        f"<div style='font-size:0.65rem;letter-spacing:0.16em;text-transform:uppercase;"
        f"color:rgba(110,231,183,0.90);font-weight:700;font-family:DM Mono,monospace;"
        f"margin-bottom:0.8rem;padding-bottom:0.5rem;border-bottom:1px solid rgba(16,185,129,0.18);'>"
        f"SEEI v3 — 두피 복합 환경노출지수 (특허 출원 중)</div>"
        f"<div style='display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.8rem;'>"
        f"{seei_chip} {ceei_chip}"
        f"<span class='chip chip-neu'>거주 {yrs}년</span>"
        f"<span class='chip chip-neu'>계절보정 ×{season_corr}</span></div>"
        f"<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem;"
        f"margin-bottom:0.8rem;'>{comp_boxes}</div>"
        f"<div class='kma-box'>"
        f"<div style='font-size:0.68rem;font-weight:700;color:rgba(220,220,240,0.55);"
        f"margin-bottom:0.5rem;letter-spacing:0.1em;'>KMA 기상청</div>"
        f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;'>"
        f"<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(245,158,11,0.22);"
        f"border-radius:10px;padding:0.6rem;text-align:center;'>"
        f"<div style='font-weight:700;color:{uv_color};font-size:1rem;"
        f"font-family:DM Mono,monospace;text-shadow:0 0 10px {uv_color};'>{uv_d}{uv_mt}</div>"
        f"<div style='color:rgba(200,200,230,0.55);font-size:0.65rem;margin-top:0.2rem;'>"
        f"자외선 [{uv_gstr}]</div>"
        f"<div style='color:rgba(180,180,220,0.35);font-size:0.60rem;'>UV ×{uv_corr}</div></div>"
        f"<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(59,130,246,0.22);"
        f"border-radius:10px;padding:0.6rem;text-align:center;'>"
        f"<div style='font-weight:700;color:#93c5fd;font-size:1rem;"
        f"font-family:DM Mono,monospace;text-shadow:0 0 10px #93c5fd;'>{hum_d}{hum_mt}</div>"
        f"<div style='color:rgba(200,200,230,0.55);font-size:0.65rem;margin-top:0.2rem;'>습도</div>"
        f"<div style='color:rgba(180,180,220,0.35);font-size:0.60rem;'>습도 ×{hum_corr}</div></div>"
        f"</div></div>"
        f"<div style='font-size:0.72rem;color:rgba(180,180,220,0.40);margin-top:0.6rem;"
        f"font-style:italic;font-family:DM Mono,monospace;'>"
        f"SEEI = (PM2.5×0.40+PM10×0.25+NO2×0.20+O3×0.15)×거주기간×계절×UV×습도</div>"
        f"<div class='result-text' style='margin-top:0.5rem;'>{seei_msg}</div></div>",
        unsafe_allow_html=True)

    pri_scores = {
        "각질":result.get("keratin_score",0),"모공피지":result.get("pore_score",0),
        "모발굵기":result.get("hair_thickness_score",0),
        "색상염증":result.get("scalp_color_score",0),
        "수분유분":result.get("moisture_balance_score",0),
        "손상도":result.get("hair_damage_score",0),
    }
    pri = sorted([(k,v) for k,v in pri_scores.items() if v>0],key=lambda x:x[1])[:3]
    if not pri: pri = sorted(pri_scores.items(),key=lambda x:x[1])[:3]
    st.markdown("<div class='glass-card' style='border-color:rgba(16,185,129,0.20);'>"
                "<div class='card-label-green'>우선 개선 항목 (두피)</div>",
                unsafe_allow_html=True)
    for i,(lbl,sc_) in enumerate(pri):
        cm = "집중 케어 필요" if sc_<40 else "개선 권장" if sc_<60 else "유지 관리"
        st.markdown(
            f"<div class='priority-item'>"
            f"<span class='priority-num' style='background:linear-gradient(135deg,#10b981,#059669);"
            f"box-shadow:0 0 10px rgba(16,185,129,0.4);'>{i+1}</span>"
            f"<span class='priority-label'>{lbl}</span>"
            f"<span class='priority-score' style='color:{score_color(sc_)};"
            f"text-shadow:0 0 10px {score_color(sc_)};'>{sc_}</span>"
            f"<span class='priority-msg'>{cm}</span></div>",
            unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    mixing_final = generate_scalp_mixing_guide(ings,result,seei_grade,total_ml=chosen_ml)
    c1,c2 = st.columns(2)
    with c1:
        html = generate_scalp_report_html(
            result,air,region,yrs,pid,age,gender,mixing_final,
            seei,seei_grade,seei_msg,seei_comp,season_corr,
            uv_val,uv_gstr,uv_corr,hum_val,hum_corr)
        st.download_button("두피 분석 리포트 다운로드",data=html.encode("utf-8"),
            file_name=f"YDLab_두피리포트_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",use_container_width=True,key="k_scalp_report")
    with c2:
        html2 = generate_scalp_order_html(
            result,air,region,yrs,pid,age,gender,mixing_final,
            seei,seei_grade,seei_msg,uv_val,uv_gstr,hum_val)
        st.download_button("두피 공방 주문서 다운로드",data=html2.encode("utf-8"),
            file_name=f"YDLab_두피주문서_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",use_container_width=True,key="k_scalp_order")

# ══════════════════════════════════════════
# HTML 리포트·주문서 (다크 테마)
# ══════════════════════════════════════════
def _html_head(title, bg_from, bg_to):
    return (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title>"
        f"<style>"
        f"@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap');"
        f"*{{box-sizing:border-box;margin:0;padding:0;}}"
        f"body{{font-family:'Noto Sans KR',sans-serif;font-size:12px;"
        f"background:linear-gradient(135deg,{bg_from},{bg_to});color:#e2e8f0;min-height:100vh;}}"
        f".wrap{{max-width:900px;margin:0 auto;padding:20px;}}"
        f".header{{background:rgba(255,255,255,0.06);backdrop-filter:blur(20px);"
        f"border:1px solid rgba(255,255,255,0.10);border-radius:16px;"
        f"padding:20px 28px;margin-bottom:16px;"
        f"display:flex;justify-content:space-between;align-items:center;}}"
        f".header h1{{font-size:18px;font-weight:700;color:white;}}"
        f".header .sub{{font-size:9px;opacity:0.6;margin-top:3px;color:#a5b4fc;}}"
        f".card{{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);"
        f"border-radius:14px;padding:16px 20px;margin-bottom:12px;}}"
        f".stitle{{font-size:8px;font-weight:700;letter-spacing:0.14em;"
        f"text-transform:uppercase;color:#a5b4fc;margin-bottom:10px;font-family:'DM Mono',monospace;}}"
        f".stitle-green{{font-size:8px;font-weight:700;letter-spacing:0.14em;"
        f"text-transform:uppercase;color:#6ee7b7;margin-bottom:10px;font-family:'DM Mono',monospace;}}"
        f"table{{width:100%;border-collapse:collapse;font-size:10px;}}"
        f"th{{background:rgba(99,102,241,0.25);color:#c7d2fe;padding:7px 8px;"
        f"text-align:left;font-size:9px;border:1px solid rgba(99,102,241,0.20);}}"
        f"td{{padding:6px 8px;border:1px solid rgba(255,255,255,0.07);color:#cbd5e1;}}"
        f"tr:nth-child(even) td{{background:rgba(255,255,255,0.03);}}"
        f".chip{{background:rgba(255,255,255,0.08);color:#94a3b8;border-radius:10px;"
        f"padding:2px 8px;font-size:9px;display:inline-block;margin:2px;"
        f"border:1px solid rgba(255,255,255,0.10);}}"
        f".footer{{text-align:center;color:rgba(255,255,255,0.30);"
        f"font-size:8px;padding:12px;margin-top:8px;}}"
        f".print-btn{{position:fixed;bottom:20px;right:20px;"
        f"background:linear-gradient(135deg,#6366f1,#8b5cf6);"
        f"color:white;border:none;padding:10px 20px;border-radius:10px;"
        f"font-size:13px;cursor:pointer;"
        f"box-shadow:0 4px 15px rgba(99,102,241,0.4);}}"
        f"@media print{{.print-btn{{display:none;}}}}"
        f"</style></head><body><div class='wrap'>"
        f"<button class='print-btn' onclick='window.print()'>PDF 저장</button>")

def _mixing_html_table(mixing, color_h):
    if not mixing: return ""
    rows = "".join([
        f"<tr><td style='text-align:center;font-weight:700;color:{color_h};'>{i+1}</td>"
        f"<td style='font-weight:700;color:#e2e8f0;'>{ing}</td>"
        f"<td style='font-weight:700;color:{color_h};font-family:monospace;'>{pct}%</td>"
        f"<td style='font-weight:700;color:#93c5fd;font-family:monospace;'>{mixing['ml'].get(ing,0)}ml</td>"
        f"<td style='color:#94a3b8;'>{(get_sample_conc(ing) or {}).get('pct','재량')}%</td>"
        f"<td style='color:#64748b;font-size:9px;'>{(get_sample_conc(ing) or {}).get('note','')}</td></tr>"
        for i,(ing,pct) in enumerate(sorted(mixing["ratios"].items(),key=lambda x:-x[1]))])
    total_row = (f"<tr style='background:rgba(99,102,241,0.20);'>"
                 f"<td colspan='3' style='text-align:right;color:#a5b4fc;font-weight:700;'>합계</td>"
                 f"<td style='font-family:monospace;color:#93c5fd;font-weight:700;'>{mixing['total_ml']}ml</td>"
                 f"<td colspan='2'></td></tr>")
    steps = "".join([
        f"<div style='display:flex;align-items:center;gap:6px;padding:4px 0;"
        f"font-size:10px;border-bottom:1px solid rgba(255,255,255,0.05);'>"
        f"<span style='background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;"
        f"border-radius:50%;width:18px;height:18px;display:inline-flex;align-items:center;"
        f"justify-content:center;font-size:8px;font-weight:700;flex-shrink:0;'>{dn}</span>"
        f"<span style='color:#cbd5e1;'><b style='color:#e2e8f0;'>{s['label']}</b>"
        f" — {' + '.join(s['items'])}</span></div>"
        for dn,s in enumerate(mixing["steps"],start=1)])
    return (f"<div class='card'><div class='stitle'>공방 제조 처방 (총 {mixing['total_ml']}ml)</div>"
            f"<table><tr><th>#</th><th>성분명</th><th>혼합비율</th>"
            f"<th>투입량</th><th>샘플농도</th><th>비고</th></tr>"
            f"{rows}{total_row}</table>"
            f"<div style='margin-top:10px;font-size:9px;font-weight:700;"
            f"color:#a5b4fc;margin-bottom:5px;font-family:DM Mono,monospace;letter-spacing:0.1em;'>"
            f"MIXING ORDER</div>{steps}</div>")

def generate_skin_report_html(result, air, region, yrs, pid, age, gender, mixing=None):
    overall  = result.get("overall_score",0)
    st_type  = result.get("skin_type","")
    ings     = result.get("recommended_ingredients",[])
    pm25_avg = REGION_PM25_AVG.get(region,22.0)
    ceei,cg,_,cm = calc_ceei(pm25_avg,yrs)
    def sc(s): return "#10b981" if s>=70 else "#f59e0b" if s>=40 else "#ef4444"
    mets = [("주름",result.get("wrinkle_score",0),result.get("wrinkle_comment","")),
            ("모공",result.get("pore_score",0),result.get("pore_comment","")),
            ("피부결",result.get("texture_score",0),result.get("texture_comment","")),
            ("피부톤",result.get("tone_score",0),result.get("tone_comment","")),
            ("수분",result.get("moisture_score",0),result.get("moisture_comment",""))]
    sboxes = "".join([
        f"<div style='flex:1;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);"
        f"border-radius:10px;padding:10px 6px;text-align:center;'>"
        f"<div style='font-size:22px;font-weight:700;color:{sc(v)};font-family:DM Mono,monospace;"
        f"text-shadow:0 0 10px {sc(v)};'>{v}</div>"
        f"<div style='font-size:8px;color:#94a3b8;margin-top:3px;'>{l}</div>"
        f"<div style='font-size:7px;color:#64748b;margin-top:3px;line-height:1.3;'>{c}</div></div>"
        for l,v,c in mets])
    ing_h = "".join([
        f"<span style='background:rgba(99,102,241,0.15);color:#a5b4fc;"
        f"border:1px solid rgba(99,102,241,0.25);border-radius:6px;"
        f"padding:2px 8px;font-size:9px;display:inline-block;margin:2px;'>{i}</span>"
        for i in ings])
    is_mock = air.get("mock",True)
    atxt    = (f"에어코리아 실측 / {air.get('station','')} / {air.get('fetch_time','')}"
               if not is_mock else "시간대 추정값")
    gc = {"낮음":"#10b981","보통":"#3b82f6","높음":"#f59e0b","매우높음":"#ef4444"}.get(cg,"#94a3b8")
    return (
        _html_head("YD Lab 피부 분석 리포트","#0a0a1a","#0d1b3e") +
        f"<div class='header'>"
        f"<div><h1>YD Lab 피부 분석 리포트</h1>"
        f"<div class='sub'>재능대학교 AI-바이오분석특화연구소 / CEEI 특허 출원 중</div></div>"
        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#a5b4fc;'>"
        f"{datetime.now().strftime('%Y.%m.%d')}</div></div>"
        f"<div class='card' style='background:rgba(99,102,241,0.08);"
        f"border-color:rgba(99,102,241,0.20);'>"
        f"<div style='font-size:9px;color:{'#6ee7b7' if not is_mock else '#fcd34d'};"
        f"font-weight:600;margin-bottom:5px;'>{atxt}</div>"
        f"<div style='font-size:10px;color:#94a3b8;'>"
        f"코드: {pid} / {age} / {gender} / {region} / 거주 {yrs}년</div></div>"
        f"<div class='card'><div class='stitle'>종합 결과</div>"
        f"<div style='display:flex;align-items:center;gap:20px;'>"
        f"<div style='font-size:52px;font-weight:900;color:{sc(overall)};"
        f"font-family:DM Mono,monospace;line-height:1;"
        f"text-shadow:0 0 20px {sc(overall)};'>{overall}</div>"
        f"<div><div style='font-size:14px;font-weight:700;color:white;margin-bottom:5px;'>"
        f"피부 타입: <span style='color:{sc(overall)};'>{st_type}</span></div>"
        f"<div style='font-size:9px;color:#94a3b8;line-height:1.65;'>{result.get('summary','')}</div>"
        f"</div></div></div>"
        f"<div class='card'><div class='stitle'>피부 5지표</div>"
        f"<div style='display:flex;gap:8px;'>{sboxes}</div></div>"
        f"<div class='card'><div class='stitle'>AI 추천 성분</div>"
        f"<div style='margin-bottom:7px;'>{ing_h}</div>"
        f"<div style='font-size:9px;color:#94a3b8;line-height:1.6;'>{result.get('care_advice','')}</div></div>"
        f"{_mixing_html_table(mixing,'#a5b4fc')}"
        f"<div class='card'><div class='stitle'>CEEI 피부 환경노출지수</div>"
        f"<div><span class='chip'>PM2.5 {air.get('pm25','-')}㎍/m³</span>"
        f"<span class='chip' style='color:{gc};border-color:{gc};'>CEEI {ceei} [{cg}]</span></div>"
        f"<div style='font-size:9px;color:#94a3b8;margin-top:5px;'>{cm}</div></div>"
        f"</div><div class='footer'>본 리포트는 참고용이며 의료적 진단을 대체하지 않습니다 | YD Lab / 재능대학교</div>"
        f"</div></body></html>")

def generate_scalp_report_html(result, air, region, yrs, pid, age, gender,
                                mixing=None, seei=0, seei_grade="낮음", seei_msg="",
                                seei_comp=None, season_corr=1.0,
                                uv_val=None, uv_gstr="알수없음",
                                uv_corr=1.0, hum_val=None, hum_corr=1.0):
    overall  = result.get("overall_score",0)
    st_type  = result.get("scalp_type","")
    ings     = result.get("recommended_ingredients",[])
    seei_comp = seei_comp or {}
    def sc(s): return "#10b981" if s>=70 else "#f59e0b" if s>=40 else "#ef4444"
    smets = [
        ("각질",result.get("keratin_score",0),result.get("keratin_comment","")),
        ("모공피지",result.get("pore_score",0),result.get("pore_comment","")),
        ("모발굵기",result.get("hair_thickness_score",0),result.get("hair_thickness_comment","")),
        ("색상염증",result.get("scalp_color_score",0),result.get("scalp_color_comment","")),
        ("수분유분",result.get("moisture_balance_score",0),result.get("moisture_balance_comment","")),
        ("손상도",result.get("hair_damage_score",0),result.get("hair_damage_comment","")),
    ]
    sboxes = "".join([
        f"<div style='flex:1;min-width:80px;background:rgba(16,185,129,0.06);"
        f"border:1px solid rgba(16,185,129,0.15);border-radius:10px;padding:10px 6px;text-align:center;'>"
        f"<div style='font-size:22px;font-weight:700;color:{sc(v)};font-family:DM Mono,monospace;"
        f"text-shadow:0 0 10px {sc(v)};'>{v}</div>"
        f"<div style='font-size:8px;color:#94a3b8;margin-top:3px;'>{l}</div>"
        f"<div style='font-size:7px;color:#64748b;margin-top:3px;'>{c}</div></div>"
        for l,v,c in smets])
    hl  = result.get("hair_loss_risk_score",0)
    hlc = result.get("hair_loss_risk_comment","")
    ing_h = "".join([
        f"<span style='background:rgba(16,185,129,0.12);color:#6ee7b7;"
        f"border:1px solid rgba(16,185,129,0.22);border-radius:6px;"
        f"padding:2px 8px;font-size:9px;display:inline-block;margin:2px;'>{i}</span>"
        for i in ings])
    sg = {"낮음":"#10b981","보통":"#3b82f6","높음":"#f59e0b","매우높음":"#ef4444"}.get(seei_grade,"#94a3b8")
    comp_h = "".join([f"<span class='chip' style='color:#6ee7b7;'>{k}: {v}</span>" for k,v in seei_comp.items()])
    is_mock = air.get("mock",True)
    atxt    = (f"에어코리아 실측 / {air.get('station','')} / {air.get('fetch_time','')}"
               if not is_mock else "시간대 추정값")
    uv_d  = f"{uv_val:.1f}" if uv_val is not None else "--"
    hum_d = f"{hum_val:.0f}%" if hum_val is not None else "--"
    return (
        _html_head("YD Lab 두피 분석 리포트","#0a0a1a","#0a1a0d") +
        f"<div class='header' style='border-color:rgba(16,185,129,0.20);'>"
        f"<div><h1 style='color:white;'>YD Lab 두피 분석 리포트</h1>"
        f"<div class='sub' style='color:#6ee7b7;'>재능대학교 / SEEI v3 특허 출원 중 / 기상청 연동</div></div>"
        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#6ee7b7;'>"
        f"{datetime.now().strftime('%Y.%m.%d')}</div></div>"
        f"<div class='card' style='background:rgba(16,185,129,0.06);"
        f"border-color:rgba(16,185,129,0.15);'>"
        f"<div style='font-size:9px;color:{'#6ee7b7' if not is_mock else '#fcd34d'};"
        f"font-weight:600;margin-bottom:5px;'>{atxt}</div>"
        f"<div style='font-size:10px;color:#94a3b8;'>"
        f"코드: {pid} / {age} / {gender} / {region} / 거주 {yrs}년 / "
        f"<span style='color:{sg};font-weight:700;'>SEEI {seei} [{seei_grade}]</span></div></div>"
        f"<div class='card'><div class='stitle-green'>종합 결과</div>"
        f"<div style='display:flex;align-items:center;gap:20px;'>"
        f"<div style='font-size:52px;font-weight:900;color:{sc(overall)};"
        f"font-family:DM Mono,monospace;line-height:1;"
        f"text-shadow:0 0 20px {sc(overall)};'>{overall}</div>"
        f"<div><div style='font-size:14px;font-weight:700;color:white;margin-bottom:5px;'>"
        f"두피 타입: <span style='color:{sc(overall)};'>{st_type}</span></div>"
        f"<div style='font-size:9px;color:#94a3b8;line-height:1.65;'>{result.get('summary','')}</div>"
        f"</div></div></div>"
        f"<div class='card'><div class='stitle-green'>두피 6지표</div>"
        f"<div style='display:flex;gap:7px;flex-wrap:wrap;'>{sboxes}</div>"
        f"<div style='margin-top:8px;background:rgba(245,158,11,0.08);"
        f"border:1px solid rgba(245,158,11,0.18);border-radius:8px;padding:6px 10px;font-size:9px;'>"
        f"탈모 진행도: <span style='color:{sc(hl)};font-weight:700;font-family:DM Mono,monospace;'>{hl}점</span>"
        f" — {hlc}</div></div>"
        f"<div class='card'><div class='stitle-green'>AI 추천 두피·모발 성분</div>"
        f"<div style='margin-bottom:7px;'>{ing_h}</div>"
        f"<div style='font-size:9px;color:#94a3b8;line-height:1.6;'>{result.get('care_advice','')}</div></div>"
        f"{_mixing_html_table(mixing,'#6ee7b7')}"
        f"<div class='card'><div class='stitle-green'>SEEI v3 두피 복합 환경노출지수</div>"
        f"<div style='margin-bottom:6px;'><span class='chip' style='color:{sg};'>SEEI {seei} [{seei_grade}]</span>"
        f"<span class='chip'>계절×{season_corr}</span><span class='chip'>UV×{uv_corr}</span>"
        f"<span class='chip'>습도×{hum_corr}</span></div>"
        f"<div style='margin:5px 0;'>{comp_h}</div>"
        f"<div style='background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.18);"
        f"border-radius:8px;padding:5px 10px;font-size:9px;color:#fcd34d;'>"
        f"자외선: {uv_d} [{uv_gstr}] / 습도: {hum_d}</div>"
        f"<div style='font-size:9px;color:#94a3b8;margin-top:5px;'>{seei_msg}</div></div>"
        f"</div><div class='footer'>본 리포트는 참고용이며 의료적 진단을 대체하지 않습니다 | YD Lab / 재능대학교</div>"
        f"</div></body></html>")

def generate_skin_order_html(result, air, region, yrs, pid, age, gender, mixing=None):
    code     = ("YDL-SKIN-"+datetime.now().strftime("%Y%m%d")+"-"
                +''.join(random.choices(string.ascii_uppercase+string.digits,k=4)))
    overall  = result.get("overall_score",0)
    st_type  = result.get("skin_type","")
    ings     = result.get("recommended_ingredients",[])
    pm25_avg = REGION_PM25_AVG.get(region,22.0)
    ceei,cg,_,cm = calc_ceei(pm25_avg,yrs)
    is_mock  = air.get("mock",True)
    total_ml = mixing["total_ml"] if mixing else 30
    purpose  = {
        "히알루론산":"즉각 수분 공급·보습","나이아신아마이드":"피부톤 균일화·모공",
        "판테놀":"피부 진정·보습 (Pro-B5)","아스코빌글루코사이드":"항산화·미백 (안정형 Vit.C)",
        "비타민C유도체":"항산화·미백","레티닐팔미테이트":"주름개선 기능성 고시",
        "아세틸헥사펩타이드-8":"주름 이완·탄력","피토스핑고신":"피부 장벽 강화",
        "펩타이드":"탄력·항노화","아데노신":"주름개선 기능성",
        "글리세린":"기초 보습","알란토인":"피부 진정·재생","스쿠알란":"보습·장벽 오일","살리실산":"각질 용해",
    }
    def sc(s): return "#10b981" if s>=70 else "#f59e0b" if s>=40 else "#ef4444"
    rows = "".join([
        f"<tr><td style='text-align:center;font-weight:700;color:#a5b4fc;'>{i+1}</td>"
        f"<td style='font-weight:700;color:#e2e8f0;'>{ing}</td>"
        f"<td style='color:#94a3b8;'>{purpose.get(ing,'피부 상태 개선')}</td>"
        f"<td style='font-weight:700;color:#10b981;font-family:monospace;'>"
        f"{mixing['ratios'].get(ing,'-') if mixing else '-'}%</td>"
        f"<td style='font-weight:700;color:#93c5fd;font-family:monospace;'>"
        f"{mixing['ml'].get(ing,'-') if mixing else '-'}ml</td>"
        f"<td style='color:#94a3b8;'>{(get_sample_conc(ing) or {}).get('pct','재량')}%</td>"
        f"<td style='color:#64748b;font-size:9px;'>{(get_sample_conc(ing) or {}).get('note','')}</td></tr>"
        for i,ing in enumerate(ings)])
    steps_h = "".join([
        f"<div style='display:flex;align-items:center;gap:7px;padding:5px 0;"
        f"font-size:10px;border-bottom:1px solid rgba(255,255,255,0.05);'>"
        f"<span style='background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;"
        f"border-radius:50%;width:18px;height:18px;display:inline-flex;align-items:center;"
        f"justify-content:center;font-size:8px;font-weight:700;flex-shrink:0;'>{dn}</span>"
        f"<span style='color:#cbd5e1;'><b style='color:#e2e8f0;'>{s['label']}</b>"
        f" — {' + '.join(s['items'])}</span></div>"
        for dn,s in enumerate(mixing["steps"],start=1)]) if mixing else ""
    gc = {"낮음":"#10b981","보통":"#3b82f6","높음":"#f59e0b","매우높음":"#ef4444"}.get(cg,"#94a3b8")
    return (
        _html_head(f"YD Lab 피부 공방 주문서 {code}","#0a0a1a","#0d1b3e") +
        f"<div class='header'>"
        f"<div><h1>YD Lab 피부 공방 주문서</h1>"
        f"<div class='sub'>AI 피부 분석 기반 맞춤형 화장품 제조 요청</div></div>"
        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#a5b4fc;'>{code}</div></div>"
        f"<div class='card' style='background:rgba(16,185,129,0.06);"
        f"border-color:rgba(16,185,129,0.15);font-size:9px;color:#6ee7b7;font-weight:600;'>"
        f"사전 준비된 권장농도 샘플을 사용하여 아래 비율대로 혼합하세요.</div>"
        f"<div class='card'><div style='font-size:10px;color:#94a3b8;'>"
        f"분석일: {datetime.now().strftime('%Y년 %m월 %d일')} / "
        f"참여자: {pid} {age} {gender} / 거주: {region} {yrs}년 / "
        f"피부타입: {st_type} / 종합: {overall}점 / 총 {total_ml}ml</div></div>"
        f"<div class='card'><div class='stitle'>성분 처방 혼합 비율</div>"
        f"<table><tr><th>#</th><th>성분명</th><th>목적</th><th>혼합비율</th>"
        f"<th>투입량</th><th>샘플농도</th><th>비고</th></tr>"
        f"{rows}"
        f"<tr style='background:rgba(99,102,241,0.20);'>"
        f"<td colspan='4' style='text-align:right;color:#a5b4fc;font-weight:700;'>합계</td>"
        f"<td style='color:#93c5fd;font-weight:700;font-family:monospace;'>{total_ml}ml</td>"
        f"<td colspan='2'></td></tr></table></div>"
        f"<div class='card'><div class='stitle'>제조 순서</div>{steps_h}</div>"
        f"<div class='card' style='font-size:10px;color:#94a3b8;'>"
        f"CEEI {ceei} [{cg}] / PM2.5 {air.get('pm25','-')}㎍/m³ / "
        f"{'에어코리아 실측' if not is_mock else '시간대 추정값'} / {cm}</div>"
        f"</div><div class='footer'>본 주문서는 AI 분석 기반이며 의료적 처방이 아닙니다 | YD Lab / 재능대학교</div>"
        f"</div></body></html>")

def generate_scalp_order_html(result, air, region, yrs, pid, age, gender,
                               mixing=None, seei=0, seei_grade="낮음", seei_msg="",
                               uv_val=None, uv_gstr="알수없음", hum_val=None):
    code     = ("YDL-SCALP-"+datetime.now().strftime("%Y%m%d")+"-"
                +''.join(random.choices(string.ascii_uppercase+string.digits,k=4)))
    overall  = result.get("overall_score",0)
    st_type  = result.get("scalp_type","")
    ings     = result.get("recommended_ingredients",[])
    is_mock  = air.get("mock",True)
    total_ml = mixing["total_ml"] if mixing else 30
    sg = {"낮음":"#10b981","보통":"#3b82f6","높음":"#f59e0b","매우높음":"#ef4444"}.get(seei_grade,"#94a3b8")
    purpose  = {
        "피록톤올아민":"비듬·항균 (ZPT 대체 / EU 허용)","살리실산":"두피 각질 용해",
        "바이오틴":"모발 강화·성장","판테놀":"두피 진정·보습","나이아신아마이드":"피지 조절·진정",
        "히알루론산":"두피 수분 공급","피토스핑고신":"두피 장벽 강화","아데노신":"혈행·모발 성장",
        "티트리오일":"항균·항염·진정","로즈마리오일":"혈행 촉진·성장","멘톨":"청량감·항균","소듐PCA":"두피 보습",
    }
    def sc(s): return "#10b981" if s>=70 else "#f59e0b" if s>=40 else "#ef4444"
    rows = "".join([
        f"<tr><td style='text-align:center;font-weight:700;color:#6ee7b7;'>{i+1}</td>"
        f"<td style='font-weight:700;color:#e2e8f0;'>{ing}</td>"
        f"<td style='color:#94a3b8;'>{purpose.get(ing,'두피·모발 개선')}</td>"
        f"<td style='font-weight:700;color:#3b82f6;font-family:monospace;'>"
        f"{mixing['ratios'].get(ing,'-') if mixing else '-'}%</td>"
        f"<td style='font-weight:700;color:#6ee7b7;font-family:monospace;'>"
        f"{mixing['ml'].get(ing,'-') if mixing else '-'}ml</td>"
        f"<td style='color:#94a3b8;'>{(get_sample_conc(ing) or {}).get('pct','재량')}%</td>"
        f"<td style='color:#64748b;font-size:9px;'>{(get_sample_conc(ing) or {}).get('note','')}</td></tr>"
        for i,ing in enumerate(ings)])
    steps_h = "".join([
        f"<div style='display:flex;align-items:center;gap:7px;padding:5px 0;"
        f"font-size:10px;border-bottom:1px solid rgba(255,255,255,0.05);'>"
        f"<span style='background:linear-gradient(135deg,#10b981,#059669);color:white;"
        f"border-radius:50%;width:18px;height:18px;display:inline-flex;align-items:center;"
        f"justify-content:center;font-size:8px;font-weight:700;flex-shrink:0;'>{dn}</span>"
        f"<span style='color:#cbd5e1;'><b style='color:#e2e8f0;'>{s['label']}</b>"
        f" — {' + '.join(s['items'])}</span></div>"
        for dn,s in enumerate(mixing["steps"],start=1)]) if mixing else ""
    uv_d  = f"{uv_val:.1f}" if uv_val is not None else "--"
    hum_d = f"{hum_val:.0f}%" if hum_val is not None else "--"
    usage = (
        f"<div class='card' style='background:rgba(16,185,129,0.06);"
        f"border-color:rgba(16,185,129,0.18);'>"
        f"<div class='stitle-green'>맞춤 두피 세럼 사용법</div>"
        f"<div style='font-size:10px;color:#94a3b8;line-height:1.9;'>"
        f"① 샴푸 후 타월로 두피 물기 제거 (촉촉한 상태 유지)<br>"
        f"② 세럼을 두피에 직접 소량 도포 (1회 약 1~2ml)<br>"
        f"③ 손가락 끝으로 두피 원형 마사지 1~2분<br>"
        f"④ 씻어내지 않고 미지근한 바람으로 건조 (Leave-on)<br>"
        f"<span style='font-size:9px;color:#64748b;'>보관: 서늘한 곳 / 개봉 후 3개월 내 사용 / 눈 접촉 금지</span>"
        f"</div></div>")
    return (
        _html_head(f"YD Lab 두피 공방 주문서 {code}","#0a0a1a","#0a1a0d") +
        f"<div class='header' style='border-color:rgba(16,185,129,0.20);'>"
        f"<div><h1>YD Lab 두피 공방 주문서</h1>"
        f"<div class='sub' style='color:#6ee7b7;'>AI 두피 분석 + SEEI v3 맞춤형 두피케어 제조</div></div>"
        f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#6ee7b7;'>{code}</div></div>"
        f"<div class='card' style='background:rgba(16,185,129,0.06);"
        f"border-color:rgba(16,185,129,0.15);font-size:9px;color:#6ee7b7;font-weight:600;'>"
        f"제조 공방에서 사전 준비된 권장농도 샘플을 아래 비율대로 혼합하세요.</div>"
        f"<div class='card'><div style='font-size:10px;color:#94a3b8;'>"
        f"분석일: {datetime.now().strftime('%Y년 %m월 %d일')} / "
        f"참여자: {pid} {age} {gender} / 거주: {region} {yrs}년 / "
        f"두피타입: {st_type} / 종합: {overall}점 / 총 {total_ml}ml / "
        f"<span style='color:{sg};font-weight:700;'>SEEI {seei} [{seei_grade}]</span> / "
        f"UV:{uv_d}[{uv_gstr}] / 습도:{hum_d}</div></div>"
        f"<div class='card'><div class='stitle-green'>두피 성분 처방 SEEI v3 반영</div>"
        f"<table>"
        f"<tr><th style='background:rgba(16,185,129,0.20);color:#6ee7b7;border-color:rgba(16,185,129,0.15);'>#</th>"
        f"<th style='background:rgba(16,185,129,0.20);color:#6ee7b7;border-color:rgba(16,185,129,0.15);'>성분명</th>"
        f"<th style='background:rgba(16,185,129,0.20);color:#6ee7b7;border-color:rgba(16,185,129,0.15);'>목적</th>"
        f"<th style='background:rgba(16,185,129,0.20);color:#6ee7b7;border-color:rgba(16,185,129,0.15);'>혼합비율</th>"
        f"<th style='background:rgba(16,185,129,0.20);color:#6ee7b7;border-color:rgba(16,185,129,0.15);'>투입량</th>"
        f"<th style='background:rgba(16,185,129,0.20);color:#6ee7b7;border-color:rgba(16,185,129,0.15);'>샘플농도</th>"
        f"<th style='background:rgba(16,185,129,0.20);color:#6ee7b7;border-color:rgba(16,185,129,0.15);'>비고</th></tr>"
        f"{rows}"
        f"<tr style='background:rgba(16,185,129,0.18);'>"
        f"<td colspan='4' style='text-align:right;color:#6ee7b7;font-weight:700;'>합계</td>"
        f"<td style='color:#6ee7b7;font-weight:700;font-family:monospace;'>{total_ml}ml</td>"
        f"<td colspan='2'></td></tr></table></div>"
        f"<div class='card'><div class='stitle-green'>두피 제조 순서</div>{steps_h}</div>"
        f"{usage}"
        f"<div class='card' style='font-size:10px;color:#94a3b8;'>"
        f"SEEI {seei} [{seei_grade}] / PM2.5 {air.get('pm25','-')}㎍/m³ / "
        f"{'에어코리아 실측' if not is_mock else '시간대 추정값'}<br>"
        f"<span style='font-size:9px;color:#64748b;'>{seei_msg}</span></div>"
        f"</div><div class='footer'>본 주문서는 AI 분석 기반이며 의료적 처방이 아닙니다 | YD Lab / 재능대학교</div>"
        f"</div></body></html>")

# ══════════════════════════════════════════
# 데이터 저장
# ══════════════════════════════════════════
DATA_FILE = Path("ydlab_skin_data.csv")
FIELDS = [
    "timestamp","participant_id","age_group","gender","region","residence_years",
    "skin_concern","body_parts","photo_count","analysis_mode",
    "pm25","pm10","o3","no2","air_station","air_source",
    "uv_index","uv_grade","uv_mock","humidity","humidity_mock",
    "ceei_score","ceei_grade",
    "seei_score","seei_grade","season_correction","uv_correction","humidity_correction_val",
    "overall_score","skin_type","key_concerns","recommended_ingredients",
    "wrinkle_score","pore_score","texture_score","tone_score","moisture_score",
    "scalp_keratin_score","scalp_pore_score","scalp_hair_thickness_score",
    "scalp_color_score","scalp_moisture_balance_score",
    "scalp_hair_damage_score","scalp_hair_loss_risk_score","scalp_comment",
    "sunscreen","smoking","sleep_hours",
    "consent","research_consent","marketing_opt_in",
]

def get_sheet():
    try:
        cd = dict(st.secrets["gcp_service_account"])
        cd["private_key"] = cd["private_key"].replace("\\n","\n")
        scopes = ["https://spreadsheets.google.com/feeds",
                  "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_info(cd,scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets.get("GOOGLE_SHEETS_ID","")).sheet1
    except Exception: return None

def get_marketing_sheet():
    try:
        cd = dict(st.secrets["gcp_service_account"])
        cd["private_key"] = cd["private_key"].replace("\\n","\n")
        scopes = ["https://spreadsheets.google.com/feeds",
                  "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_info(cd,scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets.get("GOOGLE_SHEETS_ID",""))
        try:    
          ws = sh.worksheet("marketing_opt")
        except: 
          ws = sh.add_worksheet("marketing_opt",rows=200,cols=4)
          ws.append_row(["participant_id","email","opt_in_date","region"])
        return ws
    except Exception: return None

def save_marketing_opt(pid,email,region):
    try:
        ws = get_marketing_sheet()
        if ws: ws.append_row([pid,email,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),region])
    except Exception: pass

def ensure_header(sheet):
    try:
        existing = sheet.row_values(1)
        if not existing: sheet.insert_row(FIELDS,1)
        elif existing != FIELDS:
            sheet.delete_rows(1); sheet.insert_row(FIELDS,1)
    except Exception as e: st.warning(f"헤더 확인 오류: {e}")

def save_record(r):
    try:
        sheet = get_sheet()
        if sheet:
            ensure_header(sheet)
            sheet.append_row([r.get(k,"") for k in FIELDS])
    except Exception: pass
    header = not DATA_FILE.exists()
    with open(DATA_FILE,"a",newline="",encoding="utf-8-sig") as f:
        w = csv.DictWriter(f,fieldnames=FIELDS)
        if header: w.writeheader()
        w.writerow({k:r.get(k,"") for k in FIELDS})

# ══════════════════════════════════════════
# 메인
# ══════════════════════════════════════════
def main():
    valid_codes = st.secrets.get("ACCESS_CODES",
                  [st.secrets.get("ACCESS_PASSWORD","YDLAB2025")])
    if isinstance(valid_codes,str): valid_codes=[valid_codes]

    if "authed" not in st.session_state: st.session_state["authed"]=False
    if not st.session_state["authed"]:
        url_code = st.query_params.get("code","")
        if url_code and url_code in valid_codes:
            st.session_state["authed"]=True

    if not st.session_state["authed"]:
        st.markdown(
            "<div class='hero'>"
            "<div class='hero-label'>YD Lab · 재능대학교 AI-바이오분석특화연구소</div>"
            "<h1>🔬 AI 피부·두피 분석</h1>"
            "<p>오픈랩 이벤트 참여자 전용 서비스입니다.<br>"
            "행사장에서 받은 이벤트 코드를 입력해 주세요.</p></div>",
            unsafe_allow_html=True)
        gate_pw = st.text_input("이벤트 코드",type="password",
                                placeholder="이벤트 코드를 입력하세요",key="k_gate")
        if st.button("분석 시작하기",type="primary",use_container_width=True):
            if gate_pw.upper() in [c.upper() for c in valid_codes]:
                st.session_state["authed"]=True; st.rerun()
            else: st.error("유효하지 않은 코드입니다.")
        st.stop()

    api_key = st.secrets.get("ANTHROPIC_API_KEY","")
    if not api_key:
        st.error("ANTHROPIC_API_KEY가 설정되지 않았습니다."); st.stop()

    kma_key    = st.secrets.get("KMA_API_KEY","")
    kma_status = "기상청 API 연동 중" if kma_key else "기상청 API 미연동 (시간대 추정값)"

    st.markdown(
        "<div class='hero'>"
        "<div class='hero-label'>YD Lab · 재능대학교 AI-바이오분석특화연구소</div>"
        "<h1>🔬 AI 피부·두피 분석</h1>"
        "<p>에어코리아(PM2.5·PM10·NO2·O3) + 기상청(UV·습도) + LLM 비전 AI<br>"
        "CEEI·SEEI 환경노출지수 연동 맞춤형 화장품 제안 시스템 (특허 출원 중)<br>"
        "공방 협업 제조 서비스 | 최종 확정 성분 20종</p>"
        f"<div class='hero-version'>v4.4 Dark Edition · {kma_status}</div>"
        "</div>",
        unsafe_allow_html=True)

    # 분석 모드
    st.markdown("<div class='glass-card'><div class='card-label'>분석 모드 선택</div>",
                unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        skin_sel = st.button("🧬 피부 분석\n피부 5지표 + CEEI",
                             use_container_width=True,key="k_mode_skin")
    with c2:
        scalp_sel = st.button("🌿 두피 분석\n두피 6지표 + SEEI v3",
                              use_container_width=True,key="k_mode_scalp")
    if skin_sel:  st.session_state["analysis_mode"]="skin"
    if scalp_sel: st.session_state["analysis_mode"]="scalp"
    mode = st.session_state.get("analysis_mode",None)
    if mode=="skin":
        st.info("🧬 피부 분석 모드 — 피부 5지표 + CEEI 환경노출지수")
    elif mode=="scalp":
        st.info("🌿 두피 분석 모드 — 두피 6지표 + SEEI v3 (PM2.5·PM10·NO2·O3·UV·습도)")
    else:
        st.warning("위에서 분석 모드를 먼저 선택해 주세요.")
        st.markdown("</div>",unsafe_allow_html=True); st.stop()
    st.markdown("</div>",unsafe_allow_html=True)

    # 기본 정보
    st.markdown("<div class='glass-card'><div class='card-label'>기본 정보 입력</div>",
                unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        pid = st.text_input("익명 참여 코드",placeholder="YD-001",key="k_pid")
    with c2:
        age = st.selectbox("연령대",
            ["선택","10대","20대","30대","40대","50대","60대 이상"],key="k_age")
    with c3:
        gender = st.selectbox("성별",["선택","여성","남성","기타"],key="k_gender")
    c4,c5 = st.columns(2)
    with c4:
        region = st.selectbox("거주 지역",list(REGION_PM25_AVG.keys()),key="k_region")
    with c5:
        res_str = st.selectbox("거주 기간",list(RESIDENCE_YEAR_MAP.keys()),key="k_residence")
    if mode=="skin":
        concern = st.multiselect("주요 피부 고민",
            ["주름·탄력","모공","피부톤·색소침착","수분·건조","민감성·홍조","여드름·트러블","기타"],
            key="k_concern")
    else:
        concern = st.multiselect("주요 두피·모발 고민",
            ["두피 각질","두피 지루·피지","탈모·모발 가늘어짐","두피 염증·홍조",
             "비듬","두피 건조","모발 손상·끊김","기타"],key="k_concern")
    st.markdown("</div>",unsafe_allow_html=True)

    # 생활습관
    st.markdown("<div class='confound-card'><div class='card-label'>생활습관 (연구용)</div>",
                unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        sunscreen = st.selectbox("자외선차단제",
            ["매일 사용","가끔 사용","거의 안함"],key="k_sun")
    with c2:
        smoking = st.selectbox("흡연 여부",
            ["비흡연","흡연","과거 흡연"],key="k_smoke")
    with c3:
        sleep_hr = st.selectbox("평균 수면",
            ["7시간 이상","5~7시간","5시간 미만"],key="k_sleep")
    st.markdown("</div>",unsafe_allow_html=True)

    # 촬영 부위
    st.markdown("<div class='glass-card'><div class='card-label'>촬영 부위 선택</div>",
                unsafe_allow_html=True)
    parts = st.multiselect("촬영한 부위 선택",
        SKIN_BODY_PARTS if mode=="skin" else SCALP_BODY_PARTS,key="k_parts")
    st.markdown("</div>",unsafe_allow_html=True)

    # 업로드
    label_mode = "피부" if mode=="skin" else "두피"
    st.markdown(
        f"<div class='glass-card'>"
        f"<div class='card-label'>{label_mode} 사진 업로드 (최대 3장)</div>",
        unsafe_allow_html=True)
    uploaded = st.file_uploader("JPG / PNG",type=["jpg","jpeg","png"],
                                accept_multiple_files=True,key="k_upload")
    if uploaded:
        cols = st.columns(min(len(uploaded[:3]),3))
        for i,f in enumerate(uploaded[:3]):
            with cols[i]: st.image(f,use_container_width=True)
    st.markdown("</div>",unsafe_allow_html=True)

    # 동의
    st.markdown("<div class='consent-box'>",unsafe_allow_html=True)
    consent  = st.checkbox(
        "[필수] 본 연구는 IRB 승인 후 연구담당자를 통해 별도 동의서를 작성합니다",
        key="k_consent")
    research = st.checkbox(
        "[선택] 익명화된 데이터를 학술 연구에 활용하는 것에 동의합니다.",
        key="k_research")
    st.markdown("</div>",unsafe_allow_html=True)

    with st.expander("📧 결과 알림 수신 동의 (선택)",expanded=False):
        mkt = st.checkbox(
            "SKIN-X 플랫폼 정식 출시 시 안내를 받겠습니다.",key="k_marketing")
        mkt_email = ""
        if mkt:
            mkt_email = st.text_input("이메일 주소",key="k_mkt_email")

    st.markdown("<br>",unsafe_allow_html=True)
    btn_label = ("🧬 피부 AI 분석 시작" if mode=="skin"
                 else "🌿 두피 AI 분석 시작 (SEEI v3)")
    run = st.button(btn_label,use_container_width=True,type="primary",key="k_run")

    if run:
        if not uploaded:
            st.error("사진을 업로드해 주세요."); st.stop()
        if not consent:
            st.error("IRB 동의 확인이 필요합니다."); st.stop()
        if not pid.strip():
            st.error("익명 참여 코드를 입력해 주세요."); st.stop()
        if age=="선택" or gender=="선택":
            st.warning("연령대와 성별을 선택해 주세요."); st.stop()
        if not parts:
            st.warning("촬영 부위를 하나 이상 선택해 주세요."); st.stop()

        images = []
        for f in uploaded[:3]:
            try: images.append(Image.open(f).convert("RGB"))
            except: pass

        with st.spinner("🛰️ 실시간 환경·기상 데이터 수집 중..."):
            air = fetch_air(region)
            if mode=="scalp":
                uv_data  = fetch_kma_uv(region)
                hum_data = fetch_kma_humidity(region)
            else: uv_data=hum_data=None

        spin_label = ("🧬 AI 피부 분석 중... (10~20초 소요)"
                      if mode=="skin"
                      else "🌿 AI 두피 분석 + SEEI v3 산출 중... (10~20초 소요)")
        with st.spinner(spin_label):
            result = (analyze_skin(images,api_key,parts)
                      if mode=="skin"
                      else analyze_scalp(images,api_key,parts))

        if result is None:
            st.error("분석에 실패했습니다. 사진을 확인하고 다시 시도해 주세요.")
            st.stop()

        for k,v in {
            "result":result,"air":air,"uv_data":uv_data,"humidity_data":hum_data,
            "region":region,"residence_years_str":res_str,
            "participant_id":pid,"age_group":age,"gender":gender,
            "selected_parts":parts,"skin_concern":concern,
            "consent":consent,"research_consent":research,"current_mode":mode,
        }.items(): st.session_state[k]=v

        yrs      = RESIDENCE_YEAR_MAP.get(res_str,0)
        pm25_avg = REGION_PM25_AVG.get(region,22.0)
        ceei,ceei_grade,_,_ = calc_ceei(pm25_avg,yrs)
        (seei,seei_grade,_,_,_,season_corr,
         uv_val,uv_gstr,hum_val,hum_corr) = calc_seei(air,yrs,uv_data,hum_data)
        _,uv_corr,_ = uv_index_grade(uv_val)
        pm25_safe = (air.get("pm25","")
                     if isinstance(air.get("pm25"),(int,float)) else "")

        save_record({
            "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "participant_id":pid,"age_group":age,"gender":gender,
            "region":region,"residence_years":yrs,
            "skin_concern":", ".join(concern),"body_parts":", ".join(parts),
            "photo_count":len(images),"analysis_mode":mode,
            "pm25":pm25_safe,"pm10":air.get("pm10",""),
            "o3":air.get("o3",""),"no2":air.get("no2",""),
            "air_station":air.get("station",""),
            "air_source":"실측" if not air.get("mock") else "시간대 추정값",
            "uv_index":uv_val if mode=="scalp" and uv_val is not None else "",
            "uv_grade":uv_gstr if mode=="scalp" else "",
            "uv_mock":(uv_data or {}).get("mock",True) if mode=="scalp" else "",
            "humidity":hum_val if mode=="scalp" and hum_val is not None else "",
            "humidity_mock":(hum_data or {}).get("mock",True) if mode=="scalp" else "",
            "ceei_score":ceei,"ceei_grade":ceei_grade,
            "seei_score":seei if mode=="scalp" else "",
            "seei_grade":seei_grade if mode=="scalp" else "",
            "season_correction":season_corr if mode=="scalp" else "",
            "uv_correction":uv_corr if mode=="scalp" else "",
            "humidity_correction_val":hum_corr if mode=="scalp" else "",
            "overall_score":result.get("overall_score",""),
            "skin_type":result.get("skin_type",result.get("scalp_type","")),
            "key_concerns":", ".join(result.get("key_concerns",[])),
            "recommended_ingredients":", ".join(result.get("recommended_ingredients",[])),
            "wrinkle_score":result.get("wrinkle_score","") if mode=="skin" else "",
            "pore_score":result.get("pore_score","") if mode=="skin" else "",
            "texture_score":result.get("texture_score","") if mode=="skin" else "",
            "tone_score":result.get("tone_score","") if mode=="skin" else "",
            "moisture_score":result.get("moisture_score","") if mode=="skin" else "",
            "scalp_keratin_score":result.get("keratin_score","") if mode=="scalp" else "",
            "scalp_pore_score":result.get("pore_score","") if mode=="scalp" else "",
            "scalp_hair_thickness_score":result.get("hair_thickness_score","") if mode=="scalp" else "",
            "scalp_color_score":result.get("scalp_color_score","") if mode=="scalp" else "",
            "scalp_moisture_balance_score":result.get("moisture_balance_score","") if mode=="scalp" else "",
            "scalp_hair_damage_score":result.get("hair_damage_score","") if mode=="scalp" else "",
            "scalp_hair_loss_risk_score":result.get("hair_loss_risk_score","") if mode=="scalp" else "",
            "scalp_comment":result.get("summary","") if mode=="scalp" else "",
            "sunscreen":sunscreen,"smoking":smoking,"sleep_hours":sleep_hr,
            "consent":consent,"research_consent":research,"marketing_opt_in":mkt,
        })
        if mkt and mkt_email.strip():
            save_marketing_opt(pid,mkt_email.strip(),region)

    if "result" in st.session_state:
        st.success("✅ 분석 완료!")
        cm = st.session_state.get("current_mode","skin")
        if cm=="skin":
            show_skin_result(
                st.session_state["result"],st.session_state["air"],
                st.session_state["region"],st.session_state["residence_years_str"],
                st.session_state["participant_id"],st.session_state["age_group"],
                st.session_state["gender"],st.session_state["selected_parts"])
        else:
            show_scalp_result(
                st.session_state["result"],st.session_state["air"],
                st.session_state["region"],st.session_state["residence_years_str"],
                st.session_state["participant_id"],st.session_state["age_group"],
                st.session_state["gender"],st.session_state["selected_parts"],
                st.session_state.get("uv_data"),st.session_state.get("humidity_data"))

    # 관리자 사이드바
    with st.sidebar:
        st.markdown("### ⚙️ 관리자")
        admin_pw = st.text_input("관리자 비밀번호",type="password",key="k_admin")
        if admin_pw == st.secrets.get("ADMIN_PASSWORD","ydlab2024"):
            st.success("관리자 모드")
            kma_st = "실측 연동 중" if kma_key else "키 미등록 (추정값)"
            st.markdown(f"**기상청 API:** {kma_st}")
            if DATA_FILE.exists():
                import pandas as pd
                df = pd.read_csv(DATA_FILE,encoding="utf-8-sig")
                st.markdown(f"**총 분석 건수:** {len(df)}건")
                if "analysis_mode" in df.columns:
                    st.markdown("**분석 모드**")
                    st.bar_chart(df["analysis_mode"].value_counts())
                if len(df)>0:
                    st.markdown("**피부 타입**")
                    st.bar_chart(df["skin_type"].value_counts())
                    if "ceei_grade" in df.columns:
                        st.markdown("**CEEI 등급**")
                        st.bar_chart(df["ceei_grade"].value_counts())
                    if "seei_grade" in df.columns:
                        sd = df[df["seei_grade"]!=""]["seei_grade"]
                        if len(sd)>0:
                            st.markdown("**SEEI 등급 (두피)**")
                            st.bar_chart(sd.value_counts())
                    if "air_source" in df.columns:
                        rc=(df["air_source"]=="실측").sum()
                        mc=(df["air_source"]=="시간대 추정값").sum()
                        st.markdown(f"**대기데이터** — 실측:{rc} / 추정:{mc}")
                st.download_button("전체 데이터 CSV",
                    data=open(DATA_FILE,"rb").read(),
                    file_name=f"ydlab_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",key="k_csv")
            else:
                st.info("아직 수집된 데이터가 없습니다.")

if __name__ == "__main__":
    main()
