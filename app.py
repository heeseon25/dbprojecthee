import os
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="노후준비교육 × 연금 수급 데이터 분석",
    page_icon="📊",
    layout="wide"
)

DB_PATH = "pension_education.db"


# =========================
# 디자인
# =========================
st.markdown("""
<style>
    .main {
        background-color: #f7f8fb;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .title-box {
        background: linear-gradient(135deg, #eef3ff 0%, #ffffff 100%);
        padding: 28px 34px;
        border-radius: 22px;
        border: 1px solid #e4e9f5;
        box-shadow: 0 6px 22px rgba(30, 55, 100, 0.06);
        margin-bottom: 24px;
    }
    .title-text {
        font-size: 34px;
        font-weight: 800;
        color: #24324b;
        margin-bottom: 8px;
    }
    .sub-text {
        font-size: 16px;
        color: #5f6f89;
        line-height: 1.6;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 18px;
        border: 1px solid #e8ecf3;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
    }
    .insight-box {
        background-color: #fff8df;
        border-left: 5px solid #f0c94a;
        padding: 16px 18px;
        border-radius: 12px;
        color: #3d3d3d;
        line-height: 1.6;
        margin-top: 12px;
    }
    .sql-box {
        background-color: #f3f5f8;
        border-radius: 12px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# DB 함수
# =========================
@st.cache_data
def load_data(query):
    if not os.path.exists(DB_PATH):
        st.error(f"데이터베이스 파일 `{DB_PATH}`을 찾을 수 없습니다.")
        st.stop()

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def show_sql(sql):
    with st.expander("사용한 SQL 보기"):
        st.code(sql, language="sql")


# =========================
# 데이터 불러오기
# =========================
sql_main = """
SELECT *
FROM education_pension;
"""

df = load_data(sql_main)

# 숫자형 변환
numeric_cols = [
    "교육횟수",
    "교육참여인원",
    "노령연금수급자수",
    "노령연금금액",
    "장애연금수급자수",
    "유족연금수급자수"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)


# 파생지표
if "교육참여인원" in df.columns and "노령연금수급자수" in df.columns:
    df["수급자_1천명당_교육참여인원"] = (
        df["교육참여인원"] / df["노령연금수급자수"] * 1000
    ).replace([float("inf"), -float("inf")], 0).fillna(0)

if "교육횟수" in df.columns and "교육참여인원" in df.columns:
    df["1회당_평균참여인원"] = (
        df["교육참여인원"] / df["교육횟수"]
    ).replace([float("inf"), -float("inf")], 0).fillna(0)


# =========================
# 헤더
# =========================
st.markdown("""
<div class="title-box">
    <div class="title-text">노후준비교육과 연금 수급 현황 분석 대시보드</div>
    <div class="sub-text">
        지역본부별 노후준비교육 데이터와 지역별 연금 수급자 데이터를 연결하여,
        교육 자원이 실제 수급 규모와 어떻게 대응되는지 분석합니다.
        이를 통해 노후준비 서비스의 우선 확대 지역과 운영 전략을 탐색합니다.
    </div>
</div>
""", unsafe_allow_html=True)


# =========================
# 핵심 지표
# =========================
total_participants = int(df["교육참여인원"].sum())
total_recipients = int(df["노령연금수급자수"].sum())
avg_ratio = df["수급자_1천명당_교육참여인원"].mean()
top_region = df.sort_values("교육참여인원", ascending=False).iloc[0]["지역본부"]

col1, col2, col3, col4 = st.columns(4)

col1.metric("총 교육 참여 인원", f"{total_participants:,.0f}명")
col2.metric("총 노령연금 수급자 수", f"{total_recipients:,.0f}명")
col3.metric("수급자 1천 명당 평균 교육 참여", f"{avg_ratio:,.1f}명")
col4.metric("교육 참여 최상위 지역", top_region)


st.divider()


# =========================
# 차트 1
# =========================
st.header("1. 어느 지역본부에서 노후준비교육 참여가 가장 활발할까?")

sql_1 = """
SELECT
    지역본부,
    교육참여인원
FROM education_pension
ORDER BY 교육참여인원 DESC;
"""

df1 = load_data(sql_1)
df1["교육참여인원"] = pd.to_numeric(df1["교육참여인원"], errors="coerce")

fig1 = px.bar(
    df1,
    x="교육참여인원",
    y="지역본부",
    orientation="h",
    text="교육참여인원",
    title="지역본부별 노후준비교육 참여 인원"
)
fig1.update_layout(
    yaxis={"categoryorder": "total ascending"},
    plot_bgcolor="white",
    paper_bgcolor="white",
    title_font_size=20,
    height=430
)
fig1.update_traces(texttemplate="%{text:,.0f}명", textposition="outside")

st.plotly_chart(fig1, use_container_width=True)
show_sql(sql_1)

st.markdown("""
<div class="insight-box">
<b>인사이트</b><br>
지역본부별 교육 참여 인원을 비교하면 노후준비교육 서비스가 어느 지역에 집중되어 있는지 확인할 수 있습니다.
참여 인원이 높은 지역은 기존 교육 수요가 이미 형성된 곳으로 볼 수 있고, 낮은 지역은 추가 홍보나 접근성 개선이 필요한 후보 지역으로 볼 수 있습니다.
</div>
""", unsafe_allow_html=True)


st.divider()


# =========================
# 차트 2
# =========================
st.header("2. 노령연금 수급자 규모가 큰 지역은 어디일까?")

sql_2 = """
SELECT
    지역본부,
    노령연금수급자수
FROM education_pension
ORDER BY 노령연금수급자수 DESC;
"""

df2 = load_data(sql_2)
df2["노령연금수급자수"] = pd.to_numeric(df2["노령연금수급자수"], errors="coerce")

fig2 = px.bar(
    df2,
    x="지역본부",
    y="노령연금수급자수",
    text="노령연금수급자수",
    title="지역본부별 노령연금 수급자 수"
)
fig2.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    title_font_size=20,
    height=430
)
fig2.update_traces(texttemplate="%{text:,.0f}명", textposition="outside")

st.plotly_chart(fig2, use_container_width=True)
show_sql(sql_2)

st.markdown("""
<div class="insight-box">
<b>인사이트</b><br>
노령연금 수급자 수는 해당 지역의 고령층 및 연금 수급 수요 규모를 보여주는 지표입니다.
교육 참여 인원만 보는 것이 아니라 수급자 규모와 함께 보면, 교육 자원이 실제 수요 규모에 맞게 배분되고 있는지 판단할 수 있습니다.
</div>
""", unsafe_allow_html=True)


st.divider()


# =========================
# 차트 3
# =========================
st.header("3. 교육 참여가 많은 지역은 연금 수급 규모도 클까?")

sql_3 = """
SELECT
    지역본부,
    교육참여인원,
    노령연금수급자수
FROM education_pension;
"""

df3 = load_data(sql_3)
df3["교육참여인원"] = pd.to_numeric(df3["교육참여인원"], errors="coerce")
df3["노령연금수급자수"] = pd.to_numeric(df3["노령연금수급자수"], errors="coerce")

fig3 = px.scatter(
    df3,
    x="노령연금수급자수",
    y="교육참여인원",
    text="지역본부",
    size="교육참여인원",
    title="노령연금 수급자 수와 교육 참여 인원의 관계"
)
fig3.update_traces(textposition="top center")
fig3.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    title_font_size=20,
    height=500
)

st.plotly_chart(fig3, use_container_width=True)
show_sql(sql_3)

st.markdown("""
<div class="insight-box">
<b>인사이트</b><br>
이 산점도는 연금 수급 규모가 큰 지역에서 실제 교육 참여도 함께 높게 나타나는지 보여줍니다.
만약 수급자 수는 많지만 교육 참여가 낮은 지역이 있다면, 해당 지역은 노후준비교육 확대의 우선 대상이 될 수 있습니다.
</div>
""", unsafe_allow_html=True)


st.divider()


# =========================
# 차트 4: 수급자 1천 명당 교육 참여
# =========================
st.header("4. 수급자 규모를 고려하면 어느 지역의 교육 접근성이 높을까?")

sql_4 = """
SELECT
    지역본부,
    교육참여인원,
    노령연금수급자수,
    ROUND(교육참여인원 * 1000.0 / 노령연금수급자수, 2) AS 수급자_1천명당_교육참여인원
FROM education_pension
ORDER BY 수급자_1천명당_교육참여인원 DESC;
"""

df4 = load_data(sql_4)
df4["수급자_1천명당_교육참여인원"] = pd.to_numeric(
    df4["수급자_1천명당_교육참여인원"], errors="coerce"
)

fig4 = px.bar(
    df4,
    x="지역본부",
    y="수급자_1천명당_교육참여인원",
    text="수급자_1천명당_교육참여인원",
    title="노령연금 수급자 1천 명당 교육 참여 인원"
)
fig4.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    title_font_size=20,
    height=430
)
fig4.update_traces(texttemplate="%{text:.1f}명", textposition="outside")

st.plotly_chart(fig4, use_container_width=True)
show_sql(sql_4)

st.markdown("""
<div class="insight-box">
<b>인사이트</b><br>
단순 참여 인원은 인구 규모가 큰 지역에 유리하게 보일 수 있습니다.
따라서 수급자 1천 명당 교육 참여 인원으로 표준화하면, 실제 교육 접근성이 높은 지역과 낮은 지역을 더 공정하게 비교할 수 있습니다.
</div>
""", unsafe_allow_html=True)


st.divider()


# =========================
# 차트 5: 지역 유형화
# =========================
st.header("5. 지역을 노후준비 서비스 전략 유형으로 나눌 수 있을까?")

avg_edu = df["교육참여인원"].mean()
avg_rec = df["노령연금수급자수"].mean()

def classify(row):
    if row["교육참여인원"] >= avg_edu and row["노령연금수급자수"] >= avg_rec:
        return "수요-교육 모두 높음"
    elif row["교육참여인원"] >= avg_edu and row["노령연금수급자수"] < avg_rec:
        return "교육 집중형"
    elif row["교육참여인원"] < avg_edu and row["노령연금수급자수"] >= avg_rec:
        return "교육 확대 필요형"
    else:
        return "저수요·저참여형"

df_type = df.copy()
df_type["지역유형"] = df_type.apply(classify, axis=1)

sql_5 = """
SELECT
    지역본부,
    교육참여인원,
    노령연금수급자수,
    CASE
        WHEN 교육참여인원 >= (SELECT AVG(교육참여인원) FROM education_pension)
         AND 노령연금수급자수 >= (SELECT AVG(노령연금수급자수) FROM education_pension)
        THEN '수요-교육 모두 높음'

        WHEN 교육참여인원 >= (SELECT AVG(교육참여인원) FROM education_pension)
         AND 노령연금수급자수 < (SELECT AVG(노령연금수급자수) FROM education_pension)
        THEN '교육 집중형'

        WHEN 교육참여인원 < (SELECT AVG(교육참여인원) FROM education_pension)
         AND 노령연금수급자수 >= (SELECT AVG(노령연금수급자수) FROM education_pension)
        THEN '교육 확대 필요형'

        ELSE '저수요·저참여형'
    END AS 지역유형
FROM education_pension;
"""

fig5 = px.scatter(
    df_type,
    x="노령연금수급자수",
    y="교육참여인원",
    color="지역유형",
    text="지역본부",
    size="수급자_1천명당_교육참여인원",
    title="지역본부별 노후준비 서비스 전략 유형화"
)

fig5.add_vline(x=avg_rec, line_dash="dash")
fig5.add_hline(y=avg_edu, line_dash="dash")

fig5.update_traces(textposition="top center")
fig5.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    title_font_size=20,
    height=540
)

st.plotly_chart(fig5, use_container_width=True)
show_sql(sql_5)

st.markdown("""
<div class="insight-box">
<b>비즈니스 인사이트</b><br>
지역을 단순 순위로 보는 것보다, 수급 규모와 교육 참여 수준을 함께 기준으로 유형화하면 서비스 전략이 명확해집니다.<br><br>
- <b>수요-교육 모두 높음</b>: 현재 운영이 활발한 핵심 관리 지역<br>
- <b>교육 집중형</b>: 교육 참여는 높지만 수급 규모는 상대적으로 작은 지역<br>
- <b>교육 확대 필요형</b>: 수급 규모는 크지만 교육 참여가 낮아 우선 확대가 필요한 지역<br>
- <b>저수요·저참여형</b>: 홍보보다 기초 수요 확인이 먼저 필요한 지역
</div>
""", unsafe_allow_html=True)


st.divider()


# =========================
# 원본 데이터 확인
# =========================
st.header("데이터 확인")

with st.expander("education_pension 데이터 보기"):
    st.dataframe(df, use_container_width=True)

st.caption("본 대시보드는 지역본부별 노후준비교육 현황과 지역별 연금 수급자 데이터를 SQLite DB에서 불러와 분석했습니다.")
