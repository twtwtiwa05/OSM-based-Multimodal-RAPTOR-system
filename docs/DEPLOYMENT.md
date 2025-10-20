# 🚀 배포 가이드

## GitHub에서 바로 실행하기

### 1. Streamlit Cloud 배포 (권장)

1. **GitHub 저장소 포크**
   ```bash
   # GitHub에서 이 저장소를 포크하세요
   https://github.com/yourusername/osm-multimodal-raptor
   ```

2. **Streamlit Cloud 연결**
   - [Streamlit Cloud](https://streamlit.io/cloud)에 접속
   - GitHub 계정으로 로그인
   - "New app" 클릭
   - 포크한 저장소 선택
   - Main file path: `app.py`
   - 배포 완료!

### 2. 로컬 환경 설정

```bash
# 저장소 클론
git clone https://github.com/yourusername/osm-multimodal-raptor.git
cd osm-multimodal-raptor

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 애플리케이션 실행
streamlit run app.py
```

### 3. Docker 배포

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# Docker 이미지 빌드 및 실행
docker build -t raptor-app .
docker run -p 8501:8501 raptor-app
```

## 클라우드 플랫폼 배포

### AWS EC2

```bash
# EC2 인스턴스 설정
sudo yum update -y
sudo yum install -y python3 git

# 애플리케이션 배포
git clone https://github.com/yourusername/osm-multimodal-raptor.git
cd osm-multimodal-raptor
pip3 install -r requirements.txt

# 서비스로 실행
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
```

### Google Cloud Platform

```yaml
# app.yaml (App Engine)
runtime: python39

env_variables:
  STREAMLIT_SERVER_PORT: 8080
  STREAMLIT_SERVER_ADDRESS: 0.0.0.0

automatic_scaling:
  min_instances: 0
  max_instances: 10
```

### Heroku

```bash
# Procfile
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

## 성능 최적화

### 1. 캐싱 설정

```python
# streamlit 캐싱 활용
@st.cache_resource
def load_raptor_system():
    return TraditionalRAPTOR()

@st.cache_data
def calculate_route(origin, destination, time):
    return raptor.find_routes(origin, destination, time)
```

### 2. 메모리 최적화

```python
# 메모리 사용량 모니터링
import psutil

def check_memory():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    return memory_mb
```

### 3. 로드 밸런싱

```nginx
# nginx.conf
upstream raptor_app {
    server 127.0.0.1:8501;
    server 127.0.0.1:8502;
    server 127.0.0.1:8503;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://raptor_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 모니터링 및 로깅

### 1. 애플리케이션 로깅

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('raptor_app.log'),
        logging.StreamHandler()
    ]
)
```

### 2. 성능 메트릭

```python
# 성능 메트릭 수집
import time
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('raptor_requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('raptor_request_duration_seconds', 'Request latency')

def track_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        REQUEST_COUNT.inc()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            REQUEST_LATENCY.observe(time.time() - start_time)
    
    return wrapper
```

## 보안 설정

### 1. HTTPS 설정

```bash
# Let's Encrypt SSL 인증서
sudo certbot --nginx -d your-domain.com
```

### 2. 환경 변수 관리

```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '60'))
    DATA_PATH: str = os.getenv('DATA_PATH', './data')
```

### 3. Rate Limiting

```python
from functools import wraps
import time

def rate_limit(max_requests=60, window=60):
    def decorator(func):
        calls = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # 윈도우 밖의 요청 제거
            calls[:] = [call for call in calls if call > now - window]
            
            if len(calls) >= max_requests:
                raise Exception("Rate limit exceeded")
            
            calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
```

## 문제 해결

### 일반적인 문제들

1. **메모리 부족**
   ```python
   # 메모리 사용량 확인
   import psutil
   print(f"Memory usage: {psutil.virtual_memory().percent}%")
   ```

2. **포트 충돌**
   ```bash
   # 사용 중인 포트 확인
   lsof -i :8501
   
   # 다른 포트로 실행
   streamlit run app.py --server.port 8502
   ```

3. **데이터 파일 누락**
   ```python
   import os
   
   required_files = [
       'gangnam_raptor_data/raptor_data.pkl',
       'cleaned_gtfs_data/stops.csv'
   ]
   
   for file_path in required_files:
       if not os.path.exists(file_path):
           print(f"Missing file: {file_path}")
   ```

### 로그 분석

```bash
# 실시간 로그 모니터링
tail -f raptor_app.log

# 에러 로그 필터링
grep "ERROR" raptor_app.log

# 성능 로그 분석
grep "performance" raptor_app.log | tail -100
```

## 백업 및 복원

### 1. 데이터 백업

```bash
# 중요 데이터 백업
tar -czf backup_$(date +%Y%m%d).tar.gz \
    gangnam_raptor_data/ \
    cleaned_gtfs_data/ \
    *.py

# 클라우드 스토리지 업로드
aws s3 cp backup_$(date +%Y%m%d).tar.gz s3://your-bucket/backups/
```

### 2. 자동 백업 스크립트

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup"
APP_DIR="/app"

# 백업 생성
tar -czf "$BACKUP_DIR/raptor_backup_$DATE.tar.gz" -C "$APP_DIR" .

# 오래된 백업 삭제 (7일 이상)
find "$BACKUP_DIR" -name "raptor_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: raptor_backup_$DATE.tar.gz"
```

## 업데이트 및 배포 전략

### 1. 무중단 배포

```bash
# 블루-그린 배포 스크립트
#!/bin/bash

CURRENT_PORT=$(cat current_port.txt)
NEW_PORT=$((CURRENT_PORT == 8501 ? 8502 : 8501))

# 새 버전 시작
streamlit run app.py --server.port $NEW_PORT &
NEW_PID=$!

# 헬스 체크
sleep 30
if curl -f http://localhost:$NEW_PORT/_stcore/health; then
    # 트래픽 전환
    echo $NEW_PORT > current_port.txt
    
    # 이전 버전 종료
    kill $(cat old_pid.txt)
    echo $NEW_PID > old_pid.txt
    
    echo "Deployment successful"
else
    kill $NEW_PID
    echo "Deployment failed"
    exit 1
fi
```

### 2. 롤백 전략

```bash
# 이전 버전으로 롤백
git revert HEAD~1
docker build -t raptor-app:rollback .
docker stop raptor-app-current
docker run -d --name raptor-app-current -p 8501:8501 raptor-app:rollback
```