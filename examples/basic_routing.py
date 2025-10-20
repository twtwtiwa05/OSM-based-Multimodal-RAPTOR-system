#!/usr/bin/env python3
"""
🚇 기본 경로 탐색 예제

이 예제는 OSM 기반 멀티모달 RAPTOR 시스템의 기본적인 사용법을 보여줍니다.
압구정역에서 선정릉역까지의 경로를 탐색하는 예제입니다.
"""

import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PART1_2 import Stop, Route, Trip
from PART2_NEW import TraditionalRAPTOR, RoutePreference

def basic_routing_example():
    """기본 경로 탐색 예제"""
    
    print("🚇 OSM 기반 멀티모달 RAPTOR 시스템 - 기본 예제")
    print("=" * 60)
    
    # RAPTOR 시스템 초기화
    print("🚀 RAPTOR 시스템 초기화 중...")
    raptor = TraditionalRAPTOR()
    
    # 경로 탐색 설정
    origin = (37.527070, 127.041927)      # 압구정역 (3호선)
    destination = (37.504528, 127.049348) # 선정릉역 (분당선)
    departure_time = "08:30"               # 출발 시간
    
    print(f"\n📍 경로 설정:")
    print(f"   출발지: 압구정역 {origin}")
    print(f"   목적지: 선정릉역 {destination}")
    print(f"   출발시간: {departure_time}")
    
    # 사용자 선호도 설정
    preference = RoutePreference(
        time_weight=0.4,        # 시간 중요도 40%
        transfer_weight=0.3,    # 환승 중요도 30%
        walk_weight=0.2,        # 도보 중요도 20%
        cost_weight=0.1,        # 비용 중요도 10%
        max_walk_distance=1000, # 최대 도보 거리 1km
        max_transfers=3         # 최대 환승 3회
    )
    
    print(f"\n⚙️ 탐색 설정:")
    print(f"   시간 중요도: {preference.time_weight*100}%")
    print(f"   환승 중요도: {preference.transfer_weight*100}%")
    print(f"   도보 중요도: {preference.walk_weight*100}%")
    print(f"   비용 중요도: {preference.cost_weight*100}%")
    
    # 경로 탐색 실행
    print(f"\n🔍 경로 탐색 실행...")
    journeys = raptor.find_routes(origin, destination, departure_time, preference)
    
    # 결과 출력
    if journeys:
        print(f"\n✅ {len(journeys)}개의 최적 경로를 발견했습니다!")
        print("=" * 60)
        
        for i, journey in enumerate(journeys):
            print(f"\n[경로 {i+1}]")
            raptor.print_journey(journey, preference)
            
            # 추가 정보 출력
            print(f"📊 경로 분석:")
            print(f"   - 파레토 점수: {journey.get_score(preference):.2f}")
            print(f"   - 시간 효율성: {journey.total_time:.1f}분")
            print(f"   - 비용 효율성: {journey.total_cost:.0f}원")
            print(f"   - 환승 최적화: {journey.transfer_count}회")
            print(f"   - 도보 최적화: {journey.total_walk_distance:.0f}m")
            
    else:
        print("❌ 조건에 맞는 경로를 찾을 수 없습니다.")
        print("💡 다음을 확인해보세요:")
        print("   - 출발지와 목적지가 서비스 지역 내에 있는지")
        print("   - 출발 시간이 운행 시간대인지")
        print("   - 최대 도보 거리나 환승 횟수 제한이 너무 엄격하지 않은지")

def compare_preferences_example():
    """다양한 선호도 비교 예제"""
    
    print("\n" + "=" * 60)
    print("🔄 선호도별 경로 비교 예제")
    print("=" * 60)
    
    raptor = TraditionalRAPTOR()
    
    origin = (37.484098, 127.034377)      # 양재역
    destination = (37.516173, 127.020166) # 신사역
    departure_time = "10:30"
    
    # 다양한 선호도 설정
    preferences = {
        "시간 최우선": RoutePreference(time_weight=0.7, transfer_weight=0.1, walk_weight=0.1, cost_weight=0.1),
        "환승 최소화": RoutePreference(time_weight=0.2, transfer_weight=0.6, walk_weight=0.1, cost_weight=0.1),
        "도보 최소화": RoutePreference(time_weight=0.2, transfer_weight=0.1, walk_weight=0.6, cost_weight=0.1),
        "비용 최우선": RoutePreference(time_weight=0.2, transfer_weight=0.1, walk_weight=0.1, cost_weight=0.6),
        "균형 잡힌": RoutePreference(time_weight=0.25, transfer_weight=0.25, walk_weight=0.25, cost_weight=0.25)
    }
    
    print(f"📍 양재역 → 신사역 ({departure_time} 출발)")
    
    for pref_name, preference in preferences.items():
        print(f"\n🎯 {pref_name} 선호도:")
        
        journeys = raptor.find_routes(origin, destination, departure_time, preference)
        
        if journeys:
            best_journey = journeys[0]  # 첫 번째가 가장 좋은 경로
            print(f"   ⏱️  총 시간: {best_journey.total_time:.1f}분")
            print(f"   💰 총 비용: {best_journey.total_cost:.0f}원")
            print(f"   🔄 환승 횟수: {best_journey.transfer_count}회")
            print(f"   🚶 도보 거리: {best_journey.total_walk_distance:.0f}m")
            print(f"   📊 점수: {best_journey.get_score(preference):.2f}")
        else:
            print("   ❌ 경로를 찾을 수 없음")

def time_analysis_example():
    """시간대별 경로 분석 예제"""
    
    print("\n" + "=" * 60)
    print("⏰ 시간대별 경로 분석 예제")
    print("=" * 60)
    
    raptor = TraditionalRAPTOR()
    
    origin = (37.527070, 127.041927)      # 압구정역
    destination = (37.504528, 127.049348) # 선정릉역
    
    # 다양한 시간대 테스트
    times = ["07:00", "08:30", "12:00", "18:00", "22:00"]
    preference = RoutePreference()  # 기본 설정
    
    print("📊 시간대별 경로 품질 분석:")
    print("시간    | 경로수 | 최단시간 | 최저비용 | 평균환승")
    print("-" * 50)
    
    for time_str in times:
        journeys = raptor.find_routes(origin, destination, time_str, preference)
        
        if journeys:
            min_time = min(j.total_time for j in journeys)
            min_cost = min(j.total_cost for j in journeys)
            avg_transfers = sum(j.transfer_count for j in journeys) / len(journeys)
            
            print(f"{time_str:8} | {len(journeys):4}개 | {min_time:6.1f}분 | {min_cost:6.0f}원 | {avg_transfers:6.1f}회")
        else:
            print(f"{time_str:8} | {'없음':>4} | {'없음':>6} | {'없음':>6} | {'없음':>6}")

if __name__ == "__main__":
    try:
        # 기본 경로 탐색 예제
        basic_routing_example()
        
        # 선호도 비교 예제
        compare_preferences_example()
        
        # 시간대별 분석 예제
        time_analysis_example()
        
        print("\n" + "=" * 60)
        print("✅ 모든 예제가 성공적으로 완료되었습니다!")
        print("💡 더 많은 예제는 examples/ 폴더를 확인하세요.")
        
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류가 발생했습니다: {e}")
        print("💡 데이터 파일이 올바르게 설치되었는지 확인해주세요.")
        import traceback
        traceback.print_exc()