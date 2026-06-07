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
    page_title="노후준비교육은 실제 행동으로 이어질까?",
    page_icon="📊",
    layout="wide",
)

DB_PATH = "pension_education.db"


# =========================================================
# 디자인: 깔끔한 네이비·민트·화이트 톤
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #F6F8FB 0%, #EEF4F6 48%, #FAFBFC 100%);
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1320px;
}

.hero {
    background: linear-gradient(135deg, #1F3A5F 0%, #2B5C7B 58%, #4CA6A8 100%);
    color: #FFFFFF;
    padding: 36px 40px;
    border-radius: 28px;
    box-shadow: 0 18px 42px rgba(31, 58, 95, 0.18);
    margin-bottom: 24px;
}

.hero h1 {
    font-size: 35px;
    font-weight: 800;
    margin-bottom: 10px;
    letter-spacing: -0.8px;
}

.hero p {
    font-size: 16px;
    line-height: 1.78;
    opacity: 0.95;
    max-width: 1100px;
}

.hero .subtitle {
    display: inline-block;
    background: rgba(255,255,255,0.16);
    border: 1px solid rgba(255,255,255,0.28);
    border-radius: 999px;
    padding: 7px 14px;
    margin-bottom: 14px;
    font-size: 14px;
    font-weight: 700;
}

.section {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid #DDE8EC;
    border-radius: 24px;
    padding: 25px 27px;
    box-shadow: 0 10px 30px rgba(31, 58, 95, 0.07);
    margin: 22px 0;
}

.section-title {
    font-size: 23px;
    font-weight: 800;
    color: #1F2E46;
    margin-bottom: 8px;
    letter-spacing: -0.35px;
}

.section-sub {
    color: #667085;
    font-size: 14.5px;
    line-height: 1.65;
    margin-bottom: 14px;
}

.question-box {
    background: #EEF7F7;
    border-left: 6px solid #4CA6A8;
    color: #243447;
    padding: 16px 18px;
    border-radius: 17px;
    line-height: 1.75;
    margin: 14px 0 18px 0;
    border-top: 1px solid #D2E7E8;
    border-right: 1px solid #D2E7E8;
    border-bottom: 1px solid #D2E7E8;
}

.result {
    background: #F7FAFC;
    border: 1px solid #D9E5EC;
    border-left: 6px solid #2B5C7B;
    color: #243447;
    padding: 16px 18px;
    border-radius: 17px;
    font-size: 14.5px;
    line-height: 1.78;
    margin-top: 12px;
}

.insight {
    background: #FFFDF3;
    border: 1px solid #F1E4B8;
    border-left: 6px solid #E7B84B;
    color: #3D3522;
    padding: 16px 18px;
    border-radius: 17px;
    font-size: 14.5px;
    line-height: 1.8;
    margin-top: 12px;
}

.note {
    background: #F2F4F7;
    border: 1px solid #E4E7EC;
    color: #475467;
    padding: 13px 15px;
    border-radius: 14px;
    font-size: 13.5px;
    line-height: 1.65;
    margin-top: 10px;
}

.type-card {
    background: #FFFFFF;
    border-radius: 18px;
    border: 1px solid #DDE8EC;
    box-shadow: 0 8px 20px rgba(31, 58, 95, 0.06);
    padding: 16px 17px;
    min-height: 146px;
}

.type-card b {
    display: block;
    color: #1F2E46;
    font-size: 16px;
    margin-bottom: 8px;
}

.type-card span {
    color: #667085;
    font-size: 13.5px;
    line-height: 1.62;
}

div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.97);
    border: 1px solid #DDE8EC;
    border-radius: 20px;
    padding: 18px 18px;
    box-shadow: 0 8px 22px rgba(31, 58, 95, 0.06);
}

div[data-testid="stMetricValue"] {
    color: #1F2E46;
    font-weight: 800;
    font-size: 25px;
}

div[data-testid="stMetricLabel"] {
    color: #667085;
}

hr {
    margin: 1.4rem 0;
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
    text = str(name).replace("지역본부", "").strip()
    if text in ["본부", "기타본부", "기타"]:
        return "기타"
    return text


def chart_style(fig, height=450, legend=True):
    fig.update_layout(
        height=height,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.76)",
        margin=dict(l=20, r=25, t=58, b=25),
        font=dict(family="Noto Sans KR, sans-serif", size=13, color="#243447"),
        title=dict(font=dict(size=19, color="#1F2E46")),
        showlegend=legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.78)",
        ),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(43, 92, 123, 0.13)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(43, 92, 123, 0.13)", zeroline=False)
    return fig


