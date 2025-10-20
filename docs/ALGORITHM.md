#  RAPTOR 알고리즘 상세 설명

## 개요

RAPTOR (Rapid Public Transport Router)는 대중교통 네트워크에서 효율적인 경로 탐색을 위해 설계된 라운드 기반 알고리즘입니다.

## 알고리즘 특징

### 1. 라운드 기반 접근법

RAPTOR는 라운드(round) 개념을 사용하여 환승 횟수별로 최적 경로를 탐색합니다:

- **라운드 0**: 출발지에서 도보로 접근 가능한 정류장들
- **라운드 k**: 최대 k번의 환승으로 도달 가능한 정류장들

### 2. 핵심 데이터 구조

```python
tau[k][stop] = min_arrival_time  # 라운드 k에서 정류장 stop의 최소 도착시간
parent[k][stop] = (prev_stop, trip)  # 경로 재구성을 위한 부모 정보
```

### 3. 알고리즘 단계

#### Phase 1: Route-based Propagation
```python
for route in marked_routes:
    board_stop = -1
    for stop in route.stops:
        # 탑승 가능한 정류장 찾기
        if tau[k-1][stop] < INF:
            for trip in route.trips:
                if trip.departure_time[stop] >= tau[k-1][stop]:
                    board_stop = stop
                    break
        
        # 하차 가능한 정류장 업데이트
        if board_stop >= 0:
            arrival_time = trip.arrival_time[stop]
            if arrival_time < tau[k][stop]:
                tau[k][stop] = arrival_time
                parent[k][stop] = board_stop
```

#### Phase 2: Transfer Propagation
```python
for stop in updated_stops:
    for transfer_stop in transfers[stop]:
        walk_time = transfer_distance[stop][transfer_stop] / walking_speed
        new_time = tau[k][stop] + walk_time
        
        if new_time < tau[k][transfer_stop]:
            tau[k][transfer_stop] = new_time
            parent[k][transfer_stop] = stop
```

## 최적화 기법

### 1. 조기 종료 (Early Termination)
```python
if len(updated_stops_in_round) == 0:
    break  # 더 이상 개선되는 정류장이 없으면 종료
```

### 2. 마킹 최적화 (Route Marking)
```python
marked_routes = set()
for stop in updated_stops:
    for route in routes_by_stop[stop]:
        marked_routes.add(route)
```

### 3. 파레토 최적화
다목적 최적화를 위해 파레토 프론트를 유지:

```python
def is_pareto_optimal(journey1, journey2):
    better_in_any = False
    worse_in_any = False
    
    criteria = ['time', 'cost', 'transfers', 'walk_distance']
    for criterion in criteria:
        if getattr(journey1, criterion) < getattr(journey2, criterion):
            better_in_any = True
        elif getattr(journey1, criterion) > getattr(journey2, criterion):
            worse_in_any = True
    
    return better_in_any and not worse_in_any
```

## 시간 복잡도

- **최악의 경우**: O(R × E × T)
  - R: 라운드 수 (환승 횟수)
  - E: 간선 수 (노선-정류장 연결)
  - T: 평균 trip 수

- **실제 성능**: O(R × S × log(T))
  - S: 정류장 수
  - 효율적인 데이터 구조와 조기 종료로 성능 향상

## 메모리 최적화

### 1. 압축된 시간표
```python
# 시간표를 2차원 배열로 압축
timetable[route][stop_sequence_index][trip_index] = departure_time
```

### 2. 인덱스 매핑
```python
stop_index_map = {stop_id: index for index, stop_id in enumerate(stops)}
route_index_map = {route_id: index for index, route_id in enumerate(routes)}
```

### 3. 지연 로딩
필요한 시점에만 데이터를 메모리에 로드하여 메모리 사용량 최적화

## 멀티모달 확장

### 1. 도보 연결
```python
for stop in nearby_stops:
    walk_time = distance / walking_speed
    if walk_time <= max_walk_time:
        add_transfer(origin, stop, walk_time)
```

### 2. 환승 가중치
```python
transfer_penalty = base_transfer_time + transfer_walk_time
adjusted_time = arrival_time + transfer_penalty
```

## 실시간 적용

### 1. 지연 정보 반영
```python
if route.has_delay():
    adjusted_departure = scheduled_departure + delay_minutes
    timetable[route][stop][trip] = adjusted_departure
```

### 2. 동적 노선 업데이트
운행 중단이나 우회 운행 시 노선 정보를 동적으로 업데이트

## 성능 벤치마크

| 지표 | 값 |
|------|-----|
| 정류장 수 | 12,064개 |
| 노선 수 | 944개 |
| 평균 탐색 시간 | 2.3초 |
| 메모리 사용량 | 450MB |
| 라운드 수 | 평균 4라운드 |

## 코드 최적화 팁

### 1. NumPy 활용
```python
import numpy as np

# 배열 연산 최적화
tau = np.full((max_rounds, num_stops), np.inf)
```

### 2. 캐싱 전략
```python
@lru_cache(maxsize=1000)
def calculate_walk_time(stop1, stop2):
    return distance(stop1, stop2) / walking_speed
```

### 3. 병렬 처리
```python
from multiprocessing import Pool

def parallel_route_processing(routes):
    with Pool() as pool:
        results = pool.map(process_route, routes)
    return results
```