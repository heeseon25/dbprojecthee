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
    background: linear-gradient(135deg, #f5f7fb 0%, #eef3f7 100%);
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1320px;
}

.hero {
    background: linear-gradient(135deg, #243b63 0%, #496b9c 58%, #b7c9de 100%);
    color: white;
    padding: 34px 38px;
    border-radius: 28px;
    box-shadow: 0 16px 42px rgba(36, 59, 99, 0.18);
    margin-bottom: 24px;
}

.hero-title {
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -0.8px;
    margin-bottom: 10px;
}

.hero-sub {
    font-size: 16px;
    line-height: 1.75;
    opacity: 0.94;
    max-width: 1050px;
}

.section {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid #e4eaf2;
    border-radius: 24px;
    padding: 24px 26px;
    box-shadow: 0 10px 30px rgba(36, 59, 99, 0.07);
    margin: 22px 0;
}

.section-title {
    font-size: 23px;
    font-weight: 800;
    color: #253755;
    margin-bottom: 6px;
    letter-spacing: -0.4px;
}

.section-question {
    background: #edf4fb;
    border-left: 6px solid #4e6e9d;
    color: #293a52;
    padding: 14px 16px;
    border-radius: 15px;
    line-height: 1.6;
    margin: 12px 0 18px 0;
    font-size: 15px;
}

.finding {
    background: #eef8f4;
    border: 1px solid #cbe8dc;
    border-left: 6px solid #58a882;
    color: #263d34;
    padding: 15px 17px;
    border-radius: 16px;
    line-height: 1.7;
    font-size: 14.5px;
    margin-top: 10px;
}

.insight {
    background: #fff8df;
    border: 1px solid #f0dea9;
    border-left: 6px solid #d7a229;
    color: #3e392a;
    padding: 15px 17px;
    border-radius: 16px;
    line-height: 1.7;
    font-size: 14.5px;
    margin-top: 10px;
}

.type-card {
    background: #ffffff;
    border-radius: 18px;
    border: 1px solid #e5ebf3;
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
    color: #67768c;
    font-size: 13.5px;
    line-height: 1.6;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e5ebf3;
    border-radius: 20px;
    padding: 17px 18px;
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

hr {
    margin-top: 1.4rem;
    margin-bottom: 1.4rem;
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


def show_sql(sql: str, label: str = "사용한 SQL 보기"):
    with st.expander(label):
        st.code(sql.strip(), language="sql")


def make_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def short_region(name):
    return str(name).replace("지역본부", "").strip()


def chart_style(fig, height=450, legend=True):
    fig.update_layout(
        height=height,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.65)",
        margin=dict(l=20, r=25, t=58, b=25),
        font=dict(family="Noto Sans KR, sans-serif", size=13, color="#2d3648"),
        title=dict(font=dict(size=19, color="#253755")),
        showlegend=legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(120,130,150,0.16)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(120,130,150,0.16)", zeroline=False)
    return fig


# =========================================================
# 데이터 로드 및 파생지표
# =========================================================
sql_main = """
SELECT *
FROM education_pension;
"""

df = load_data(sql_main)

df = make_numeric(df, [
    "교육횟수",
    "교육참여인원",
    "노령연금수급자수",
    "노령연금금액",
])

df["지역본부_표시"] = df["지역본부"].apply(short_region)

df["교육효율성"] = (
    df["교육참여인원"] / df["교육횟수"]
).replace([float("inf"), -float("inf")], 0).fillna(0)

df["수급자1천명당교육참여"] = (
    df["교육참여인원"] / df["노령연금수급자수"] * 1000
).replace([float("inf"), -float("inf")], 0).fillna(0)

df["수급자1만명당교육횟수"] = (
    df["교육횟수"] / df["노령연금수급자수"] * 10000
).replace([float("inf"), -float("inf")], 0).fillna(0)


# 지역 유형화
avg_participants = df["교육참여인원"].mean()
avg_recipients = df["노령연금수급자수"].mean()

def classify(row):
    if row["교육참여인원"] >= avg_participants and row["노령연금수급자수"] >= avg_recipients:
        return "핵심관리형"
    elif row["교육참여인원"] >= avg_participants and row["노령연금수급자수"] < avg_recipients:
        return "교육집중형"
    elif row["교육참여인원"] < avg_participants and row["노령연금수급자수"] >= avg_recipients:
        return "확대필요형"
    else:
        return "저수요형"

df["지역유형"] = df.apply(classify, axis=1)


# 주요 지역 자동 추출
top_edu_count = df.sort_values("교육횟수", ascending=False).iloc[0]
low_edu_count = df.sort_values("교육횟수", ascending=True).iloc[0]
top_participant = df.sort_values("교육참여인원", ascending=False).iloc[0]
top_demand = df.sort_values("노령연금수급자수", ascending=False).iloc[0]
top_efficiency = df.sort_values("교육효율성", ascending=False).iloc[0]


# =========================================================
# Hero
# =========================================================
st.markdown(f"""
<div class="hero">
    <div class="hero-title">노후준비교육의 공급과 수요는 일치하는가?</div>
    <div class="hero-sub">
        국민연금공단의 <b>지역본부별 노후준비교육 현황</b>과 <b>지역별 노령연금 수급 현황</b>을 결합하여,
        교육 공급량과 실제 노후준비 수요가 어떻게 대응되는지 분석했습니다.
        단순 현황 파악을 넘어, 교육 횟수와 참여, 수급 규모 사이의 관계를 통해
        노후준비교육 운영 전략과 개인 맞춤형 노후 재무 시뮬레이션 서비스의 필요성을 도출합니다.
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# KPI
# =========================================================
k1, k2, k3, k4 = st.columns(4)
k1.metric("총 교육횟수", f"{df['교육횟수'].sum():,.0f}회")
k2.metric("총 교육참여인원", f"{df['교육참여인원'].sum():,.0f}명")
k3.metric("총 노령연금 수급자", f"{df['노령연금수급자수'].sum():,.0f}명")
k4.metric("교육 효율성 최상위", f"{top_efficiency['지역본부_표시']}")

st.divider()


# =========================================================
# 01 문제제기 & 데이터
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">01. 문제제기와 데이터 설계</div>', unsafe_allow_html=True)

st.markdown("""
<div class="section-question">
<b>노후준비교육은 정말 필요한 지역에 충분히 제공되고 있을까?</b><br>
고령화가 가속화되면서 노후준비교육의 중요성은 커지고 있습니다.
하지만 교육을 많이 운영하는 지역이 실제 노후준비 수요가 높은 지역인지,
또 교육 공급량이 실제 참여로 이어지는지는 별도로 확인이 필요합니다.
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""
<div class="type-card">
<b>데이터 1: 노후준비교육 현황</b>
<span>지역본부별 교육횟수와 교육참여인원을 사용하여 교육 공급과 참여 수준을 측정했습니다.</span>
</div>
""", unsafe_allow_html=True)
with c2:
    st.markdown("""
<div class="type-card">
<b>데이터 2: 노령연금 수급 현황</b>
<span>지역별 노령연금 수급자 수와 수급금액을 사용하여 노후준비 수요 규모를 파악했습니다.</span>
</div>
""", unsafe_allow_html=True)
with c3:
    st.markdown("""
<div class="type-card">
<b>데이터 3: 지역 매핑 테이블</b>
<span>시도·시군구 단위 연금 데이터를 국민연금공단 지역본부 기준으로 통합하기 위해 직접 구축했습니다.</span>
</div>
""", unsafe_allow_html=True)

show_sql("""
SELECT *
FROM education_pension;
""", "메인 VIEW 조회 SQL 보기")

st.markdown("""
<div class="insight">
<b>분석 방향</b><br>
본 분석은 교육 공급을 의미하는 <b>교육횟수·교육참여인원</b>과
노후준비 수요를 의미하는 <b>노령연금 수급자 수</b>를 비교합니다.
이를 통해 “교육을 많이 제공하면 참여도 높을까?”, “수요가 높은 지역은 교육도 활발할까?”라는 가정을 검증합니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 02 교육 공급 현황
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">02. 교육 공급은 지역별로 균등하게 이루어지고 있을까?</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-question">
<b>질문</b> 지역본부별 노후준비교육 공급 규모에는 차이가 있을까?
</div>
""", unsafe_allow_html=True)

sql_edu_count = """
SELECT
    지역본부,
    교육횟수
FROM education_pension
ORDER BY 교육횟수 DESC;
"""
df_edu_count = load_data(sql_edu_count)
df_edu_count = make_numeric(df_edu_count, ["교육횟수"])
df_edu_count["지역본부_표시"] = df_edu_count["지역본부"].apply(short_region)

fig1 = px.bar(
    df_edu_count.sort_values("교육횟수", ascending=True),
    x="교육횟수",
    y="지역본부_표시",
    orientation="h",
    text="교육횟수",
    color="교육횟수",
    color_continuous_scale="Blues",
    title="지역본부별 노후준비교육 교육횟수",
    labels={"교육횟수": "교육횟수", "지역본부_표시": "지역본부"},
)
fig1.update_traces(texttemplate="%{text:,.0f}회", textposition="outside", cliponaxis=False)
fig1.update_layout(coloraxis_showscale=False)
fig1 = chart_style(fig1, height=460, legend=False)
st.plotly_chart(fig1, use_container_width=True)
show_sql(sql_edu_count, "차트 SQL 보기")

st.markdown(f"""
<div class="finding">
<b>결과</b><br>
{top_edu_count['지역본부_표시']}지역본부는 <b>{top_edu_count['교육횟수']:,.0f}회</b>로 가장 많은 교육을 운영한 반면,
{low_edu_count['지역본부_표시']}지역본부는 <b>{low_edu_count['교육횟수']:,.0f}회</b> 수준에 머물렀습니다.
지역별 교육 공급 규모에는 뚜렷한 차이가 존재합니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
노후준비교육은 전국에 균등하게 제공되지 않고 있으며, 지역별 교육 공급 수준에 상당한 편차가 존재합니다.
특히 일부 지역은 수급 규모에 비해 교육 공급이 활발한 반면, 일부 지역은 상대적으로 적은 교육 기회를 제공합니다.
이는 노후준비교육이 단순히 수요 규모만을 기준으로 운영된다기보다 지역별 운영 역량과 정책 우선순위의 영향을 받을 가능성을 시사합니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 03 교육 효율성
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">03. 교육을 많이 제공하면 참여도도 높을까?</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-question">
<b>질문</b> 교육횟수가 많은 지역이 실제 교육참여인원도 많을까?
</div>
""", unsafe_allow_html=True)

sql_efficiency = """
SELECT
    지역본부,
    교육횟수,
    교육참여인원,
    ROUND(교육참여인원 * 1.0 / 교육횟수, 2) AS 교육효율성
FROM education_pension
ORDER BY 교육효율성 DESC;
"""
df_eff = load_data(sql_efficiency)
df_eff = make_numeric(df_eff, ["교육횟수", "교육참여인원", "교육효율성"])
df_eff["지역본부_표시"] = df_eff["지역본부"].apply(short_region)

left, right = st.columns([1.15, 1])

with left:
    fig2 = px.scatter(
        df,
        x="교육횟수",
        y="교육참여인원",
        size="교육효율성",
        color="지역본부_표시",
        text="지역본부_표시",
        title="교육횟수와 교육참여인원의 관계",
        labels={
            "교육횟수": "교육횟수",
            "교육참여인원": "교육참여인원",
            "지역본부_표시": "지역본부",
            "교육효율성": "1회당 평균 참여인원",
        },
    )
    fig2.update_traces(textposition="top center", marker=dict(opacity=0.85, line=dict(width=1, color="white")))
    fig2 = chart_style(fig2, height=500, legend=False)
    st.plotly_chart(fig2, use_container_width=True)

with right:
    fig3 = px.bar(
        df_eff.sort_values("교육효율성", ascending=True),
        x="교육효율성",
        y="지역본부_표시",
        orientation="h",
        text="교육효율성",
        color="교육효율성",
        color_continuous_scale="Teal",
        title="교육 1회당 평균 참여인원",
        labels={"교육효율성": "1회당 평균 참여인원", "지역본부_표시": "지역본부"},
    )
    fig3.update_traces(texttemplate="%{text:.1f}명", textposition="outside", cliponaxis=False)
    fig3.update_layout(coloraxis_showscale=False)
    fig3 = chart_style(fig3, height=500, legend=False)
    st.plotly_chart(fig3, use_container_width=True)

show_sql(sql_efficiency, "차트 SQL 보기")

st.markdown(f"""
<div class="finding">
<b>결과</b><br>
교육횟수가 가장 많은 {top_edu_count['지역본부_표시']}지역본부가 참여인원 1위는 아니었습니다.
반면 {top_participant['지역본부_표시']}지역본부는 상대적으로 적은 교육횟수에도
<b>{top_participant['교육참여인원']:,.0f}명</b>으로 가장 높은 참여인원을 기록했습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
일반적으로 교육 공급이 증가하면 참여도 함께 증가할 것으로 예상할 수 있습니다.
그러나 분석 결과, 교육횟수가 가장 많은 지역이 반드시 가장 많은 참여자를 확보하지는 못했습니다.
이는 교육 성과가 단순 공급량보다 교육 접근성, 홍보 전략, 교육 내용의 적합성 등 질적 요소에 의해 결정될 수 있음을 보여줍니다.
따라서 노후준비교육의 효과를 높이기 위해서는 교육 횟수 확대보다 참여를 유도하는 운영 전략이 함께 고려되어야 합니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 04 노후준비 수요 현황
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">04. 노후준비 수요가 높은 지역은 어디일까?</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-question">
<b>질문</b> 노령연금 수급자 규모를 기준으로 볼 때, 어느 지역의 노후준비 수요가 가장 클까?
</div>
""", unsafe_allow_html=True)

sql_demand = """
SELECT
    지역본부,
    노령연금수급자수
FROM education_pension
ORDER BY 노령연금수급자수 DESC;
"""
df_demand = load_data(sql_demand)
df_demand = make_numeric(df_demand, ["노령연금수급자수"])
df_demand["지역본부_표시"] = df_demand["지역본부"].apply(short_region)

fig4 = px.bar(
    df_demand.sort_values("노령연금수급자수", ascending=False),
    x="지역본부_표시",
    y="노령연금수급자수",
    text="노령연금수급자수",
    color="노령연금수급자수",
    color_continuous_scale="Purples",
    title="지역본부별 노령연금 수급자 수",
    labels={"지역본부_표시": "지역본부", "노령연금수급자수": "노령연금 수급자 수"},
)
fig4.update_traces(texttemplate="%{text:,.0f}명", textposition="outside", cliponaxis=False)
fig4.update_layout(coloraxis_showscale=False)
fig4 = chart_style(fig4, height=470, legend=False)
st.plotly_chart(fig4, use_container_width=True)
show_sql(sql_demand, "차트 SQL 보기")

st.markdown(f"""
<div class="finding">
<b>결과</b><br>
{top_demand['지역본부_표시']}지역본부는 <b>{top_demand['노령연금수급자수']:,.0f}명</b>으로
가장 큰 노령연금 수급 규모를 보였습니다.
이는 지역별 노후준비 수요가 동일하지 않으며, 특정 지역에 수요가 집중되어 있음을 보여줍니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
노령연금 수급자 수는 지역별로 큰 차이를 보였습니다.
이는 노후준비 수요가 전국에 균등하게 분포하지 않으며, 특정 지역에 집중되어 있음을 의미합니다.
따라서 동일한 규모의 교육 서비스를 전국에 일괄적으로 제공하는 방식은 실제 수요를 충분히 반영하지 못할 가능성이 있습니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 05 공급과 수요 관계
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">05. 노후준비 수요가 높은 지역은 교육 참여도 높을까?</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-question">
<b>질문</b> 노령연금 수급자 수가 많은 지역일수록 노후준비교육 참여도 많을까?
</div>
""", unsafe_allow_html=True)

sql_relation = """
SELECT
    지역본부,
    교육참여인원,
    노령연금수급자수,
    ROUND(교육참여인원 * 1000.0 / 노령연금수급자수, 2) AS 수급자1천명당교육참여
FROM education_pension;
"""

fig5 = px.scatter(
    df,
    x="노령연금수급자수",
    y="교육참여인원",
    size="수급자1천명당교육참여",
    color="지역본부_표시",
    text="지역본부_표시",
    title="노령연금 수급 규모와 교육 참여 수준의 관계",
    labels={
        "노령연금수급자수": "노령연금 수급자 수",
        "교육참여인원": "교육참여인원",
        "수급자1천명당교육참여": "수급자 1천 명당 교육참여",
        "지역본부_표시": "지역본부",
    },
)
fig5.update_traces(textposition="top center", marker=dict(opacity=0.85, line=dict(width=1, color="white")))
fig5 = chart_style(fig5, height=540, legend=False)
st.plotly_chart(fig5, use_container_width=True)
show_sql(sql_relation, "차트 SQL 보기")

st.markdown("""
<div class="finding">
<b>결과</b><br>
노령연금 수급자 수가 많은 지역이 반드시 교육참여인원도 가장 높은 것은 아니었습니다.
수급 규모가 큰 지역에서도 참여가 상대적으로 낮게 나타나는 경우가 있었고,
반대로 수급 규모가 상대적으로 작아도 높은 참여 수준을 보이는 지역이 존재했습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
우리는 일반적으로 노후준비가 필요한 사람이 많은 지역일수록 교육 참여도 높을 것이라고 예상합니다.
그러나 실제 데이터에서는 수급 규모와 교육 참여 수준 사이에 뚜렷한 비례 관계가 나타나지 않았습니다.
이는 노후준비 수요가 존재하더라도 해당 수요가 실제 교육 참여 행동으로 연결되지 않을 수 있음을 의미합니다.
다시 말해 노후준비교육의 과제는 단순한 교육 제공이 아니라, 잠재적 수요를 실제 참여로 전환하는 과정에 있을 가능성이 있습니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 06 지역 유형화
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">06. 데이터 기반 지역 유형화</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-question">
<b>질문</b> 교육 참여 수준과 노후준비 수요를 함께 고려하면 지역을 어떻게 구분할 수 있을까?
</div>
""", unsafe_allow_html=True)

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

fig6 = px.scatter(
    df,
    x="노령연금수급자수",
    y="교육참여인원",
    color="지역유형",
    size="수급자1천명당교육참여",
    text="지역본부_표시",
    title="교육 참여 수준과 노후준비 수요에 따른 지역 유형화",
    labels={
        "노령연금수급자수": "노령연금 수급자 수",
        "교육참여인원": "교육참여인원",
        "지역유형": "지역 유형",
        "수급자1천명당교육참여": "수급자 1천 명당 교육참여",
    },
)
fig6.add_vline(x=avg_recipients, line_dash="dash", line_color="gray")
fig6.add_hline(y=avg_participants, line_dash="dash", line_color="gray")
fig6.update_traces(textposition="top center", marker=dict(opacity=0.85, line=dict(width=1, color="white")))
fig6 = chart_style(fig6, height=620, legend=True)
st.plotly_chart(fig6, use_container_width=True)
show_sql(sql_type, "지역 유형화 SQL 보기")

tc1, tc2, tc3, tc4 = st.columns(4)
tc1.markdown('<div class="type-card"><b>핵심관리형</b><span>수요와 참여가 모두 높은 지역입니다. 현재 운영을 유지하며 우수사례로 활용할 수 있습니다.</span></div>', unsafe_allow_html=True)
tc2.markdown('<div class="type-card"><b>교육집중형</b><span>수요 규모에 비해 참여가 높은 지역입니다. 효과적인 운영 방식의 단서를 찾을 수 있습니다.</span></div>', unsafe_allow_html=True)
tc3.markdown('<div class="type-card"><b>확대필요형</b><span>수요는 크지만 참여가 낮은 지역입니다. 향후 교육 확대와 참여 유도 전략이 필요한 후보입니다.</span></div>', unsafe_allow_html=True)
tc4.markdown('<div class="type-card"><b>저수요형</b><span>수요와 참여가 모두 낮은 지역입니다. 잠재 수요와 지역 특성에 대한 추가 확인이 필요합니다.</span></div>', unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
지역을 단순히 교육 규모 순위로 비교하는 것보다 수요와 참여를 함께 고려할 때 정책적 우선순위를 더 명확하게 확인할 수 있습니다.
특히 확대필요형 지역은 노후준비 수요는 높지만 교육 참여는 낮은 지역으로, 향후 노후준비교육 확대 정책의 우선 개입 대상이 될 수 있습니다.
반대로 교육집중형 지역은 현재의 교육 운영 방식이 효과적으로 작동하고 있는 사례로 해석할 수 있으며, 다른 지역의 벤치마킹 대상으로 활용될 수 있습니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 07 결론과 서비스 제안
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">07. 결론 및 서비스 제안</div>', unsafe_allow_html=True)

st.markdown("""
<div class="finding">
<b>결론</b><br>
이번 분석은 노후준비교육의 공급 규모와 노후준비 수요 규모가 반드시 일치하지 않음을 보여주었습니다.
특히 교육 횟수를 늘리는 것만으로는 참여 확대가 보장되지 않았으며,
수요가 높은 지역에서도 교육 참여가 충분하지 않은 사례가 확인되었습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>종합 인사이트</b><br>
이는 노후준비교육 정책이 단순 공급 확대 중심에서 벗어나
지역별 수요와 참여 특성을 고려한 맞춤형 전략으로 전환될 필요가 있음을 시사합니다.
또한 같은 지역 안에서도 개인의 소득, 자산, 연금 수준은 크게 다르기 때문에
지역 단위 교육만으로는 개인별 노후준비 수준을 충분히 설명하기 어렵습니다.
따라서 향후에는 교육 서비스와 함께 개인 맞춤형 노후 재무 시뮬레이션 서비스를 제공하여,
개인이 자신의 미래 재무 상태를 직접 확인하고 노후준비 전략을 수립할 수 있도록 지원할 필요가 있습니다.
</div>
""", unsafe_allow_html=True)

p1, p2, p3 = st.columns(3)
p1.success("1. 개인 정보 입력\n\n나이, 소득, 현재 자산, 월 저축액")
p2.info("2. 미래 자산 시뮬레이션\n\n예상 연금과 미래 생활비를 반영한 자산 변화 확인")
p3.warning("3. 맞춤형 노후준비 전략\n\n부족 구간과 필요한 준비 방향 제안")

with st.expander("분석 데이터 확인"):
    st.dataframe(df.sort_values("노령연금수급자수", ascending=False), use_container_width=True, hide_index=True)

st.markdown('</div>', unsafe_allow_html=True)

st.caption("경영정보처리론 데이터 분석 및 시각화 프로젝트 | SQLite + Streamlit + Plotly")
