"""
YD Lab 피부·두피 분석 앱 v4.7  ─ Dark Glassmorphism Edition (+사업용 매장 UX)
설치: pip install streamlit anthropic pillow requests pandas gspread google-auth
실행: streamlit run ydlab_skin_analyzer_v4.7.py
secrets.toml:
  ANTHROPIC_API_KEY = "..."
  AIRKOREA_API_KEY  = "..."
  KMA_API_KEY       = "..."
  EDU_ACCESS_CODES  = ["EDU2026"]
  BIZ_ACCESS_CODES  = ["BIZ2026"]
  ADMIN_PASSWORD    = "YDLAB2025"
  GOOGLE_SHEETS_ID  = "..."
  [gcp_service_account] ...

v4.7 변경사항 (v4.6 대비):
  1) 사업용 모드 사진 업로드 UX 개선
     - 갤러리 선택 탭 (무선 현미경 촬영 사진용)
     - 카메라 직접 촬영 탭 (태블릿 후면 카메라용)
     - 매장 직원용 단계별 안내 문구
  2) 사업용 모드 "다음 고객 (초기화)" 버튼 추가
     - 결과 화면 위/아래 두 곳에 배치
     - 클릭 시 인증·모드 정보만 남기고 세션 초기화
  3) 나머지 로직은 v4.6과 100% 동일
"""
import streamlit as st
import streamlit.components.v1 as components
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
    background: none;
    pointer-events: none;
    z-index: 0;
}
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
label,
.stTextInput label, .stSelectbox label, .stMultiSelect label,
.stNumberInput label, .stTextArea label, .stRadio label,
.stCheckbox label, .stSlider label, .stFileUploader label,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
[data-testid="stWidgetLabel"] div,
.stCheckbox label p,
.stRadio [data-testid="stMarkdownContainer"] p {
    color: #c4b5fd !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}
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
[data-baseweb="select"] > div:focus,
[data-baseweb="select"] > div[aria-expanded="true"] {
    border-color: rgba(99,102,241,0.70) !important;
    box-shadow: none !important;
    outline: none !important;
}
.stSelectbox svg, .stMultiSelect svg {
    fill: #a78bfa !important;
    color: #a78bfa !important;
}
[data-baseweb="select"],
[data-baseweb="select"] *,
[data-baseweb="select"] div,
[data-baseweb="select"] span {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="listbox"] {
    border: 1px solid rgba(99,102,241,0.45) !important;
    border-radius: 10px !important;
}
[role="option"], [data-baseweb="option"] {
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 0.87rem !important;
}
.stCheckbox > label > div[data-testid="stMarkdownContainer"] p,
.stCheckbox span,
.stRadio > div label span,
.stRadio span {
    color: #e2e8f0 !important;
    font-size: 0.88rem !important;
}
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
    color: #e2e8f0 !important;
}
[data-testid="stFileUploader"] small,
[data-testid="stFileUploaderDropzoneInstructions"] small {
    color: #a5b4fc !important;
    font-size: 0.82rem !important;
}
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
    color: #ffffff !important;
}
.stButton > button {
    background: #4f46e5 !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.6rem 1.2rem !important;
    transition: filter 0.15s ease !important;
    box-shadow: none !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}
