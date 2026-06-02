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
    page_title="노후준비교육 × 연금 수급 분석",
    page_icon="📊",
    layout="wide",
)

DB_PATH = "pension_education.db"


# =========================================================
# 디자인 설정
# =========================================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #f5f7fb 0%, #eef3f8 45%, #f9fafc 100%);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3.5rem;
        max-width: 1320px;
    }

    .hero {
        background: linear-gradient(135deg, #23395d 0%, #3f5f8f 48%, #8aa6c8 100%);
        padding: 34px 38px;
        border-radius: 28px;
        color: white;
        box-shadow: 0 18px 45px rgba(34, 57, 93, 0.18);
        margin-bottom: 22px;
    }

    .hero-title {
        font-size: 34px;
        font-weight: 800;
        letter-spacing: -0.7px;
        margin-bottom: 10px;
    }

    .hero-sub {
        font-size: 16px;
        line-height: 1.75;
        opacity: 0.92;
        max-width: 980px;
    }

    .section-card {
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid rgba(218, 225, 235, 0.9);
        border-radius: 24px;
        padding: 22px 24px;
        box-shadow: 0 10px 30px rgba(34, 57, 93, 0.07);
        margin-bottom: 18px;
    }

    .mini-title {
        font-size: 19px;
        font-weight: 800;
        color: #26364f;
        margin-bottom: 4px;
    }

    .mini-sub {
        color: #69778c;
        font-size: 14px;
        line-height: 1.55;
        margin-bottom: 12px;
    }

    .insight {
        background: #fff7df;
        border: 1px solid #f1dfaa;
        border-left: 6px solid #d8a31f;
        padding: 16px 18px;
        border-radius: 16px;
        color: #3f3a2a;
        line-height: 1.7;
        font-size: 14.5px;
        margin-top: 12px;
    }

    .strategy-card {
        border-radius: 18px;
        padding: 16px 17px;
        min-height: 132px;
        background: white;
        border: 1px solid #e6ebf2;
        box-shadow: 0 8px 22px rgba(34, 57, 93, 0.06);
    }

    .strategy-card b {
        display: block;
        font-size: 16px;
        margin-bottom: 8px;
        color: #24324b;
    }

    .strategy-card span {
        color: #66758b;
        font-size: 13.5px;
        line-height: 1.6;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid #e5ebf3;
        padding: 18px 18px;
        border-radius: 20px;
        box-shadow: 0 8px 24px rgba(34, 57, 93, 0.06);
    }

    div[data-testid="stMetricLabel"] {
        color: #66758b;
        font-size: 13px;
    }

    div[data-testid="stMetricValue"] {
        color: #24324b;
        font-size: 25px;
        font-weight: 800;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(255,255,255,0.55);
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
        background: #263f68 !important;
        color: white !important;
        border: 1px solid #263f68;
    }
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# DB 함수
# =========================================================
@st.cache_data(show_spinner=False)
def load_data(query: str) -> pd.DataFrame:
    if not os.path.exists(DB_PATH):
        st.error(f"데이터베이스 파일 `{DB_PATH}`을 찾을 수 없습니다. app.py와 같은 폴더에 DB 파일을 넣어 주세요.")
        st.stop()

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def show_sql(sql: str, label: str = "사용한 SQL 보기") -> None:
    with st.expander(label):
        st.code(sql.strip(), language="sql")


def to_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def clean_region_name(name: str) -> str:
    return str(name).replace("지역본부", "").replace("본부", "본부").strip()


def apply_chart_style(fig, height=420, show_legend=True):
    fig.update_layout(
        height=height,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.55)",
        margin=dict(l=20, r=20, t=55, b=25),
        font=dict(family="Noto Sans KR, sans-serif", size=13, color="#2b3445"),
        title=dict(font=dict(size=19, color="#26364f")),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.65)",
        ),
        showlegend=show_legend,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(120,130,150,0.16)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(120,130,150,0.16)", zeroline=False)
    return fig


# =========================================================
# 데이터 불러오기 및 전처리
# =========================================================
sql_main = """
SELECT *
FROM education_pension;
"""

df = load_data(sql_main)

numeric_cols = [
    "교육횟수",
    "교육참여인원",
    "노령연금수급자수",
    "노령연금금액",
    "장애연금수급자수",
    "유족연금수급자수",
]
df = to_numeric(df, numeric_cols)

df["지역본부_표시"] = df["지역본부"].apply(clean_region_name)

df["수급자_1천명당_교육참여인원"] = (
    df["교육참여인원"] / df["노령연금수급자수"] * 1000
).replace([float("inf"), -float("inf")], 0).fillna(0)

