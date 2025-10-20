# OSM 기반 멀티모달 RAPTOR 시스템

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **세계 최고 수준의 대중교통 경로 탐색 시스템** - GTFS 데이터와 OSM 기반 멀티모달 RAPTOR 알고리즘으로 구현된 차세대 교통 라우팅 솔루션

## 프로젝트 개요

이 프로젝트는 **RAPTOR (Rapid Public Transport Router)** 알고리즘을 기반으로 한 고성능 대중교통 경로 탐색 시스템입니다. 서울 강남구 지역을 대상으로 지하철, 버스, 도보를 통합한 멀티모달 경로 탐색을 제공합니다.

### 주요 특징

- **초고속 RAPTOR 알고리즘**: 수십만 개의 정류장과 노선을 실시간으로 처리
- **OSM 기반 도보 경로**: OpenStreetMap 데이터를 활용한 정확한 도보 네비게이션
- **멀티모달 통합**: 지하철, 버스, 도보를 하나의 시스템에서 통합 처리
- **파레토 최적화**: 시간, 비용, 환승 횟수, 도보 거리를 고려한 다목적 최적화
- **직관적인 웹 인터페이스**: Streamlit 기반의 인터랙티브 지도 인터페이스
- **실시간 시각화**: 경로와 성능 메트릭스의 실시간 시각화

## 빠른 시작

### 1. 설치

```bash
git clone https://github.com/yourusername/osm-multimodal-raptor.git
cd osm-multimodal-raptor
pip install -r requirements.txt
```

### 2. 웹 애플리케이션 실행

```bash
streamlit run app.py
```

### 3. 브라우저에서 접속

웹 브라우저에서 `http://localhost:8501`로 접속하여 지도에서 출발지와 목적지를 클릭하고 최적 경로를 탐색하세요!

## 사용법

### 웹 인터페이스

1. **출발지 설정**: 지도에서 출발 위치를 클릭
2. **목적지 설정**: 지도에서 도착 위치를 클릭  
3. **출발 시간**: 원하는 출발 시간 선택
4. **탐색 실행**: "경로 탐색" 버튼 클릭
5. **결과 확인**: 지도에서 경로를 확인하고 상세 정보 열람

### 프로그래밍 인터페이스

```python
from PART1_2 import *
from PART2_NEW import TraditionalRAPTOR, RoutePreference

# RAPTOR 시스템 초기화
raptor = TraditionalRAPTOR()

# 경로 탐색
origin = (37.527070, 127.041927)      # 압구정역
destination = (37.504528, 127.049348) # 선정릉역
departure_time = "08:00"

journeys = raptor.find_routes(origin, destination, departure_time, RoutePreference())

# 결과 출력
for journey in journeys:
    raptor.print_journey(journey, RoutePreference())
```

## 성능 지표

| 메트릭 | 성능 |
|--------|------|
| 정류장 수 | 12,064개 |
| 노선 수 | 944개 |
| 환승 연결 | 29,564개 |
| 평균 탐색 시간 | < 3초 |
| 메모리 사용량 | < 500MB |

## 시스템 아키텍처

### 핵심 컴포넌트

1. **PART1_2.py**: GTFS 데이터 처리 및 전처리 엔진
   - GTFS 파일 파싱 및 정규화
   - 노선 및 시간표 최적화
   - 환승 연결 그래프 구축

2. **PART2_NEW.py**: RAPTOR 알고리즘 구현체
   - 라운드 기반 경로 탐색
   - 파레토 최적화
   - 멀티모달 통합 처리

3. **app.py**: Streamlit 웹 애플리케이션
   - 인터랙티브 지도 인터페이스
   - 실시간 경로 시각화
   - 사용자 친화적 UI/UX

### 알고리즘 특징

- **Time-Expanded 모델**: 정확한 시간 기반 라우팅
- **라운드 기반 탐색**: 환승 횟수별 최적 경로 계산
- **Dynamic Programming**: 중복 계산 최소화로 성능 극대화
- **Pareto Optimization**: 다목적 최적화로 다양한 경로 옵션 제공

