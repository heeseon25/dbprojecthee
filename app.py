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
    page_title="노후준비교육의 공급과 수요는 일치하는가?",
    page_icon="🐥",
    layout="wide",
)

DB_PATH = "pension_education.db"


# =========================================================
# 디자인: 병아리/버터 옐로우 테마
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #FFFDF4 0%, #FFF7D6 44%, #FFFDF8 100%);
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1320px;
}

.hero {
    background: linear-gradient(135deg, #FFE27A 0%, #F6C453 48%, #E8A317 100%);
    color: #3B2E00;
    padding: 36px 40px;
    border-radius: 30px;
    box-shadow: 0 18px 42px rgba(232, 163, 23, 0.22);
    margin-bottom: 24px;
    border: 1px solid rgba(255, 224, 120, 0.95);
}

.hero h1 {
    font-size: 35px;
    font-weight: 800;
    margin-bottom: 10px;
    letter-spacing: -0.8px;
}

.hero p {
    font-size: 16px;
    line-height: 1.75;
    opacity: 0.94;
    max-width: 1060px;
}

.card {
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid #F5E5B7;
    border-radius: 25px;
    padding: 24px 26px;
    box-shadow: 0 10px 30px rgba(191, 139, 22, 0.08);
    margin-bottom: 18px;
}

.card-title {
    font-size: 22px;
    font-weight: 800;
    color: #4A3710;
    margin-bottom: 8px;
    letter-spacing: -0.3px;
}

.card-sub {
    color: #74613A;
    font-size: 14.5px;
    line-height: 1.6;
    margin-bottom: 10px;
}

.question-box {
    background: #FFF6D8;
    border-left: 6px solid #F6C453;
    color: #4B3A12;
    padding: 16px 18px;
    border-radius: 17px;
    line-height: 1.7;
    margin-bottom: 18px;
    border-top: 1px solid #F5E5B7;
    border-right: 1px solid #F5E5B7;
    border-bottom: 1px solid #F5E5B7;
}

.insight {
    background: #FFF9E8;
    border: 1px solid #F0D98B;
    border-left: 6px solid #E8A317;
    color: #3E3215;
    padding: 16px 18px;
    border-radius: 17px;
    font-size: 14.5px;
    line-height: 1.75;
    margin-top: 12px;
}

.result {
    background: #FFFDF5;
    border: 1px solid #EFDCA6;
    border-left: 6px solid #C58A00;
    color: #3D3218;
    padding: 16px 18px;
    border-radius: 17px;
    font-size: 14.5px;
    line-height: 1.75;
    margin-top: 12px;
}

.type-card {
    background: #FFFFFF;
    border-radius: 18px;
    border: 1px solid #F0E1B8;
    box-shadow: 0 8px 20px rgba(191, 139, 22, 0.07);
    padding: 16px 17px;
    min-height: 136px;
}

.type-card b {
    display: block;
    color: #4A3710;
    font-size: 16px;
    margin-bottom: 8px;
}

.type-card span {
    color: #6F5D3B;
    font-size: 13.5px;
    line-height: 1.6;
}

div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid #F0E1B8;
    border-radius: 20px;
    padding: 18px 18px;
    box-shadow: 0 8px 22px rgba(191, 139, 22, 0.07);
}

div[data-testid="stMetricValue"] {
    color: #4A3710;
    font-weight: 800;
    font-size: 25px;
}

div[data-testid="stMetricLabel"] {
    color: #806B40;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background: rgba(255, 248, 220, 0.95);
    padding: 8px;
    border-radius: 18px;
    border: 1px solid #F3E4B7;
}

.stTabs [data-baseweb="tab"] {
    background: #FFFFFF;
    color: #5A4515;
    border-radius: 14px;
    padding: 10px 18px;
    border: 1px solid #F0E1B8;
}

.stTabs [aria-selected="true"] {
    background: #F6C453 !important;
    color: #3B2E00 !important;
    border: 1px solid #E8A317 !important;
    font-weight: 800;
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
        plot_bgcolor="rgba(255,255,255,0.72)",
        margin=dict(l=20, r=20, t=55, b=25),
        font=dict(family="Noto Sans KR, sans-serif", size=13, color="#3D3218"),
        title=dict(font=dict(size=19, color="#4A3710")),
        showlegend=legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.75)",
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(194, 148, 36, 0.16)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(194, 148, 36, 0.16)", zeroline=False)
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


