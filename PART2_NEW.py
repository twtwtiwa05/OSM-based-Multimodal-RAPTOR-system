#!/usr/bin/env python3
"""
강남구 Time-Expanded Multimodal RAPTOR v2.0
- 대중교통 + 공유 모빌리티 통합 경로 탐색
- OSM 기반 도보/모빌리티 경로 계산
- 파레토 최적화 및 사용자 선호도 반영
"""

import pickle
import networkx as nx
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math
import logging
import sys

# PART1_2의 클래스 import (pickle 로드를 위해)
sys.path.append('.')
try:
    from PART1_2 import Stop, Route, Trip
    CLASSES_LOADED = True
except ImportError:
    CLASSES_LOADED = False
    # 클래스 정의 (pickle 로드용)
    @dataclass
    class Stop:
        stop_id: str
        stop_name: str
        stop_lat: float
        stop_lon: float
        stop_type: int = 0
        zone_id: str = 'gangnam'
    
    @dataclass  
    class Route:
        route_id: str
        route_short_name: str
        route_long_name: str
        route_type: int
        route_color: str = None
        n_trips: int = 0
    
    @dataclass
    class Trip:
        trip_id: str
        route_id: str
        service_id: str
        direction_id: int = 0
        stop_times: List = field(default_factory=list)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# 1. 데이터 구조 및 설정
# ============================================================================

class TransportMode(Enum):
    """교통 수단 타입"""
    WALK = "walk"
    BUS = "bus"
    SUBWAY = "subway"
    BIKE = "bike"           # 따릉이
    KICKBOARD = "kickboard" # 전동킥보드
    EBIKE = "ebike"         # 전기자전거


@dataclass
class RoutePreference:
    """사용자 선호도 설정"""
    # 기본 가중치 (합이 1.0)
    time_weight: float = 0.4        # 시간 중요도
    transfer_weight: float = 0.3    # 환승 횟수 중요도  
    walk_weight: float = 0.2        # 도보 거리 중요도
    cost_weight: float = 0.1        # 비용 중요도
    
    # 제약 조건
    max_walk_distance: float = 1000  # 최대 도보 거리 (미터)
    max_total_time: float = 120      # 최대 총 소요시간 (분)
    max_transfers: int = 3           # 최대 환승 횟수


@dataclass 
class JourneyState:
    """여정 중 상태"""
    total_cost: float = 0.0
    
    def copy(self):
        return JourneyState(
            total_cost=self.total_cost
        )

@dataclass
class AccessOption:
    """출발지 접근 옵션"""
    stop_id: str
    stop_idx: int
    access_time: float                  # 접근 시간 (분)
    access_mode: TransportMode
    access_cost: float = 0.0
    initial_state: JourneyState = field(default_factory=JourneyState)

@dataclass
class Journey:
    """완성된 여정"""
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    departure_time: int
    arrival_time: int
    total_time: float
    total_cost: float
    transfers: int
    total_walk_distance: float
    
    legs: List[Dict] = field(default_factory=list)
    
    def get_score(self, preference: RoutePreference) -> float:
        """선호도 기반 점수 계산 (낮을수록 좋음)"""
        score = (
            self.total_time * preference.time_weight +
            self.transfers * 10 * preference.transfer_weight +  # 환승당 10분 페널티
            self.total_walk_distance / 80 * preference.walk_weight +  # 도보속도 80m/분
            self.total_cost / 1000 * preference.cost_weight  # 비용 정규화
        )
            
        return score

# ============================================================================
# 2. 설정 상수
# ============================================================================

# 교통수단별 속도 (km/h)
SPEEDS = {
    TransportMode.WALK: 4.8,
    TransportMode.BUS: 50.0,
    TransportMode.SUBWAY: 40.0
}

# 교통수단별 비용 (원)
COSTS = {
    TransportMode.WALK: 0,
    
    TransportMode.BUS: 1370,
    TransportMode.SUBWAY: 1370
}

# 알고리즘 설정
MAX_ROUNDS = 6
INF = float('inf')

# ============================================================================
# 3. 메인 클래스
# ============================================================================

