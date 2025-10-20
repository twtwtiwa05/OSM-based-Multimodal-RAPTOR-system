#!/usr/bin/env python3
"""
 성능 벤치마크 테스트

이 스크립트는 RAPTOR 시스템의 성능을 측정하고 분석합니다.
다양한 조건에서의 탐색 시간, 메모리 사용량, 경로 품질을 평가합니다.
"""

import sys
import os
import time
import psutil
import random
from statistics import mean, median, stdev

# 프로젝트 루트를 Python path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PART1_2 import Stop, Route, Trip
from PART2_NEW import TraditionalRAPTOR, RoutePreference

class PerformanceTester:
    """RAPTOR 시스템 성능 테스트 클래스"""
    
    def __init__(self):
        self.raptor = None
        self.test_results = []
        
    def initialize_system(self):
        """시스템 초기화 및 초기화 시간 측정"""
        print("🚀 RAPTOR 시스템 초기화 성능 테스트")
        print("=" * 50)
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        self.raptor = TraditionalRAPTOR()
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        init_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        print(f"⏱️  초기화 시간: {init_time:.2f}초")
        print(f"💾 메모리 사용량: {memory_usage:.1f}MB")
        print(f"🚏 정류장 수: {len(self.raptor.stops):,}개")
        print(f"🚌 노선 수: {len(self.raptor.routes):,}개")
        
        return init_time, memory_usage
    
    def generate_test_cases(self, num_cases=50):
        """무작위 테스트 케이스 생성"""
        test_cases = []
        
        # 강남구 영역 내의 무작위 좌표 생성
        for _ in range(num_cases):
            origin_lat = random.uniform(37.46, 37.57)
            origin_lon = random.uniform(127.0, 127.1)
            dest_lat = random.uniform(37.46, 37.57)
            dest_lon = random.uniform(127.0, 127.1)
            
            # 시간대 다양화
            hour = random.randint(6, 23)
            minute = random.choice([0, 15, 30, 45])
            departure_time = f"{hour:02d}:{minute:02d}"
            
            test_cases.append({
                'origin': (origin_lat, origin_lon),
                'destination': (dest_lat, dest_lon),
                'departure_time': departure_time
            })
        
        return test_cases
    
    def run_single_test(self, test_case, preference):
        """단일 테스트 케이스 실행"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            journeys = self.raptor.find_routes(
                test_case['origin'],
                test_case['destination'],
                test_case['departure_time'],
                preference
            )
            success = True
            num_routes = len(journeys) if journeys else 0
            
        except Exception as e:
            journeys = []
            success = False
            num_routes = 0
            print(f"❌ 테스트 실패: {e}")
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        return {
            'success': success,
            'execution_time': end_time - start_time,
            'memory_delta': end_memory - start_memory,
            'num_routes': num_routes,
            'journeys': journeys
        }
    
    def benchmark_performance(self, num_tests=50):
        """성능 벤치마크 실행"""
        print(f"\n⚡ 성능 벤치마크 테스트 ({num_tests}개 케이스)")
        print("=" * 50)
        
        if not self.raptor:
            print("❌ RAPTOR 시스템이 초기화되지 않았습니다.")
            return
        
        test_cases = self.generate_test_cases(num_tests)
        preference = RoutePreference()
        
        results = []
        successful_tests = 0
        
        print("진행률: ", end="")
        for i, test_case in enumerate(test_cases):
            # 진행률 표시
            if i % (num_tests // 10) == 0:
                print(f"{i*100//num_tests}%", end=" ")
            
            result = self.run_single_test(test_case, preference)
            results.append(result)
            
            if result['success']:
                successful_tests += 1
        
        print("100% 완료!")
        
        # 통계 분석
        self.analyze_results(results, successful_tests, num_tests)
    
    def analyze_results(self, results, successful_tests, total_tests):
        """결과 분석 및 통계 출력"""
        print(f"\n📊 성능 분석 결과")
        print("=" * 50)
        
        # 성공률
        success_rate = (successful_tests / total_tests) * 100
        print(f"✅ 성공률: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        
        # 성공한 테스트만 분석
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            print("❌ 분석할 성공 케이스가 없습니다.")
            return
        
        # 실행 시간 통계
        execution_times = [r['execution_time'] for r in successful_results]
        print(f"\n⏱️  실행 시간 통계:")
        print(f"   평균: {mean(execution_times):.3f}초")
        print(f"   중앙값: {median(execution_times):.3f}초")
        print(f"   최솟값: {min(execution_times):.3f}초")
        print(f"   최댓값: {max(execution_times):.3f}초")
        if len(execution_times) > 1:
            print(f"   표준편차: {stdev(execution_times):.3f}초")
        
        # 경로 수 통계
        route_counts = [r['num_routes'] for r in successful_results]
        print(f"\n🛤️  경로 수 통계:")
        print(f"   평균: {mean(route_counts):.1f}개")
        print(f"   중앙값: {median(route_counts):.1f}개")
        print(f"   최솟값: {min(route_counts)}개")
        print(f"   최댓값: {max(route_counts)}개")
        
        # 성능 등급 분류
        self.classify_performance(execution_times)
    
    def classify_performance(self, execution_times):
        """성능 등급 분류"""
        print(f"\n🏆 성능 등급 분석:")
        
        excellent = sum(1 for t in execution_times if t < 1.0)
        good = sum(1 for t in execution_times if 1.0 <= t < 3.0)
        average = sum(1 for t in execution_times if 3.0 <= t < 5.0)
        poor = sum(1 for t in execution_times if t >= 5.0)
        
        total = len(execution_times)
        
        print(f"   🥇 우수 (< 1초): {excellent}개 ({excellent/total*100:.1f}%)")
        print(f"   🥈 양호 (1-3초): {good}개 ({good/total*100:.1f}%)")
        print(f"   🥉 보통 (3-5초): {average}개 ({average/total*100:.1f}%)")
        print(f"   📉 개선필요 (≥ 5초): {poor}개 ({poor/total*100:.1f}%)")
    
    def stress_test(self, duration_minutes=5):
        """스트레스 테스트 - 지정된 시간 동안 연속 실행"""
        print(f"\n🔥 스트레스 테스트 ({duration_minutes}분간)")
        print("=" * 50)
        
        if not self.raptor:
            print("❌ RAPTOR 시스템이 초기화되지 않았습니다.")
            return
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        test_count = 0
        success_count = 0
        total_execution_time = 0
        
        preference = RoutePreference()
        
        while time.time() < end_time:
            test_case = self.generate_test_cases(1)[0]
            result = self.run_single_test(test_case, preference)
            
            test_count += 1
            if result['success']:
                success_count += 1
                total_execution_time += result['execution_time']
            
            # 진행 상황 표시 (10초마다)
            if test_count % 10 == 0:
                elapsed = time.time() - start_time
                remaining = duration_minutes * 60 - elapsed
                print(f"진행: {elapsed/60:.1f}분 경과, {remaining/60:.1f}분 남음, {test_count}회 테스트")
        
        # 스트레스 테스트 결과
        print(f"\n📈 스트레스 테스트 결과:")
        print(f"   총 테스트 수: {test_count}개")
        print(f"   성공률: {success_count/test_count*100:.1f}%")
        print(f"   평균 처리율: {test_count/(duration_minutes*60):.1f} 테스트/초")
        if success_count > 0:
            print(f"   평균 실행 시간: {total_execution_time/success_count:.3f}초")
    
    def memory_profile_test(self):
        """메모리 프로파일링 테스트"""
        print(f"\n💾 메모리 프로파일링 테스트")
        print("=" * 50)
        
        if not self.raptor:
            print("❌ RAPTOR 시스템이 초기화되지 않았습니다.")
            return
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        print(f"초기 메모리 사용량: {initial_memory:.1f}MB")
        
        # 100회 연속 테스트로 메모리 누수 확인
        for i in range(100):
            test_case = self.generate_test_cases(1)[0]
            self.run_single_test(test_case, RoutePreference())
            
            if i % 20 == 19:  # 20회마다 메모리 체크
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"{i+1:3d}회 후: {current_memory:.1f}MB (증가: +{current_memory-initial_memory:.1f}MB)")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"\n최종 메모리 사용량: {final_memory:.1f}MB")
        print(f"총 메모리 증가량: +{memory_increase:.1f}MB")
        
        if memory_increase < 10:
            print("✅ 메모리 사용량이 안정적입니다.")
        elif memory_increase < 50:
            print("⚠️ 메모리 사용량이 약간 증가했습니다.")
        else:
            print("❌ 메모리 누수 가능성이 있습니다.")

def main():
    """메인 함수"""
    print("🧪 RAPTOR 시스템 성능 테스트 시작")
    print("=" * 60)
    
    tester = PerformanceTester()
    
    try:
        # 시스템 초기화 성능
        init_time, memory_usage = tester.initialize_system()
        
        # 기본 성능 벤치마크
        tester.benchmark_performance(50)
        
        # 메모리 프로파일링
        tester.memory_profile_test()
        
        # 스트레스 테스트 (1분간)
        tester.stress_test(1)
        
        print("\n🎉 모든 성능 테스트가 완료되었습니다!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()