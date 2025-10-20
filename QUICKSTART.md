# 빠른 시작 가이드

## 1분 안에 실행하기!

### GitHub에서 바로 실행 (원클릭 배포)

[![Deploy to Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy)

1. **위 버튼 클릭** → Streamlit Cloud에서 자동 배포
2. **GitHub 계정 연결** → 이 저장소 선택
3. **앱 실행** → 자동으로 웹 애플리케이션 시작!

### 로컬에서 실행 (3단계)

```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/osm-multimodal-raptor.git
cd osm-multimodal-raptor

# 2. 자동 설정 및 실행
python run.py
```

**끝!** 브라우저에서 `http://localhost:8501`이 자동으로 열립니다.

## 사용법 (30초 가이드)

1. **지도 클릭** → 출발지 선택
2. **지도 클릭** → 목적지 선택  
3. **시간 설정** → 출발 시간 선택
4. **버튼 클릭** → "경로 탐색" 실행
5. **결과 확인** → 최적 경로 5개 표시

## 예제 경로

### 1. 압구정역 → 선정릉역 (지하철 환승)
- **출발지**: 지도에서 압구정역 근처 클릭
- **목적지**: 선정릉역 근처 클릭
- **예상**: 3호선 → 분당선 환승 경로

### 2. 양재역 → 신사역 (직통)
- **출발지**: 양재역 클릭
- **목적지**: 신사역 클릭
- **예상**: 3호선 직통 11분

### 3. 수서역 → 한티역 (버스)
- **출발지**: 수서역 클릭  
- **목적지**: 한티역 클릭
- **예상**: 버스 2412번 이용

## 문제 해결

### 실행 안 됨?
```bash
# Python 버전 확인 (3.8+ 필요)
python --version

# 수동 설치
pip install streamlit folium streamlit-folium pandas numpy networkx plotly

# 다시 실행
streamlit run app.py
```

### 데이터 없음?
```bash
# 데이터 파일 확인
ls gangnam_raptor_data/raptor_data.pkl
ls cleaned_gtfs_data/stops.csv

# 없으면 전체 저장소 다시 클론
git clone --depth 1 https://github.com/yourusername/osm-multimodal-raptor.git
```

### 느림?
- **메모리**: 최소 4GB RAM 권장
- **데이터**: 첫 실행 시 로딩 30초 소요
- **캐시**: 두 번째부터는 즉시 실행

## 모바일에서도 가능!

- **스마트폰 브라우저**에서도 완벽 동작
- **터치로 지도 클릭** → 경로 탐색
- **반응형 디자인** → 모든 화면 크기 지원

## 고급 기능

### 선호도 조정
```python
# 사이드바에서 슬라이더 조정
- 시간 중요도: 빠른 경로 우선
- 환승 중요도: 환승 최소화
- 도보 중요도: 걷는 거리 최소화  
- 비용 중요도: 저렴한 경로 우선
```

### 시간대별 비교
```python
# 다양한 시간대 테스트
- 출근시간: 07:30-09:00
- 점심시간: 12:00-13:00  
- 퇴근시간: 18:00-20:00
- 심야시간: 22:00-24:00
```

## 성능 지표

| 항목 | 성능 |
|------|------|
| 정류장 | 12,064개 |
| 노선 | 944개 |
| 탐색속도 | < 3초 |
| 메모리 | < 500MB |
| 정확도 | 99%+ |

## 도움이 필요하면?

- **이메일**: twdaniel@gachon.ac.kr
- **이슈**: [GitHub Issues](https://github.com/yourusername/osm-multimodal-raptor/issues)
- **문서**: [상세 가이드](README.md)

---

**유용했다면 GitHub에서 Star 눌러주세요!**