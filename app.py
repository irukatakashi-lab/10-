import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import platform
import os

# -----------------------------------------------------------
# 1. [설정] 한글 폰트 설정 (2번 코드 기준 통일)
# -----------------------------------------------------------
def set_korean_font():
    font_path = 'NanumGothic.ttf'
    if os.path.exists(font_path):
        fm.fontManager.addfont(font_path)
        font_name = fm.FontProperties(fname=font_path).get_name()
        plt.rcParams['font.family'] = font_name
    else:
        system_name = platform.system()
        if system_name == 'Darwin': 
            plt.rcParams['font.family'] = 'AppleGothic'
        elif system_name == 'Windows': 
            plt.rcParams['font.family'] = 'Malgun Gothic'
        else: 
            plt.rcParams['font.family'] = 'NanumGothic'
            
    plt.rcParams['axes.unicode_minus'] = False

# 페이지 설정
st.set_page_config(page_title="암 사망률 변화 분석", layout="wide")

# Seaborn 테마 적용 (2번 코드와 유사한 깔끔한 스타일)
sns.set_theme(style="white", font_scale=1.1)

# 폰트 설정 적용
set_korean_font()

# -----------------------------------------------------------
# 2. 데이터 전처리 함수 (2번 코드의 표준 암종 명칭 반영)
# -----------------------------------------------------------
def standardize_cancer_name(text):
    # 1차 전처리: 코드 제거 및 기본 정리
    text = text.split('(')[0].strip()
    
    # 2번 코드 기준 표준 명칭 매핑
    mapping = {
        '위': '위암', '위의 악성신생물': '위암',
        '대장': '대장암', '대장·직장·항문암': '대장암', '결장, 직장 및 항문의 악성신생물': '대장암',
        '폐': '폐암', '기관·기관지·폐암': '폐암', '기관, 기관지 및 폐의 악성신생물': '폐암',
        '간': '간암', '간 및 간내 담관의 악성신생물': '간암',
        '유방': '유방암', '여성 유방암': '유방암', '유방의 악성신생물': '유방암',
        '자궁경부': '자궁경부암', '자궁경부암': '자궁경부암', '자궁경부의 악성신생물': '자궁경부암',
        '전립선': '전립선암', '전립선의 악성신생물': '전립선암',
        '췌장': '췌장암', '췌장의 악성신생물': '췌장암',
        '백혈병': '백혈병', 
        '방광': '방광암', '방광의 악성신생물': '방광암',
        '난소': '난소암', '난소의 악성신생물': '난소암',
        '갑상선': '갑상선암', '갑상선의 악성신생물': '갑상선암',
        '식도': '식도암', '식도의 악성신생물': '식도암',
        '담낭': '담낭암', '담낭 및 기타 담도': '담낭암', '담낭 및 기타 담도의 악성신생물': '담낭암'
    }
    
    # 매핑된 이름이 있으면 반환, 없으면 '암' 붙이기 등 일반화
    if text in mapping:
        return mapping[text]
    
    # 림프종 통합
    if '림프종' in text:
        return '림프종'
        
    # 기타 일반적인 이름 정리
    if text.endswith('의 악성신생물'):
        return text.replace('의 악성신생물', '암')
    if text.endswith('악성신생물'):
        return text.replace('악성신생물', '암')
        
    return text

@st.cache_data
def load_data(file_path):
    # 2번 코드의 safe loading 방식 차용
    if not os.path.exists(file_path):
        return None, []
        
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except:
        try:
            df = pd.read_csv(file_path, encoding='cp949')
        except:
            return None, []

    df_clean = df[(df['성별'] == '계') & (df['연령(5세)별'] == '계')].copy()
    df_clean.rename(columns={'사망원인별(104항목)': 'Cancer Type'}, inplace=True)

    year_columns = [col for col in df_clean.columns if col.isdigit()]
    for col in year_columns:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    # 표준 이름 적용
    df_clean['Cancer Type'] = df_clean['Cancer Type'].apply(standardize_cancer_name)
    df_clean = df_clean[~df_clean['Cancer Type'].isin(['암', '악성신생물'])] # 합계 행 제거
    
    # 중복된 이름 합산 (매핑으로 인해 같아진 이름들)
    df_clean = df_clean.groupby('Cancer Type', as_index=False)[year_columns].sum()

    return df_clean, year_columns

