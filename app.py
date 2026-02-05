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
        '담낭': '담낭암', '담낭 및 기타 담도': '담낭암', '담낭 및 기타 담도의 악성신생물': '담낭암'}