# 주요값 자동 추출
top_eff_row = df.sort_values("교육효율성", ascending=False).iloc[0]
top_part_row = df.sort_values("교육참여인원", ascending=False).iloc[0]
top_count_row = df.sort_values("교육횟수", ascending=False).iloc[0]
top_rec_row = df.sort_values("노령연금수급자수", ascending=False).iloc[0]


# =========================================================
# 헤더
# =========================================================
st.markdown("""
<div class="hero">
    <h1>노후준비교육의 공급과 수요는 일치하는가?</h1>
    <p>
    국민연금공단의 지역본부별 노후준비교육 현황과 지역별 노령연금 수급 데이터를 결합하여,
    교육이 활발한 지역이 실제 노후준비 수요가 높은 지역과 일치하는지 분석합니다.
    나아가 교육 공급량과 교육 참여 수준 사이의 차이를 통해,
    향후 개인 맞춤형 노후 재무 시뮬레이션 서비스의 필요성을 제안합니다.
    </p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# KPI
# =========================================================
total_edu = int(df["교육횟수"].sum())
total_part = int(df["교육참여인원"].sum())
total_rec = int(df["노령연금수급자수"].sum())
top_eff = top_eff_row["지역본부_표시"]

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
    "05 결론 및 서비스 제안",
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
고령화가 빠르게 진행되면서 개인의 노후준비 역량은 점점 더 중요해지고 있습니다.
국민연금공단은 노후준비교육을 통해 국민들의 노후설계를 지원하고 있지만,
교육이 많이 이루어지는 지역이 실제 노후준비 수요가 높은 지역과 일치하는지는 별도의 데이터 분석이 필요합니다.
</div>
""", unsafe_allow_html=True)

    q1, q2, q3 = st.columns(3)
    q1.info("Q1. 어느 지역에서 노후준비교육이 가장 활발한가?")
    q2.info("Q2. 교육을 많이 운영하면 실제 참여도 높아지는가?")
    q3.info("Q3. 교육 참여 수준과 노후준비 수요는 일치하는가?")

    st.markdown("""
<div class="insight">
<b>분석 관점</b><br>
본 프로젝트는 단순히 교육 현황을 나열하는 것이 아니라,
<b>교육 공급(교육횟수)</b>, <b>교육 성과(교육참여인원)</b>, <b>노후준비 수요(노령연금 수급자 규모)</b>를 함께 비교합니다.
이를 통해 교육 공급량이 실제 참여로 이어지는지, 그리고 수요가 큰 지역에서 교육 참여도 충분한지를 검토합니다.
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

    st.markdown("""
<div class="insight">
<b>데이터 통합 의의</b><br>
교육 데이터는 지역본부 단위이고, 연금 수급 데이터는 시도·시군구 단위이기 때문에 두 데이터를 바로 비교할 수 없습니다.
따라서 지역 매핑 테이블을 별도로 구축하여 연금 데이터를 지역본부 기준으로 변환했고,
이를 통해 교육 공급과 노후준비 수요를 같은 기준에서 비교할 수 있도록 설계했습니다.
</div>
""", unsafe_allow_html=True)

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
    st.markdown("""
<div class="question-box">
<b>질문</b><br>
일반적으로 교육을 많이 운영하는 지역일수록 참여자도 많을 것이라고 예상할 수 있습니다.
실제로도 교육횟수와 참여인원은 같은 방향으로 움직일까요?
</div>
""", unsafe_allow_html=True)

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
        fig1.add_trace(go.Bar(
            x=df_edu["지역본부_표시"],
            y=df_edu["교육횟수"],
            name="교육횟수",
            marker_color="#F6C453",
        ))
        fig1.add_trace(go.Scatter(
            x=df_edu["지역본부_표시"],
            y=df_edu["교육참여인원"],
            name="교육참여인원",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color="#8B5E00", width=3),
            marker=dict(size=9, color="#8B5E00"),
        ))
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
            color_continuous_scale="YlOrBr",
            title="교육 1회당 평균 참여인원",
        )
        fig2.update_traces(texttemplate="%{text:.1f}명", textposition="outside", cliponaxis=False)
        fig2.update_layout(coloraxis_showscale=False)
        fig2 = plot_style(fig2, height=470, legend=False)
        st.plotly_chart(fig2, use_container_width=True)
        show_sql(sql_eff, "차트 2 SQL 보기")

    st.markdown(f"""
<div class="result">
<b>결과</b><br>
교육횟수가 가장 많은 지역은 <b>{top_count_row['지역본부_표시']}지역본부</b>였지만,
교육참여인원이 가장 높은 지역은 <b>{top_part_row['지역본부_표시']}지역본부</b>였습니다.
또한 교육 1회당 평균 참여인원을 보면 <b>{top_eff_row['지역본부_표시']}지역본부</b>의 교육 효율성이 가장 높게 나타났습니다.
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="insight">
<b>인사이트</b><br>
분석 결과, 교육횟수가 가장 많은 지역이 반드시 가장 많은 참여자를 확보하지는 못했습니다.
이는 노후준비교육의 성과가 단순한 공급량보다 교육 접근성, 홍보 전략, 교육 내용의 적합성 등 질적 요소에 의해 결정될 수 있음을 보여줍니다.
따라서 노후준비교육의 효과를 높이기 위해서는 교육 횟수를 늘리는 것뿐 아니라,
실제 참여를 유도하는 운영 전략과 지역별 맞춤형 홍보 방식이 함께 고려되어야 합니다.
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
        labels={
            "노령연금수급자수": "노령연금 수급자 수",
            "교육참여인원": "교육 참여 인원",
            "지역본부_표시": "지역본부",
        },
        color_discrete_sequence=["#E8A317", "#F6C453", "#C58A00", "#FFD86B", "#A96F00", "#FAD98D", "#8B5E00"],
    )
    fig3.update_traces(textposition="top center", marker=dict(opacity=0.86, line=dict(width=1, color="white")))
    fig3 = plot_style(fig3, height=520, legend=False)
    st.plotly_chart(fig3, use_container_width=True)
    show_sql(sql_scatter, "차트 3 SQL 보기")

    st.markdown(f"""
<div class="result">
<b>결과</b><br>
노령연금 수급자 수가 가장 많은 지역은 <b>{top_rec_row['지역본부_표시']}지역본부</b>였지만,
교육참여인원 최고 지역과 일치하지 않았습니다.
즉, 노후준비 수요가 큰 지역에서 교육 참여가 자동적으로 높아지는 구조는 확인되지 않았습니다.
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="insight">
<b>인사이트</b><br>
노후준비 수요가 존재한다고 해서 교육 참여가 자연스럽게 발생하는 것은 아닙니다.
수요와 참여 사이에는 정보 부족, 접근성 문제, 교육 필요성에 대한 인식 차이와 같은 행동 장벽이 존재할 수 있습니다.
따라서 노후준비교육의 핵심 과제는 단순히 교육을 제공하는 것이 아니라,
잠재적 수요를 실제 참여로 전환하는 과정에 있다고 해석할 수 있습니다.
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
        labels={
            "노령연금수급자수": "노령연금 수급자 수",
            "교육참여인원": "교육 참여 인원",
            "지역유형": "지역 유형",
        },
        color_discrete_sequence=["#E8A317", "#F6C453", "#8B5E00", "#FFD86B"],
    )

    fig4.add_vline(x=avg_rec, line_dash="dash", line_color="#9A7A2F")
    fig4.add_hline(y=avg_part, line_dash="dash", line_color="#9A7A2F")
    fig4.update_traces(textposition="top center", marker=dict(opacity=0.86, line=dict(width=1, color="white")))
    fig4 = plot_style(fig4, height=620)
    st.plotly_chart(fig4, use_container_width=True)
    show_sql(sql_type, "지역 유형화 SQL 보기")

    t1, t2, t3, t4 = st.columns(4)
    t1.markdown('<div class="type-card"><b>핵심관리형</b><span>수급 규모와 교육 참여가 모두 높은 지역입니다. 현재 운영을 유지하며 우수사례로 활용할 수 있습니다.</span></div>', unsafe_allow_html=True)
    t2.markdown('<div class="type-card"><b>교육집중형</b><span>수급 규모에 비해 교육 참여가 높은 지역입니다. 효과적인 운영 방식의 단서를 찾을 수 있습니다.</span></div>', unsafe_allow_html=True)
    t3.markdown('<div class="type-card"><b>확대필요형</b><span>수급 규모는 크지만 교육 참여가 낮은 지역입니다. 향후 교육 확대와 참여 유도 전략이 필요한 후보입니다.</span></div>', unsafe_allow_html=True)
    t4.markdown('<div class="type-card"><b>저수요형</b><span>수급 규모와 교육 참여가 모두 낮은 지역입니다. 지역 특성과 잠재 수요 확인이 필요합니다.</span></div>', unsafe_allow_html=True)

    st.markdown("""
<div class="result">
<b>발견</b><br>
지역을 유형화하면 단순 순위에서는 보이지 않던 차이가 드러납니다.
동일한 교육 프로그램이라도 지역별로 수급 규모와 참여 수준이 다르게 나타나므로,
노후준비교육은 지역별로 서로 다른 전략이 필요합니다.
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="insight">
<b>인사이트</b><br>
지역을 단순히 교육 규모 순위로 비교하는 것보다 수요와 참여를 함께 고려할 때 정책적 우선순위를 더 명확하게 확인할 수 있습니다.
특히 확대필요형 지역은 노후준비 수요는 높지만 교육 참여는 낮은 지역으로, 향후 노후준비교육 확대 정책의 우선 개입 대상이 될 수 있습니다.
반대로 교육집중형 지역은 현재의 교육 운영 방식이 효과적으로 작동하고 있는 사례로 해석할 수 있으며,
다른 지역의 벤치마킹 대상으로 활용될 수 있습니다.
</div>
""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 05 결론 및 서비스 제안
# =========================================================
with tab5:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">05. 결론 및 서비스 제안</div>', unsafe_allow_html=True)

    st.markdown("""
<div class="question-box">
<b>분석 결론</b><br><br>
노후준비교육 현황과 노령연금 수급 현황을 결합해 분석한 결과,
교육횟수와 참여인원, 그리고 수급 규모는 지역별로 서로 다른 양상을 보였습니다.
특히 교육 횟수를 늘리는 것만으로는 참여 확대가 보장되지 않았으며,
수요가 높은 지역에서도 교육 참여가 충분하지 않은 사례가 확인되었습니다.
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="insight">
<b>종합 인사이트</b><br>
이번 분석은 노후준비교육 정책이 단순 공급 확대 중심에서 벗어나야 함을 보여줍니다.
교육의 양을 늘리는 것만으로는 참여가 자동적으로 증가하지 않으며,
노후준비 수요가 큰 지역에서도 참여로 이어지기 위해서는 별도의 접근 전략과 참여 유도 장치가 필요합니다.
따라서 향후 노후준비교육은 지역별 수요 규모, 참여 수준, 교육 효율성을 함께 고려한 맞춤형 운영 전략으로 전환될 필요가 있습니다.
</div>
""", unsafe_allow_html=True)

    st.markdown("### 개인 맞춤형 노후 재무 시뮬레이션 서비스 제안")

    p1, p2, p3 = st.columns(3)
    p1.success("1. 개인 정보 입력\n\n나이, 소득, 현재 자산, 월 저축액")
    p2.info("2. 미래 자산 시뮬레이션\n\n예상 연금과 미래 생활비를 함께 계산")
    p3.warning("3. 맞춤형 노후준비 전략\n\n부족 구간과 필요한 자산 성장률 제시")

    st.markdown("""
<div class="result">
<b>서비스 제안</b><br>
지역 단위 분석은 교육 서비스의 배분 문제를 보여주지만,
개인의 실제 노후준비 수준은 개인별 소득, 자산, 저축액, 예상 연금 상황에 따라 달라집니다.
따라서 지역 단위 교육과 함께 개인 맞춤형 노후 재무 시뮬레이션 서비스를 제공한다면,
개인이 자신의 미래 재무 상태를 직접 확인하고 구체적인 노후준비 전략을 수립하는 데 도움을 줄 수 있습니다.
</div>
""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


st.caption("경영정보처리론 데이터 분석 및 시각화 프로젝트 | SQLite + Streamlit + Plotly")