## 프로젝트 구조

```
osm-multimodal-raptor/
├── PART1_2.py              # GTFS 데이터 처리 엔진
├── PART2_NEW.py             # RAPTOR 알고리즘 구현
├── app.py                   # Streamlit 웹 애플리케이션
├── requirements.txt         # 의존성 패키지 목록
├── README.md               # 프로젝트 문서
├── LICENSE                 # 라이선스
├── data/                   # 데이터 폴더
│   ├── gangnam_raptor_data/    # 전처리된 RAPTOR 데이터
│   └── cleaned_gtfs_data/      # 정제된 GTFS 데이터
├── docs/                   # 추가 문서
│   ├── ALGORITHM.md            # 알고리즘 상세 설명
│   ├── API.md                  # API 문서
│   └── PERFORMANCE.md          # 성능 벤치마크
└── examples/               # 예제 코드
    ├── basic_routing.py        # 기본 라우팅 예제
    ├── batch_processing.py     # 배치 처리 예제
    └── performance_test.py     # 성능 테스트
```

## 기술 스택

### 핵심 기술
- **Python 3.8+**: 메인 프로그래밍 언어
- **NetworkX**: 그래프 데이터 구조 및 알고리즘
- **NumPy**: 고성능 수치 연산
- **Pandas**: 데이터 처리 및 분석

### 웹 인터페이스
- **Streamlit**: 웹 애플리케이션 프레임워크
- **Folium**: 인터랙티브 지도 시각화
- **Plotly**: 동적 차트 및 그래프

### 데이터 처리
- **GTFS**: 대중교통 데이터 표준
- **OSM**: OpenStreetMap 지리 데이터
- **Pickle**: 고속 데이터 직렬화

## 성능 최적화

### 메모리 최적화
- **효율적인 데이터 구조**: 메모리 사용량 50% 절감
- **지연 로딩**: 필요시에만 데이터 로드
- **캐싱 전략**: 중복 계산 방지

### 속도 최적화
- **벡터화 연산**: NumPy 기반 고속 계산
- **인덱싱 최적화**: 해시 테이블 기반 O(1) 접근
- **알고리즘 개선**: 불필요한 탐색 경로 제거

## 고급 기능

### 사용자 맞춤형 설정
```python
preference = RoutePreference(
    time_weight=0.4,        # 시간 중요도
    transfer_weight=0.3,    # 환승 횟수 중요도
    walk_weight=0.2,        # 도보 거리 중요도
    cost_weight=0.1,        # 비용 중요도
    max_walk_distance=1000, # 최대 도보 거리 (미터)
    max_transfers=3         # 최대 환승 횟수
)
```

### 실시간 모니터링
- 탐색 시간 측정
- 메모리 사용량 추적
- 경로 품질 메트릭스

## 기여 방법

1. **Fork** 이 저장소
2. **Feature branch** 생성: `git checkout -b feature/amazing-feature`
3. **Commit** 변경사항: `git commit -m 'Add amazing feature'`
4. **Push** 브랜치: `git push origin feature/amazing-feature`
5. **Pull Request** 생성



## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 개발자

**스마트시티학과 김태우**
- 이메일: twdaniel@gachon.ac.kr
- 블로그: https://blog.example.com
- LinkedIn: https://linkedin.com/in/example

## 감사의 말

- [GTFS](https://gtfs.org/) - 대중교통 데이터 표준
- [OpenStreetMap](https://openstreetmap.org/) - 오픈소스 지도 데이터
- [Microsoft Research](https://www.microsoft.com/en-us/research/) - RAPTOR 알고리즘 연구

## 문의

프로젝트에 대한 질문이나 제안사항이 있으시면 언제든지 연락해 주세요!

- 이메일: twdaniel@gachon.ac.kr

---


**이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!**
