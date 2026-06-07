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
    page_title="노후준비교육은 실제 노후준비 행동으로 이어질까?",
    page_icon="📊",
    layout="wide",
)

DB_PATH = "pension_education.db"


# =========================================================
# 디자인: 깔끔한 네이비·민트 톤
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #F6F8FB 0%, #EEF5F6 52%, #FAFBFC 100%);
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
    border-radius: 30px;
    box-shadow: 0 18px 42px rgba(31, 58, 95, 0.18);
    margin-bottom: 24px;
    border: 1px solid rgba(255, 255, 255, 0.12);
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
    max-width: 1080px;
}

.section {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid #DDE8EC;
    border-radius: 25px;
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
    line-height: 1.76;
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
    line-height: 1.82;
    margin-top: 12px;
}

.type-card {
    background: #FFFFFF;
    border-radius: 18px;
    border: 1px solid #DDE8EC;
    box-shadow: 0 8px 20px rgba(31, 58, 95, 0.06);
    padding: 16px 17px;
    min-height: 150px;
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


def has_final_consonant(word: str) -> bool:
    """한글 마지막 글자의 받침 여부를 확인합니다."""
    if not word:
        return False
    last = str(word)[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return (code - 0xAC00) % 28 != 0
    return False


def subject_josa(word: str) -> str:
    """이/가"""
    return "이" if has_final_consonant(word) else "가"


def topic_josa(word: str) -> str:
    """은/는"""
    return "은" if has_final_consonant(word) else "는"


def chart_style(fig, height=450, legend=True):
    fig.update_layout(
        height=height,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.72)",
        margin=dict(l=35, r=70, t=58, b=35),
        font=dict(family="Noto Sans KR, sans-serif", size=13, color="#243447"),
        title=dict(font=dict(size=19, color="#1F2E46")),
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
    fig.update_xaxes(showgrid=True, gridcolor="rgba(43, 92, 123, 0.13)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(43, 92, 123, 0.13)", zeroline=False)
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

df["연금지표1천단위당교육참여"] = (
    df["교육참여인원"] / df["노령연금수급자수"] * 1000
).replace([float("inf"), -float("inf")], 0).fillna(0)

df["연금지표1만단위당교육횟수"] = (
    df["교육횟수"] / df["노령연금수급자수"] * 10000
).replace([float("inf"), -float("inf")], 0).fillna(0)


# 지역 유형화
avg_participants = df["교육참여인원"].mean()
avg_recipients = df["노령연금수급자수"].mean()

def classify(row):
    if row["교육참여인원"] >= avg_participants and row["노령연금수급자수"] >= avg_recipients:
        return "행동연계형"
    elif row["교육참여인원"] >= avg_participants and row["노령연금수급자수"] < avg_recipients:
        return "참여우수형"
    elif row["교육참여인원"] < avg_participants and row["노령연금수급자수"] >= avg_recipients:
        return "전환필요형"
    else:
        return "기초관리형"

df["지역유형"] = df.apply(classify, axis=1)

# 분석 해석용 데이터
# '기타'는 여러 지역이 묶인 보조 범주이므로, 1위·최상위·최하위 해석에서는 제외합니다.
df_interpret = df[df["지역본부_표시"] != "기타"].copy()
if df_interpret.empty:
    df_interpret = df.copy()

# 주요값 자동 추출: 기타 제외 기준
top_edu_count = df_interpret.sort_values("교육횟수", ascending=False).iloc[0]
low_edu_count = df_interpret.sort_values("교육횟수", ascending=True).iloc[0]
top_participant = df_interpret.sort_values("교육참여인원", ascending=False).iloc[0]
top_demand = df_interpret.sort_values("노령연금수급자수", ascending=False).iloc[0]
top_efficiency = df_interpret.sort_values("교육효율성", ascending=False).iloc[0]

# 결론용 지역 사례 자동 추출: 기타 제외 기준
# 1) 교육 효율성이 가장 높은 지역: 우수 운영·벤치마킹 후보
case_efficiency = df_interpret.sort_values("교육효율성", ascending=False).iloc[0]

# 2) 교육횟수는 많지만 1회당 참여 효율성이 낮은 지역: 효율성 개선 후보
case_low_eff_among_high_supply = (
    df_interpret[df_interpret["교육횟수"] >= df_interpret["교육횟수"].mean()]
    .sort_values("교육효율성", ascending=True)
)
if case_low_eff_among_high_supply.empty:
    case_low_efficiency = df_interpret.sort_values("교육효율성", ascending=True).iloc[0]
else:
    case_low_efficiency = case_low_eff_among_high_supply.iloc[0]

# 3) 연금 관련 지표가 가장 큰 지역: 행동연계/수요 집중 지역
case_high_indicator = df_interpret.sort_values("노령연금수급자수", ascending=False).iloc[0]

# 4) 연금 관련 지표는 큰 편이지만 교육참여가 평균보다 낮은 지역: 참여 전환 필요 후보
case_conversion_candidates = df_interpret[
    (df_interpret["노령연금수급자수"] >= df_interpret["노령연금수급자수"].mean()) &
    (df_interpret["교육참여인원"] < df_interpret["교육참여인원"].mean())
].copy()
if case_conversion_candidates.empty:
    case_conversion = df_interpret.sort_values("연금지표1천단위당교육참여", ascending=True).iloc[0]
else:
    case_conversion = case_conversion_candidates.sort_values("연금지표1천단위당교육참여", ascending=True).iloc[0]


# =========================================================
# Hero
# =========================================================
st.markdown("""
<div class="hero">
    <h1>노후준비교육은 실제 노후준비 행동으로 이어질까?</h1>
    <p>
        <b>지역별 노후준비교육 현황과 연금 관련 지표를 활용한 탐색적 분석</b><br>
        한국 사회는 빠르게 고령화되고 있으며, 오래 사는 시대가 되면서 노후 준비는 개인의 선택을 넘어 중요한 사회적 과제가 되고 있습니다.
        본 대시보드는 국민연금공단의 노후준비교육 데이터와 지역별 연금 관련 지표를 결합하여,
        교육 공급이 실제 참여로 이어지는지, 그리고 교육 참여가 연금 관련 준비 지표와 어떤 관계를 보이는지 분석합니다.
        단, 본 분석은 노후준비 행동 전체를 단정하는 것이 아니라, 연금 관련 지표를 노후준비 행동의 하나의 대리 지표로 활용한 탐색적 분석입니다.
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
<div class="result">
<b>해석 유의</b><br>
연금 관련 행동 지표 합계는 실제 인구 수나 노후준비 행동 전체를 의미하지 않습니다.
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
<b>노후준비교육은 실제 노후준비 행동과 연결되어 있을까?</b><br>
한국 사회는 빠르게 고령화되고 있으며, 기대수명이 길어지면서 은퇴 이후의 삶은 과거보다 훨씬 길어졌습니다.
이에 따라 노후 준비의 중요성은 지속적으로 커지고 있지만, 많은 사람들은 노후 준비의 필요성을 인식하면서도 실제 행동으로 옮기지는 못하고 있습니다.<br><br>
국민연금공단은 이러한 문제를 해결하기 위해 노후준비교육을 운영하며 국민들의 재무적 노후 준비를 지원하고 있습니다.
하지만 교육이 제공된다고 해서 반드시 사람들이 교육에 참여하는 것은 아니며, 교육에 참여했다고 해서 실제 노후준비 행동으로 이어진다고 단정할 수도 없습니다.<br><br>
특히 현재 노후준비교육의 성과는 교육횟수나 참여인원 중심으로 평가되는 경우가 많습니다.
그러나 이러한 지표는 교육이 실제 행동 변화와 어떤 관계를 가지는지 충분히 보여주지 못한다는 한계가 있습니다.
예를 들어 교육이 활발하게 운영되는 지역이라도 참여 효율이 낮을 수 있으며, 반대로 교육 참여가 높은 지역이라도 연금 관련 준비 지표가 기대만큼 높지 않을 수 있습니다.<br><br>
본 프로젝트는 국민연금공단의 노후준비교육 데이터와 지역별 연금 관련 데이터를 결합하여
<b>교육 공급 → 교육 참여 → 연금 관련 준비 지표</b>의 관계를 분석합니다.
이를 통해 노후준비교육이 실제 행동으로 이어지는 과정에서 어떤 한계가 존재하는지 탐색하고,
보다 효과적인 노후준비 지원 정책과 개인 맞춤형 서비스 방향을 제안하고자 합니다.
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
<span>지역별 노령연금 수급 규모와 수급금액을 사용하여 노후준비 행동을 간접적으로 파악하는 대리 지표로 활용했습니다.</span>
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
본 분석은 <b>교육 공급(교육횟수)</b>, <b>교육 참여(교육참여인원)</b>, <b>연금 관련 행동 지표(노령연금 수급 규모)</b>를 단계적으로 비교합니다.
이를 통해 “교육을 많이 제공하면 실제 참여도 높아질까?”, “교육 참여가 높은 지역은 연금 관련 지표도 높게 나타날까?”라는 질문을 검증합니다.
다만 본 분석은 교육이 직접적으로 연금 관련 행동을 유발했다고 주장하는 것이 아니라,
지역 단위 데이터에서 나타나는 <b>관계와 패턴을 탐색</b>하는 데 목적이 있습니다.
즉, 교육의 효과를 단정하기보다 교육 이후 행동 전환이 어디에서 막히는지 확인하는 데 초점을 둡니다.
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
노후준비교육은 전국에 동일한 수준으로 공급되지 않았습니다.
이는 교육 서비스가 제도적으로 존재하는 것만으로는 충분하지 않으며, 지역별로 교육 접근 기회 자체가 다르게 형성될 수 있음을 의미합니다.
다만 이 차이를 특정 지역의 우수성이나 부족함으로 단정하기보다는, 교육 공급이 지역본부별 운영 역량, 교육 인프라, 행정적 우선순위의 영향을 받는 구조적 결과로 해석할 필요가 있습니다.
따라서 이후 분석에서는 단순히 “교육을 많이 했는가”가 아니라, 그 교육이 실제 참여로 이어졌는지, 그리고 연금 관련 준비 지표와 어떤 관계를 보이는지 함께 확인해야 합니다.
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
    max_participants = df["교육참여인원"].max()
    fig2.update_layout(
        title="교육횟수와 교육참여인원 비교",
        yaxis=dict(title="교육횟수"),
        yaxis2=dict(
            title="교육참여인원",
            overlaying="y",
            side="right",
            range=[0, max_participants * 1.18],
            tickvals=[0, 5000, 10000, 15000, 20000],
            ticktext=["0", "5천", "1만", "1.5만", "2만"],
            showgrid=False,
        ),
        legend=dict(orientation="h"),
    )
    fig2 = chart_style(fig2, height=540)
    fig2.update_layout(margin=dict(l=45, r=85, t=58, b=45))
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
    fig3 = chart_style(fig3, height=540, legend=False)
    st.plotly_chart(fig3, use_container_width=True)

show_sql(sql_efficiency, "차트 SQL 보기")

st.markdown(f"""
<div class="result">
<b>결과</b><br>
※ 아래 결과 해석은 여러 지역이 묶인 ‘기타’를 제외한 주요 지역본부 기준입니다.<br>
교육횟수가 가장 많은 지역과 교육참여인원이 가장 많은 지역은 일치하지 않았습니다.
또한 교육 1회당 평균 참여인원을 기준으로 보면 <b>{top_efficiency['지역본부_표시']}</b>{subject_josa(top_efficiency['지역본부_표시'])} 가장 높게 나타났습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
교육 공급이 증가하면 참여도 함께 증가할 것이라는 예상과 달리, 교육횟수와 교육참여인원은 완전히 비례하지 않았습니다.
특히 <b>광주</b>는 교육횟수 기준으로 최상위 지역이 아님에도 교육 1회당 평균 참여인원이 가장 높게 나타났습니다.
이는 교육 성과가 단순한 공급량보다 <b>교육 운영 방식, 홍보 전략, 접근성, 프로그램 구성</b>에 의해 결정될 수 있음을 보여줍니다.
따라서 노후준비교육 정책은 교육횟수 확대에만 집중하기보다, 광주처럼 참여 효율성이 높은 지역의 운영 방식을 분석하고 <b>우수 운영 사례를 다른 지역으로 확산</b>하는 방향으로 발전할 필요가 있습니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 04 연금 관련 준비 지표 현황
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">04. 연금 관련 준비 수준은 지역별로 차이가 있을까?</div>', unsafe_allow_html=True)
st.markdown("""
<div class="question-box">
<b>질문</b> 노령연금 수급 규모를 기준으로 볼 때, 어느 지역의 연금 관련 준비 지표가 가장 클까?
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
    color_continuous_scale="Teal",
    title="지역본부별 연금 관련 지표",
    labels={"지역본부_표시": "지역본부", "노령연금수급자수": "연금 관련 지표"},
)
fig4.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
fig4.update_layout(coloraxis_showscale=False)
fig4 = chart_style(fig4, height=470, legend=False)
st.plotly_chart(fig4, use_container_width=True)
show_sql(sql_demand, "차트 SQL 보기")

st.markdown(f"""
<div class="result">
<b>결과</b><br>
※ 아래 결과 해석은 여러 지역이 묶인 ‘기타’를 제외한 주요 지역본부 기준입니다.<br>
노령연금 수급 규모가 가장 큰 지역은 <b>{top_demand['지역본부_표시']}</b>입니다.
이는 연금 관련 준비 지표가 전국에 균등하게 분포하지 않고 특정 지역에 집중되어 있음을 보여줍니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
연금 관련 지표는 지역별로 큰 차이를 보였으며, 이는 노후준비와 관련된 행동 또는 결과가 모든 지역에서 동일하게 나타나지 않음을 의미합니다.
다만 연금 관련 지표는 노후준비 행동 전체를 직접 측정하는 값이 아니라, 연금이라는 한 영역을 통해 노후준비 수준을 간접적으로 파악하기 위한 대리 지표입니다.
따라서 이 결과는 “어느 지역이 더 잘 준비했다”는 단정이 아니라, 교육 참여 수준과 비교해 볼 필요가 있는 <b>연금 관련 준비 지표의 지역 차이</b>로 해석하는 것이 적절합니다.
이 차이를 교육참여 데이터와 함께 보면, 교육이 실제 행동 지표와 어떻게 연결되는지에 대한 더 의미 있는 질문을 만들 수 있습니다.
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 05 공급과 수요 관계
# =========================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="section-title">05. 교육 참여는 연금 관련 행동 지표와 연결될까?</div>', unsafe_allow_html=True)
st.markdown("""
<div class="question-box">
<b>질문</b> 연금 관련 지표가 큰 지역일수록 노후준비교육 참여도 높게 나타날까?
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
fig5 = chart_style(fig5, height=580, legend=False)
fig5.update_xaxes(range=[0, df["노령연금수급자수"].max() * 1.12])
fig5.update_yaxes(range=[0, df["교육참여인원"].max() * 1.18])
fig5.update_layout(margin=dict(l=45, r=95, t=58, b=45))
st.plotly_chart(fig5, use_container_width=True)
show_sql(sql_relation, "차트 SQL 보기")

st.markdown("""
<div class="result">
<b>결과</b><br>
노령연금 수급 규모가 큰 지역이 반드시 교육참여인원도 가장 높은 것은 아니었습니다.
수급 규모가 큰 지역에서도 참여가 상대적으로 낮게 나타나는 경우가 있었고,
반대로 수급 규모가 상대적으로 작아도 높은 참여 수준을 보이는 지역이 존재했습니다.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
본 분석의 핵심 질문은 “노후준비교육 참여가 실제 연금 관련 준비 지표와 연결되는가?”입니다.
분석 결과, 교육 참여 수준과 연금 관련 지표 사이에는 단순한 비례 관계가 뚜렷하게 나타나지 않았습니다.
특히 <b>경인</b>은 연금 관련 지표가 가장 큰 지역임에도 교육참여 수준이 압도적으로 높지는 않았습니다.
이는 노후준비와 관련된 잠재 수요가 존재한다고 해서 교육 참여가 자동으로 발생하지는 않는다는 점을 보여줍니다.
따라서 경인과 같이 연금 관련 지표가 큰 지역은 단순한 공급 확대보다, <b>수요층을 교육으로 연결하는 전략</b>이 중요합니다.
교육 이후 실제 행동 변화를 유도하기 위해서는 교육 제공에서 끝나는 것이 아니라, 개인별 상황에 맞춘 상담, 후속 점검, 의사결정 도구가 함께 필요합니다.
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
fig6.add_vline(x=avg_recipients, line_dash="dash", line_color="#667085")
fig6.add_hline(y=avg_participants, line_dash="dash", line_color="#667085")
fig6.update_traces(textposition="top center", marker=dict(opacity=0.86, line=dict(width=1, color="white")))
fig6 = chart_style(fig6, height=640, legend=True)
fig6.update_xaxes(range=[0, df["노령연금수급자수"].max() * 1.12])
fig6.update_yaxes(range=[0, df["교육참여인원"].max() * 1.18])
fig6.update_layout(margin=dict(l=45, r=95, t=58, b=45))
st.plotly_chart(fig6, use_container_width=True)
show_sql(sql_type, "지역 유형화 SQL 보기")

tc1, tc2, tc3, tc4 = st.columns(4)
tc1.markdown('<div class="type-card"><b>행동연계형</b><span>교육 참여와 연금 관련 지표가 모두 높은 지역입니다. 교육과 행동 지표가 함께 나타나는 우수 사례로 볼 수 있습니다.</span></div>', unsafe_allow_html=True)
tc2.markdown('<div class="type-card"><b>참여우수형</b><span>교육 참여는 높지만 연금 관련 지표는 상대적으로 낮은 지역입니다. 교육 이후 행동 전환을 높이는 후속 지원이 필요합니다.</span></div>', unsafe_allow_html=True)
tc3.markdown('<div class="type-card"><b>전환필요형</b><span>연금 관련 지표는 높지만 교육 참여가 낮은 지역입니다. 기존 준비 행동은 존재하나 교육 참여로 연결되지 않은 집단일 수 있습니다.</span></div>', unsafe_allow_html=True)
tc4.markdown('<div class="type-card"><b>기초관리형</b><span>교육 참여와 연금 관련 지표가 모두 낮은 지역입니다. 기초 홍보와 접근성 개선이 우선 필요한 지역입니다.</span></div>', unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>인사이트</b><br>
지역을 단순히 교육횟수나 참여인원 순위로만 비교하면 정책적 의미를 찾기 어렵습니다.
교육 참여와 연금 관련 지표를 함께 고려하면, 지역별로 서로 다른 개입 전략을 설계할 수 있습니다.
<b>행동연계형</b>은 교육 참여와 연금 관련 지표가 함께 높은 지역으로, 현재의 교육 운영 방식을 우수 사례로 검토할 수 있습니다.
<b>참여우수형</b>은 교육 참여는 높지만 연금 관련 지표가 상대적으로 낮은 지역으로, 교육 이후 실제 행동 전환을 지원하는 후속 서비스가 필요합니다.
<b>전환필요형</b>은 연금 관련 지표는 높지만 교육 참여가 낮은 지역으로, 기존 준비 행동은 존재하나 교육 서비스와 연결되지 않은 집단일 가능성이 있으므로 홍보와 접근성 개선이 필요합니다.
<b>기초관리형</b>은 교육 참여와 연금 관련 지표가 모두 낮은 지역으로, 기초적인 인식 개선과 교육 접근성 확대가 우선되어야 합니다.
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
이번 분석은 노후준비교육의 공급 규모와 참여 수준, 그리고 연금 관련 지표가 반드시 함께 증가하지는 않는다는 사실을 보여주었습니다.<br><br>
첫째, 교육 공급량이 많다고 해서 참여가 높아지는 것은 아니었습니다. 이는 노후준비교육의 성과가 단순한 공급 확대보다 <b>참여 전환 과정</b>에 의해 결정될 수 있음을 시사합니다.<br>
둘째, 연금 관련 지표가 높은 지역에서도 교육 참여 수준은 다양하게 나타났습니다. 이는 노후준비 수요가 존재하더라도 실제 교육 참여로 연결되기 위해서는 별도의 접근 전략이 필요함을 의미합니다.<br>
셋째, 지역 유형화 결과 각 지역은 서로 다른 특성을 보였습니다. 따라서 향후 노후준비교육 정책은 전국 단일 방식의 공급 확대보다 <b>지역 유형에 따른 차별화된 운영 전략</b>이 필요합니다.<br><br>
결국 본 분석은 노후준비교육의 양적 확대보다 <b>교육 이후 행동 전환을 지원하는 전략</b>이 중요함을 보여줍니다.
앞으로의 노후준비 정책은 “얼마나 많은 교육을 제공했는가”가 아니라, <b>얼마나 많은 사람이 실제 준비 행동으로 이어졌는가</b>를 평가하는 방향으로 발전할 필요가 있습니다.
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title" style="font-size:20px; margin-top:22px;">지역별 결론: 어느 지역에 어떤 전략이 필요할까?</div>', unsafe_allow_html=True)

r1, r2 = st.columns(2)

with r1:
    st.markdown(f"""
<div class="type-card">
<b>{case_efficiency['지역본부_표시']} · 우수 운영 사례</b>
<span>
{case_efficiency['지역본부_표시']}{topic_josa(case_efficiency['지역본부_표시'])} 교육횟수 기준으로 최상위 지역은 아니지만, 교육 1회당 평균 참여인원이 <b>{case_efficiency['교육효율성']:.1f}명</b>으로 가장 높게 나타났습니다.
이는 교육 성과가 공급량보다 운영 방식에 의해 결정될 수 있음을 보여줍니다.
따라서 이 지역은 <b>우수 운영 사례 확산을 위한 벤치마킹 대상</b>으로 활용할 수 있습니다.
</span>
</div>
""", unsafe_allow_html=True)

with r2:
    st.markdown(f"""
<div class="type-card">
<b>{case_low_efficiency['지역본부_표시']} · 교육 효율성 개선 필요</b>
<span>
{case_low_efficiency['지역본부_표시']}{topic_josa(case_low_efficiency['지역본부_표시'])} 교육 공급이 많은 편이지만, 교육 1회당 평균 참여인원은 <b>{case_low_efficiency['교육효율성']:.1f}명</b> 수준으로 나타났습니다.
이는 교육을 많이 제공해도 참여가 충분히 따라오지 않을 수 있음을 보여줍니다.
따라서 추가적인 교육 확대보다 <b>교육 대상자 선정, 홍보 방식, 프로그램 구성 개선</b>을 통해 참여 효율성을 높이는 전략이 필요합니다.
</span>
</div>
""", unsafe_allow_html=True)

r3, r4 = st.columns(2)

with r3:
    st.markdown(f"""
<div class="type-card">
<b>{case_high_indicator['지역본부_표시']} · 연금 관련 지표 집중 지역</b>
<span>
{case_high_indicator['지역본부_표시']}{topic_josa(case_high_indicator['지역본부_표시'])} 연금 관련 지표가 가장 크게 나타난 지역입니다.
그러나 연금 관련 지표 규모에 비해 교육참여 수준이 압도적으로 높지는 않아, 수요가 존재한다고 해서 교육 참여가 자동으로 발생하지 않음을 보여줍니다.
따라서 이 지역은 공급 확대보다 <b>수요층을 교육으로 연결하는 홍보·상담·후속 관리 전략</b>이 중요합니다.
</span>
</div>
""", unsafe_allow_html=True)

with r4:
    st.markdown(f"""
<div class="type-card">
<b>{case_conversion['지역본부_표시']} · 참여 전환 전략 필요</b>
<span>
{case_conversion['지역본부_표시']}{topic_josa(case_conversion['지역본부_표시'])} 연금 관련 지표 대비 교육 참여 수준을 더 끌어올릴 필요가 있는 지역으로 볼 수 있습니다.
이미 노후준비와 관련된 기반은 존재할 수 있지만, 교육 서비스와 충분히 연결되지 않았을 가능성이 있습니다.
따라서 <b>온라인 교육 확대, 지역 맞춤형 홍보, 접근성 개선</b>을 통해 잠재 수요를 실제 교육 참여로 전환하는 전략이 필요합니다.
</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="insight">
<b>종합 서비스 제안</b><br>
지역별 분석은 교육 자원을 어디에, 어떤 방식으로 배분할지에 대한 방향을 제시합니다.
그러나 같은 지역 안에서도 개인의 소득, 자산, 저축액, 예상 연금 수준은 크게 다릅니다.
따라서 집단 교육과 함께 <b>개인 맞춤형 노후 재무 시뮬레이션 서비스</b>를 제공한다면,
사용자가 자신의 현재 소득·자산·월 저축액·예상 연금을 바탕으로 미래 자산 변화와 노후 준비 부족 구간을 직접 확인할 수 있습니다.
즉, 지역 단위 분석은 교육 정책의 우선순위를 제시하고, 개인 맞춤형 서비스는 교육 이후 실제 노후준비 행동으로 이어지도록 돕는 보완적 의사결정 지원 도구가 될 수 있습니다.
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