df["1회당_평균참여인원"] = (
    df["교육참여인원"] / df["교육횟수"]
).replace([float("inf"), -float("inf")], 0).fillna(0)

df["연금수급자_대비_교육참여율"] = (
    df["교육참여인원"] / df["노령연금수급자수"] * 100
).replace([float("inf"), -float("inf")], 0).fillna(0)


# 유형화
avg_edu = df["교육참여인원"].mean()
avg_rec = df["노령연금수급자수"].mean()

def classify(row):
    if row["교육참여인원"] >= avg_edu and row["노령연금수급자수"] >= avg_rec:
        return "핵심 관리형"
    if row["교육참여인원"] >= avg_edu and row["노령연금수급자수"] < avg_rec:
        return "교육 집중형"
    if row["교육참여인원"] < avg_edu and row["노령연금수급자수"] >= avg_rec:
        return "교육 확대 필요형"
    return "기초 수요 확인형"

df_type = df.copy()
df_type["지역유형"] = df_type.apply(classify, axis=1)


# =========================================================
# 헤더
# =========================================================
st.markdown(
    """
<div class="hero">
    <div class="hero-title">노후준비교육 × 연금 수급 데이터 분석</div>
    <div class="hero-sub">
        지역본부별 노후준비교육 현황과 지역별 연금 수급자 데이터를 SQLite로 통합하고,
        수급 규모 대비 교육 참여 수준을 비교하여 <b>노후준비 서비스의 우선 확대 지역</b>을 도출하는
        데이터 기반 의사결정 대시보드입니다.
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# KPI
# =========================================================
total_participants = int(df["교육참여인원"].sum())
total_recipients = int(df["노령연금수급자수"].sum())
avg_ratio = df["수급자_1천명당_교육참여인원"].mean()
top_priority = df_type[df_type["지역유형"] == "교육 확대 필요형"]

if not top_priority.empty:
    priority_region = top_priority.sort_values("노령연금수급자수", ascending=False).iloc[0]["지역본부_표시"]
else:
    priority_region = df.sort_values("수급자_1천명당_교육참여인원").iloc[0]["지역본부_표시"]

k1, k2, k3, k4 = st.columns(4)
k1.metric("총 교육 참여 인원", f"{total_participants:,.0f}명")
k2.metric("총 노령연금 수급자", f"{total_recipients:,.0f}명")
k3.metric("수급자 1천 명당 교육 참여", f"{avg_ratio:,.1f}명")
k4.metric("우선 점검 지역", priority_region)


st.markdown("")


# =========================================================
# 탭 구성
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📌 한눈에 보기", "🔍 수요 대비 교육 접근성", "🧭 전략 유형화", "🗂️ SQL & 데이터"]
)


# =========================================================
# Tab 1. 핵심 현황
# =========================================================
with tab1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="mini-title">지역별 교육 공급과 연금 수급 수요 비교</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mini-sub">교육 참여 인원과 노령연금 수급자 수를 나란히 비교하여, 지역별 서비스 규모와 잠재 수요를 함께 확인합니다.</div>',
        unsafe_allow_html=True,
    )

    sql_1 = """
    SELECT
        지역본부,
        교육참여인원
    FROM education_pension
    ORDER BY 교육참여인원 DESC;
    """

    sql_2 = """
    SELECT
        지역본부,
        노령연금수급자수
    FROM education_pension
    ORDER BY 노령연금수급자수 DESC;
    """

    df1 = load_data(sql_1)
    df2 = load_data(sql_2)
    df1 = to_numeric(df1, ["교육참여인원"])
    df2 = to_numeric(df2, ["노령연금수급자수"])
    df1["지역본부_표시"] = df1["지역본부"].apply(clean_region_name)
    df2["지역본부_표시"] = df2["지역본부"].apply(clean_region_name)

    c1, c2 = st.columns(2)

    with c1:
        fig1 = px.bar(
            df1.sort_values("교육참여인원", ascending=True),
            x="교육참여인원",
            y="지역본부_표시",
            orientation="h",
            text="교육참여인원",
            color="교육참여인원",
            color_continuous_scale="Blues",
            title="지역본부별 노후준비교육 참여 인원",
        )
        fig1.update_traces(texttemplate="%{text:,.0f}명", textposition="outside", cliponaxis=False)
        fig1.update_layout(coloraxis_showscale=False)
        fig1 = apply_chart_style(fig1, height=430, show_legend=False)
        st.plotly_chart(fig1, use_container_width=True)
        show_sql(sql_1, "차트 1 SQL 보기")

    with c2:
        fig2 = px.bar(
            df2.sort_values("노령연금수급자수", ascending=False),
            x="지역본부_표시",
            y="노령연금수급자수",
            text="노령연금수급자수",
            color="노령연금수급자수",
            color_continuous_scale="Teal",
            title="지역본부별 노령연금 수급자 수",
        )
        fig2.update_traces(texttemplate="%{text:,.0f}명", textposition="outside", cliponaxis=False)
        fig2.update_layout(coloraxis_showscale=False)
        fig2 = apply_chart_style(fig2, height=430, show_legend=False)
        st.plotly_chart(fig2, use_container_width=True)
        show_sql(sql_2, "차트 2 SQL 보기")

    st.markdown(
        """
<div class="insight">
<b>인사이트</b><br>
단순히 교육 참여 인원만 비교하면 교육이 활발한 지역만 보이지만,
노령연금 수급자 수와 함께 보면 <b>교육 공급 규모와 실제 수요 규모가 맞게 대응되는지</b> 판단할 수 있습니다.
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Tab 2. 관계 분석
# =========================================================
with tab2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="mini-title">수급 규모 대비 교육 접근성 분석</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mini-sub">노령연금 수급자 수가 많은 지역일수록 교육 참여도 함께 높은지, 그리고 수급자 규모를 보정했을 때 어느 지역의 접근성이 높은지 확인합니다.</div>',
        unsafe_allow_html=True,
    )

    sql_3 = """
    SELECT
        지역본부,
        교육참여인원,
        노령연금수급자수
    FROM education_pension;
    """

    sql_4 = """
    SELECT
        지역본부,
        교육참여인원,
        노령연금수급자수,
        ROUND(교육참여인원 * 1000.0 / 노령연금수급자수, 2) AS 수급자_1천명당_교육참여인원
    FROM education_pension
    ORDER BY 수급자_1천명당_교육참여인원 DESC;
    """

    df3 = load_data(sql_3)
    df4 = load_data(sql_4)
    df3 = to_numeric(df3, ["교육참여인원", "노령연금수급자수"])
    df4 = to_numeric(df4, ["교육참여인원", "노령연금수급자수", "수급자_1천명당_교육참여인원"])
    df3["지역본부_표시"] = df3["지역본부"].apply(clean_region_name)
    df4["지역본부_표시"] = df4["지역본부"].apply(clean_region_name)

    left, right = st.columns([1.18, 1])

    with left:
        fig3 = px.scatter(
            df3,
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
        )
        fig3.update_traces(textposition="top center", marker=dict(opacity=0.82, line=dict(width=1, color="white")))
        fig3 = apply_chart_style(fig3, height=520, show_legend=False)
        st.plotly_chart(fig3, use_container_width=True)
        show_sql(sql_3, "차트 3 SQL 보기")

    with right:
        fig4 = px.bar(
            df4.sort_values("수급자_1천명당_교육참여인원", ascending=True),
            x="수급자_1천명당_교육참여인원",
            y="지역본부_표시",
            orientation="h",
            text="수급자_1천명당_교육참여인원",
            color="수급자_1천명당_교육참여인원",
            color_continuous_scale="Purples",
            title="노령연금 수급자 1천 명당 교육 참여 인원",
            labels={
                "수급자_1천명당_교육참여인원": "수급자 1천 명당 교육 참여 인원",
                "지역본부_표시": "지역본부",
            },
        )
        fig4.update_traces(texttemplate="%{text:.1f}명", textposition="outside", cliponaxis=False)
        fig4.update_layout(coloraxis_showscale=False)
        fig4 = apply_chart_style(fig4, height=520, show_legend=False)
        st.plotly_chart(fig4, use_container_width=True)
        show_sql(sql_4, "차트 4 SQL 보기")

    st.markdown(
        """
<div class="insight">
<b>인사이트</b><br>
수급자 수가 많은 지역은 잠재적인 노후준비 서비스 수요가 큰 지역입니다.
하지만 수급자 1천 명당 교육 참여 인원이 낮다면, 단순 규모가 아니라 <b>수요 대비 교육 접근성이 낮은 지역</b>으로 해석할 수 있습니다.
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Tab 3. 전략 유형화
# =========================================================
with tab3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="mini-title">지역본부별 노후준비 서비스 전략 유형화</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mini-sub">평균 수급자 수와 평균 교육 참여 인원을 기준선으로 두고, 지역을 네 가지 서비스 전략 유형으로 분류합니다.</div>',
        unsafe_allow_html=True,
    )

    sql_5 = """
    SELECT
        지역본부,
        교육참여인원,
        노령연금수급자수,
        CASE
            WHEN 교육참여인원 >= (SELECT AVG(교육참여인원) FROM education_pension)
             AND 노령연금수급자수 >= (SELECT AVG(노령연금수급자수) FROM education_pension)
            THEN '핵심 관리형'

            WHEN 교육참여인원 >= (SELECT AVG(교육참여인원) FROM education_pension)
             AND 노령연금수급자수 < (SELECT AVG(노령연금수급자수) FROM education_pension)
            THEN '교육 집중형'

            WHEN 교육참여인원 < (SELECT AVG(교육참여인원) FROM education_pension)
             AND 노령연금수급자수 >= (SELECT AVG(노령연금수급자수) FROM education_pension)
            THEN '교육 확대 필요형'

            ELSE '기초 수요 확인형'
        END AS 지역유형
    FROM education_pension;
    """

    fig5 = px.scatter(
        df_type,
        x="노령연금수급자수",
        y="교육참여인원",
        color="지역유형",
        size="수급자_1천명당_교육참여인원",
        text="지역본부_표시",
        title="수급 규모와 교육 참여 수준에 따른 지역 유형화",
        labels={
            "노령연금수급자수": "노령연금 수급자 수",
            "교육참여인원": "교육 참여 인원",
            "지역유형": "지역 유형",
        },
        hover_data={
            "지역본부_표시": True,
            "지역유형": True,
            "수급자_1천명당_교육참여인원": ":.2f",
            "노령연금수급자수": ":,.0f",
            "교육참여인원": ":,.0f",
        },
    )

    fig5.add_vline(x=avg_rec, line_dash="dash", line_color="rgba(80,80,80,0.55)")
    fig5.add_hline(y=avg_edu, line_dash="dash", line_color="rgba(80,80,80,0.55)")

    fig5.add_annotation(
        x=avg_rec,
        y=df["교육참여인원"].max() * 1.04,
        text="평균 수급자 수",
        showarrow=False,
        font=dict(size=12, color="#596579"),
    )
    fig5.add_annotation(
        x=df["노령연금수급자수"].max() * 0.98,
        y=avg_edu,
        text="평균 교육 참여",
        showarrow=False,
        font=dict(size=12, color="#596579"),
    )

    fig5.update_traces(textposition="top center", marker=dict(opacity=0.84, line=dict(width=1, color="white")))
    fig5 = apply_chart_style(fig5, height=620, show_legend=True)

    st.plotly_chart(fig5, use_container_width=True)
    show_sql(sql_5, "차트 5 SQL 보기")

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(
            '<div class="strategy-card"><b>핵심 관리형</b><span>수급 규모와 교육 참여가 모두 높은 지역입니다. 현재 운영 수준을 유지하면서 우수사례로 활용할 수 있습니다.</span></div>',
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            '<div class="strategy-card"><b>교육 집중형</b><span>교육 참여는 높지만 수급 규모는 상대적으로 낮은 지역입니다. 교육 운영 효율성을 점검할 필요가 있습니다.</span></div>',
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            '<div class="strategy-card"><b>교육 확대 필요형</b><span>수급 규모는 크지만 교육 참여가 낮은 지역입니다. 노후준비교육 확대의 우선 후보 지역입니다.</span></div>',
            unsafe_allow_html=True,
        )
    with s4:
        st.markdown(
            '<div class="strategy-card"><b>기초 수요 확인형</b><span>수급 규모와 교육 참여가 모두 낮은 지역입니다. 홍보 확대보다 지역 특성 및 잠재 수요 확인이 우선입니다.</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        """
<div class="insight">
<b>최종 비즈니스 인사이트</b><br>
노후준비교육은 전체 지역에 동일하게 확대하기보다, <b>노령연금 수급자 수는 많지만 교육 참여가 낮은 지역</b>을 우선적으로 공략하는 것이 효과적입니다.
이 유형화는 교육 예산 배분, 지역별 홍보 전략, 상담 서비스 확대 순서를 결정하는 데 활용될 수 있습니다.
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Tab 4. SQL & 데이터
# =========================================================
with tab4:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="mini-title">데이터베이스 구축 및 분석 데이터 확인</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mini-sub">본 대시보드는 education, pension_region, region_mapping 테이블을 통합한 education_pension VIEW를 기반으로 분석합니다.</div>',
        unsafe_allow_html=True,
    )

    with st.expander("메인 VIEW 조회 SQL"):
        st.code(sql_main.strip(), language="sql")

    st.dataframe(
        df.sort_values("노령연금수급자수", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        """
<div class="insight">
<b>데이터 통합 과정</b><br>
지역별 연금 수급자 데이터는 시도·시군구 단위이고, 노후준비교육 데이터는 지역본부 단위입니다.
따라서 region_mapping 테이블을 별도로 구축하여 지역 단위를 지역본부 기준으로 정리한 뒤,
education_pension VIEW를 생성하여 분석에 활용했습니다.
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


st.caption("경영정보처리론 데이터 분석 및 시각화 프로젝트 | SQLite + Streamlit + Plotly")