class TraditionalRAPTOR:
    """Traditional RAPTOR 경로 탐색기"""
    
    def __init__(self, data_path: str = "gangnam_raptor_data"):
        """초기화"""
        print("🚀 Traditional RAPTOR 초기화...")
        
        # 데이터 로드
        self.raptor_data = self._load_raptor_data(data_path)
        self.road_network = self._load_road_network()
        
        # 성능 최적화용 캐시
        self._road_distance_cache = {}
        
        # RAPTOR 데이터 추출
        self.stops = self.raptor_data['stops']
        self.routes = self.raptor_data['routes'] 
        self.trips = self.raptor_data['trips']
        self.timetables = self.raptor_data['timetables']
        self.transfers = self.raptor_data['transfers']
        self.stop_routes = self.raptor_data['stop_routes']
        self.routes_by_stop = self.raptor_data['routes_by_stop']  # 추가!
        self.route_stop_sequences = self.raptor_data['route_stop_sequences']
        self.stop_index_map = self.raptor_data['stop_index_map']
        self.index_to_stop = self.raptor_data['index_to_stop']
        
        
        print(f"   ✅ 정류장: {len(self.stops):,}개")
        print(f"   ✅ 노선: {len(self.routes):,}개") 
        print(f"   ✅ 환승: {sum(len(t) for t in self.transfers.values()):,}개")
        
    def _load_raptor_data(self, data_path: str) -> Dict:
        """RAPTOR 데이터 로드"""
        try:
            with open(f"{data_path}/raptor_data.pkl", 'rb') as f:
                data = pickle.load(f)
            return data
        except Exception as e:
            raise Exception(f"RAPTOR 데이터 로드 실패: {e}")
    
    def _load_road_network(self) -> nx.Graph:
        """도로 네트워크 로드"""
        try:
            # pickle 파일 우선 시도
            try:
                with open("gangnam_road_network.pkl", 'rb') as f:
                    return pickle.load(f)
            except:
                # GraphML 파일 시도
                return nx.read_graphml("gangnam_road_network.graphml")
        except Exception as e:
            logger.warning(f"도로 네트워크 로드 실패: {e}")
            return None
    
    # ========================================================================
    # 4. 접근점 탐색
    # ========================================================================
    
    def find_access_options(self, origin: Tuple[float, float], 
                          preference: RoutePreference) -> List[AccessOption]:
        """출발지에서 도보로 접근 가능한 정류장들 탐색"""
        
        print(f"\n🎯 도보 접근점 탐색")
        
        # 도보로 갈 수 있는 정류장만
        walking_options = self._find_walking_access(origin, preference.max_walk_distance)
        
        # 거리순 정렬 후 상위 30개만
        walking_options.sort(key=lambda x: x.access_time)
        limited_options = walking_options[:30]
        
        print(f"   ✅ 총 {len(limited_options)}개 도보 접근점 발견")
        return limited_options
    
    def _find_walking_access(self, origin: Tuple[float, float], 
                           max_distance: float) -> List[AccessOption]:
        """도보로 접근 가능한 정류장 탐색"""
        options = []
        
        for stop_id, stop in self.stops.items():
            distance = self._calculate_walk_distance(origin, (stop.stop_lat, stop.stop_lon))
            
            if distance <= max_distance:
                walk_time = distance / (SPEEDS[TransportMode.WALK] * 1000 / 60)  # 분 변환
                
                if stop_id in self.stop_index_map:
                    stop_idx = self.stop_index_map[stop_id]
                    
                    options.append(AccessOption(
                        stop_id=stop_id,
                        stop_idx=stop_idx,
                        access_time=walk_time,
                        access_mode=TransportMode.WALK,
                        access_cost=0.0,
                        initial_state=JourneyState()
                    ))
        
        return sorted(options, key=lambda x: x.access_time)[:20]  # 상위 20개만
    
    
    
    
    
    
    # ========================================================================
    # 5. Time-Expanded RAPTOR 알고리즘
    # ========================================================================
    
    def find_routes(self, origin: Tuple[float, float], destination: Tuple[float, float],
                   departure_time: str, preference: RoutePreference = None) -> List[Journey]:
        """경로 탐색 메인 함수"""
        
        if preference is None:
            preference = RoutePreference()
        
        print(f"\n🚀 대중교통 경로 탐색 시작")
        print(f"   출발: {origin}")
        print(f"   도착: {destination}")  
        print(f"   출발시간: {departure_time}")
        
        # 출발시간을 분 단위로 변환
        dep_minutes = self._time_to_minutes(departure_time)
        
        # 1. 도보 접근점 탐색
        access_options = self.find_access_options(origin, preference)
        if not access_options:
            print("❌ 접근 가능한 정류장을 찾을 수 없습니다")
            return []
        
        # 2. Traditional RAPTOR 실행
        journeys = self._run_traditional_raptor(
            access_options, destination, dep_minutes, preference
        )
        
        # 3. 파레토 최적화
        optimized_journeys = self._pareto_optimize(journeys, preference)
        
        print(f"\n✅ 총 {len(optimized_journeys)}개 최적 경로 발견")
        return optimized_journeys
    
    def _run_traditional_raptor(self, access_options: List[AccessOption],
                                destination: Tuple[float, float], departure_time: int,
                                preference: RoutePreference) -> List[Journey]:
        """Traditional RAPTOR 알고리즘 실행"""
        
        print(f"\n⚡ Traditional RAPTOR 실행...")
        
        n_stops = len(self.stops)
        
        # tau[k][stop] = 라운드 k에서 stop에 도착하는 최소 시간
        tau = [[INF] * n_stops for _ in range(MAX_ROUNDS + 1)]
        
        # journey_states[k][stop] = 라운드 k에서 stop에서의 여정 상태
        journey_states = [{} for _ in range(MAX_ROUNDS + 1)]
        
        # parent 추적 (경로 재구성용)
        parent = [{} for _ in range(MAX_ROUNDS + 1)]
        
        # 1. 초기화: 접근점들 설정
        initial_stops = []
        for option in access_options:
            arrival_time = departure_time + option.access_time
            stop_idx = option.stop_idx
            
            tau[0][stop_idx] = arrival_time
            journey_states[0][stop_idx] = option.initial_state.copy()
            parent[0][stop_idx] = {
                'type': 'access',
                'access_option': option,
                'departure_time': departure_time
            }
            initial_stops.append((option.stop_id, arrival_time))
        
        print(f"   초기 접근 정류장: {len(initial_stops)}개")
        for stop_id, arr_time in initial_stops[:5]:  # 처음 5개만 출력
            stop = self.stops[stop_id]
            arr_time_int = int(arr_time)
            print(f"      - {stop.stop_name}: {arr_time_int//60:02d}:{arr_time_int%60:02d} 도착")
        
        # 2. RAPTOR 라운드 진행
        for k in range(1, MAX_ROUNDS + 1):
            print(f"   라운드 {k} 시작...")
            marked_stops = set()
            
            # 2-1. 대중교통 기반 전파
            route_marked = self._route_based_propagation(k, tau, journey_states, parent)
            marked_stops.update(route_marked)
            print(f"      대중교통 전파: {len(route_marked)}개 정류장 업데이트")
            
            
            # 2-2. 환승 전파 (도보)
            transfer_before = sum(1 for i in range(len(tau[k])) if tau[k][i] < INF)
            self._transfer_propagation(k, tau, journey_states, parent)
            transfer_after = sum(1 for i in range(len(tau[k])) if tau[k][i] < INF)
            print(f"      환승 전파: {transfer_after - transfer_before}개 정류장 추가")
            
            total_reachable = sum(1 for i in range(len(tau[k])) if tau[k][i] < INF)
            print(f"      라운드 {k} 총 도달 가능: {total_reachable}개 정류장")
            
            if not marked_stops:
                print(f"   라운드 {k}에서 더 이상 개선 없음, 종료")
                break
        
        # 3. 목적지로의 경로 수집
        journeys = self._collect_destination_journeys(destination, tau, journey_states, parent, preference)
        
        return journeys
    
    def _route_based_propagation(self, k: int, tau: List[List[float]], 
                               journey_states: List[Dict], parent: List[Dict]) -> Set[int]:
        """대중교통 노선 기반 전파 - RAPTOR 표준 알고리즘"""
        marked = set()
        routes_to_scan = set()
        
        # 1단계: k-1 라운드에 도달한 정류장에서 탑승 가능한 노선들 수집
        for stop_idx in range(len(tau[k-1])):
            if tau[k-1][stop_idx] < INF:
                # routes_by_stop을 사용하여 효율적으로 노선 찾기
                if stop_idx in self.routes_by_stop:
                    for route_id in self.routes_by_stop[stop_idx]:
                        routes_to_scan.add(route_id)
        
        
        # 2단계: 각 노선별로 처리
        
        for route_id in routes_to_scan:
            
            timetable = self.timetables.get(route_id)
            stop_sequence = self.route_stop_sequences.get(route_id, [])
            
            if not timetable or len(stop_sequence) < 2:
                continue
            
            # 시간표가 정상적인 구조인지 확인
            if not isinstance(timetable[0], list):
                continue
            
            # 이 노선의 각 trip별로 처리
            # 버그 수정: 지하철 노선들의 시간표 불일치 문제 해결 (확장된 수정)
            if timetable:
                trips_counts = [len(times) for times in timetable]
                min_trips = min(trips_counts)
                max_trips = max(trips_counts)
                
                # 지하철 노선에서 시간표 불일치가 있는 경우 최대값 사용
                if route_id.startswith('RR_') and min_trips != max_trips:
                    n_trips = max_trips
                else:
                    n_trips = len(timetable[0])
                
            else:
                n_trips = 0
            
            
            for trip_idx in range(n_trips):
                
                # 이 trip에서 탑승할 정류장 찾기
                board_stop_idx = -1
                board_time = INF
                
                for i, stop_id in enumerate(stop_sequence):
                    if stop_id not in self.stop_index_map:
                        continue
                    
                    stop_idx = self.stop_index_map[stop_id]
                    arrival_time = tau[k-1][stop_idx]
                    
                    
                    if arrival_time < INF and i < len(timetable):
                        if trip_idx < len(timetable[i]):
                            dep_time = timetable[i][trip_idx]
                            
                            # 24시간 초과 출발시간 정규화
                            if dep_time >= 24 * 60:  # 24시간(1440분) 초과
                                dep_time = dep_time % (24 * 60)
                            
                            # 도착시간 이후에 출발하는 경우만 탑승 가능
                            if dep_time >= arrival_time:
                                board_stop_idx = i
                                board_time = dep_time
                                
                                # 디버깅: 탑승 성공  
                                break
                
                # 탑승 가능하면 이후 정류장들 업데이트
                if board_stop_idx >= 0:
                    board_stop_id = stop_sequence[board_stop_idx]
                    
                    
                    # 하차 가능한 정류장들 업데이트
                    for j in range(board_stop_idx + 1, len(stop_sequence)):
                        alight_stop_id = stop_sequence[j]
                        if alight_stop_id not in self.stop_index_map:
                            continue
                        
                        alight_stop_idx = self.stop_index_map[alight_stop_id]
                        
                        
                        # 같은 trip의 도착 시간
                        if j < len(timetable) and trip_idx < len(timetable[j]):
                            alight_time = timetable[j][trip_idx]
                            
                            # 24시간 초과 시간표 정규화 (다음날 데이터를 당일로 변환)
                            if alight_time >= 24 * 60:  # 24시간(1440분) 초과
                                alight_time = alight_time % (24 * 60)
                            
                            
                            # 시간 순환 문제 해결: 도착시간이 탑승시간보다 이른 경우
                            if alight_time < board_time:
                                # 탑승시간이 22시 이후이고 도착시간이 6시 이전인 경우 (자정 넘김)
                                if board_time >= 22 * 60 and alight_time <= 6 * 60:
                                    alight_time += 24 * 60  # 다음날로 처리
                                else:
                                    continue  # 잘못된 데이터 건너뛰기
                            
                            # 개선된 경우만 업데이트
                            if alight_time < tau[k][alight_stop_idx]:
                                tau[k][alight_stop_idx] = alight_time
                                
                            else:
                                
                                # 여정 상태 복사
                                board_state = journey_states[k-1].get(
                                    self.stop_index_map[board_stop_id], JourneyState()
                                )
                                journey_states[k][alight_stop_idx] = board_state.copy()
                                
                                # 대중교통 비용 추가 (첫 탑승 시에만)
                                # board_state가 이미 같은 노선을 타고 있었는지 확인
                                prev_parent = parent[k-1].get(self.stop_index_map[board_stop_id], {})
                                if prev_parent.get('type') != 'route' or prev_parent.get('route_id') != route_id:
                                    # 새로운 노선에 탑승하는 경우만 비용 추가
                                    route = self.routes.get(route_id)
                                    if route and route.route_type == 1:  # 지하철
                                        journey_states[k][alight_stop_idx].total_cost += COSTS[TransportMode.SUBWAY]
                                    else:  # 버스
                                        journey_states[k][alight_stop_idx].total_cost += COSTS[TransportMode.BUS]
                                
                                parent[k][alight_stop_idx] = {
                                    'type': 'route',
                                    'route_id': route_id,
                                    'board_stop': board_stop_id,
                                    'alight_stop': alight_stop_id,
                                    'board_time': board_time,
                                    'alight_time': alight_time,
                                    'from_round': k-1,
                                    'from_stop': self.stop_index_map[board_stop_id]
                                }
                                
                                marked.add(alight_stop_idx)
        
        return marked
    
    
    
    
    
    def _transfer_propagation(self, k: int, tau: List[List[float]],
                             journey_states: List[Dict], parent: List[Dict]):
        """도보 환승 전파"""
        
        for stop_idx in range(len(tau[k])):
            if tau[k][stop_idx] == INF:
                continue
            
            stop_id = self.index_to_stop.get(stop_idx)
            if not stop_id or stop_id not in self.transfers:
                continue
            
            current_time = tau[k][stop_idx]
            current_state = journey_states[k].get(stop_idx, JourneyState())
            
            # 도보 환승
            for transfer_stop_id, transfer_time in self.transfers[stop_id]:
                if transfer_stop_id not in self.stop_index_map:
                    continue
                
                transfer_idx = self.stop_index_map[transfer_stop_id]
                arrival_time = current_time + transfer_time
                
                if arrival_time < tau[k][transfer_idx]:
                    tau[k][transfer_idx] = arrival_time
                    journey_states[k][transfer_idx] = current_state.copy()
                    
                    parent[k][transfer_idx] = {
                        'type': 'transfer',
                        'transfer_type': 'walk',
                        'from_stop': stop_id,
                        'to_stop': transfer_stop_id,
                        'transfer_time': transfer_time,
                        'from_round': k,
                        'from_stop_idx': stop_idx
                    }
    
    
    # ========================================================================
    # 6. 목적지 도달 및 경로 재구성
    # ========================================================================
    
    def _collect_destination_journeys(self, destination: Tuple[float, float],
                                    tau: List[List[float]], journey_states: List[Dict],
                                    parent: List[Dict], preference: RoutePreference) -> List[Journey]:
        """목적지로 도달하는 모든 경로 수집"""
        
        print(f"\n🎯 목적지 도달 경로 수집...")
        journeys = []
        
        # 목적지 근처 정류장들 찾기
        destination_stops = self._find_destination_stops(destination, preference.max_walk_distance)
        print(f"   목적지 근처 정류장: {len(destination_stops)}개")
        for stop_id, egress_time, mode in destination_stops[:5]:
            stop = self.stops[stop_id]
            print(f"      - {stop.stop_name}: {egress_time:.1f}분 도보")
        
        # 출발 시간 가져오기 (첫 번째 접근점의 출발시간)
        departure_time = INF
        for stop_idx in range(len(tau[0])):
            if stop_idx in parent[0] and parent[0][stop_idx]['type'] == 'access':
                departure_time = min(departure_time, parent[0][stop_idx]['departure_time'])
        
        # 각 라운드에서 도달 가능한 정류장 확인
        found_paths = 0
        for k in range(MAX_ROUNDS + 1):
            round_paths = 0
            for dest_stop_id, egress_time, egress_mode in destination_stops:
                # 신사역 관련 디버깅
                if dest_stop_id not in self.stop_index_map:
                    continue
                
                stop_idx = self.stop_index_map[dest_stop_id]
                if tau[k][stop_idx] < INF:
                    arrival_time = tau[k][stop_idx]
                    
                    # 출발시간보다 이른 도착시간은 무시 (전날 데이터)
                    if arrival_time < departure_time:
                        continue
                    
                    round_paths += 1
                    arrival_time_int = int(arrival_time)
                    stop = self.stops[dest_stop_id]
                    print(f"      {stop.stop_name}: {arrival_time_int//60:02d}:{arrival_time_int%60:02d} 도착")
                    
                    # 경로 재구성
                    journey = self._reconstruct_journey(
                        destination, k, stop_idx, arrival_time,
                        egress_time, egress_mode, journey_states[k].get(stop_idx, JourneyState()),
                        parent
                    )
                    
                    if journey and journey.departure_time >= departure_time:
                        journeys.append(journey)
                        found_paths += 1
                    else:
                        print(f"         경로 재구성 실패 또는 유효하지 않은 시간")
            
            if round_paths > 0:
                print(f"   라운드 {k}: {round_paths}개 목적지 정류장 도달 가능")
        
        print(f"   ✅ {found_paths}개 경로 발견")
        
        # 대중교통 구간이 같은 경로는 제거 (가장 짧은 도보 거리만 유지)
        unique_transit_journeys = {}
        for journey in journeys:
            # 대중교통 구간만 추출
            transit_key = []
            for leg in journey.legs:
                if leg['type'] == 'transit':
                    transit_key.append((leg['from'], leg['to'], leg.get('route_name', '')))
            
            transit_tuple = tuple(transit_key)
            
            # 처음 보는 대중교통 경로이거나 더 짧은 도보 거리인 경우만 저장
            if transit_tuple not in unique_transit_journeys or \
               journey.total_walk_distance < unique_transit_journeys[transit_tuple].total_walk_distance:
                unique_transit_journeys[transit_tuple] = journey
        
        return list(unique_transit_journeys.values())
    
    def _find_destination_stops(self, destination: Tuple[float, float], 
                              max_distance: float) -> List[Tuple[str, float, str]]:
        """목적지 근처 정류장들 찾기"""
        dest_stops = []
        
        for stop_id, stop in self.stops.items():
            distance = self._calculate_walk_distance(destination, (stop.stop_lat, stop.stop_lon))
            
            if distance <= max_distance:
                walk_time = distance / (SPEEDS[TransportMode.WALK] * 1000 / 60)
                dest_stops.append((stop_id, walk_time, 'walk'))
        
        return sorted(dest_stops, key=lambda x: x[1])[:20]  # 상위 20개
    
    def _reconstruct_journey(self, destination: Tuple[float, float], final_round: int,
                           final_stop_idx: int, arrival_time: float, egress_time: float,
                           egress_mode: str, final_state: JourneyState,
                           parent: List[Dict]) -> Optional[Journey]:
        """경로 재구성"""
        
        try:
            legs = []
            current_round = final_round
            current_stop_idx = final_stop_idx
            total_walk_distance = 0
            transfers = 0
            last_route_id = None  # 이전 노선 추적
            
            # 도착 구간 추가
            final_stop_id = self.index_to_stop[final_stop_idx]
            final_stop = self.stops[final_stop_id]
            
            legs.append({
                'type': 'egress',
                'mode': egress_mode,
                'from': final_stop.stop_name,
                'to': 'destination',
                'departure_time': arrival_time,
                'arrival_time': arrival_time + egress_time,
                'duration': egress_time,
                'distance': egress_time * SPEEDS[TransportMode.WALK] * 1000 / 60
            })
            
            total_walk_distance += egress_time * SPEEDS[TransportMode.WALK] * 1000 / 60
            
            # 역방향으로 경로 추적
            while current_round >= 0 and current_stop_idx in parent[current_round]:
                p = parent[current_round][current_stop_idx]
                
                if p['type'] == 'access':
                    # 접근 구간
                    option = p['access_option']
                    legs.append({
                        'type': 'access',
                        'mode': option.access_mode.value,
                        'from': 'origin',
                        'to': self.stops[option.stop_id].stop_name,
                        'departure_time': p['departure_time'],
                        'arrival_time': p['departure_time'] + option.access_time,
                        'duration': option.access_time,
                        'cost': option.access_cost
                    })
                    
                    total_walk_distance += option.access_time * SPEEDS[TransportMode.WALK] * 1000 / 60
                    
                    break
                
                elif p['type'] == 'route':
                    # 대중교통 구간
                    route = self.routes[p['route_id']]
                    mode = 'subway' if route.route_type == 1 else 'bus'
                    
                    legs.append({
                        'type': 'transit',
                        'mode': mode,
                        'route_name': route.route_short_name,
                        'from': self.stops[p['board_stop']].stop_name,
                        'to': self.stops[p['alight_stop']].stop_name,
                        'departure_time': p['board_time'],
                        'arrival_time': p['alight_time'],
                        'duration': p['alight_time'] - p['board_time'],
                        'cost': COSTS[TransportMode.SUBWAY] if mode == 'subway' else COSTS[TransportMode.BUS]
                    })
                    
                    # 대중교통 사용 카운트 (첫 번째 탑승 이후부터 환승)
                    if last_route_id is not None:
                        transfers += 1
                    last_route_id = p['route_id']
                    
                    current_round = p['from_round']
                    current_stop_idx = p['from_stop']
                
                
                elif p['type'] == 'transfer':
                    # 환승 구간 - 같은 정류장 간 환승은 제외
                    from_stop_name = self.stops[p['from_stop']].stop_name
                    to_stop_name = self.stops[p['to_stop']].stop_name
                    
                    # 같은 정류장 간 환승은 추가하지 않음
                    if from_stop_name != to_stop_name and p['transfer_time'] > 0:
                        legs.append({
                            'type': 'transfer',
                            'mode': p['transfer_type'],
                            'from': from_stop_name,
                            'to': to_stop_name,
                            'duration': p['transfer_time'],
                            'cost': 0
                        })
                        
                        if p['transfer_type'] == 'walk':
                            total_walk_distance += p['transfer_time'] * SPEEDS[TransportMode.WALK] * 1000 / 60
                    
                    current_stop_idx = p['from_stop_idx']
                
                else:
                    break
            
            # 리스트 뒤집기 (시간 순서대로)
            legs.reverse()
            
            # 경로 정리: 불필요한 환승 제거 및 같은 노선 합치기
            cleaned_legs = []
            
            for i, leg in enumerate(legs):
                # 불필요한 환승 건너뛰기 (같은 정류장 간 0분 환승)
                if (leg['type'] == 'transfer' and 
                    leg.get('duration', 0) == 0 and 
                    leg.get('from') == leg.get('to')):
                    continue
                
                # 연속된 같은 노선 합치기
                if (leg['type'] == 'transit' and cleaned_legs and 
                    cleaned_legs[-1]['type'] == 'transit' and
                    cleaned_legs[-1].get('route_name') == leg.get('route_name')):
                    # 마지막 leg를 확장
                    cleaned_legs[-1]['to'] = leg['to']
                    cleaned_legs[-1]['arrival_time'] = leg['arrival_time']
                    cleaned_legs[-1]['duration'] = leg['arrival_time'] - cleaned_legs[-1]['departure_time']
                else:
                    cleaned_legs.append(leg)
            
            legs = cleaned_legs
            
            # Journey 객체 생성
            total_time = arrival_time + egress_time - legs[0]['departure_time'] if legs else 0
            # 비용은 final_state에 이미 정확히 계산되어 있음
            total_cost = final_state.total_cost
            
            return Journey(
                origin=destination,  # 임시
                destination=destination,
                departure_time=legs[0]['departure_time'] if legs else 0,
                arrival_time=arrival_time + egress_time,
                total_time=total_time,
                total_cost=total_cost,
                transfers=transfers,
                total_walk_distance=total_walk_distance,
                legs=legs
            )
            
        except Exception as e:
            logger.error(f"경로 재구성 오류: {e}")
            return None
    
    # ========================================================================
    # 7. 파레토 최적화
    # ========================================================================
    
    def _pareto_optimize(self, journeys: List[Journey], 
                        preference: RoutePreference) -> List[Journey]:
        """파레토 최적화 및 선호도 기반 정렬"""
        
        if not journeys:
            return []
        
        print(f"\n🎯 최적 경로 선택 ({len(journeys)}개 → ", end="")
        
        # 1. 중복 제거 및 기본 필터링
        unique_journeys = {}
        for journey in journeys:
            if (journey.total_time <= preference.max_total_time and
                journey.transfers <= preference.max_transfers and
                journey.total_walk_distance <= preference.max_walk_distance):
                
                # 경로 키 생성 (주요 경유 정류장 포함)
                main_stops = []
                for leg in journey.legs:
                    if leg['type'] == 'transit':
                        main_stops.append((leg['from'], leg['to'], leg.get('route_name', '')))
                
                # 출발/도착 시간을 분 단위로 반올림해서 미세한 차이는 무시
                journey_key = (
                    round(journey.departure_time),  # 분 단위 반올림
                    round(journey.arrival_time),    # 분 단위 반올림
                    journey.total_cost,
                    journey.transfers,
                    tuple(main_stops)
                )
                
                # 중복이 아니거나 더 나은 점수인 경우만 저장
                if journey_key not in unique_journeys or \
                   journey.get_score(preference) < unique_journeys[journey_key].get_score(preference):
                    unique_journeys[journey_key] = journey
        
        filtered = list(unique_journeys.values())
        
        if not filtered:
            print("0개) - 제약조건을 만족하는 경로 없음")
            return []
        
        # 2. 파레토 최적화
        pareto_optimal = []
        
        for i, journey1 in enumerate(filtered):
            is_dominated = False
            
            for j, journey2 in enumerate(filtered):
                if i != j:
                    # journey2가 journey1을 지배하는지 확인
                    if (journey2.total_time <= journey1.total_time and
                        journey2.transfers <= journey1.transfers and
                        journey2.total_walk_distance <= journey1.total_walk_distance and
                        journey2.total_cost <= journey1.total_cost):
                        
                        # 적어도 하나는 더 좋아야 함 (같으면 지배하지 않음)
                        if (journey2.total_time < journey1.total_time or
                            journey2.transfers < journey1.transfers or
                            journey2.total_walk_distance < journey1.total_walk_distance or
                            journey2.total_cost < journey1.total_cost):
                            is_dominated = True
                            break
            
            if not is_dominated:
                pareto_optimal.append(journey1)
        
        # 3. 선호도 기반 정렬 후 상위 5개 선택
        pareto_optimal.sort(key=lambda j: j.get_score(preference))
        
        # 파레토 최적이 너무 적으면 필터링된 전체에서 상위 5개 선택
        if len(pareto_optimal) < 5:
            print(f"{len(pareto_optimal)}개 파레토 최적 → 전체 중 상위 5개)")
            # 필터링된 전체를 점수순 정렬
            filtered.sort(key=lambda j: j.get_score(preference))
            # 중복 제거하면서 상위 5개 선택
            final_selection = []
            seen_keys = set()
            for journey in filtered:
                # 더 구체적인 키로 중복 체크 (주요 대중교통 구간 포함)
                transit_segments = []
                for leg in journey.legs:
                    if leg['type'] == 'transit':
                        transit_segments.append((leg['from'], leg['to'], leg.get('route_name', '')))
                
                key = (
                    round(journey.total_time), 
                    journey.transfers, 
                    journey.total_cost,
                    tuple(transit_segments)  # 주요 대중교통 구간 포함
                )
                
                if key not in seen_keys:
                    seen_keys.add(key)
                    final_selection.append(journey)
                if len(final_selection) >= 5:
                    break
            return final_selection
        else:
            print(f"{len(pareto_optimal)}개 파레토 최적 → 상위 5개)")
            return pareto_optimal[:5]
    
    # ========================================================================
    # 8. 유틸리티 함수들
    # ========================================================================
    
    def _time_to_minutes(self, time_str: str) -> int:
        """시간 문자열을 분으로 변환"""
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            return time_obj.hour * 60 + time_obj.minute
        except:
            # 기본값: 오전 8시
            return 8 * 60
    
    def _calculate_distance(self, coord1: Tuple[float, float], 
                          coord2: Tuple[float, float]) -> float:
        """두 좌표 간 직선거리 계산 (미터)"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        R = 6371000  # 지구 반지름 (미터)
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _calculate_road_distance(self, coord1: Tuple[float, float],
                               coord2: Tuple[float, float]) -> float:
        """OSM 도로망 기반 최단거리 계산 (일단 직선거리로 근사)"""
        # OSM 계산이 너무 오래 걸리므로 일단 직선거리로 근사
        return self._calculate_distance(coord1, coord2) * 1.3  # 도로 우회 계수
    
    def _calculate_walk_distance(self, coord1: Tuple[float, float],
                               coord2: Tuple[float, float]) -> float:
        """도보 거리 계산 - 짧은 거리는 OSM 사용"""
        straight_distance = self._calculate_distance(coord1, coord2)
        
        # 300m 이내이고 OSM 네트워크가 있으면 실제 경로 계산
        if straight_distance <= 300 and self.road_network:
            # 캐시 확인
            cache_key = (round(coord1[0], 5), round(coord1[1], 5), 
                        round(coord2[0], 5), round(coord2[1], 5))
            if cache_key in self._road_distance_cache:
                return self._road_distance_cache[cache_key]
            
            try:
                # 가장 가까운 노드 찾기
                node1 = self._find_nearest_node(coord1)
                node2 = self._find_nearest_node(coord2)
                
                if node1 and node2 and node1 != node2:
                    # 최단 경로 계산
                    path_length = nx.shortest_path_length(self.road_network, 
                                                        node1, node2, weight='length')
                    
                    # 캐시 저장
                    if len(self._road_distance_cache) < 5000:
                        self._road_distance_cache[cache_key] = path_length
                    
                    return path_length
            except:
                pass
        
        # 실패시 또는 먼 거리는 근사값
        return straight_distance * 1.2  # 도보는 1.2 계수 (더 직선적)
    
    def _find_nearest_node(self, coord: Tuple[float, float]) -> Optional[Any]:
        """가장 가까운 도로 네트워크 노드 찾기"""
        if not self.road_network:
            return None
        
        # 캐시 확인
        cache_key = (round(coord[0], 5), round(coord[1], 5))
        if hasattr(self, '_nearest_node_cache'):
            if cache_key in self._nearest_node_cache:
                return self._nearest_node_cache[cache_key]
        else:
            self._nearest_node_cache = {}
        
        min_distance = INF
        nearest_node = None
        
        for node, data in self.road_network.nodes(data=True):
            if 'y' in data and 'x' in data:
                node_coord = (data['y'], data['x'])
                distance = self._calculate_distance(coord, node_coord)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node
                
                # 10m 이내면 충분히 가까움
                if distance < 10:
                    break
        
        # 캐시 저장
        if len(self._nearest_node_cache) < 10000:
            self._nearest_node_cache[cache_key] = nearest_node
        
        return nearest_node
    
    def print_journey(self, journey: Journey, preference: RoutePreference):
        """여정 정보 출력"""
        print(f"\n{'='*80}")
        print(f"🎯 여정 정보 (점수: {journey.get_score(preference):.2f})")
        print(f"{'='*80}")
        dep_time_int = int(journey.departure_time)
        arr_time_int = int(journey.arrival_time)
        print(f"📍 출발시간: {dep_time_int//60:02d}:{dep_time_int%60:02d}")
        print(f"📍 도착시간: {arr_time_int//60:02d}:{arr_time_int%60:02d}")
        print(f"⏰ 총 소요시간: {journey.total_time:.1f}분")
        print(f"💰 총 비용: {journey.total_cost:,.0f}원")
        print(f"🔄 환승 횟수: {journey.transfers}회")
        print(f"🚶 도보 거리: {journey.total_walk_distance:.0f}m")
        
        print(f"\n📋 상세 경로:")
        for i, leg in enumerate(journey.legs, 1):
            mode_emoji = {
                'walk': '🚶', 'bus': '🚌', 'subway': '🚇',
                'bike': '🚲', 'kickboard': '🛴', 'ebike': '🚴'
            }
            
            emoji = mode_emoji.get(leg['mode'], '🔸')
            
            if leg['type'] == 'access':
                print(f"   {i}. {emoji} {leg['from']} → {leg['to']} ({leg['duration']:.1f}분)")
            elif leg['type'] == 'transit':
                print(f"   {i}. {emoji} {leg['route_name']}: {leg['from']} → {leg['to']} ({leg['duration']:.1f}분)")
            elif leg['type'] == 'transfer':
                print(f"   {i}. {emoji} 환승: {leg['from']} → {leg['to']} ({leg['duration']:.1f}분)")
            elif leg['type'] == 'egress':
                print(f"   {i}. {emoji} {leg['from']} → {leg['to']} ({leg['duration']:.1f}분)")

# ============================================================================
# 9. 메인 실행
# ============================================================================

def main():
    """메인 실행 함수"""
    print("🚀 Traditional RAPTOR 시작")
    
    try:
        # 시스템 초기화
        raptor = TraditionalRAPTOR()
        
        # 예시 경로 탐색
        print(f"\n" + "="*80)
        print("📍 예시 경로 탐색")
        print("="*80)
        
        # 출발지/목적지 설정 (압구정역 → 선정릉역) - 3호선 → 분당선 환승 테스트
        origin = (37.527070, 127.041927)      # 압구정역 (3호선)
        destination = (37.504528, 127.049348) # 선정릉역 (분당선)
        departure_time = "12:00"  # 오전 8시 - 출근시간대
        
        # 사용자 선호도 설정
        preference = RoutePreference(
            time_weight=0.4,
            transfer_weight=0.3,
            walk_weight=0.2,
            cost_weight=0.1
        )
        
        # 대중교통 경로 탐색
        print(f"\n🚇 대중교통 경로 탐색")
        journeys = raptor.find_routes(
            origin, destination, departure_time, preference
        )
        
        if journeys:
            print(f"\n✅ 최적 대중교통 경로 ({len(journeys)}개):")
            for i, journey in enumerate(journeys[:3], 1):
                print(f"\n[경로 {i}]")
                raptor.print_journey(journey, preference)
        
        print(f"\n🎉 경로 탐색 완료!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)