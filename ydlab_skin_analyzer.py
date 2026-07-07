# -*- coding: utf-8 -*-
"""
YD Lab 사업용(유형 매칭) 확장 모듈
──────────────────────────────────────────────
기존 ydlab_skin_analyzer.py(v4.5)를 건드리지 않고 "사업용 10종 완제품 매칭" 기능을
얹기 위한 별도 모듈입니다. 통합 방법은 파일 맨 아래 "통합 가이드" 주석 참조.

설계 원칙
1) 진단 엔진(analyze_skin/analyze_scalp)은 그대로 재사용 — 추가 AI 호출 없음.
2) 사업용 매칭은 20종 혼합(생성) 없이 "10종 중 1개 완제품"만 고르는 결정론적 로직.
3) CEEI/SEEI 환경등급이 높아도 완제품 배합은 절대 바꾸지 않음(=혼합 행위 없음).
   대신 "부스터 앰플 별도 사용 권장" 안내 문구로만 처리(레이어링, 조제 아님).
4) 교육용/사업용 구분은 화면 버튼이 아니라 "접속 코드"로 고정 — 매장 손님에게
   실습용 옵션이 노출되지 않도록 함.
"""

# ── 사업용 10종 완제품 유형 DB (기존 SKIN_INGREDIENT_LIST/SCALP_INGREDIENT_LIST 성분만 사용) ──
SKIN_PRODUCT_TYPES = {
    "P-SK01": {"name": "건성-보습중점형", "skin_type": "건성",
               "ingredients": ["히알루론산", "글리세린", "피토스핑고신"],
               "desc": "고보습 라인 — 극건성·당김 완화 집중"},
    "P-SK02": {"name": "건성-노화케어형", "skin_type": "건성",
               "ingredients": ["레티닐팔미테이트", "펩타이드", "히알루론산"],
               "desc": "주름·탄력 집중 케어 (야간 사용 권장)"},
    "P-SK03": {"name": "지성-피지모공형", "skin_type": "지성",
               "ingredients": ["살리실산", "나이아신아마이드"],
               "desc": "피지·모공 케어, 산뜻한 제형"},
    "P-SK04": {"name": "지성-톤개선형", "skin_type": "지성",
               "ingredients": ["아스코빌글루코사이드", "나이아신아마이드"],
               "desc": "칙칙함·색소침착 케어, 산뜻한 제형"},
    "P-SK05": {"name": "복합성-밸런스형", "skin_type": "복합성"},
    "P-SK06": {"name": "민감성-장벽강화형", "skin_type": "민감성",
               "ingredients": ["판테놀", "알란토인", "피토스핑고신"],
               "desc": "저자극 장벽 강화, 진정 집중"},
}
# P-SK05는 아래에서 dict.update로 채웁니다(라인 길이 정리용)
SKIN_PRODUCT_TYPES["P-SK05"].update({
    "ingredients": ["판테놀", "히알루론산", "나이아신아마이드"],
    "desc": "T존·U존 밸런스 케어 (복합성·중성 공용)",
})