# -----------------------------------------------------------
# 3. 메인 앱 구성
# -----------------------------------------------------------
st.title("📊 암 사망률 변화 (Top 10)")
st.markdown("데이터 출처: 국립암센터 / 통계청")

df, years = load_data('cancer_data.csv')

if df is None:
    st.warning("폴더에 'cancer_data.csv' 파일이 없습니다.")
    st.stop()

# 세션 상태 초기화
if 'year_range' not in st.session_state:
    st.session_state['year_range'] = (2013, 2023)

min_year, max_year = int(min(years)), int(max(years))
start_year, end_year = st.session_state['year_range']

# -----------------------------------------------------------
# 4. 차트 구현 (2번 코드 스타일 적용)
# -----------------------------------------------------------
if start_year >= end_year:
    st.error("시작 연도는 종료 연도보다 작아야 합니다. 아래 슬라이더를 조절해주세요.")
else:
    cols = ['Cancer Type', str(start_year), str(end_year)]
    plot_data = df[cols].copy()
    plot_data.columns = ['Cancer Type', 'Start', 'End']
    plot_data.dropna(inplace=True)

    # 상위 10개 추출
    top_cancers = plot_data.sort_values(by='End', ascending=True).tail(10)
    top_cancers['Diff'] = top_cancers['End'] - top_cancers['Start']
    
    # [색상 통일] 2번 코드의 'Reds', 'Blues' 팔레트 활용
    palette_red = sns.color_palette("Reds", n_colors=5)[-2] 
    palette_blue = sns.color_palette("Blues", n_colors=5)[-2] 
    
    top_cancers['Color'] = top_cancers['Diff'].apply(lambda x: palette_red if x > 0 else palette_blue)
    top_cancers['Left'] = top_cancers.apply(lambda x: min(x['Start'], x['End']), axis=1)
    top_cancers['Width'] = top_cancers['Diff'].abs()

    fig, ax = plt.subplots(figsize=(14, 6)) # 2번 코드와 너비 유사하게 맞춤

    # Floating Bar Chart
    bars = ax.barh(y=top_cancers['Cancer Type'], width=top_cancers['Width'], 
                   left=top_cancers['Left'], color=top_cancers['Color'], 
                   alpha=0.85, height=0.6, edgecolor='white')

    # [스타일 통일] 제목 폰트, 크기, 굵기 2번 코드와 일치시킴
    ax.set_title(f'{start_year}년 대비 {end_year}년 암 사망률 변화 (10만 명당 사망자 수)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.set_xlabel('사망률', fontsize=12)
    ax.set_ylabel('암종', fontsize=12) # Y축 라벨 추가 (2번 코드 스타일)
    ax.grid(axis='y', linestyle='--', alpha=0.5) 

    # 범례
    red_patch = mpatches.Patch(color=palette_red, label='증가')
    blue_patch = mpatches.Patch(color=palette_blue, label='감소')
    ax.legend(handles=[red_patch, blue_patch], loc='lower right', frameon=True)

    st.pyplot(fig)

    with st.expander("상세 데이터 보기"):
        display_df = top_cancers[['Cancer Type', 'Start', 'End', 'Diff']].sort_values(by='End', ascending=False)
        display_df.columns = ['암종', f'{start_year}년 사망률', f'{end_year}년 사망률', '변화량']
        st.dataframe(display_df.style.format("{:.1f}", subset=display_df.columns[1:]))

# -----------------------------------------------------------
# 5. 하단 슬라이더
# -----------------------------------------------------------
st.markdown("---") 
st.subheader("📅 비교 기간 설정")
st.slider(
    "비교할 연도 범위를 선택하세요",
    min_value=min_year,
    max_value=max_year,
    key='year_range',
    step=1
)