def fmt_num(x, suffix=""):
    try:
        return f"{float(x):,.0f}{suffix}"
    except Exception:
        return str(x)


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

df["연금지표1천단위당교육참여"] = (
    df["교육참여인원"] / df["노령연금수급자수"] * 1000
).replace([float("inf"), -float("inf")], 0).fillna(0)

df["연금지표1만단위당교육횟수"] = (
    df["교육횟수"] / df["노령연금수급자수"] * 10000
).replace([float("inf"), -float("inf")], 0).fillna(0)


# '기타'는 여러 지역을 묶은 보조 범주이므로 해석용 자동 추출에서는 제외
df_interpret = df[df["지역본부_표시"] != "기타"].copy()
if df_interpret.empty:
    df_interpret = df.copy()


# 지역 유형화: 그래프에서는 전체 표시, 해석은 기타 제외
avg_participants = df_interpret["교육참여인원"].mean()
avg_indicator = df_interpret["노령연금수급자수"].mean()

def classify(row):
    if row["교육참여인원"] >= avg_participants and row["노령연금수급자수"] >= avg_indicator:
        return "행동연계형"
    elif row["교육참여인원"] >= avg_participants and row["노령연금수급자수"] < avg_indicator:
        return "참여우수형"
    elif row["교육참여인원"] < avg_participants and row["노령연금수급자수"] >= avg_indicator:
        return "전환필요형"
    else:
        return "기초관리형"

df["지역유형"] = df.apply(classify, axis=1)


# 주요값 자동 추출: 기타 제외 기준
top_edu_count = df_interpret.sort_values("교육횟수", ascending=False).iloc[0]
low_edu_count = df_interpret.sort_values("교육횟수", ascending=True).iloc[0]
top_participant = df_interpret.sort_values("교육참여인원", ascending=False).iloc[0]
top_indicator = df_interpret.sort_values("노령연금수급자수", ascending=False).iloc[0]
top_efficiency = df_interpret.sort_values("교육효율성", ascending=False).iloc[0]