SCALP_PRODUCT_TYPES = {
    "P-SC01": {"name": "건성두피-각질케어형", "scalp_type": "건성",
               "ingredients": ["판테놀", "피토스핑고신", "소듐PCA"],
               "desc": "각질·가려움 완화, 수분 공급"},
    "P-SC02": {"name": "지성두피-피지모공케어형", "scalp_type": "지성",
               "ingredients": ["살리실산", "티트리오일"],
               "desc": "피지·모공 관리, 청량 제형"},
    "P-SC03": {"name": "얇은모발-볼륨케어형", "scalp_type": None,
               "ingredients": ["바이오틴", "아데노신", "로즈마리오일"],
               "desc": "모발 굵기·볼륨감 집중 케어"},
    "P-SC04": {"name": "민감두피-저자극진정형", "scalp_type": "민감성",
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
    else:  # 복합성, 중성 등
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
        code = "P-SC03"          # 모발굵기가 가장 취약한 축이면 볼륨케어 우선
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
    import streamlit as st
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


# ══════════════════════════════════════════════════════════════════════
# 통합 가이드 (ydlab_skin_analyzer.py 수정 지점 3곳)
# ══════════════════════════════════════════════════════════════════════
"""
[1] 파일 상단 import 부분에 추가:
    from ydlab_business_mode import (
        match_skin_product, match_scalp_product, show_product_match_card,
    )

[2] secrets.toml에 기존 ACCESS_PASSWORD 대신(또는 함께) 아래 추가:
    EDU_ACCESS_CODES = ["YDLAB_EDU_2026"]   # 대학 실습실용
    BIZ_ACCESS_CODES = ["YDLAB_BIZ_2026"]  # 파트너 매장용

[3] main() 함수의 인증 부분을 아래처럼 교체 (valid_codes 만들던 두 줄 대체):

    edu_codes = st.secrets.get("EDU_ACCESS_CODES",
                [st.secrets.get("ACCESS_PASSWORD", "YDLAB2025")])
    biz_codes = st.secrets.get("BIZ_ACCESS_CODES", [])
    if isinstance(edu_codes, str): edu_codes = [edu_codes]
    if isinstance(biz_codes, str): biz_codes = [biz_codes]
    valid_codes = edu_codes + biz_codes

    if "authed" not in st.session_state: st.session_state["authed"] = False
    if not st.session_state["authed"]:
        url_code = st.query_params.get("code", "")
        if url_code and url_code in valid_codes:
            st.session_state["authed"] = True
            st.session_state["usage_mode"] = (
                "biz" if url_code in biz_codes else "edu")
    if not st.session_state["authed"]:
        ... (기존 안내 문구 동일)
        if st.button("분석 시작하기", ...):
            entered = gate_pw.upper()
            if entered in [c.upper() for c in edu_codes]:
                st.session_state["authed"] = True
                st.session_state["usage_mode"] = "edu"; st.rerun()
            elif entered in [c.upper() for c in biz_codes]:
                st.session_state["authed"] = True
                st.session_state["usage_mode"] = "biz"; st.rerun()
            else:
                st.error("유효하지 않은 코드입니다.")
        st.stop()

    # usage_mode 기본값 보장 (구버전 세션 대비)
    usage_mode = st.session_state.get("usage_mode", "edu")

[4] show_skin_result() 함수 안, "우선 개선 항목" glass-card를 그린 직후
    (st.markdown("</div>", unsafe_allow_html=True) 다음, st.markdown("---") 이전)에 추가:

    usage_mode = st.session_state.get("usage_mode", "edu")
    if usage_mode == "biz":
        product = match_skin_product(result, ceei_grade)
        show_product_match_card(product, "CEEI", ceei_grade, is_scalp=False)
        return   # 교육용 전용인 혼합가이드·공방주문서는 사업용에서 건너뜀

    # ↓ 이 아래 기존 코드(vol_selector, mixing card, 리포트/주문서 다운로드)는 그대로 둡니다.

[5] show_scalp_result()도 동일하게, "우선 개선 항목 (두피)" 카드 직후에:

    usage_mode = st.session_state.get("usage_mode", "edu")
    if usage_mode == "biz":
        product = match_scalp_product(result, seei_grade)
        show_product_match_card(product, "SEEI", seei_grade, is_scalp=True)
        return

    # ↓ 기존 두피 혼합가이드·공방주문서 코드는 그대로 둡니다.

이렇게 하면:
- 교육용 코드로 접속 → 지금과 완전히 동일한 20종 혼합가이드 + 공방주문서 흐름
- 사업용 코드로 접속 → 같은 진단 엔진을 쓰되, 10종 중 매칭된 완제품 1개만 카드로 안내
  (혼합가이드·공방주문서 UI 자체가 아예 렌더링되지 않음 → 매장 손님에게 혼동 없음)
- CSV/Sheets 저장(save_record)에 usage_mode 필드 하나만 추가하면, 나중에
  교육용/사업용 이용 현황과 매장별 유형 매칭 분포까지 그대로 집계 가능합니다.
"""