.stButton > button:hover {
    filter: brightness(1.12) !important;
}
.stButton > button[kind="primary"] {
    background: #6366f1 !important;
    font-size: 1rem !important;
    padding: 0.8rem 1.5rem !important;
    box-shadow: none !important;
}
.stDownloadButton > button {
    background: rgba(79,70,229,0.20) !important;
    border: 1px solid rgba(99,102,241,0.50) !important;
    color: #a5b4fc !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    background: rgba(79,70,229,0.35) !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] {
    background: rgba(10,10,26,0.97) !important;
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
[data-testid="stDataFrame"] th {
    background: rgba(99,102,241,0.28) !important;
    color: #c7d2fe !important;
}
[data-testid="stDataFrame"] td { color: #cbd5e1 !important; }
[data-testid="stSpinner"] p,
[data-testid="stSpinner"] span { color: #c4b5fd !important; }
hr { border-color: rgba(255,255,255,0.08) !important; }
[data-testid="stToolbar"] { display: none !important; }
#MainMenu { visibility: hidden !important; }
footer    { visibility: hidden !important; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track  { background: rgba(255,255,255,0.03); }
::-webkit-scrollbar-thumb  { background: rgba(99,102,241,0.50); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.80); }
body, html { font-size: 16px !important; }
[data-testid="stMarkdownContainer"] { font-size: 15px !important; }
[data-testid="stMarkdownContainer"] p { font-size: 15px !important; }
[data-testid="stMarkdownContainer"] span { font-size: inherit !important; }
[data-testid="stMarkdownContainer"] div { font-size: inherit !important; }
.stMarkdown { font-size: 15px !important; }
.stMarkdown p { font-size: 15px !important; }
small, .small,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploaderDropzoneInstructions"] small {
    font-size: 0.82rem !important;
}
.stMarkdown p, .stMarkdown span,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] * {
    font-size: 0.88rem !important;
    line-height: 1.7 !important;
}
.stSelectbox label, .stMultiSelect label,
.stTextInput label, .stNumberInput label,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] * {
    font-size: 0.88rem !important;
}
/* 사업용 카메라 촬영 탭 스타일 */
[data-testid="stCameraInput"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(99,102,241,0.30) !important;
    border-radius: 12px !important;
    padding: 12px !important;
}
[data-testid="stCameraInput"] button {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
/* 탭(사업용 업로드 갤러리/카메라) 스타일 */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,255,255,0.03);
    padding: 6px;
    border-radius: 10px;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.05) !important;
    border-radius: 8px !important;
    color: #a5b4fc !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(99,102,241,0.30) !important;
    color: #ffffff !important;
}
/* 커스텀 컴포넌트 */
.glass-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px;
    padding: 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: none;
    transition: border-color 0.15s ease;
    color: #e2e8f0;
}
.glass-card:hover {
    border-color: rgba(99,102,241,0.30);
}
.glass-card p, .glass-card span, .glass-card div { color: #e2e8f0 !important; }
.glass-card h1, .glass-card h2, .glass-card h3 { color: #ffffff !important; }
.hero {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    border-left: 3px solid rgba(99,102,241,0.65);
    border-radius: 14px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.6rem;
    box-shadow: none;
    position: relative;
}
.hero-label {
    font-size: 13px !important;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(16,185,129,0.90) !important;
    margin-bottom: 0.7rem;
    font-family: 'DM Mono', monospace;
    display: block !important;
}
.hero h1,
.hero h1 *,
[data-testid="stMarkdownContainer"] .hero h1 {
    font-size: 30px !important;
    font-weight: 800 !important;
    color: white !important;
    margin-bottom: 0.6rem !important;
    line-height: 1.2 !important;
}
.hero p,
[data-testid="stMarkdownContainer"] .hero p {
    font-size: 15px !important;
    color: rgba(255,255,255,0.70) !important;
    line-height: 1.75 !important;
}
.hero-version {
    font-family: 'DM Mono', monospace;
    font-size: 12px !important;
    color: rgba(16,185,129,0.80) !important;
    margin-top: 0.5rem;
    display: block !important;
}
.card-label,
[data-testid="stMarkdownContainer"] .card-label {
    font-size: 13px !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: rgba(165,180,252,1) !important;
    font-weight: 700 !important;
    font-family: 'DM Mono', monospace !important;
    margin-bottom: 1rem !important;
    padding-bottom: 0.7rem !important;
    border-bottom: 1px solid rgba(99,102,241,0.20) !important;
    display: block !important;
}
.card-label-green,
[data-testid="stMarkdownContainer"] .card-label-green {
    font-size: 13px !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: rgba(110,231,183,1) !important;
    font-weight: 700 !important;
    font-family: 'DM Mono', monospace !important;
    margin-bottom: 1rem !important;
    padding-bottom: 0.7rem !important;
    border-bottom: 1px solid rgba(16,185,129,0.20) !important;
    display: block !important;
}
.gauge-wrap  { text-align: center; padding: 0.8rem 0.4rem; }
.gauge-num,
[data-testid="stMarkdownContainer"] .gauge-num {
    font-size: 36px !important;
    font-weight: 700 !important;
    font-family: 'DM Mono', monospace !important;
    line-height: 1 !important;
    text-shadow: 0 0 20px currentColor !important;
    display: block !important;
}
.gauge-lbl,
[data-testid="stMarkdownContainer"] .gauge-lbl {
    font-size: 13px !important;
    color: rgba(255,255,255,0.65) !important;
    margin-top: 0.3rem !important;
    display: block !important;
}
.gauge-cmt,
[data-testid="stMarkdownContainer"] .gauge-cmt {
    font-size: 12px !important;
    color: rgba(255,255,255,0.45) !important;
    margin-top: 0.3rem !important;
    line-height: 1.4 !important;
    display: block !important;
}
.score-high  { color: #10b981 !important; }
.score-mid   { color: #f59e0b !important; }
.score-low   { color: #ef4444 !important; }
.big-score,
[data-testid="stMarkdownContainer"] .big-score {
    font-size: 88px !important;
    font-weight: 900 !important;
    font-family: 'DM Mono', monospace !important;
    line-height: 1 !important;
    text-shadow: 0 0 40px currentColor, 0 0 80px currentColor !important;
    letter-spacing: -2px !important;
    display: block !important;
}
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
    transform: translateY(-1px);
}
.scalp-chip {
    display: inline-block;
    background: rgba(16,185,129,0.16);
    border: 1px solid rgba(16,185,129,0.38);
    color: rgba(110,231,183,1) !important;
    border-radius: 8px;
    padding: 0.28rem 0.75rem;
    font-size: 0.82rem;
    margin: 0.2rem;
    font-weight: 500;
    transition: all 0.2s ease;
    cursor: default;
}
.scalp-chip:hover {
    background: rgba(16,185,129,0.32);
    border-color: rgba(16,185,129,0.72);
    transform: translateY(-1px);
}
.chip {
    display: inline-flex; align-items: center;
    padding: 0.28rem 0.75rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 0.2rem;
}
.chip-good { background:rgba(16,185,129,0.16); color:#6ee7b7 !important; border:1px solid rgba(16,185,129,0.32); }
.chip-mid  { background:rgba(59,130,246,0.16);  color:#93c5fd !important; border:1px solid rgba(59,130,246,0.32); }
.chip-warn { background:rgba(245,158,11,0.16);  color:#fcd34d !important; border:1px solid rgba(245,158,11,0.32); }
.chip-bad  { background:rgba(239,68,68,0.16);   color:#fca5a5 !important; border:1px solid rgba(239,68,68,0.32); }
.chip-neu  { background:rgba(255,255,255,0.07); color:rgba(210,210,235,0.80) !important;
             border:1px solid rgba(255,255,255,0.13); }
.mixing-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(16,185,129,0.20);
    border-radius: 14px;
    padding: 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: none;
}
.mixing-row {
    display: flex; align-items: center; gap: 0.8rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.mixing-sno  { font-size: 0.76rem; font-family: 'DM Mono', monospace;
               color: #a5b4fc !important; min-width: 36px; font-weight: 700; }
.mixing-ing  { font-weight: 600; flex: 1; font-size: 15px !important; color: rgba(255,255,255,0.90) !important; }
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
.mixing-conc { font-size: 0.73rem; color: rgba(200,200,230,0.45) !important; min-width: 72px; }
.step-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 22px; height: 22px; border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white !important; font-size: 0.72rem; font-weight: 700;
    margin-right: 0.5rem; flex-shrink: 0;
    box-shadow: 0 0 8px rgba(99,102,241,0.5);
}
.step-badge-green {
    display: inline-flex; align-items: center; justify-content: center;
    width: 22px; height: 22px; border-radius: 50%;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white !important; font-size: 0.72rem; font-weight: 700;
    margin-right: 0.5rem; flex-shrink: 0;
    box-shadow: 0 0 8px rgba(16,185,129,0.5);
}
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
    font-size: 0.73rem; font-weight: 700;
    box-shadow: 0 0 10px rgba(99,102,241,0.4);
}
.priority-label { font-weight: 600; flex: 1; font-size: 15px !important; color: rgba(255,255,255,0.90) !important; }
.priority-score { font-weight: 700; font-family: 'DM Mono', monospace; font-size: 15px !important; }
.priority-msg   { font-size: 13px !important; color: rgba(200,200,230,0.65) !important; }
.patent-banner {
    background: rgba(59,130,246,0.12);
    border: 1px solid rgba(59,130,246,0.28);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    font-size: 0.82rem;
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
    font-size: 0.82rem;
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
    font-size: 0.82rem;
    color: #6ee7b7 !important;
    margin-bottom: 0.8rem;
    font-weight: 600;
}
.air-mock {
    background: rgba(245,158,11,0.10);
    border: 1px solid rgba(245,158,11,0.28);
    border-radius: 10px;
    padding: 0.5rem 1rem;
    font-size: 0.82rem;
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
.seei-box {
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.20);
    border-radius: 14px;
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
.consent-box {
    background: rgba(255,255,255,0.04);
    border-left: 3px solid rgba(99,102,241,0.65);
    border-radius: 0 10px 10px 0;
    padding: 0.9rem 1rem;
    font-size: 0.84rem;
    color: rgba(220,220,240,0.70) !important;
    line-height: 1.75;
    margin-bottom: 1rem;
}
.confound-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 16px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    color: #e2e8f0 !important;
}
.confound-card p, .confound-card span, .confound-card div { color: #e2e8f0 !important; }
.scalp-section {
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.18);
    border-radius: 16px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}
.scalp-section p, .scalp-section span, .scalp-section div { color: #e2e8f0 !important; }
.result-text,
[data-testid="stMarkdownContainer"] .result-text {
    font-size: 15px !important;
    color: rgba(220,220,245,0.90) !important;
    line-height: 1.8 !important;
}
.hair-loss-box {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.22);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    font-size: 0.86rem;
    margin-top: 0.8rem;
    color: #e2e8f0 !important;
}
.hair-loss-box span { color: inherit !important; }
.sample-notice {
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    font-size: 0.82rem;
    color: #a5b4fc !important;
    margin-bottom: 0.8rem;
    font-weight: 500;
}
div[data-baseweb="select"],
div[data-baseweb="select"] *,
div[data-baseweb="select"] input {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
}
div[data-baseweb="select"] input::placeholder {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 0.9 !important;
}
div[data-baseweb="select"] svg {
    fill: #ffffff !important;
    color: #ffffff !important;
}
/* 다음 고객 초기화 버튼 강조 스타일 */
.next-customer-btn button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: #ffffff !important;
    font-size: 1.1rem !important;
    padding: 1rem 2rem !important;
    box-shadow: 0 0 20px rgba(16,185,129,0.35) !important;
}
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
# ── 20종 샘플 DB (v4.2 프로토콜 기준) ──
SAMPLE_CONC_DB = {
    "히알루론산":           {"sample_no":"S01","pct":1.0,   "note":"저분자+고분자 1:1 / 냉장 3개월"},
    "나이아신아마이드":     {"sample_no":"S02","pct":5.0,   "note":"pH 6.0~7.0 / 냉장 6개월"},
    "판테놀":               {"sample_no":"S03","pct":3.0,   "note":"Pro-비타민B5 / 냉장·실온 6개월"},
    "아스코빌글루코사이드": {"sample_no":"S04","pct":5.0,   "note":"안정형 Vit.C / 차광냉장 6개월"},
    "비타민C유도체":        {"sample_no":"S04","pct":5.0,   "note":"아스코빌글루코사이드 동일"},
    "레티닐팔미테이트":     {"sample_no":"S05","pct":0.3,   "note":"주름개선 기능성 / 차광냉장 2개월"},
    "아세틸헥사펩타이드-8": {"sample_no":"S06","pct":0.002, "note":"EGF 대체 펩타이드 / 냉장 1~2개월"},
    "피토스핑고신":         {"sample_no":"S07","pct":0.1,   "note":"수용성 장벽 / 산성조건 냉장 3개월"},
    "펩타이드":             {"sample_no":"S08","pct":3.0,   "note":"콜라겐 펩타이드 / 냉장 3개월"},
    "아데노신":             {"sample_no":"S09","pct":0.04,  "note":"식약처 주름기능성 / 냉장 6개월"},
    "글리세린":             {"sample_no":"S10","pct":5.0,   "note":"식물성 99.5% / 실온 12개월"},
    "알란토인":             {"sample_no":"S11","pct":0.3,   "note":"피부진정·재생 / 냉장·실온 6개월"},
    "스쿠알란":             {"sample_no":"S12","pct":3.0,   "note":"올리브유래 원액 / 실온 6개월"},
    "살리실산":             {"sample_no":"S13","pct":1.0,   "note":"에탄올 선용해 / 냉장차광 6개월"},
    "피록톤올아민":         {"sample_no":"S14","pct":0.5,   "note":"비듬·항균 ZPT대체 / 냉장 6개월"},
    "바이오틴":             {"sample_no":"S16","pct":0.05,  "note":"모발강화 / 냉장 3개월"},
    "티트리오일":           {"sample_no":"S17","pct":1.0,   "note":"가용화액(PS80 1:3) / 실온 3개월"},
    "로즈마리오일":         {"sample_no":"S18","pct":0.5,   "note":"가용화액(PS80 1:3) / 실온 3개월"},
    "멘톨":                 {"sample_no":"S19","pct":0.3,   "note":"에탄올 선용해 / 실온밀봉 6개월"},
    "소듐PCA":              {"sample_no":"S20","pct":3.0,   "note":"두피보습 / 실온·냉장 6개월"},
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
# 사업용 완제품 유형 DB (교육용 20종 혼합과 별개)
# ══════════════════════════════════════════
SKIN_PRODUCT_TYPES = {
    "P-SK01": {"name": "SKIN-X 하이드라 배리어", "skin_type": "건성",
               "ingredients": ["히알루론산", "글리세린", "피토스핑고신"],
               "desc": "고보습 라인 — 극건성·당김 완화 집중"},
    "P-SK02": {"name": "SKIN-X 타임 리페어", "skin_type": "건성",
               "ingredients": ["레티닐팔미테이트", "펩타이드", "히알루론산"],
               "desc": "주름·탄력 집중 케어 (야간 사용 권장)"},
    "P-SK03": {"name": "SKIN-X 퓨어 세범", "skin_type": "지성",
               "ingredients": ["살리실산", "나이아신아마이드"],
               "desc": "피지·모공 케어, 산뜻한 제형"},
    "P-SK04": {"name": "SKIN-X 브라이트 클리어", "skin_type": "지성",
               "ingredients": ["아스코빌글루코사이드", "나이아신아마이드"],
               "desc": "칙칙함·색소침착 케어, 산뜻한 제형"},
    "P-SK05": {"name": "SKIN-X 밸런스 듀오", "skin_type": "복합성",
               "ingredients": ["판테놀", "히알루론산", "나이아신아마이드"],
               "desc": "T존·U존 밸런스 케어 (복합성·중성 공용)"},
    "P-SK06": {"name": "SKIN-X 캄 배리어", "skin_type": "민감성",
               "ingredients": ["판테놀", "알란토인", "피토스핑고신"],
               "desc": "저자극 장벽 강화, 진정 집중"},
}
SCALP_PRODUCT_TYPES = {
    "P-SC01": {"name": "SKIN-X 스칼프 하이드레이트", "scalp_type": "건성",
               "ingredients": ["판테놀", "피토스핑고신", "소듐PCA"],
               "desc": "각질·가려움 완화, 수분 공급"},
    "P-SC02": {"name": "SKIN-X 스칼프 퓨리파이", "scalp_type": "지성",
               "ingredients": ["살리실산", "티트리오일"],
               "desc": "피지·모공 관리, 청량 제형"},
    "P-SC03": {"name": "SKIN-X 덴시티 부스트", "scalp_type": None,
               "ingredients": ["바이오틴", "아데노신", "로즈마리오일"],
               "desc": "모발 굵기·볼륨감 집중 케어"},
    "P-SC04": {"name": "SKIN-X 스칼프 캄", "scalp_type": "민감성",
               "ingredients": ["판테놀", "히알루론산"],
               "desc": "저자극 진정, 홍조·자극 완화"},
}

def match_skin_product(result, ceei_grade):
    """분석 결과 → 사업용 6종 중 피부 유형 1개 매칭 (단일 매칭, 혼합 없음)."""
    skin_type = result.get("skin_type", "")
    moisture  = result.get("moisture_score", 50)
    wrinkle   = result.get("wrinkle_score", 50)
    pore      = result.get("pore_score", 50)
    tone      = result.get("tone_score", 50)
    if skin_type == "건성":
        code = "P-SK01" if moisture <= wrinkle else "P-SK02"
    elif skin_type == "지성":
        code = "P-SK03" if pore <= tone else "P-SK04"
    elif skin_type == "민감성":
        code = "P-SK06"
    else:
        code = "P-SK05"
    info = dict(SKIN_PRODUCT_TYPES[code])
    info["code"] = code
    info["booster_recommended"] = ceei_grade in ["높음", "매우높음"]
    return info

def match_scalp_product(result, seei_grade):
    """분석 결과 → 사업용 4종 중 두피 유형 1개 매칭 (단일 매칭, 혼합 없음)."""
    scalp_type = result.get("scalp_type", "")
    keratin    = result.get("keratin_score", 50)
    pore       = result.get("pore_score", 50)
    thickness  = result.get("hair_thickness_score", 50)
    color      = result.get("scalp_color_score", 50)
    lowest = min(keratin, pore, thickness, color)
    if thickness == lowest and thickness < 55:
        code = "P-SC03"
    elif scalp_type == "민감성" or color == lowest:
        code = "P-SC04"
    elif scalp_type == "지성" or pore <= keratin:
        code = "P-SC02"
    else:
        code = "P-SC01"
    info = dict(SCALP_PRODUCT_TYPES[code])
    info["code"] = code
    info["booster_recommended"] = seei_grade in ["높음", "매우높음"]
    return info

def show_product_match_card(product, grade_label, grade_value, is_scalp=False):
    """사업용 결과 카드 — 완제품 유형 매칭 (혼합 없음, 바로 사용 가능)."""
    accent = "#10b981" if is_scalp else "#6366f1"
    chip_cls = "scalp-chip" if is_scalp else "ing-chip"
    ing_html = "".join(f"<span class='{chip_cls}'>{i}</span>"
                        for i in product.get("ingredients", []))
    booster_html = ""
    if product.get("booster_recommended"):
        booster_html = (
            "<div class='hair-loss-box' style='margin-top:0.8rem;'>"
            f"오늘 {grade_label} {grade_value} — 항산화 부스터 앰플 추가 사용을 권장합니다 "
            "(완제품 배합 변경 없음, 별도 제품 레이어링)</div>"
        )
    label_cls = "card-label-green" if is_scalp else "card-label"
    st.markdown(
        f"<div class='glass-card' style='border-color:{accent}55;'>"
        f"<div class='{label_cls}'>매장 추천 제품 (완제품 · 즉시 사용 가능)</div>"
        f"<div style='font-size:1.3rem;font-weight:800;color:white;margin-bottom:0.3rem;'>"
        f"{product['code']} · {product['name']}</div>"
        f"<div class='result-text' style='margin-bottom:0.6rem;'>{product.get('desc','')}</div>"
        f"<div>{ing_html}</div>"
        f"{booster_html}"
        f"<div class='sample-notice' style='margin-top:0.8rem;'>"
        f"이 제품은 완제품으로 사전 제조되어 있습니다. 매장에서 추가 혼합·소분 없이 바로 전달하세요."
        f"</div></div>",
        unsafe_allow_html=True,
    )

def generate_biz_match_report_html(product, grade_label, grade_value,
                                    region, pid, age, gender, overall,
                                    result, is_scalp=False):
    """사업용(매장) 모드 전용 — 진단 결과 + 매장 전달용 추천 제품·사용법 안내 리포트."""
    accent  = "#10b981" if is_scalp else "#6366f1"
    label   = "두피" if is_scalp else "피부"
    stitle  = "stitle-green" if is_scalp else "stitle"
    bg_from, bg_to = ("#0a0a1a","#0a1a0d") if is_scalp else ("#0a0a1a","#0d1b3e")
    def sc(s): return "#10b981" if s>=70 else "#f59e0b" if s>=40 else "#ef4444"

    if is_scalp:
        metrics = [
            ("각질",     result.get("keratin_score",0),          result.get("keratin_comment","")),
            ("모공피지", result.get("pore_score",0),             result.get("pore_comment","")),
            ("모발굵기", result.get("hair_thickness_score",0),   result.get("hair_thickness_comment","")),
            ("색상염증", result.get("scalp_color_score",0),      result.get("scalp_color_comment","")),
            ("수분유분", result.get("moisture_balance_score",0), result.get("moisture_balance_comment","")),
            ("손상도",   result.get("hair_damage_score",0),      result.get("hair_damage_comment","")),
        ]
        type_val = result.get("scalp_type","")
    else:
        metrics = [
            ("주름",   result.get("wrinkle_score",0),  result.get("wrinkle_comment","")),
            ("모공",   result.get("pore_score",0),      result.get("pore_comment","")),
            ("피부결", result.get("texture_score",0),   result.get("texture_comment","")),
            ("피부톤", result.get("tone_score",0),       result.get("tone_comment","")),
            ("수분",   result.get("moisture_score",0),  result.get("moisture_comment","")),
        ]
        type_val = result.get("skin_type","")

    metric_boxes = "".join([
        f"<div style='flex:1;min-width:88px;background:rgba(255,255,255,0.04);"
        f"border:1px solid {accent}22;border-radius:10px;"
        f"padding:12px 8px;text-align:center;'>"
        f"<div style='font-size:24px;font-weight:700;color:{sc(v)};"
        f"font-family:DM Mono,monospace;text-shadow:0 0 10px {sc(v)};'>{v}</div>"
        f"<div style='font-size:11px;color:#94a3b8;margin-top:4px;'>{l}</div>"
        f"<div style='font-size:10px;color:#64748b;margin-top:4px;line-height:1.4;'>{c}</div></div>"
        for l,v,c in metrics])

    ing_h = "".join([
        f"<span class='chip' style='color:{accent};border-color:{accent}55;"
        f"background:{accent}22;'>{i}</span>"
        for i in product.get("ingredients", [])])

    booster_html = ""
    if product.get("booster_recommended"):
        booster_html = (
            f"<div class='card' style='background:rgba(245,158,11,0.08);"
            f"border-color:rgba(245,158,11,0.20);'>"
            f"<div style='font-size:13px;color:#fcd34d;line-height:1.7;'>"
            f"오늘 {grade_label} <b>{grade_value}</b> — 항산화 부스터 앰플 추가 사용을 "
            f"권장합니다 (완제품 배합 변경 없음, 별도 제품 레이어링)</div></div>")

    if is_scalp:
        usage_steps = [
            "샴푸 후 타월로 두피 물기를 가볍게 제거합니다 (촉촉한 상태 유지).",
            f"{product['name']}을(를) 두피에 직접 소량(1~2ml) 도포합니다.",
            "손가락 끝으로 두피를 원형으로 1~2분 마사지합니다.",
            "씻어내지 않고 미지근한 바람으로 건조합니다 (Leave-on 타입).",
            "주 3~4회, 샴푸 직후 사용을 권장합니다.",
        ]
        usage_note = "보관: 서늘한 곳 / 개봉 후 3개월 내 사용 / 눈 접촉 시 즉시 세척"
    else:
        usage_steps = [
            "세안 후 토너(스킨)로 피부결을 정돈합니다.",
            f"{product['name']}을(를) 적당량 덜어 얼굴 전체에 고르게 펴 바릅니다.",
            "가볍게 두드려 흡수시킵니다.",
            "이후 로션·크림으로 마무리합니다 (아침에는 자외선차단제 필수).",
            "아침·저녁 1일 2회 사용을 권장합니다.",
        ]
        usage_note = "보관: 직사광선을 피한 서늘한 곳 / 개봉 후 6개월 내 사용"
    usage_html = "".join([
        f"<div style='display:flex;align-items:flex-start;gap:8px;padding:6px 0;"
        f"font-size:13px;color:#cbd5e1;border-bottom:1px solid rgba(255,255,255,0.05);'>"
        f"<span style='background:{accent};color:white;border-radius:50%;"
        f"width:20px;height:20px;min-width:20px;display:inline-flex;align-items:center;"
        f"justify-content:center;font-size:10px;font-weight:700;'>{i+1}</span>"
        f"<span>{step}</span></div>"
        for i, step in enumerate(usage_steps)])

    code = ("YDL-" + ("SC" if is_scalp else "SK") + "-BIZ-"
            + datetime.now().strftime("%Y%m%d") + "-"
            + ''.join(random.choices(string.ascii_uppercase+string.digits, k=4)))
    return (
        _html_head(f"YD Lab {label} 추천 제품 안내", bg_from, bg_to) +
        f"<div class='header' style='{'border-color:rgba(16,185,129,0.20);' if is_scalp else ''}'>"
        f"<div><h1>YD Lab {label} 진단 · 추천 제품 안내</h1>"
        f"<div class='sub' style='{'color:#6ee7b7;' if is_scalp else ''}'>"
        f"AI {label} 분석 기반 매장 추천 완제품 (특허 출원 중)</div></div>"
        f"<div style='font-family:DM Mono,monospace;font-size:11px;"
        f"color:{'#6ee7b7' if is_scalp else '#a5b4fc'};'>{code}</div></div>"
        f"<div class='card'>"
        f"<div style='font-size:13px;color:#94a3b8;line-height:1.8;'>"
        f"분석일: {datetime.now().strftime('%Y년 %m월 %d일')} &nbsp;|&nbsp; "
        f"참여자: {pid} {age} {gender} &nbsp;|&nbsp; 지역: {region}</div></div>"
        f"<div class='card'><div class='{stitle}'>종합 분석 결과</div>"
        f"<div style='display:flex;align-items:center;gap:20px;flex-wrap:wrap;'>"
        f"<div style='font-size:52px;font-weight:900;color:{sc(overall)};"
        f"font-family:DM Mono,monospace;line-height:1;"
        f"text-shadow:0 0 20px {sc(overall)};'>{overall}</div>"
        f"<div><div style='font-size:15px;font-weight:700;color:white;margin-bottom:4px;'>"
        f"{label} 타입: <span style='color:{sc(overall)};'>{type_val}</span> "
        f"&nbsp;|&nbsp; {grade_label} 등급: <span style='color:{accent};font-weight:700;'>{grade_value}</span></div>"
        f"<div style='font-size:13px;color:#94a3b8;line-height:1.7;'>{result.get('summary','')}</div>"
        f"</div></div></div>"
        f"<div class='card'><div class='{stitle}'>{label} 세부 지표</div>"
        f"<div style='display:flex;gap:8px;flex-wrap:wrap;'>{metric_boxes}</div></div>"
        f"<div class='card'><div class='{stitle}'>매장 추천 제품 (완제품 · 즉시 사용 가능)</div>"
        f"<div style='font-size:20px;font-weight:800;color:white;margin-bottom:6px;'>"
        f"{product['code']} · {product['name']}</div>"
        f"<div style='font-size:13px;color:#94a3b8;margin-bottom:10px;'>"
        f"{product.get('desc','')}</div>"
        f"<div>{ing_h}</div></div>"
        f"{booster_html}"
        f"<div class='card'><div class='{stitle}'>사용 방법</div>{usage_html}"
        f"<div style='font-size:11px;color:#64748b;margin-top:10px;'>{usage_note}</div></div>"
        f"<div class='card' style='font-size:12px;color:#64748b;'>"
        f"이 제품은 완제품으로 사전 제조되어 있습니다. 매장에서 추가 혼합·소분 없이 "
        f"바로 전달하시면 됩니다.</div>"
        f"<div class='footer'>"
        f"본 안내는 AI 분석 기반 참고용이며 의료적 처방이 아닙니다<br>"
        f"YD Lab / 재능대학교 AI-바이오분석특화연구소</div>"
        f"</div></body></html>")

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
    if ingredient in SAMPLE_CONC_DB:
        return SAMPLE_CONC_DB[ingredient]
    for k in SAMPLE_CONC_DB:
        if k in ingredient or ingredient in k:
            return SAMPLE_CONC_DB[k]
    return None

def get_pollution_alert(pm25, ceei):
    if isinstance(pm25, (int, float)) and float(pm25) > PM25_ALERT_THRESHOLD:
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
      fill="{c}" font-size="21" font-weight="700"
      font-family="DM Mono,monospace"
      style="filter:drop-shadow(0 0 4px {c})">{score}</text>
    <text x="50" y="60" text-anchor="middle"
      fill="rgba(255,255,255,0.60)" font-size="11"
      font-family="Noto Sans KR,sans-serif">{label}</text>
  </svg>
  <div style="font-size:0.68rem;color:rgba(210,210,240,0.50);
    line-height:1.3;margin-top:0.1rem;max-width:90px;
    margin-left:auto;margin-right:auto;">
    {comment}</div>
</div>"""

# ══════════════════════════════════════════
# 환경 지수
# ══════════════════════════════════════════
CEEI_GRADE_LOW  = 50
CEEI_GRADE_MID  = 150
CEEI_GRADE_HIGH = 260

def calc_ceei(pm25_avg, residence_years):
    ceei = round(pm25_avg * residence_years, 1)
    if ceei < CEEI_GRADE_LOW:
        return (ceei,"낮음",
                f"<span class='chip chip-good'>CEEI {ceei} 낮음</span>",
                "WHO 대기질 권고기준(PM2.5 연평균 5㎍/m³) 이내 수준의 누적 노출 — 기본 보습·자외선 차단 유지")
    elif ceei < CEEI_GRADE_MID:
        return (ceei,"보통",
                f"<span class='chip chip-mid'>CEEI {ceei} 보통</span>",
                "국내 대기환경기준(PM2.5 연평균 15㎍/m³) 이내 수준 — 항산화 성분 정기 사용 권장")
    elif ceei < CEEI_GRADE_HIGH:
        return (ceei,"높음",
                f"<span class='chip chip-warn'>CEEI {ceei} 높음</span>",
                "선행연구에서 피부 유해영향이 보고되기 시작하는 노출 수준(PM2.5 약 26㎍/m³ 이상 장기노출)에 근접 — 항산화·장벽강화 집중 케어 필요")
    else:
        return (ceei,"매우높음",
                f"<span class='chip chip-bad'>CEEI {ceei} 매우높음</span>",
                "선행연구 상 피부 유해영향이 관찰된 노출 수준을 초과하는 누적 노출 — 피부과 상담·기능성 화장품 집중 케어 권장")

def uv_index_grade(uv):
    if uv is None: return ("알수없음", 1.0, "#888888")
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

SEEI_GRADE_LOW  = 50
SEEI_GRADE_MID  = 150
SEEI_GRADE_HIGH = 300

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
    if seei < SEEI_GRADE_LOW:
        grade, chip, msg = ("낮음",
            f"<span class='chip chip-good'>SEEI {seei} 낮음</span>",
            "복합 환경 노출 낮음(잠정 기준) — 기본 두피 보습·청결 유지")
    elif seei < SEEI_GRADE_MID:
        grade, chip, msg = ("보통",
            f"<span class='chip chip-mid'>SEEI {seei} 보통</span>",
            "중간 수준 복합 오염(잠정 기준) — 두피 항산화·항균 성분 정기 사용 권장")
    elif seei < SEEI_GRADE_HIGH:
        grade, chip, msg = ("높음",
            f"<span class='chip chip-warn'>SEEI {seei} 높음</span>",
            "높은 복합 오염 누적(잠정 기준, 두피 특이적 검증 진행 중) — 탈모 위험 증가, 두피케어 집중 필요")
    else:
        grade, chip, msg = ("매우높음",
            f"<span class='chip chip-bad'>SEEI {seei} 매우높음</span>",
            "매우 높은 누적(잠정 기준, 두피 특이적 검증 진행 중) — 두피 전문 케어·피부과 상담 권장")
    return (seei, grade, chip, msg, components, season,
            uv_val, uv_gstr, hum_val, hum_corr)

# ══════════════════════════════════════════
# 데이터 수집
# ══════════════════════════════════════════
def fetch_air(region):
    key = st.secrets.get("AIRKOREA_API_KEY","")
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
    for station in STATION_CANDIDATES.get(region, ["중구"]):
        if not key: break
        try:
            params = dict(serviceKey=key, stationName=station, dataTerm="DAILY",
                          pageNo=1, numOfRows=1, returnType="json", ver="1.3")
            r     = requests.get(url, params=params, timeout=8)
            items = r.json()["response"]["body"]["items"]
            if not (items and isinstance(items, list)): continue
            item  = items[0]
            def _s(k):
                v = item.get(k,"")
                return float(v) if v and str(v).strip() not in ["-","","None"] else None
            pm25 = _s("pm25Value")
            if pm25 is None: continue
            return dict(pm25=pm25, pm10=_s("pm10Value") or 0.0,
                        o3=_s("o3Value") or 0.0, no2=_s("no2Value") or 0.0,
                        station=station,
                        fetch_time=datetime.now().strftime("%Y-%m-%d %H:%M"), mock=False)
        except Exception: continue
    return dict(pm25=float(random.randint(12,65)), pm10=float(random.randint(18,85)),
                o3=round(random.uniform(0.010,0.080),3),
                no2=round(random.uniform(0.010,0.050),3),
                station="시간대 추정값",
                fetch_time=datetime.now().strftime("%Y-%m-%d %H:%M"), mock=True)

def fetch_kma_uv(region):
    key     = st.secrets.get("KMA_API_KEY","")
    area_no = KMA_AREA_CODE.get(region,"2800000000")
    today   = datetime.now().strftime("%Y%m%d")
    if key:
        try:
            url    = "http://apis.data.go.kr/1360000/LivingWthrIdxServiceV4/getUVIdxV4"
            params = dict(serviceKey=key, pageNo=1, numOfRows=10, dataType="JSON",
                          areaNo=area_no, time=today+"0600")
            r      = requests.get(url, params=params, timeout=8)
            items  = (r.json().get("response",{}).get("body",{})
                               .get("items",{}).get("item",[]))
            if items:
                uv_val = items[0].get("h12") or items[0].get("h0") or 0
                return {"uv_index": float(uv_val), "mock": False}
        except Exception: pass
    hour = datetime.now().hour
    if   6  <= hour <= 8:  est = 2.0
    elif 9  <= hour <= 11: est = 5.0
    elif hour == 12:       est = 8.0
    elif 13 <= hour <= 14: est = 9.0
    elif 15 <= hour <= 17: est = 5.0
    elif 18 <= hour <= 19: est = 2.0
    else:                  est = 0.0
    return {"uv_index": est, "mock": True}

def fetch_kma_humidity(region):
    key    = st.secrets.get("KMA_API_KEY","")
    nx, ny = KMA_GRID.get(region,(54,124))
    now    = datetime.now()
    if key:
        try:
            url      = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
            obs_time = now - timedelta(hours=1) if now.minute < 40 else now
            params   = dict(serviceKey=key, pageNo=1, numOfRows=10, dataType="JSON",
                            base_date=obs_time.strftime("%Y%m%d"),
                            base_time=obs_time.strftime("%H00"), nx=nx, ny=ny)
            r      = requests.get(url, params=params, timeout=8)
            items  = (r.json().get("response",{}).get("body",{})
                               .get("items",{}).get("item",[]))
            for item in items:
                if item.get("category") == "REH":
                    return {"humidity": float(item.get("obsrValue",50)), "mock": False}
        except Exception: pass
        try:
            base_hours = [2,5,8,11,14,17,20,23]
            candidates = [h for h in base_hours if h <= now.hour]
            if candidates: base_hour = max(candidates); base_date = now.strftime("%Y%m%d")
            else:          base_hour = 23; base_date = (now-timedelta(days=1)).strftime("%Y%m%d")
            url    = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
            params = dict(serviceKey=key, pageNo=1, numOfRows=100, dataType="JSON",
                          base_date=base_date, base_time=f"{base_hour:02d}00", nx=nx, ny=ny)
            r      = requests.get(url, params=params, timeout=8)
            items  = (r.json().get("response",{}).get("body",{})
                               .get("items",{}).get("item",[]))
            now_str   = now.strftime("%Y%m%d%H%M")[:10]
            reh_items = sorted([i for i in items if i.get("category")=="REH"],
                               key=lambda x: x.get("fcstDate","")+x.get("fcstTime",""))
            for item in reh_items:
                fdt = item.get("fcstDate","") + item.get("fcstTime","")[:2]
                if fdt >= now_str:
                    return {"humidity": float(item.get("fcstValue",50)), "mock": False}
            if reh_items:
                return {"humidity": float(reh_items[-1].get("fcstValue",50)), "mock": False}
        except Exception: pass
    month = now.month
    if month in [6,7,8]:    hum = random.randint(65,85)
    elif month in [12,1,2]: hum = random.randint(30,50)
    else:                   hum = random.randint(45,65)
    return {"humidity": float(hum), "mock": True}

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
        msg = client.messages.create(model="claude-haiku-4-5", max_tokens=1200,
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
        msg = client.messages.create(model="claude-haiku-4-5", max_tokens=1200,
                                     messages=[{"role":"user","content":content}])
        return json.loads(re.sub(r"```json|```","",msg.content[0].text.strip()).strip())
    except Exception as e:
        st.error(f"두피 분석 오류: {e}"); return None

# ══════════════════════════════════════════
# 혼합 가이드 — 20종 샘플 기반 (교육용 전용)
# ══════════════════════════════════════════
def generate_mixing_guide(ingredients, skin_type, ceei_grade, total_ml=30):
    BW = {
        "히알루론산":35,"나이아신아마이드":20,"판테놀":25,
        "아스코빌글루코사이드":15,"비타민C유도체":15,
        "레티닐팔미테이트":8,"아세틸헥사펩타이드-8":8,"피토스핑고신":12,
        "펩타이드":15,"아데노신":10,"글리세린":20,"알란토인":10,
        "스쿠알란":10,"살리실산":10,
    }
    boost       = {"낮음":1.0,"보통":1.2,"높음":1.5,"매우높음":1.8}.get(ceei_grade,1.0)
    antioxidants  = {"아스코빌글루코사이드","비타민C유도체","나이아신아마이드",
                     "펩타이드","레티닐팔미테이트"}
    sensitive_red = {"레티닐팔미테이트","살리실산"}
    is_s = skin_type in ["민감성","건성"]
    weights = {}
    for ing in ingredients:
        w = BW.get(ing, 10)
        if ing in antioxidants:           w = round(w * boost)
        if is_s and ing in sensitive_red: w = max(3, round(w * 0.5))
        weights[ing] = w
    tw     = sum(weights.values())
    ratios = {ing: round(w/tw*100) for ing,w in weights.items()}
    diff   = 100 - sum(ratios.values())
    if diff and ratios: ratios[max(ratios, key=ratios.get)] += diff
    ml_dict = {ing: round(total_ml * pct/100, 1) for ing,pct in ratios.items()}
    OG = {
        1: {"히알루론산","판테놀","글리세린"},
        2: {"나이아신아마이드","아스코빌글루코사이드","비타민C유도체","펩타이드"},
        3: {"아데노신","아세틸헥사펩타이드-8","레티닐팔미테이트","알란토인","피토스핑고신"},
        4: {"살리실산","스쿠알란"},
    }
    steps = {}
    for ing in ingredients:
        g = next((k for k,s in OG.items() if ing in s), 5)
        steps.setdefault(g,[]).append(ing)
    SL = {1:"수용성 베이스 혼합",2:"기능성 성분 첨가",
          3:"고기능 활성 성분 첨가",4:"특수 성분 첨가",5:"기타"}
    return {"ratios":ratios,"ml":ml_dict,
            "steps":[{"label":SL.get(g,"성분 첨가"),"items":steps[g]}
                     for g in sorted(steps)],
            "total_ml":total_ml}

def generate_scalp_mixing_guide(ingredients, scalp_result, seei_grade, total_ml=30):
    BW = {
        "피록톤올아민":25,"살리실산":20,"바이오틴":20,"판테놀":25,
        "나이아신아마이드":15,"히알루론산":15,"피토스핑고신":12,"아데노신":10,
        "티트리오일":15,"로즈마리오일":10,"멘톨":5,"소듐PCA":15,
    }
    ks = scalp_result.get("keratin_score",70)
    ps = scalp_result.get("pore_score",70)
    ts = scalp_result.get("hair_thickness_score",70)
    cs = scalp_result.get("scalp_color_score",70)
    ms = scalp_result.get("moisture_balance_score",70)
    ds = scalp_result.get("hair_damage_score",70)
    eb = {"낮음":1.0,"보통":1.3,"높음":1.6,"매우높음":2.0}.get(seei_grade,1.0)
    weights = {}
    for ing in ingredients:
        w = BW.get(ing, 10)
        if ing in {"살리실산","피록톤올아민","티트리오일"} and ks < 50: w = round(w*1.5)
        if ing == "살리실산" and ps < 50:                               w = round(w*1.3)
        if ing in {"바이오틴","판테놀"} and ts < 50:                    w = round(w*1.5)
        if ing in {"판테놀","피토스핑고신"} and cs < 50:                w = round(w*1.4)
        if ing in {"판테놀","히알루론산","소듐PCA"} and ms < 50:        w = round(w*1.3)
        if ing in {"바이오틴","판테놀"} and ds < 50:                    w = round(w*1.3)
        if ing in {"나이아신아마이드","피토스핑고신"}:                   w = round(w*eb)
        weights[ing] = max(w, 5)
    tw     = sum(weights.values())
    ratios = {ing: round(w/tw*100) for ing,w in weights.items()}
    diff   = 100 - sum(ratios.values())
    if diff and ratios: ratios[max(ratios, key=ratios.get)] += diff
    ml_dict = {ing: round(total_ml * pct/100, 1) for ing,pct in ratios.items()}
    OG = {
        1: {"히알루론산","판테놀","소듐PCA"},
        2: {"나이아신아마이드","아데노신"},
        3: {"바이오틴","피토스핑고신"},
        4: {"피록톤올아민","살리실산","티트리오일","로즈마리오일","멘톨"},
    }
    steps = {}
    for ing in ingredients:
        g = next((k for k,s in OG.items() if ing in s), 5)
        steps.setdefault(g,[]).append(ing)
    SL = {1:"두피 베이스 혼합",2:"기능성 성분 첨가",
          3:"모발·장벽 강화",4:"특수 성분 첨가",5:"기타"}
    return {"ratios":ratios,"ml":ml_dict,
            "steps":[{"label":SL.get(g,"성분 첨가"),"items":steps[g]}
                     for g in sorted(steps)],
            "total_ml":total_ml}

# ══════════════════════════════════════════
# UI 컴포넌트
# ══════════════════════════════════════════
def show_mixing_card(mixing, title, is_scalp=False):
    bar_cls   = "scalp-mixing-bar" if is_scalp else "mixing-bar"
    lbl_color = "#6ee7b7" if is_scalp else "#a5b4fc"
    st.markdown("<div class='mixing-card'>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-size:0.72rem;letter-spacing:0.16em;text-transform:uppercase;"
        f"color:{lbl_color};font-weight:700;font-family:DM Mono,monospace;"
        f"margin-bottom:0.5rem;padding-bottom:0.7rem;"
        f"border-bottom:1px solid rgba(255,255,255,0.08);'>{title}</div>",
        unsafe_allow_html=True)
    st.markdown(
        "<div class='sample-notice'>"
        "📦 YD Lab 사전 준비 20종 샘플(v4.2) 기반 — 권장농도 샘플을 아래 비율로 혼합하세요"
        "</div>",
        unsafe_allow_html=True)
    rows = ""
    for ing, pct in sorted(mixing["ratios"].items(), key=lambda x: -x[1]):
        ml    = mixing["ml"].get(ing, 0)
        conc  = get_sample_conc(ing)
        sno   = conc["sample_no"] if conc else "─"
        c_pct = f"{conc['pct']}%" if conc else "재량"
        rows += (
            f"<div class='mixing-row'>"
            f"<span class='mixing-sno'>{sno}</span>"
            f"<span class='mixing-ing'>{ing}</span>"
            f"<div class='mixing-bar-wrap'>"
            f"<div class='{bar_cls}' style='width:{pct}%;'></div></div>"
            f"<span class='mixing-pct'>{pct}%</span>"
            f"<span class='mixing-ml'>{ml}ml</span>"
            f"<span class='mixing-conc'>샘플 {c_pct}</span>"
            f"</div>")
    st.markdown(rows, unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align:right;font-size:0.86rem;font-weight:700;"
        f"color:rgba(220,220,240,0.65);padding:0.5rem 0;'>"
        f"총 {mixing['total_ml']}ml</div>",
        unsafe_allow_html=True)
    badge = "step-badge-green" if is_scalp else "step-badge"
    st.markdown(
        "<div style='margin-top:0.8rem;font-size:0.82rem;font-weight:700;"
        "color:rgba(210,210,240,0.65);margin-bottom:0.5rem;letter-spacing:0.08em;'>"
        "MIXING ORDER</div>", unsafe_allow_html=True)
    for dn, s in enumerate(mixing["steps"], start=1):
        items_str = " + ".join(s["items"])
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.5rem;"
            f"padding:0.4rem 0;font-size:0.86rem;color:rgba(220,220,240,0.80);'>"
            f"<span class='{badge}'>{dn}</span>"
            f"<span><b style='color:rgba(255,255,255,0.92);'>{s['label']}</b>"
            f" — {items_str}</span></div>",
            unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def show_air_status(air, uv_data=None, humidity_data=None):
    is_mock = air.get("mock")
    uv_mock = (uv_data or {}).get("mock", True)
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

def scroll_to_results():
    components.html(
        """
        <script>
        setTimeout(function() {
            const doc = window.parent.document;
            const el = doc.getElementById('ydlab-results-anchor');
            if (el) { el.scrollIntoView({behavior: 'smooth', block: 'start'}); }
        }, 150);
        </script>
        """,
        height=0,
    )

def force_selectbox_white():
    components.html(
        """
        <script>
        (function() {
            function paintWhite(root) {
                var boxes = root.querySelectorAll('[data-baseweb="select"]');
                boxes.forEach(function(box) {
                    box.style.setProperty('color', '#ffffff', 'important');
                    box.style.setProperty('-webkit-text-fill-color', '#ffffff', 'important');
                    var all = box.querySelectorAll('*');
                    all.forEach(function(el) {
                        el.style.setProperty('color', '#ffffff', 'important');
                        el.style.setProperty('-webkit-text-fill-color', '#ffffff', 'important');
                        el.style.setProperty('opacity', '1', 'important');
                    });
                });
            }
            var doc = window.parent.document;
            paintWhite(doc);
            var observer = new MutationObserver(function() { paintWhite(doc); });
            observer.observe(doc.body, {childList: true, subtree: true});
            setInterval(function() { paintWhite(doc); }, 800);
        })();
        </script>
        """,
        height=0,
    )

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
                st.session_state["scroll_pending"] = True
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
    pm25_avg = REGION_PM25_AVG.get(region, 22.0)
    yrs      = RESIDENCE_YEAR_MAP.get(res_str, 0)
    ceei, ceei_grade, ceei_chip, ceei_msg = calc_ceei(pm25_avg, yrs)
    pm25_val  = air.get("pm25")
    alert     = get_pollution_alert(pm25_val, ceei)
    overall   = result.get("overall_score", 0)
    skin_type = result.get("skin_type", "")
    ings      = result.get("recommended_ingredients", [])
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
        f"<div style='font-size:0.76rem;color:rgba(200,200,230,0.55);margin-top:0.3rem;"
        f"font-family:DM Mono,monospace;letter-spacing:0.1em;'>OVERALL SCORE</div>"
        f"</div>"
        f"<div style='flex:1;'>"
        f"<div style='font-size:1.2rem;font-weight:700;color:white;margin-bottom:0.5rem;'>"
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
    for i, (lbl,val,cmt) in enumerate(metrics):
        with cols[i]:
            st.markdown(svg_gauge(val, lbl, cmt, 96), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    ing_html = "".join([f"<span class='ing-chip'>{ing}</span>" for ing in ings])
    st.markdown(
        f"<div class='glass-card'><div class='card-label'>AI 추천 화장품 성분</div>"
        f"<div style='margin-bottom:0.8rem;'>{ing_html}</div>"
        f"<div class='result-text'>{result.get('care_advice','')}</div></div>",
        unsafe_allow_html=True)
    scores = {
        "주름":result.get("wrinkle_score",0),
        "모공":result.get("pore_score",0),
        "피부결":result.get("texture_score",0),
        "피부톤":result.get("tone_score",0),
        "수분":result.get("moisture_score",0),
    }
    pri = sorted([(k,v) for k,v in scores.items() if v>0], key=lambda x:x[1])[:3]
    if not pri: pri = sorted(scores.items(), key=lambda x:x[1])[:3]
    st.markdown("<div class='glass-card'><div class='card-label'>우선 개선 항목</div>",
                unsafe_allow_html=True)
    for i, (lbl, sc_) in enumerate(pri):
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

    # 사업용 모드 분기
    usage_mode = st.session_state.get("usage_mode", "edu")
    if usage_mode == "biz":
        product = match_skin_product(result, ceei_grade)
        show_product_match_card(product, "CEEI", ceei_grade, is_scalp=False)
        biz_html = generate_biz_match_report_html(
            product, "CEEI", ceei_grade, region, pid, age, gender,
            overall, result, is_scalp=False)
        st.download_button("매장 전달용 리포트 다운로드", data=biz_html.encode("utf-8"),
            file_name=f"YDLab_피부추천제품_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html", use_container_width=True, key="k_skin_biz_report")
        return

    # 교육용 전용
    chosen_ml = vol_selector("skin")
    if ings:
        mixing = generate_mixing_guide(ings, skin_type, ceei_grade, total_ml=chosen_ml)
        show_mixing_card(mixing,
            f"피부 맞춤 혼합 — {chosen_ml}ml / {skin_type}", is_scalp=False)
    st.markdown(
        f"<div class='glass-card'><div class='card-label'>CEEI 피부 누적 환경노출지수</div>"
        f"<div style='display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.7rem;'>"
        f"{pm25_chip(pm25_val)} {ceei_chip}"
        f"<span class='chip chip-neu'>연평균 {pm25_avg}㎍/m³</span>"
        f"<span class='chip chip-neu'>거주 {yrs}년</span></div>"
        f"<div class='result-text'>{ceei_msg}</div>"
        f"<div style='font-size:0.70rem;color:rgba(180,180,220,0.40);margin-top:0.5rem;'>"
        f"* 등급 기준: WHO(2021) 대기질 권고기준, 국내 대기환경기준, "
        f"Kim et al. 2017(Int J Environ Res Public Health) 참고 — 의학적 진단 아님</div></div>",
        unsafe_allow_html=True)
    st.markdown("---")
    mixing_final = generate_mixing_guide(ings, skin_type, ceei_grade, total_ml=chosen_ml)
    c1, c2 = st.columns(2)
    with c1:
        html = generate_skin_report_html(
            result, air, region, yrs, pid, age, gender, mixing_final)
        st.download_button("피부 분석 리포트 다운로드", data=html.encode("utf-8"),
            file_name=f"YDLab_피부리포트_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html", use_container_width=True, key="k_skin_report")
    with c2:
        html2 = generate_skin_order_html(
            result, air, region, yrs, pid, age, gender, mixing_final)
        st.download_button("피부 공방 주문서 다운로드", data=html2.encode("utf-8"),
            file_name=f"YDLab_피부주문서_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html", use_container_width=True, key="k_skin_order")

# ══════════════════════════════════════════
# 결과 렌더링 — 두피
# ══════════════════════════════════════════
def show_scalp_result(result, air, region, res_str, pid, age, gender, parts,
                      uv_data=None, humidity_data=None):
    pm25_avg  = REGION_PM25_AVG.get(region, 22.0)
    yrs       = RESIDENCE_YEAR_MAP.get(res_str, 0)
    ceei, ceei_grade, ceei_chip, _ = calc_ceei(pm25_avg, yrs)
    (seei, seei_grade, seei_chip, seei_msg, seei_comp, season_corr,
     uv_val, uv_gstr, hum_val, hum_corr) = calc_seei(air, yrs, uv_data, humidity_data)
    _, uv_corr, uv_color = uv_index_grade(uv_val)
    pm25_val   = air.get("pm25")
    overall    = result.get("overall_score", 0)
    scalp_type = result.get("scalp_type", "")
    ings       = result.get("recommended_ingredients", [])
    st.markdown("<div class='patent-banner'>본 기술은 특허 출원 중입니다 (CEEI·SEEI 알고리즘 / 기상청 연동)</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='medical-disclaimer'>본 분석 결과는 AI 기반 참고용 정보이며 의학적 진단이 아닙니다.</div>",
                unsafe_allow_html=True)
    show_air_status(air, uv_data, humidity_data)
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
    for i, (lbl,val,cmt) in enumerate(scalp_metrics):
        with cols[i%3]:
            st.markdown(svg_gauge(val, lbl, cmt, 96), unsafe_allow_html=True)
    hl  = result.get("hair_loss_risk_score", 0)
    hlc = result.get("hair_loss_risk_comment", "")
    st.markdown(
        f"<div class='hair-loss-box'>"
        f"<span style='color:rgba(220,220,240,0.75);font-size:0.86rem;'>"
        f"탈모 진행도 (참고용)</span> "
        f"<span style='font-weight:700;font-family:DM Mono,monospace;"
        f"color:{score_color(hl)};text-shadow:0 0 10px {score_color(hl)};'>{hl}점</span>"
        f"<span style='color:rgba(200,200,230,0.60);font-size:0.82rem;'> — {hlc}</span></div>",
        unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    ing_html = "".join([f"<span class='scalp-chip'>{ing}</span>" for ing in ings])
    st.markdown(
        f"<div class='glass-card' style='border-color:rgba(16,185,129,0.20);'>"
        f"<div class='card-label-green'>AI 추천 두피·모발 성분</div>"
        f"<div style='margin-bottom:0.8rem;'>{ing_html}</div>"
        f"<div class='result-text'>{result.get('care_advice','')}</div></div>",
        unsafe_allow_html=True)
    comp_boxes = "".join([
        f"<div style='background:rgba(255,255,255,0.05);border:1px solid rgba(16,185,129,0.16);"
        f"border-radius:10px;padding:0.6rem;text-align:center;'>"
        f"<div style='font-weight:700;color:#6ee7b7;font-size:0.88rem;"
        f"font-family:DM Mono,monospace;'>{v}</div>"
        f"<div style='color:rgba(200,200,230,0.55);font-size:0.72rem;margin-top:0.2rem;'>{k}</div></div>"
        for k,v in seei_comp.items()])
    uv_d   = f"{uv_val:.1f}" if uv_val is not None else "--"
    hum_d  = f"{hum_val:.0f}%" if hum_val is not None else "--"
    uv_mt  = "" if not (uv_data  or {}).get("mock", True) else " (추정)"
    hum_mt = "" if not (humidity_data or {}).get("mock", True) else " (추정)"
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
        f"<div style='font-size:0.78rem;color:rgba(180,180,220,0.40);margin-top:0.6rem;"
        f"font-style:italic;font-family:DM Mono,monospace;'>"
        f"SEEI = (PM2.5×0.40+PM10×0.25+NO2×0.20+O3×0.15)×거주기간×계절×UV×습도</div>"
        f"<div class='result-text' style='margin-top:0.5rem;'>{seei_msg}</div>"
        f"<div style='font-size:0.70rem;color:rgba(180,180,220,0.40);margin-top:0.5rem;'>"
        f"* 등급 구간은 CEEI(피부) 문헌 기준을 잠정 준용 — 두피 특이적 검증은 자체 데이터 축적 후 진행 예정</div></div>",
        unsafe_allow_html=True)
    pri_scores = {
        "각질":result.get("keratin_score",0),
        "모공피지":result.get("pore_score",0),
        "모발굵기":result.get("hair_thickness_score",0),
        "색상염증":result.get("scalp_color_score",0),
        "수분유분":result.get("moisture_balance_score",0),
        "손상도":result.get("hair_damage_score",0),
    }
    pri = sorted([(k,v) for k,v in pri_scores.items() if v>0], key=lambda x:x[1])[:3]
    if not pri: pri = sorted(pri_scores.items(), key=lambda x:x[1])[:3]
    st.markdown(
        "<div class='glass-card' style='border-color:rgba(16,185,129,0.20);'>"
        "<div class='card-label-green'>우선 개선 항목 (두피)</div>",
        unsafe_allow_html=True)
    for i, (lbl, sc_) in enumerate(pri):
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

    # 사업용 모드 분기
    usage_mode = st.session_state.get("usage_mode", "edu")
    if usage_mode == "biz":
        product = match_scalp_product(result, seei_grade)
        show_product_match_card(product, "SEEI", seei_grade, is_scalp=True)
        biz_html = generate_biz_match_report_html(
            product, "SEEI", seei_grade, region, pid, age, gender,
            overall, result, is_scalp=True)
        st.download_button("매장 전달용 리포트 다운로드", data=biz_html.encode("utf-8"),
            file_name=f"YDLab_두피추천제품_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html", use_container_width=True, key="k_scalp_biz_report")
        return

    # 교육용 전용
    chosen_ml = vol_selector("scalp")
    if ings:
        mixing = generate_scalp_mixing_guide(
            ings, result, seei_grade, total_ml=chosen_ml)
        show_mixing_card(mixing,
            f"두피 맞춤 혼합 — {chosen_ml}ml / {scalp_type} / SEEI {seei_grade}",
            is_scalp=True)
    st.markdown("---")
    mixing_final = generate_scalp_mixing_guide(
        ings, result, seei_grade, total_ml=chosen_ml)
    c1, c2 = st.columns(2)
    with c1:
        html = generate_scalp_report_html(
            result, air, region, yrs, pid, age, gender, mixing_final,
            seei, seei_grade, seei_msg, seei_comp, season_corr,
            uv_val, uv_gstr, uv_corr, hum_val, hum_corr)
        st.download_button("두피 분석 리포트 다운로드", data=html.encode("utf-8"),
            file_name=f"YDLab_두피리포트_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html", use_container_width=True, key="k_scalp_report")
    with c2:
        html2 = generate_scalp_order_html(
            result, air, region, yrs, pid, age, gender, mixing_final,
            seei, seei_grade, seei_msg, uv_val, uv_gstr, hum_val)
        st.download_button("두피 공방 주문서 다운로드", data=html2.encode("utf-8"),
            file_name=f"YDLab_두피주문서_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html", use_container_width=True, key="k_scalp_order")
# ============================================================
# HTML 리포트 헤더
# ============================================================
def _html_head(title: str) -> str:
    return f"""<!DOCTYPE html><html lang='ko'><head><meta charset='utf-8'>
<title>{title}</title>
<style>
body{{font-family:'Malgun Gothic','Noto Sans KR',sans-serif;background:#f7f7fb;color:#222;padding:24px;max-width:960px;margin:0 auto;}}
h1{{color:#4b3fa7;border-bottom:3px solid #4b3fa7;padding-bottom:8px;}}
h2{{color:#2d2a6e;margin-top:24px;border-left:5px solid #4b3fa7;padding-left:10px;}}
h3{{color:#333;margin-top:16px;}}
table{{width:100%;border-collapse:collapse;margin:12px 0;background:#fff;}}
th,td{{border:1px solid #d0d0e0;padding:8px 10px;text-align:left;font-size:14px;}}
th{{background:#eeeaff;color:#2d2a6e;}}
.chip{{display:inline-block;padding:4px 10px;margin:2px;border-radius:12px;background:#eeeaff;color:#2d2a6e;font-size:12px;}}
.card{{background:#fff;border:1px solid #e0e0ee;border-radius:8px;padding:14px;margin:10px 0;box-shadow:0 2px 6px rgba(0,0,0,0.04);}}
.footer{{margin-top:32px;font-size:12px;color:#666;border-top:1px solid #ccc;padding-top:10px;}}
.alert{{background:#fff4e6;border-left:4px solid #ff9500;padding:10px;margin:10px 0;}}
.score-big{{font-size:36px;font-weight:800;color:#4b3fa7;}}
</style></head><body>"""

def _mixing_html_table(guide: dict) -> str:
    """혼합 가이드를 HTML 표로"""
    if not guide or "steps" not in guide:
        return ""
    rows = ""
    for s in guide["steps"]:
        rows += f"<tr><td>{s.get('order','')}</td><td>{s.get('ingredient','')}</td><td>{s.get('amount_ml','')} ml</td><td>{s.get('pct','')}%</td><td>{s.get('note','')}</td></tr>"
    return f"""<table><thead><tr><th>순서</th><th>성분</th><th>용량</th><th>농도</th><th>비고</th></tr></thead><tbody>{rows}</tbody></table>"""

# ============================================================
# 교육용 리포트 생성 (피부)
# ============================================================
def generate_skin_report_html(result: dict, ceei: float, ceei_grade: str, air: dict, guide: dict, meta: dict) -> str:
    html = _html_head("YD Lab 피부 분석 리포트")
    html += f"<h1>🌿 YD Lab 피부 분석 리포트</h1>"
    html += f"<div class='card'><b>분석일시:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br>"
    html += f"<b>고객명:</b> {meta.get('name','-')} | <b>연령대:</b> {meta.get('age','-')} | <b>성별:</b> {meta.get('gender','-')}<br>"
    html += f"<b>지역:</b> {meta.get('region','-')} | <b>거주기간:</b> {meta.get('years','-')}년</div>"
    
    html += f"<h2>📊 종합 점수</h2><div class='card'><span class='score-big'>{result.get('overall_score',0)}</span> / 100<br>"
    html += f"<b>피부 타입:</b> {result.get('skin_type','-')}<br>"
    html += f"<b>종합 코멘트:</b> {result.get('overall_comment','-')}</div>"
    
    html += "<h2>🔬 세부 지표</h2><table><thead><tr><th>항목</th><th>점수</th><th>코멘트</th></tr></thead><tbody>"
    for k, label in [("hydration","수분"),("oil","유분"),("elasticity","탄력"),("pigmentation","색소침착"),("pores","모공"),("sensitivity","민감도")]:
        m = result.get("metrics", {}).get(k, {})
        html += f"<tr><td>{label}</td><td>{m.get('score','-')}</td><td>{m.get('comment','-')}</td></tr>"
    html += "</tbody></table>"
    
    html += f"<h2>🌫️ 환경 지수 (CEEI)</h2><div class='card'>"
    html += f"<b>CEEI:</b> {ceei:.1f} ({ceei_grade})<br>"
    html += f"<b>PM2.5:</b> {air.get('pm25','-')} µg/m³ | <b>UV:</b> {air.get('uv','-')} | <b>습도:</b> {air.get('humidity','-')}%</div>"
    
    html += "<h2>💧 추천 성분</h2><div class='card'>"
    for ing in result.get("recommended_ingredients", []):
        html += f"<span class='chip'>{ing}</span>"
    html += "</div>"
    
    if guide:
        html += "<h2>🧪 혼합 가이드</h2>" + _mixing_html_table(guide)
    
    html += "<div class='footer'>본 리포트는 YD Lab 교육용 자료이며 의료 진단이 아닙니다. © YD Lab</div>"
    html += "</body></html>"
    return html

# ============================================================
# 교육용 리포트 생성 (두피)
# ============================================================
def generate_scalp_report_html(result: dict, seei: float, seei_grade: str, air: dict, guide: dict, meta: dict) -> str:
    html = _html_head("YD Lab 두피 분석 리포트")
    html += f"<h1>🌿 YD Lab 두피 분석 리포트</h1>"
    html += f"<div class='card'><b>분석일시:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br>"
    html += f"<b>고객명:</b> {meta.get('name','-')} | <b>연령대:</b> {meta.get('age','-')} | <b>성별:</b> {meta.get('gender','-')}</div>"
    
    html += f"<h2>📊 종합 점수</h2><div class='card'><span class='score-big'>{result.get('overall_score',0)}</span> / 100<br>"
    html += f"<b>두피 타입:</b> {result.get('scalp_type','-')}<br>"
    html += f"<b>종합 코멘트:</b> {result.get('overall_comment','-')}</div>"
    
    html += "<h2>🔬 세부 지표</h2><table><thead><tr><th>항목</th><th>점수</th><th>코멘트</th></tr></thead><tbody>"
    for k, label in [("sebum","피지"),("dandruff","비듬"),("redness","홍반"),("hair_density","모발밀도"),("follicle","모낭건강"),("sensitivity","민감도")]:
        m = result.get("metrics", {}).get(k, {})
        html += f"<tr><td>{label}</td><td>{m.get('score','-')}</td><td>{m.get('comment','-')}</td></tr>"
    html += "</tbody></table>"
    
    html += f"<h2>🌫️ 환경 지수 (SEEI)</h2><div class='card'>"
    html += f"<b>SEEI:</b> {seei:.1f} ({seei_grade})<br>"
    html += f"<b>PM2.5:</b> {air.get('pm25','-')} µg/m³ | <b>UV:</b> {air.get('uv','-')} | <b>습도:</b> {air.get('humidity','-')}%</div>"
    
    html += "<h2>💧 추천 성분</h2><div class='card'>"
    for ing in result.get("recommended_ingredients", []):
        html += f"<span class='chip'>{ing}</span>"
    html += "</div>"
    
    if guide:
        html += "<h2>🧪 혼합 가이드</h2>" + _mixing_html_table(guide)
    
    html += "<div class='footer'>본 리포트는 YD Lab 교육용 자료이며 의료 진단이 아닙니다. © YD Lab</div>"
    html += "</body></html>"
    return html

# ============================================================
# 교육용 공방 주문서
# ============================================================
def generate_skin_order_html(guide: dict, meta: dict, volume: int) -> str:
    html = _html_head("YD Lab 공방 주문서")
    html += f"<h1>📋 YD Lab 공방 주문서</h1>"
    html += f"<div class='card'><b>주문일시:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br>"
    html += f"<b>주문자:</b> {meta.get('name','-')}<br>"
    html += f"<b>제조 용량:</b> {volume} ml</div>"
    html += "<h2>🧪 배합 지시서</h2>" + _mixing_html_table(guide)
    html += "<div class='footer'>본 주문서는 YD Lab 교육용 실습 자료입니다.</div></body></html>"
    return html

# ============================================================
# 데이터 저장 (CSV + Google Sheets)
# ============================================================
FIELDS = ["timestamp","usage_mode","mode","name","age","gender","region","years",
          "overall_score","skin_or_scalp_type","ceei_seei","grade","pm25","uv","humidity",
          "matched_product_code","event_code"]

def save_to_csv(row: dict, path: str = "ydlab_records.csv"):
    try:
        p = Path(path)
        write_header = not p.exists()
        with p.open("a", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if write_header:
                w.writeheader()
            w.writerow({k: row.get(k, "") for k in FIELDS})
    except Exception as e:
        print(f"CSV save error: {e}")

def save_to_gsheet(row: dict):
    try:
        sheet_id = st.secrets.get("GOOGLE_SHEETS_ID", "")
        if not sheet_id:
            return
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(sheet_id).sheet1
        # 헤더 확인
        try:
            headers = sh.row_values(1)
            if not headers:
                sh.append_row(FIELDS)
        except:
            sh.append_row(FIELDS)
        sh.append_row([str(row.get(k, "")) for k in FIELDS])
    except Exception as e:
        print(f"GSheet save error: {e}")

def save_record(row: dict):
    save_to_csv(row)
    save_to_gsheet(row)

# ============================================================
# 스크롤 및 selectbox 유틸
# ============================================================
def scroll_to_results():
    components.html("""
    <script>
    setTimeout(function(){
        const anchor = window.parent.document.getElementById('ydlab-results-anchor');
        if(anchor){ anchor.scrollIntoView({behavior:'smooth', block:'start'}); }
    }, 150);
    </script>
    """, height=0)

def force_selectbox_white():
    components.html("""
    <script>
    function paintSelects(){
        const doc = window.parent.document;
        doc.querySelectorAll('div[data-baseweb="select"] *').forEach(el=>{
            el.style.color = '#ffffff';
            el.style.webkitTextFillColor = '#ffffff';
        });
    }
    paintSelects();
    const obs = new MutationObserver(paintSelects);
    obs.observe(window.parent.document.body, {childList:true, subtree:true});
    setInterval(paintSelects, 800);
    </script>
    """, height=0)

# ============================================================
# 로그인/인증
# ============================================================
def check_access_code(code: str) -> str:
    """반환: 'edu' / 'biz' / '' """
    code = (code or "").strip().upper()
    edu_codes = [c.strip().upper() for c in st.secrets.get("EDU_ACCESS_CODES", "").split(",") if c.strip()]
    biz_codes = [c.strip().upper() for c in st.secrets.get("BIZ_ACCESS_CODES", "").split(",") if c.strip()]
    if code in edu_codes:
        return "edu"
    if code in biz_codes:
        return "biz"
    return ""

def login_screen():
    st.markdown("<div class='glass-card' style='text-align:center;'><h1>🌿 YD Lab</h1><p>피부·두피 분석 시스템</p></div>", unsafe_allow_html=True)
    # URL 파라미터 자동 인식
    qp = st.query_params
    url_code = qp.get("code", "")
    if url_code and not st.session_state.get("authed"):
        mode = check_access_code(url_code)
        if mode:
            st.session_state["authed"] = True
            st.session_state["usage_mode"] = mode
            st.rerun()
    with st.form("login_form"):
        code = st.text_input("접속 코드를 입력하세요", type="password")
        submitted = st.form_submit_button("입장", type="primary", use_container_width=True)
        if submitted:
            mode = check_access_code(code)
            if mode:
                st.session_state["authed"] = True
                st.session_state["usage_mode"] = mode
                st.success(f"✅ {'교육용' if mode=='edu' else '사업용'} 모드로 접속합니다.")
                st.rerun()
            else:
                st.error("❌ 유효하지 않은 접속 코드입니다.")

# ============================================================
# 관리자 사이드바
# ============================================================
def admin_sidebar():
    with st.sidebar:
        st.markdown("### 🔐 관리자")
        pw = st.text_input("관리자 비밀번호", type="password", key="k_admin_pw")
        if pw and pw == st.secrets.get("ADMIN_PASSWORD", ""):
            st.success("관리자 인증됨")
            try:
                df = pd.read_csv("ydlab_records.csv")
                st.metric("총 기록", len(df))
                if "usage_mode" in df.columns:
                    st.write("**모드별**")
                    st.bar_chart(df["usage_mode"].value_counts())
                if "matched_product_code" in df.columns:
                    st.write("**매칭 상품**")
                    st.bar_chart(df["matched_product_code"].value_counts())
                st.download_button("📥 CSV 다운로드", df.to_csv(index=False).encode("utf-8-sig"),
                                   file_name="ydlab_records.csv", mime="text/csv")
            except FileNotFoundError:
                st.info("아직 기록이 없습니다.")
            except Exception as e:
                st.error(f"오류: {e}")
        st.markdown("---")
        if st.session_state.get("authed"):
            if st.button("🚪 로그아웃", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()

# ============================================================
# 메인
# ============================================================
def main():
    force_selectbox_white()
    
    if not st.session_state.get("authed"):
        login_screen()
        return
    
    admin_sidebar()
    
    usage_mode = st.session_state.get("usage_mode", "edu")
    mode_label = "🏪 사업용 모드" if usage_mode == "biz" else "🎓 교육용 모드"
    st.markdown(f"<div class='mode-banner'>{mode_label}</div>", unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align:center;'>🌿 YD Lab 피부·두피 분석</h1>", unsafe_allow_html=True)
    
    # 분석 유형 선택
    st.markdown("<div class='glass-card'><div class='card-label'>분석 유형 선택</div>", unsafe_allow_html=True)
    mode = st.radio("분석 유형", ["skin", "scalp"], format_func=lambda x: "🌸 피부 분석" if x=="skin" else "💇 두피 분석",
                    horizontal=True, key="k_mode", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 고객 정보
    st.markdown("<div class='glass-card'><div class='card-label'>고객 정보</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("이름/닉네임", key="k_name")
        age = st.selectbox("연령대", ["10대","20대","30대","40대","50대","60대+"], key="k_age")
    with c2:
        gender = st.selectbox("성별", ["여성","남성","선택안함"], key="k_gender")
        region = st.selectbox("거주 지역", list(REGION_PM25.keys()), key="k_region")
    with c3:
        years = st.selectbox("거주 기간", list(RESIDENCE_YEARS.keys()), key="k_years")
        if mode == "skin":
            body = st.selectbox("촬영 부위", BODY_PARTS_SKIN, key="k_body")
        else:
            body = st.selectbox("촬영 부위", BODY_PARTS_SCALP, key="k_body")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 업로드 (v4.7 개선)
    label_mode = "피부" if mode == "skin" else "두피"
    st.markdown(f"<div class='glass-card'><div class='card-label'>{label_mode} 사진 업로드 (최대 3장)</div>", unsafe_allow_html=True)
    uploaded = None
    if usage_mode == "biz":
        st.markdown("<div class='sample-notice' style='margin-bottom:0.8rem;'>📱 <b>매장 촬영 안내</b><br>① 무선 현미경 앱으로 사진 촬영 → 갤러리 저장<br>② [갤러리에서 선택] 탭 → [Browse files] 클릭 → 사진 선택<br>③ 또는 [카메라로 촬영] 탭에서 태블릿 카메라로 직접 촬영</div>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📁 갤러리에서 선택 (무선 현미경 사진)", "📷 카메라로 직접 촬영"])
        with tab1:
            uploaded = st.file_uploader("JPG / PNG 파일 선택 (최대 3장)", type=["jpg","jpeg","png"],
                                        accept_multiple_files=True, key="k_upload")
        with tab2:
            cam_photo = st.camera_input("촬영 버튼을 눌러 사진을 찍으세요", key="k_camera")
            if cam_photo is not None:
                uploaded = [cam_photo] if not uploaded else list(uploaded) + [cam_photo]
    else:
        uploaded = st.file_uploader("JPG / PNG (최대 3장)", type=["jpg","jpeg","png"],
                                    accept_multiple_files=True, key="k_upload")
    if uploaded:
        cols = st.columns(min(len(uploaded[:3]), 3))
        for i, f in enumerate(uploaded[:3]):
            with cols[i]:
                st.image(f, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 분석 버튼
    if st.button("🔬 분석 시작", type="primary", use_container_width=True, key="k_analyze"):
        if not uploaded:
            st.error("❌ 사진을 1장 이상 업로드해주세요.")
        elif not name:
            st.error("❌ 이름/닉네임을 입력해주세요.")
        else:
            with st.spinner("AI 분석 중... (약 20-40초)"):
                try:
                    imgs = list(uploaded[:3])
                    if mode == "skin":
                        result = analyze_skin(imgs, {"age":age,"gender":gender,"body":body})
                    else:
                        result = analyze_scalp(imgs, {"age":age,"gender":gender,"body":body})
                    st.session_state["result"] = result
                    st.session_state["current_mode"] = mode
                    st.session_state["meta"] = {"name":name,"age":age,"gender":gender,
                                                "region":region,"years":years,"body":body}
                    st.session_state["scroll_pending"] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 분석 오류: {e}")
    
    # 결과 표시
    if "result" in st.session_state:
        st.markdown("<div id='ydlab-results-anchor'></div>", unsafe_allow_html=True)
        if st.session_state.pop("scroll_pending", False):
            scroll_to_results()
        st.success("✅ 분석 완료! 위로 스크롤하면 분석 모드 선택 화면도 그대로 있습니다.")
        
        # 사업용: 상단 "다음 고객" 버튼
        if usage_mode == "biz":
            col_a, col_b, col_c = st.columns([1,2,1])
            with col_b:
                if st.button("🔄 다음 고객 (초기화)", type="primary", use_container_width=True, key="k_next_customer_top"):
                    preserve_keys = {"authed", "usage_mode"}
                    for k in list(st.session_state.keys()):
                        if k not in preserve_keys:
                            del st.session_state[k]
                    st.rerun()
            st.markdown("---")
        
        cm = st.session_state.get("current_mode", "skin")
        result = st.session_state["result"]
        meta = st.session_state["meta"]
        air = fetch_air(meta["region"])
        uv = fetch_kma_uv(meta["region"])
        humidity = fetch_kma_humidity(meta["region"])
        air["uv"] = uv
        air["humidity"] = humidity
        
        if cm == "skin":
            show_skin_result(result, meta, air, usage_mode)
        else:
            show_scalp_result(result, meta, air, usage_mode)
        
        # 사업용: 하단 "다음 고객" 버튼
        if usage_mode == "biz":
            st.markdown("---")
            col_a, col_b, col_c = st.columns([1,2,1])
            with col_b:
                if st.button("🔄 다음 고객 (초기화)", type="primary", use_container_width=True, key="k_next_customer_bottom"):
                    preserve_keys = {"authed", "usage_mode"}
                    for k in list(st.session_state.keys()):
                        if k not in preserve_keys:
                            del st.session_state[k]
                    st.rerun()

if __name__ == "__main__":
    main()