# =========================================================
# Hero
# =========================================================
st.markdown("""
<div class="hero">
    <div class="subtitle">지역별 노후준비교육 현황과 연금 관련 지표를 활용한 탐색적 분석</div>
    <h1>노후준비교육은 실제 행동으로 이어질까?</h1>
    <p>
        고령화가 심화되면서 노후준비교육의 중요성은 커지고 있습니다.
        그러나 교육을 많이 제공한다고 해서 실제 노후준비 행동으로 이어지는지는 별도의 데이터 분석이 필요합니다.
        본 대시보드는 국민연금공단의 노후준비교육 데이터와 지역별 연금 관련 지표를 결합하여,
        교육 공급, 교육 참여, 연금 관련 준비 지표 사이의 관계를 탐색합니다.
    </p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# KPI
# =========================================================
k1, k2, k3, k4 = st.columns(4)
k1.metric("총 교육횟수", f"{df['교육횟수'].sum():,.0f}회")
k2.metric("총 교육참여인원", f"{df['교육참여인원'].sum():,.0f}명")
k3.metric("연금 관련 행동 지표 합계", f"{df['노령연금수급자수'].sum():,.0f}")
k4.metric("교육 효율성 최상위", f"{top_efficiency['지역본부_표시']}")

st.markdown("""
<div class="note">
<b>해석 유의</b> 연금 관련 행동 지표는 실제 인구 수나 노후준비 행동 전체를 의미하지 않습니다.
본 분석에서는 지역별 비교를 위한 대리 지표로 사용하며, 저축·투자·보험·부동산 등 다양한 노후준비 행동을 모두 포함하지는 않습니다.
또한 ‘기타’는 여러 지역이 묶인 보조 범주이므로, 결과 해석의 최상위·최하위 판단에서는 제외했습니다.
</div>
""", unsafe_allow_html=True)

st.divider()


# =========================================================
# 01 문제제기 & 데이터
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">01. 문제정의와 데이터 설계</div>', unsafe_allow_html=True)

st.markdown("""
<div class="question-box">
<b>왜 이 분석이 필요한가?</b><br>
한국 사회는 빠른 고령화와 함께 노후 불안이 커지고 있습니다.
국민연금공단은 이러한 문제에 대응하기 위해 노후준비교육을 운영하고 있지만,
교육이 실제 노후준비 행동으로 이어지는지는 단순한 교육횟수나 참여인원만으로 판단하기 어렵습니다.
특히 노후준비 행동은 저축, 투자, 보험, 부동산, 연금 등 다양한 요소를 포함하기 때문에 직접 측정하기 어렵습니다.
따라서 본 분석에서는 연금 관련 지표를 노후준비 행동의 하나의 대리 지표로 활용하여,
노후준비교육의 공급과 참여가 실제 준비 지표와 어떤 관계를 보이는지 탐색하고자 합니다.
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
<b>데이터 2: 연금 관련 지표</b>
<span>지역별 노령연금 수급 규모와 수급금액을 활용하여 노후준비 행동을 간접적으로 파악하는 대리 지표로 사용했습니다.</span>
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
<b>분석 흐름</b><br>
본 분석은 <b>교육 공급(교육횟수)</b> → <b>교육 참여(교육참여인원)</b> → <b>연금 관련 행동 지표</b>의 흐름으로 구성됩니다.
이를 통해 “교육을 많이 제공하면 실제 참여도 높아질까?”, “교육 참여가 높은 지역은 연금 관련 지표도 높게 나타날까?”라는 질문을 검증합니다.
다만 본 분석은 교육이 직접적으로 행동을 유발했다는 인과관계를 주장하는 것이 아니라,
지역 단위 데이터에서 나타나는 관계와 패턴을 탐색하는 데 목적이 있습니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 02 교육 공급 현황
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">02. 노후준비교육은 어디에서 활발하게 이루어지고 있을까?</div>', unsafe_allow_html=True)
st.markdown("""
<div class="question-box">
<b>질문</b> 노후준비교육은 지역별로 얼마나 다르게 제공되고 있을까?
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
    color_continuous_scale="Teal",
    title="지역본부별 노후준비교육 교육횟수",
    labels={"교육횟수": "교육횟수", "지역본부_표시": "지역본부"},
)
fig1.update_traces(texttemplate="%{text:,.0f}회", textposition="outside", cliponaxis=False)
fig1.update_layout(coloraxis_showscale=False)
fig1 = chart_style(fig1, height=460, legend=False)
st.plotly_chart(fig1, use_container_width=True)
show_sql(sql_edu_count, "차트 SQL 보기")

st.markdown(f"""
<div class="result">
<b>결과</b><br>
※ 아래 결과 해석은 여러 지역이 묶인 ‘기타’를 제외한 주요 지역본부 기준입니다.<br>
교육횟수가 가장 많은 지역은 <b>{top_edu_count['지역본부_표시']}</b>이며, 가장 적은 지역은 <b>{low_edu_count['지역본부_표시']}</b>입니다.
지역별 교육 공급 규모에는 뚜렷한 편차가 존재합니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
노후준비교육은 모든 지역에서 동일한 수준으로 제공되지 않았습니다.
이는 교육 서비스가 제도적으로 존재하는 것만으로는 충분하지 않으며, 지역별 교육 접근 기회 자체가 다르게 형성될 수 있음을 의미합니다.
다만 이 차이를 특정 지역의 우수성이나 부족함으로 단정하기보다는, 교육 공급이 지역본부의 운영 역량, 교육 인프라, 행정적 우선순위의 영향을 받는 구조적 결과로 해석할 필요가 있습니다.
따라서 다음 단계에서는 교육 공급량의 차이가 실제 교육 참여와 연금 관련 준비 지표의 차이로 이어지는지 확인해야 합니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 03 교육 효율성
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">03. 교육을 많이 제공하면 참여도도 높을까?</div>', unsafe_allow_html=True)
st.markdown("""
<div class="question-box">
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
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df["지역본부_표시"],
        y=df["교육횟수"],
        name="교육횟수",
        marker_color="#4CA6A8",
    ))
    fig2.add_trace(go.Scatter(
        x=df["지역본부_표시"],
        y=df["교육참여인원"],
        name="교육참여인원",
        mode="lines+markers",
        yaxis="y2",
        line=dict(color="#1F3A5F", width=3),
        marker=dict(size=9, color="#1F3A5F"),
    ))
    fig2.update_layout(
        title="교육횟수와 교육참여인원 비교",
        yaxis=dict(title="교육횟수"),
        yaxis2=dict(title="교육참여인원", overlaying="y", side="right"),
        legend=dict(orientation="h"),
    )
    fig2 = chart_style(fig2, height=500)
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
<div class="result">
<b>결과</b><br>
※ 아래 결과 해석은 여러 지역이 묶인 ‘기타’를 제외한 주요 지역본부 기준입니다.<br>
교육횟수가 가장 많은 지역과 교육참여인원이 가장 많은 지역은 일치하지 않았습니다.
교육 1회당 평균 참여인원을 기준으로 보면 <b>{top_efficiency['지역본부_표시']}</b>이 가장 높게 나타났습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
일반적으로 교육을 많이 열면 참여도 자연스럽게 증가할 것이라고 예상할 수 있습니다.
그러나 실제 데이터에서는 교육횟수와 참여인원이 완전히 비례하지 않았습니다.
일부 지역은 상대적으로 적은 교육횟수에도 높은 참여를 기록했고, 반대로 많은 교육을 운영했음에도 1회당 참여 규모가 낮은 지역도 나타났습니다.
이는 노후준비교육의 1차 성과가 교육 공급량보다 <b>참여 전환 능력</b>에 의해 좌우될 수 있음을 보여줍니다.
따라서 교육 정책을 평가할 때 단순히 “몇 회 운영했는가”가 아니라 “얼마나 많은 사람이 실제로 참여했는가”, “교육 1회당 참여 효율성이 어떠한가”를 함께 봐야 합니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 04 연금 관련 지표
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">04. 연금 관련 준비 수준은 지역별로 차이가 있을까?</div>', unsafe_allow_html=True)
st.markdown("""
<div class="question-box">
<b>질문</b> 연금 관련 지표를 기준으로 볼 때, 노후준비 행동 수준은 지역별로 차이가 있을까?
</div>
""", unsafe_allow_html=True)

sql_indicator = """
SELECT
    지역본부,
    노령연금수급자수
FROM education_pension
ORDER BY 노령연금수급자수 DESC;
"""
df_indicator = load_data(sql_indicator)
df_indicator = make_numeric(df_indicator, ["노령연금수급자수"])
df_indicator["지역본부_표시"] = df_indicator["지역본부"].apply(short_region)

fig4 = px.bar(
    df_indicator.sort_values("노령연금수급자수", ascending=False),
    x="지역본부_표시",
    y="노령연금수급자수",
    text="노령연금수급자수",
    color="노령연금수급자수",
    color_continuous_scale="Teal",
    title="지역본부별 연금 관련 지표",
    labels={"지역본부_표시": "지역본부", "노령연금수급자수": "연금 관련 지표"},
)
fig4.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
fig4.update_layout(coloraxis_showscale=False)
fig4 = chart_style(fig4, height=470, legend=False)
st.plotly_chart(fig4, use_container_width=True)
show_sql(sql_indicator, "차트 SQL 보기")

st.markdown(f"""
<div class="result">
<b>결과</b><br>
※ 아래 결과 해석은 여러 지역이 묶인 ‘기타’를 제외한 주요 지역본부 기준입니다.<br>
연금 관련 지표가 가장 크게 나타난 지역은 <b>{top_indicator['지역본부_표시']}</b>입니다.
이는 연금 관련 준비 지표가 지역별로 균등하게 분포하지 않음을 보여줍니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
연금 관련 지표는 지역별로 큰 차이를 보였습니다.
이는 노후준비와 관련된 행동 또는 결과가 모든 지역에서 동일하게 나타나지 않음을 의미합니다.
다만 연금 관련 지표는 노후준비 행동 전체를 직접 측정하는 값이 아니라, 노후준비 수준을 간접적으로 파악하기 위한 대리 지표입니다.
따라서 이 결과는 “어느 지역이 더 잘 준비했다”는 단정이 아니라, 교육 참여 수준과 비교해 볼 필요가 있는 <b>연금 관련 준비 지표의 지역 차이</b>로 해석하는 것이 적절합니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 05 교육 참여와 연금 관련 지표의 관계
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">05. 교육 참여는 연금 관련 행동 지표와 연결될까?</div>', unsafe_allow_html=True)
st.markdown("""
<div class="question-box">
<b>질문</b> 노후준비교육 참여가 높은 지역은 연금 관련 지표도 높게 나타날까?
</div>
""", unsafe_allow_html=True)

sql_relation = """
SELECT
    지역본부,
    교육참여인원,
    노령연금수급자수,
    ROUND(교육참여인원 * 1000.0 / 노령연금수급자수, 2) AS 연금지표1천단위당교육참여
FROM education_pension;
"""

fig5 = px.scatter(
    df,
    x="노령연금수급자수",
    y="교육참여인원",
    size="연금지표1천단위당교육참여",
    color="지역본부_표시",
    text="지역본부_표시",
    title="교육 참여 수준과 연금 관련 지표의 관계",
    labels={
        "노령연금수급자수": "연금 관련 지표",
        "교육참여인원": "교육참여인원",
        "연금지표1천단위당교육참여": "연금 지표 1천 단위당 교육참여",
        "지역본부_표시": "지역본부",
    },
    color_discrete_sequence=["#1F3A5F", "#2B5C7B", "#4CA6A8", "#7CC7C9", "#95A3B3", "#5E8BA6", "#B7DDE0", "#334E68"],
)
fig5.update_traces(textposition="top center", marker=dict(opacity=0.86, line=dict(width=1, color="white")))
fig5 = chart_style(fig5, height=540, legend=False)
st.plotly_chart(fig5, use_container_width=True)
show_sql(sql_relation, "차트 SQL 보기")

st.markdown("""
<div class="result">
<b>결과</b><br>
교육참여인원이 높은 지역이 반드시 연금 관련 지표도 높게 나타나지는 않았습니다.
반대로 연금 관련 지표가 큰 지역에서도 교육 참여 수준은 서로 다르게 나타났습니다.
즉, 교육 참여와 연금 관련 지표 사이에 단순한 비례 관계는 뚜렷하게 확인되지 않았습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
본 분석의 핵심 질문은 “노후준비교육 참여가 실제 연금 관련 준비 지표와 연결되는가?”입니다.
분석 결과, 교육 참여 수준과 연금 관련 지표 사이에는 단순한 비례 관계가 뚜렷하게 나타나지 않았습니다.
이는 노후준비교육이 중요하지 않다는 의미가 아니라, 교육 참여만으로 실제 노후준비 행동을 충분히 설명하기 어렵다는 점을 보여줍니다.
노후준비 행동은 교육 외에도 소득, 자산, 직업 안정성, 금융 접근성, 지역의 생활 여건 등 다양한 요인의 영향을 받을 가능성이 있습니다.
따라서 교육 이후 실제 행동 변화를 유도하기 위해서는 교육 제공에서 끝나는 것이 아니라, 개인별 상황에 맞춘 후속 지원과 의사결정 도구가 함께 필요합니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 06 지역 유형화
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">06. 교육 참여와 연금 관련 지표로 지역을 유형화할 수 있을까?</div>', unsafe_allow_html=True)
st.markdown("""
<div class="question-box">
<b>질문</b> 교육 참여 수준과 연금 관련 지표를 함께 고려하면 지역을 어떻게 구분할 수 있을까?
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
        THEN '행동연계형'

        WHEN 교육참여인원 >= (SELECT AVG(교육참여인원) FROM education_pension)
         AND 노령연금수급자수 < (SELECT AVG(노령연금수급자수) FROM education_pension)
        THEN '참여우수형'

        WHEN 교육참여인원 < (SELECT AVG(교육참여인원) FROM education_pension)
         AND 노령연금수급자수 >= (SELECT AVG(노령연금수급자수) FROM education_pension)
        THEN '전환필요형'

        ELSE '기초관리형'
    END AS 지역유형
FROM education_pension;
"""

fig6 = px.scatter(
    df,
    x="노령연금수급자수",
    y="교육참여인원",
    color="지역유형",
    size="연금지표1천단위당교육참여",
    text="지역본부_표시",
    title="교육 참여 수준과 연금 관련 준비 지표에 따른 지역 유형화",
    labels={
        "노령연금수급자수": "연금 관련 지표",
        "교육참여인원": "교육참여인원",
        "지역유형": "지역 유형",
        "연금지표1천단위당교육참여": "연금 지표 1천 단위당 교육참여",
    },
    color_discrete_sequence=["#1F3A5F", "#4CA6A8", "#E7B84B", "#95A3B3"],
)
fig6.add_vline(x=avg_indicator, line_dash="dash", line_color="#667085")
fig6.add_hline(y=avg_participants, line_dash="dash", line_color="#667085")
fig6.update_traces(textposition="top center", marker=dict(opacity=0.86, line=dict(width=1, color="white")))
fig6 = chart_style(fig6, height=620, legend=True)
st.plotly_chart(fig6, use_container_width=True)
show_sql(sql_type, "지역 유형화 SQL 보기")

tc1, tc2, tc3, tc4 = st.columns(4)
tc1.markdown('<div class="type-card"><b>행동연계형</b><span>교육 참여와 연금 관련 지표가 모두 높은 지역입니다. 교육과 준비 지표가 함께 나타나는 사례로 볼 수 있습니다.</span></div>', unsafe_allow_html=True)
tc2.markdown('<div class="type-card"><b>참여우수형</b><span>교육 참여는 높지만 연금 관련 지표는 상대적으로 낮은 지역입니다. 교육 이후 행동 전환을 높이는 후속 지원이 필요합니다.</span></div>', unsafe_allow_html=True)
tc3.markdown('<div class="type-card"><b>전환필요형</b><span>연금 관련 지표는 높지만 교육 참여가 낮은 지역입니다. 기존 준비 행동은 존재하나 교육 서비스와 연결되지 않은 집단일 수 있습니다.</span></div>', unsafe_allow_html=True)
tc4.markdown('<div class="type-card"><b>기초관리형</b><span>교육 참여와 연금 관련 지표가 모두 낮은 지역입니다. 기초 홍보와 접근성 개선이 우선 필요한 지역입니다.</span></div>', unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
지역을 단순히 교육횟수나 참여인원 순위로만 비교하면 정책적 의미를 찾기 어렵습니다.
교육 참여와 연금 관련 지표를 함께 고려하면, 지역별로 다른 개입 전략을 설계할 수 있습니다.
<b>행동연계형</b>은 교육 참여와 연금 관련 지표가 함께 높은 지역으로, 교육과 준비 지표가 함께 나타나는 사례입니다.
<b>참여우수형</b>은 교육 참여는 높지만 연금 관련 지표가 상대적으로 낮은 지역으로, 교육 이후 실제 행동 전환을 지원하는 후속 서비스가 필요합니다.
<b>전환필요형</b>은 연금 관련 지표는 높지만 교육 참여가 낮은 지역으로, 이미 준비 행동은 존재하지만 교육 서비스와 연결되지 않은 집단일 가능성이 있습니다.
이처럼 유형화는 단순 현황 비교를 넘어, 지역별로 어떤 교육 전략과 후속 서비스를 설계해야 하는지 판단하는 의사결정 도구로 활용될 수 있습니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 07 결론과 서비스 제안
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">07. 결론 및 개인 맞춤형 서비스 제안</div>', unsafe_allow_html=True)

st.markdown("""
<div class="result">
<b>최종 결론</b><br>
이번 분석은 노후준비교육이 활발하게 이루어진 지역이 반드시 더 높은 연금 관련 준비 지표를 보이는 것은 아니라는 점을 보여주었습니다.
교육횟수를 늘리는 것만으로는 참여 확대가 보장되지 않았고, 교육 참여가 높다고 해서 연금 관련 지표가 단순히 함께 높아지는 구조도 뚜렷하게 확인되지 않았습니다.
이는 노후준비교육이 중요한 출발점이 될 수는 있지만, 교육만으로 개인의 노후준비 행동을 충분히 설명하기 어렵다는 것을 의미합니다.
따라서 노후준비교육의 성과를 높이기 위해서는 교육 공급, 교육 참여, 교육 이후 행동 전환을 구분하여 관리할 필요가 있습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>서비스 제안</b><br>
본 분석은 지역 단위에서 노후준비교육과 연금 관련 지표의 관계를 탐색했습니다.
그러나 같은 지역 안에서도 개인의 소득, 자산, 저축액, 예상 연금 수준은 크게 다를 수 있습니다.
따라서 향후에는 집단 교육과 함께 <b>개인 맞춤형 노후 재무 시뮬레이션 서비스</b>를 제공할 필요가 있습니다.
이 서비스는 사용자가 자신의 현재 소득, 자산, 월 저축액, 예상 연금을 입력하면 미래 자산 변화와 노후 준비 부족 구간을 확인할 수 있도록 돕습니다.
즉, 지역 단위 분석은 교육 자원 배분의 방향을 제시하고, 개인 맞춤형 서비스는 교육 이후 실제 노후준비 행동으로 이어지도록 돕는 보완적 의사결정 지원 도구가 될 수 있습니다.
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
