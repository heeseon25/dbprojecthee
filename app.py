import os
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="노후준비교육은 실제 수요를 반영하고 있는가?",
    page_icon="📊",
    layout="wide",
)

DB_PATH = "pension_education.db"


# =========================================================
# 디자인
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background: #f5f7fb;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1320px;
}

.hero {
    background: linear-gradient(135deg, #243b63 0%, #4e6e9d 62%, #b7c7dd 100%);
    color: white;
    padding: 36px 40px;
    border-radius: 28px;
    box-shadow: 0 16px 40px rgba(36, 59, 99, 0.18);
    margin-bottom: 24px;
}

.hero h1 {
    font-size: 34px;
    font-weight: 800;
    margin-bottom: 10px;
    letter-spacing: -0.8px;
}

.hero p {
    font-size: 16px;
    line-height: 1.75;
    opacity: 0.94;
    max-width: 1000px;
}

.card {
    background: white;
    border: 1px solid #e6ebf2;
    border-radius: 24px;
    padding: 22px 24px;
    box-shadow: 0 10px 28px rgba(36, 59, 99, 0.07);
    margin-bottom: 18px;
}

.card-title {
    font-size: 21px;
    font-weight: 800;
    color: #253755;
    margin-bottom: 6px;
}

.card-sub {
    color: #6b778c;
    font-size: 14.5px;
    line-height: 1.6;
    margin-bottom: 10px;
}

.question-box {
    background: #eef4fb;
    border-left: 6px solid #4e6e9d;
    color: #2d3b50;
    padding: 16px 18px;
    border-radius: 16px;
    line-height: 1.65;
    margin-bottom: 18px;
}

.insight {
    background: #fff8df;
    border: 1px solid #f0dea9;
    border-left: 6px solid #d6a22a;
    color: #3e392a;
    padding: 16px 18px;
    border-radius: 16px;
    font-size: 14.5px;
    line-height: 1.7;
    margin-top: 10px;
}

.result {
    background: #eef8f4;
    border: 1px solid #cbe9dc;
    border-left: 6px solid #58a882;
    color: #263d34;
    padding: 16px 18px;
    border-radius: 16px;
    font-size: 14.5px;
    line-height: 1.7;
    margin-top: 10px;
}

.type-card {
    background: #ffffff;
    border-radius: 18px;
    border: 1px solid #e6ebf2;
    box-shadow: 0 8px 20px rgba(36, 59, 99, 0.06);
    padding: 16px 17px;
    min-height: 132px;
}

.type-card b {
    display: block;
    color: #253755;
    font-size: 16px;
    margin-bottom: 8px;
}

.type-card span {
    color: #68778d;
    font-size: 13.5px;
    line-height: 1.6;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e6ebf2;
    border-radius: 20px;
    padding: 18px 18px;
    box-shadow: 0 8px 22px rgba(36, 59, 99, 0.06);
}

div[data-testid="stMetricValue"] {
    color: #253755;
    font-weight: 800;
    font-size: 25px;
}

div[data-testid="stMetricLabel"] {
    color: #68778d;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background: rgba(255,255,255,0.7);
    padding: 8px;
    border-radius: 18px;
}

.stTabs [data-baseweb="tab"] {
    background: white;
    border-radius: 14px;
    padding: 10px 18px;
    border: 1px solid #e6ebf2;
}

.stTabs [aria-selected="true"] {
    background: #253755 !important;
    color: white !important;
    border: 1px solid #253755;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# DB 함수
# =========================================================
@st.cache_data(show_spinner=False)
def load_data(query: str) -> pd.DataFrame:
    if not os.path.exists(DB_PATH):
        st.error(f"`{DB_PATH}` 파일을 찾을 수 없습니다. app.py와 같은 폴더에 DB 파일을 넣어 주세요.")
        st.stop()

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def show_sql(sql: str, label="사용한 SQL 보기"):
    with st.expander(label):
        st.code(sql.strip(), language="sql")


def make_numeric(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def short_region(name):
    return str(name).replace("지역본부", "").strip()


def plot_style(fig, height=430, legend=True):
    fig.update_layout(
        height=height,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.6)",
        margin=dict(l=20, r=20, t=55, b=25),
        font=dict(family="Noto Sans KR, sans-serif", size=13, color="#2d3648"),
        title=dict(font=dict(size=19, color="#253755")),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(120,130,150,0.16)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(120,130,150,0.16)", zeroline=False)
    return fig


# =========================================================
# 데이터 로드
# =========================================================
sql_main = """
SELECT *
FROM education_pension;
"""

df = load_data(sql_main)

num_cols = ["교육횟수", "교육참여인원", "노령연금수급자수", "노령연금금액"]
df = make_numeric(df, num_cols)

df["지역본부_표시"] = df["지역본부"].apply(short_region)
df["교육효율성"] = (df["교육참여인원"] / df["교육횟수"]).replace([float("inf"), -float("inf")], 0).fillna(0)
df["수급자1천명당교육참여"] = (df["교육참여인원"] / df["노령연금수급자수"] * 1000).replace([float("inf"), -float("inf")], 0).fillna(0)


# 유형화
avg_part = df["교육참여인원"].mean()
avg_rec = df["노령연금수급자수"].mean()


def classify(row):
    if row["교육참여인원"] >= avg_part and row["노령연금수급자수"] >= avg_rec:
        return "핵심관리형"
    elif row["교육참여인원"] >= avg_part and row["노령연금수급자수"] < avg_rec:
        return "교육집중형"
    elif row["교육참여인원"] < avg_part and row["노령연금수급자수"] >= avg_rec:
        return "확대필요형"
    else:
        return "저수요형"


df["지역유형"] = df.apply(classify, axis=1)


# =========================================================
# 헤더
# =========================================================
st.markdown("""
<div class="hero">
    <h1>노후준비교육은 실제 노후준비 수요를 반영하고 있는가?</h1>
    <p>
    국민연금공단의 지역본부별 노후준비교육 현황과 지역별 노령연금 수급 데이터를 결합하여,
    교육이 활발한 지역이 실제 노후준비 수요가 높은 지역과 일치하는지 분석합니다.
    나아가 교육만으로 해결하기 어려운 개인별 노후설계의 필요성을 확인하고,
    부가 서비스로서 플코(PLCO)의 활용 가능성을 제안합니다.
    </p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# KPI
# =========================================================
total_edu = int(df["교육횟수"].sum())
total_part = int(df["교육참여인원"].sum())
total_rec = int(df["노령연금수급자수"].sum())
top_eff = df.sort_values("교육효율성", ascending=False).iloc[0]["지역본부_표시"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("총 교육횟수", f"{total_edu:,.0f}회")
c2.metric("총 교육참여인원", f"{total_part:,.0f}명")
c3.metric("총 노령연금 수급자", f"{total_rec:,.0f}명")
c4.metric("교육 효율성 최상위", top_eff)


tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "01 문제제기",
    "02 데이터와 DB",
    "03 분석 결과",
    "04 지역 유형화",
    "05 결론과 플코",
])


# =========================================================
# 01 문제제기
# =========================================================
with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">01. 문제제기</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="question-box">
<b>노후준비교육은 정말 필요한 지역에 제공되고 있을까?</b><br><br>
한국은 빠르게 고령화되고 있으며, 개인의 노후준비 역량은 점점 더 중요해지고 있습니다.
국민연금공단은 노후준비교육을 통해 국민들의 노후설계를 지원하고 있지만,
교육이 많이 이루어지는 지역이 실제 노후준비 수요가 높은 지역과 일치하는지는 확인이 필요합니다.
</div>
""", unsafe_allow_html=True)

    q1, q2, q3 = st.columns(3)
    q1.info("Q1. 어느 지역에서 노후준비교육이 가장 활발한가?")
    q2.info("Q2. 어느 지역에서 노령연금 수급 규모가 큰가?")
    q3.info("Q3. 교육 참여 수준과 노후준비 수요는 일치하는가?")

    st.markdown("""
<div class="insight">
<b>분석 관점</b><br>
이 프로젝트는 단순히 교육 현황을 보여주는 것이 아니라,
<b>교육 공급(교육횟수·참여인원)</b>과 <b>노후준비 수요(노령연금 수급자 규모)</b>를 함께 비교하여
지역별 차이와 의사결정 포인트를 찾는 것을 목표로 합니다.
</div>
""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 02 데이터와 DB
# =========================================================
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">02. 데이터 선택 및 데이터베이스 구축</div>', unsafe_allow_html=True)

    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown("""
<div class="type-card">
<b>데이터 1: 노후준비교육 현황</b>
<span>국민연금공단 지역본부별 노후준비교육 현황<br>
사용 변수: 지역본부, 교육횟수, 교육참여인원</span>
</div>
""", unsafe_allow_html=True)
    with d2:
        st.markdown("""
<div class="type-card">
<b>데이터 2: 연금 수급 현황</b>
<span>지역별 연금종별 수급자 현황<br>
사용 변수: 법정동시도, 시군구, 노령연금수급자수, 노령연금금액</span>
</div>
""", unsafe_allow_html=True)
    with d3:
        st.markdown("""
<div class="type-card">
<b>데이터 3: 지역 매핑 테이블</b>
<span>시도·시군구 단위 데이터를 지역본부 기준으로 통합하기 위해 직접 구축한 매핑 테이블</span>
</div>
""", unsafe_allow_html=True)

    st.markdown("### DB 통합 구조")
    st.code("""
education
    지역본부, 교육횟수, 교육참여인원

pension_region
    법정동시도, 법정동시군_일부통합, 노령연금수급자수, 노령연금금액

region_mapping
    sido, sigungu, region_hq

education_pension VIEW
    education + pension_region + region_mapping JOIN 결과
""", language="text")

    show_sql(sql_main, "메인 VIEW 조회 SQL 보기")

    with st.expander("education_pension 데이터 보기"):
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 03 분석 결과
# =========================================================
with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">03. 분석 결과: 교육이 많으면 참여도 높을까?</div>', unsafe_allow_html=True)

    sql_edu = """
    SELECT
        지역본부,
        교육횟수,
        교육참여인원
    FROM education_pension
    ORDER BY 교육횟수 DESC;
    """

    sql_eff = """
    SELECT
        지역본부,
        교육횟수,
        교육참여인원,
        ROUND(교육참여인원 * 1.0 / 교육횟수, 2) AS 교육효율성
    FROM education_pension
    ORDER BY 교육효율성 DESC;
    """

    df_edu = load_data(sql_edu)
    df_eff = load_data(sql_eff)

    df_edu = make_numeric(df_edu, ["교육횟수", "교육참여인원"])
    df_eff = make_numeric(df_eff, ["교육횟수", "교육참여인원", "교육효율성"])

    df_edu["지역본부_표시"] = df_edu["지역본부"].apply(short_region)
    df_eff["지역본부_표시"] = df_eff["지역본부"].apply(short_region)

    left, right = st.columns(2)

    with left:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=df_edu["지역본부_표시"], y=df_edu["교육횟수"], name="교육횟수"))
        fig1.add_trace(go.Scatter(x=df_edu["지역본부_표시"], y=df_edu["교육참여인원"], name="교육참여인원", mode="lines+markers", yaxis="y2"))
        fig1.update_layout(
            title="교육횟수와 교육참여인원 비교",
            yaxis=dict(title="교육횟수"),
            yaxis2=dict(title="교육참여인원", overlaying="y", side="right"),
            legend=dict(orientation="h"),
        )
        fig1 = plot_style(fig1, height=470)
        st.plotly_chart(fig1, use_container_width=True)
        show_sql(sql_edu, "차트 1 SQL 보기")

    with right:
        fig2 = px.bar(
            df_eff.sort_values("교육효율성", ascending=True),
            x="교육효율성",
            y="지역본부_표시",
            orientation="h",
            text="교육효율성",
            color="교육효율성",
            color_continuous_scale="Teal",
            title="교육 1회당 평균 참여인원",
        )
        fig2.update_traces(texttemplate="%{text:.1f}명", textposition="outside", cliponaxis=False)
        fig2.update_layout(coloraxis_showscale=False)
        fig2 = plot_style(fig2, height=470, legend=False)
        st.plotly_chart(fig2, use_container_width=True)
        show_sql(sql_eff, "차트 2 SQL 보기")

    st.markdown("""
<div class="result">
<b>발견 1</b><br>
교육횟수가 많다고 반드시 교육참여인원이 가장 높은 것은 아니었습니다.
예를 들어 서울북부지역본부는 교육횟수가 가장 많지만 참여인원은 최상위가 아니고,
광주지역본부는 교육횟수는 중간 수준이지만 참여인원이 가장 높게 나타납니다.
</div>
""", unsafe_allow_html=True)

    st.markdown("### 교육 참여 수준과 노령연금 수급 규모의 관계")

    sql_scatter = """
    SELECT
        지역본부,
        교육참여인원,
        노령연금수급자수
    FROM education_pension;
    """

    df_scatter = load_data(sql_scatter)
    df_scatter = make_numeric(df_scatter, ["교육참여인원", "노령연금수급자수"])
    df_scatter["지역본부_표시"] = df_scatter["지역본부"].apply(short_region)

    fig3 = px.scatter(
        df_scatter,
        x="노령연금수급자수",
        y="교육참여인원",
        size="교육참여인원",
        color="지역본부_표시",
        text="지역본부_표시",
        title="노령연금 수급자 수와 교육 참여 인원의 관계",
        labels={"노령연금수급자수": "노령연금 수급자 수", "교육참여인원": "교육 참여 인원", "지역본부_표시": "지역본부"},
    )
    fig3.update_traces(textposition="top center", marker=dict(opacity=0.85, line=dict(width=1, color="white")))
    fig3 = plot_style(fig3, height=520, legend=False)
    st.plotly_chart(fig3, use_container_width=True)
    show_sql(sql_scatter, "차트 3 SQL 보기")

    st.markdown("""
<div class="insight">
<b>인사이트</b><br>
노후준비교육은 지역별 수급 규모와 완전히 일치하지 않았습니다.
이는 교육이 단순히 수급자 규모에 따라 자동적으로 운영되는 것이 아니라,
지역별 접근성, 운영 방식, 홍보 수준 등 다른 요인의 영향을 받을 가능성을 보여줍니다.
</div>
""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 04 지역 유형화
# =========================================================
with tab4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">04. 데이터 기반 지역 유형화</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-sub">교육 참여 수준과 노령연금 수급자 규모를 기준으로 지역본부를 네 가지 유형으로 분류했습니다.</div>', unsafe_allow_html=True)

    sql_type = """
    SELECT
        지역본부,
        교육참여인원,
        노령연금수급자수,
        CASE
            WHEN 교육참여인원 >= (SELECT AVG(교육참여인원) FROM education_pension)
             AND 노령연금수급자수 >= (SELECT AVG(노령연금수급자수) FROM education_pension)
            THEN '핵심관리형'

            WHEN 교육참여인원 >= (SELECT AVG(교육참여인원) FROM education_pension)
             AND 노령연금수급자수 < (SELECT AVG(노령연금수급자수) FROM education_pension)
            THEN '교육집중형'

            WHEN 교육참여인원 < (SELECT AVG(교육참여인원) FROM education_pension)
             AND 노령연금수급자수 >= (SELECT AVG(노령연금수급자수) FROM education_pension)
            THEN '확대필요형'

            ELSE '저수요형'
        END AS 지역유형
    FROM education_pension;
    """

    fig4 = px.scatter(
        df,
        x="노령연금수급자수",
        y="교육참여인원",
        color="지역유형",
        size="수급자1천명당교육참여",
        text="지역본부_표시",
        title="노후준비교육 참여 수준과 노령연금 수급 규모에 따른 지역 유형화",
        labels={"노령연금수급자수": "노령연금 수급자 수", "교육참여인원": "교육 참여 인원", "지역유형": "지역 유형"},
    )

    fig4.add_vline(x=avg_rec, line_dash="dash", line_color="gray")
    fig4.add_hline(y=avg_part, line_dash="dash", line_color="gray")
    fig4.update_traces(textposition="top center", marker=dict(opacity=0.85, line=dict(width=1, color="white")))
    fig4 = plot_style(fig4, height=620)
    st.plotly_chart(fig4, use_container_width=True)
    show_sql(sql_type, "지역 유형화 SQL 보기")

    t1, t2, t3, t4 = st.columns(4)
    t1.markdown('<div class="type-card"><b>핵심관리형</b><span>수급 규모와 교육 참여가 모두 높은 지역. 현재 운영을 유지하며 우수사례로 활용 가능.</span></div>', unsafe_allow_html=True)
    t2.markdown('<div class="type-card"><b>교육집중형</b><span>수급 규모에 비해 교육 참여가 높은 지역. 교육 방식의 강점을 확인할 필요.</span></div>', unsafe_allow_html=True)
    t3.markdown('<div class="type-card"><b>확대필요형</b><span>수급 규모는 크지만 교육 참여가 낮은 지역. 향후 교육 확대 우선 후보.</span></div>', unsafe_allow_html=True)
    t4.markdown('<div class="type-card"><b>저수요형</b><span>수급 규모와 교육 참여가 모두 낮은 지역. 지역 특성과 잠재 수요 확인 필요.</span></div>', unsafe_allow_html=True)

    st.markdown("""
<div class="result">
<b>발견 2</b><br>
지역을 유형화하면 단순 순위에서는 보이지 않던 차이가 드러납니다.
같은 교육 프로그램이라도 지역별로 참여 수준과 수급 규모가 다르게 나타나므로,
노후준비교육은 모든 지역에 동일하게 운영하기보다 지역 특성을 반영한 차별화 전략이 필요합니다.
</div>
""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 05 결론과 플코
# =========================================================
with tab5:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">05. 결론: 교육만으로 충분할까?</div>', unsafe_allow_html=True)

    st.markdown("""
<div class="question-box">
<b>분석 결론</b><br><br>
노후준비교육 현황과 노령연금 수급 현황을 결합해 분석한 결과,
교육횟수와 참여인원, 그리고 수급 규모는 지역별로 서로 다른 양상을 보였습니다.
즉, 교육을 많이 운영한다고 반드시 참여가 높은 것도 아니며,
수급 규모가 큰 지역에서 항상 교육 참여가 높은 것도 아니었습니다.
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="insight">
<b>핵심 인사이트</b><br>
노후준비교육은 단순히 교육 횟수를 늘리는 방식만으로는 충분하지 않습니다.
지역별 수요와 참여 수준을 고려한 교육 운영 전략이 필요하며,
동시에 개인마다 다른 소득, 저축액, 연금 상황을 반영한 맞춤형 노후설계 지원이 필요합니다.
</div>
""", unsafe_allow_html=True)

    st.markdown("### 플코(PLCO) 부가서비스 제안")

    p1, p2, p3 = st.columns(3)
    p1.success("1. 개인 정보 입력\n\n나이, 소득, 현재 자산, 월 저축액")
    p2.info("2. 미래 자산 시뮬레이션\n\n예상 연금과 미래 생활비를 함께 계산")
    p3.warning("3. 맞춤형 노후준비 전략\n\n부족 구간과 필요한 자산 성장률 제시")

    st.markdown("""
<div class="result">
<b>플코 연결</b><br>
지역 단위 분석은 교육 서비스의 배분 문제를 보여주지만,
개인의 실제 노후준비 수준은 개인별 소득과 자산 상황에 따라 달라집니다.
따라서 본 프로젝트는 분석 결과를 바탕으로,
개인이 자신의 미래 재무 상태를 직접 확인할 수 있는
데이터 기반 노후 재무 시뮬레이션 서비스 <b>플코(PLCO)</b>를 부가 기능으로 제안합니다.
</div>
""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


st.caption("경영정보처리론 데이터 분석 및 시각화 프로젝트 | SQLite + Streamlit + Plotly")
