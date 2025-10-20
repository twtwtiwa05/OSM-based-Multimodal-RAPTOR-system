#!/usr/bin/env python3
"""
OSM 기반 멀티모달 RAPTOR 시스템 - Streamlit 웹 애플리케이션

GitHub에서 바로 실행 가능한 인터랙티브 경로 탐색 웹 애플리케이션
지도에서 출발지와 목적지를 클릭하여 최적 경로를 탐색할 수 있습니다.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, time
import sys
import os
import time as timer

# 프로젝트 루트를 Python path에 추가
sys.path.append('.')

try:
    from PART1_2 import Stop, Route, Trip
    from PART2_NEW import TraditionalRAPTOR, RoutePreference
    RAPTOR_AVAILABLE = True
except ImportError as e:
    RAPTOR_AVAILABLE = False
    st.error(f"RAPTOR 모듈을 로드할 수 없습니다: {e}")

# 페이지 설정
st.set_page_config(
    page_title="OSM 멀티모달 RAPTOR",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 메인 헤더
st.title("OSM 기반 멀티모달 RAPTOR 시스템")
st.markdown("**세계 최고 수준의 대중교통 경로 탐색 시스템** - 지도에서 출발지와 목적지를 클릭하여 최적 경로를 탐색하세요!")

# 사이드바 설정
st.sidebar.header("경로 탐색 설정")

# RAPTOR 시스템 초기화
@st.cache_resource
def initialize_raptor():
    """RAPTOR 시스템 초기화 (캐싱으로 성능 최적화)"""
    if not RAPTOR_AVAILABLE:
        return None
    
    try:
        with st.spinner("RAPTOR 시스템 초기화 중..."):
            raptor = TraditionalRAPTOR()
        st.success("RAPTOR 시스템 초기화 완료!")
        return raptor
    except Exception as e:
        st.error(f"RAPTOR 초기화 실패: {e}")
        return None

# 기본 지도 설정 (강남구 중심)
DEFAULT_LAT = 37.5172
DEFAULT_LON = 127.0473
GANGNAM_BOUNDS = [[37.46, 127.0], [37.57, 127.1]]

def create_base_map():
    """기본 지도 생성"""
    m = folium.Map(
        location=[DEFAULT_LAT, DEFAULT_LON],
        zoom_start=13,
        tiles="OpenStreetMap"
    )
    
    # 강남구 경계 표시
    folium.Rectangle(
        bounds=GANGNAM_BOUNDS,
        color="blue",
        fill=False,
        weight=2,
        popup="강남구 서비스 지역"
    ).add_to(m)
    
    return m

def add_route_to_map(map_obj, journey, journey_idx=0):
    """경로를 지도에 추가"""
    colors = ['red', 'blue', 'green', 'purple', 'orange']
    color = colors[journey_idx % len(colors)]
    
    # 경로 단계별 표시
    for i, leg in enumerate(journey.legs):
        if hasattr(leg, 'coordinates') and leg.coordinates:
            # 경로 라인 그리기
            folium.PolyLine(
                locations=leg.coordinates,
                color=color,
                weight=4,
                opacity=0.8,
                popup=f"경로 {journey_idx+1}: {leg.mode.value if hasattr(leg.mode, 'value') else leg.mode}"
            ).add_to(map_obj)
        
        # 정류장/포인트 마커
        if hasattr(leg, 'from_stop') and leg.from_stop:
            folium.CircleMarker(
                location=[leg.from_stop.stop_lat, leg.from_stop.stop_lon],
                radius=5,
                color=color,
                popup=f"{leg.from_stop.stop_name}",
                fillOpacity=0.8
            ).add_to(map_obj)

def display_journey_details(journeys, preference):
    """경로 상세 정보 표시"""
    if not journeys:
        st.warning("찾은 경로가 없습니다.")
        return
    
    st.subheader(f"탐색 결과 ({len(journeys)}개 경로)")
    
    # 경로 요약 테이블
    journey_data = []
    for i, journey in enumerate(journeys):
        journey_data.append({
            "경로": f"경로 {i+1}",
            "총 시간": f"{journey.total_time:.1f}분",
            "비용": f"{journey.total_cost:.0f}원",
            "환승": f"{journey.transfer_count}회",
            "도보": f"{journey.total_walk_distance:.0f}m",
            "점수": f"{journey.get_score(preference):.2f}"
        })
    
    df = pd.DataFrame(journey_data)
    st.dataframe(df, use_container_width=True)
    
    # 선택된 경로 상세 정보
    selected_route = st.selectbox("상세 보기할 경로를 선택하세요:", 
                                 options=range(len(journeys)),
                                 format_func=lambda x: f"경로 {x+1}")
    
    if selected_route is not None:
        journey = journeys[selected_route]
        
        st.markdown("### 상세 경로")
        
        # 경로 단계별 정보
        for i, leg in enumerate(journey.legs):
            with st.expander(f"단계 {i+1}: {leg.mode.value if hasattr(leg.mode, 'value') else leg.mode}"):
                if hasattr(leg, 'route_name') and leg.route_name:
                    st.write(f"**노선**: {leg.route_name}")
                if hasattr(leg, 'from_stop') and leg.from_stop:
                    st.write(f"**출발**: {leg.from_stop.stop_name}")
                if hasattr(leg, 'to_stop') and leg.to_stop:
                    st.write(f"**도착**: {leg.to_stop.stop_name}")
                if hasattr(leg, 'duration'):
                    st.write(f"**소요시간**: {leg.duration:.1f}분")
                if hasattr(leg, 'cost'):
                    st.write(f"**비용**: {leg.cost:.0f}원")

def create_performance_chart(raptor_stats):
    """성능 차트 생성"""
    if not raptor_stats:
        return None
    
    # 라운드별 성능 데이터
    rounds_data = []
    for round_num, stats in raptor_stats.items():
        if isinstance(stats, dict) and 'reachable_stops' in stats:
            rounds_data.append({
                'Round': round_num,
                'Reachable Stops': stats['reachable_stops'],
                'Processing Time': stats.get('time', 0)
            })
    
    if rounds_data:
        df_rounds = pd.DataFrame(rounds_data)
        
        # 도달 가능한 정류장 수 차트
        fig = px.bar(df_rounds, x='Round', y='Reachable Stops',
                    title="라운드별 도달 가능한 정류장 수")
        st.plotly_chart(fig, use_container_width=True)

def main():
    """메인 애플리케이션"""
    
    # RAPTOR 시스템 초기화
    raptor = initialize_raptor()
    
    if not raptor:
        st.error("RAPTOR 시스템을 사용할 수 없습니다. 데이터 파일을 확인해주세요.")
        st.info("**데이터 준비 방법:**\n"
               "1. `gangnam_raptor_data/raptor_data.pkl` 파일이 존재하는지 확인\n"
               "2. PART1_2.py를 실행하여 데이터를 전처리\n"
               "3. 애플리케이션을 다시 시작")
        return
    
    # 사이드바 설정
    st.sidebar.subheader("탐색 옵션")
    
    # 출발 시간 설정
    departure_time = st.sidebar.time_input(
        "출발 시간",
        value=time(8, 30),
        help="경로 탐색할 출발 시간을 설정하세요"
    )
    
    # 사용자 선호도 설정
    st.sidebar.subheader("경로 선호도")
    
    time_weight = st.sidebar.slider("시간 중요도", 0.0, 1.0, 0.4, 0.1)
    transfer_weight = st.sidebar.slider("환승 중요도", 0.0, 1.0, 0.3, 0.1)
    walk_weight = st.sidebar.slider("도보 중요도", 0.0, 1.0, 0.2, 0.1)
    cost_weight = st.sidebar.slider("비용 중요도", 0.0, 1.0, 0.1, 0.1)
    
    # 가중치 정규화
    total_weight = time_weight + transfer_weight + walk_weight + cost_weight
    if total_weight > 0:
        time_weight /= total_weight
        transfer_weight /= total_weight
        walk_weight /= total_weight
        cost_weight /= total_weight
    
    preference = RoutePreference(
        time_weight=time_weight,
        transfer_weight=transfer_weight,
        walk_weight=walk_weight,
        cost_weight=cost_weight,
        max_walk_distance=st.sidebar.slider("최대 도보 거리 (m)", 100, 2000, 1000, 100),
        max_transfers=st.sidebar.slider("최대 환승 횟수", 0, 5, 3, 1)
    )
    
    # 메인 컨텐츠 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("인터랙티브 지도")
        st.info("**사용법**: 지도에서 출발지와 목적지를 클릭하여 선택하세요!")
        
        # 지도 표시
        base_map = create_base_map()
        
        # 세션 상태에 좌표 저장
        if 'origin' not in st.session_state:
            st.session_state.origin = None
        if 'destination' not in st.session_state:
            st.session_state.destination = None
        
        # 지도 클릭 이벤트 처리
        map_data = st_folium(base_map, width=700, height=500, returned_objects=["last_clicked"])
        
        if map_data["last_clicked"]:
            clicked_lat = map_data["last_clicked"]["lat"]
            clicked_lng = map_data["last_clicked"]["lng"]
            
            # 출발지/목적지 설정 버튼
            col_origin, col_dest = st.columns(2)
            
            with col_origin:
                if st.button("출발지로 설정"):
                    st.session_state.origin = (clicked_lat, clicked_lng)
                    st.success(f"출발지 설정: ({clicked_lat:.4f}, {clicked_lng:.4f})")
            
            with col_dest:
                if st.button("목적지로 설정"):
                    st.session_state.destination = (clicked_lat, clicked_lng)
                    st.success(f"목적지 설정: ({clicked_lat:.4f}, {clicked_lng:.4f})")
    
    with col2:
        st.subheader("선택된 위치")
        
        if st.session_state.origin:
            st.write("**출발지:**")
            st.write(f"위도: {st.session_state.origin[0]:.4f}")
            st.write(f"경도: {st.session_state.origin[1]:.4f}")
        else:
            st.write("출발지가 선택되지 않았습니다.")
        
        st.write("---")
        
        if st.session_state.destination:
            st.write("**목적지:**")
            st.write(f"위도: {st.session_state.destination[0]:.4f}")
            st.write(f"경도: {st.session_state.destination[1]:.4f}")
        else:
            st.write("목적지가 선택되지 않았습니다.")
        
        st.write("---")
        
        # 경로 탐색 버튼
        if st.button("경로 탐색", type="primary", use_container_width=True):
            if not st.session_state.origin or not st.session_state.destination:
                st.error("출발지와 목적지를 모두 선택해주세요!")
            else:
                # 경로 탐색 실행
                with st.spinner("최적 경로 탐색 중..."):
                    start_time = timer.time()
                    
                    try:
                        departure_str = departure_time.strftime("%H:%M")
                        journeys = raptor.find_routes(
                            st.session_state.origin,
                            st.session_state.destination,
                            departure_str,
                            preference
                        )
                        
                        end_time = timer.time()
                        search_time = end_time - start_time
                        
                        st.success(f"탐색 완료! ({search_time:.2f}초)")
                        
                        # 세션 상태에 결과 저장
                        st.session_state.journeys = journeys
                        st.session_state.search_time = search_time
                        
                    except Exception as e:
                        st.error(f"경로 탐색 중 오류가 발생했습니다: {e}")
                        st.session_state.journeys = None
        
        # 위치 초기화 버튼
        if st.button("위치 초기화", use_container_width=True):
            st.session_state.origin = None
            st.session_state.destination = None
            if 'journeys' in st.session_state:
                del st.session_state.journeys
            st.rerun()
    
    # 결과 표시
    if 'journeys' in st.session_state and st.session_state.journeys:
        st.markdown("---")
        display_journey_details(st.session_state.journeys, preference)
        
        # 성능 통계
        if 'search_time' in st.session_state:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("탐색 시간", f"{st.session_state.search_time:.2f}초")
            with col2:
                st.metric("발견 경로", f"{len(st.session_state.journeys)}개")
            with col3:
                if st.session_state.journeys:
                    best_time = min(j.total_time for j in st.session_state.journeys)
                    st.metric("최단 시간", f"{best_time:.1f}분")

    # 시스템 정보
    with st.expander("시스템 정보"):
        if raptor:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("정류장 수", f"{len(raptor.stops):,}")
            with col2:
                st.metric("노선 수", f"{len(raptor.routes):,}")
            with col3:
                if hasattr(raptor, 'transfers'):
                    total_transfers = sum(len(t) for t in raptor.transfers.values())
                    st.metric("환승 연결", f"{total_transfers:,}")
        
        st.markdown("""
        **기술 스택:**
        - Python + Streamlit
        - Folium + OpenStreetMap
        - RAPTOR 알고리즘
        - Plotly 시각화
        
        **데이터 소스:**
        - GTFS (General Transit Feed Specification)
        - OpenStreetMap (OSM)
        """)

    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        OSM 기반 멀티모달 RAPTOR 시스템 | 
        <a href='https://github.com/yourusername/osm-multimodal-raptor'>GitHub</a> |
        Made with Love using Streamlit
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()