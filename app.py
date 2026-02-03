import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches
import platform

# ---------------------------------------------------------
# 1. 페이지 및 폰트 설정
# ---------------------------------------------------------
st.set_page_config(page_title="암 사망률 변화 분석", layout="wide")

# Seaborn 테마 적용
sns.set_theme(style="whitegrid", font_scale=1.1)

# 한글 폰트 설정
system_name = platform.system()
if system_name == "Darwin":  # Mac
    plt.rc('font', family='AppleGothic')
elif system_name == "Windows":  # Windows
    plt.rc('font', family='Malgun Gothic')
else:  # Linux
    plt.rc('font', family='NanumGothic')

plt.rc('axes', unicode_minus=False)

# ---------------------------------------------------------
# 2. 데이터 전처리 함수
# ---------------------------------------------------------
def clean_cancer_name(text):
    text = text.split('(')[0].strip()
    if '림프종' in text:
        return '림프종'
    if text.endswith('의 악성신생물'):
        text = text.replace('의 악성신생물', '암')
    elif text.endswith('악성신생물'):
        text = text.replace('악성신생물', '암')
    return text

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='cp949')

    df_clean = df[(df['성별'] == '계') & (df['연령(5세)별'] == '계')].copy()
    df_clean.rename(columns={'사망원인별(104항목)': 'Cancer Type'}, inplace=True)

    year_columns = [col for col in df_clean.columns if col.isdigit()]
    for col in year_columns:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    df_clean['Cancer Type'] = df_clean['Cancer Type'].apply(clean_cancer_name)
    df_clean = df_clean[df_clean['Cancer Type'] != '암']
    
    # 중복된 이름(림프종 등) 합산
    df_clean = df_clean.groupby('Cancer Type', as_index=False)[year_columns].sum()

    return df_clean, year_columns

# ---------------------------------------------------------
# 3. 메인 앱 구성
# ---------------------------------------------------------
st.title("📊 암 사망률 변화 (Top 10)")
st.markdown("데이터 출처: 국립암센터 / 통계청")

try:
    df, years = load_data('cancer_data.csv')
    min_year, max_year = int(min(years)), int(max(years))
except FileNotFoundError:
    st.warning("폴더에 '암사망률.csv' 파일이 없습니다.")
    st.stop()

# [수정됨] 세션 상태 초기화 (슬라이더 값을 저장하기 위함)
if 'year_range' not in st.session_state:
    st.session_state['year_range'] = (2013, 2023)

# 사이드바 설정 제거 -> 차트 그리기 준비
# 세션 상태에서 현재 선택된 연도를 가져옵니다.
start_year, end_year = st.session_state['year_range']

# ---------------------------------------------------------
# 4. 차트 구현
# ---------------------------------------------------------
if start_year >= end_year:
    st.error("시작 연도는 종료 연도보다 작아야 합니다. 아래 슬라이더를 조절해주세요.")
else:
    cols = ['Cancer Type', str(start_year), str(end_year)]
    plot_data = df[cols].copy()
    plot_data.columns = ['Cancer Type', 'Start', 'End']
    plot_data.dropna(inplace=True)

    top_cancers = plot_data.sort_values(by='End', ascending=True).tail(10)

    top_cancers['Diff'] = top_cancers['End'] - top_cancers['Start']
    
    palette_red = sns.color_palette("Reds", n_colors=5)[-2] 
    palette_blue = sns.color_palette("Blues", n_colors=5)[-2] 
    
    top_cancers['Color'] = top_cancers['Diff'].apply(lambda x: palette_red if x > 0 else palette_blue)
    top_cancers['Left'] = top_cancers.apply(lambda x: min(x['Start'], x['End']), axis=1)
    top_cancers['Width'] = top_cancers['Diff'].abs()

    fig, ax = plt.subplots(figsize=(12, 6))

    # Floating Bar Chart
    bars = ax.barh(y=top_cancers['Cancer Type'], width=top_cancers['Width'], 
                   left=top_cancers['Left'], color=top_cancers['Color'], 
                   alpha=0.85, height=0.6, edgecolor='white')

    ax.set_title(f'{start_year}년 대비 {end_year}년 암 사망률 변화 (10만 명당)', fontsize=16, pad=20)
    ax.set_xlabel('사망률', fontsize=12)
    ax.grid(axis='y') 

    red_patch = mpatches.Patch(color=palette_red, label='증가 (Worsened)')
    blue_patch = mpatches.Patch(color=palette_blue, label='감소 (Improved)')
    ax.legend(handles=[red_patch, blue_patch], loc='lower right', frameon=True)

    st.pyplot(fig)

    with st.expander("상세 데이터 보기"):
        display_df = top_cancers[['Cancer Type', 'Start', 'End', 'Diff']].sort_values(by='End', ascending=False)
        display_df.columns = ['암종', f'{start_year}년 사망률', f'{end_year}년 사망률', '변화량']
        st.dataframe(display_df.style.format("{:.1f}", subset=display_df.columns[1:]))

# ---------------------------------------------------------
# 5. 하단 슬라이더 배치 (key를 이용해 위쪽 차트와 연동)
# ---------------------------------------------------------
st.markdown("---") # 구분선
st.subheader("📅 비교 기간 설정")
st.slider(
    "비교할 연도 범위를 선택하세요",
    min_value=min_year,
    max_value=max_year,
    key='year_range', # 이 key가 위의 st.session_state['year_range']와 자동으로 연결됩니다.
    step=1
)
