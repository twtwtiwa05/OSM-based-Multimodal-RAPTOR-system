#!/usr/bin/env python3
"""
🚀 OSM 기반 멀티모달 RAPTOR 시스템 실행 스크립트

이 스크립트는 시스템을 자동으로 설정하고 Streamlit 웹 애플리케이션을 실행합니다.
GitHub에서 클론한 후 바로 실행할 수 있도록 설계되었습니다.
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        print(f"현재 버전: {sys.version}")
        return False
    print(f"✅ Python 버전: {sys.version.split()[0]}")
    return True

def check_data_files():
    """필수 데이터 파일 확인"""
    required_files = [
        'gangnam_raptor_data/raptor_data.pkl',
        'cleaned_gtfs_data/stops.csv',
        'PART1_2.py',
        'PART2_NEW.py',
        'app.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 필수 파일이 누락되었습니다:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ 모든 필수 파일이 존재합니다.")
    return True

def install_dependencies():
    """의존성 패키지 설치"""
    print("📦 의존성 패키지 설치 중...")
    
    try:
        # requirements.txt가 있으면 설치
        if os.path.exists('requirements.txt'):
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("❌ 패키지 설치 실패:")
                print(result.stderr)
                return False
            
            print("✅ 의존성 패키지 설치 완료")
        else:
            # 기본 패키지 설치
            basic_packages = [
                'streamlit>=1.28.0',
                'folium>=0.14.0',
                'streamlit-folium>=0.13.0',
                'pandas>=1.5.0',
                'numpy>=1.21.0',
                'networkx>=2.8.0',
                'plotly>=5.11.0'
            ]
            
            for package in basic_packages:
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"❌ {package} 설치 실패")
                    return False
                
                print(f"✅ {package} 설치 완료")
        
        return True
    
    except Exception as e:
        print(f"❌ 설치 중 오류 발생: {e}")
        return False

def test_raptor_system():
    """RAPTOR 시스템 테스트"""
    print("🧪 RAPTOR 시스템 테스트 중...")
    
    try:
        # 빠른 임포트 테스트
        from PART1_2 import Stop, Route, Trip
        from PART2_NEW import TraditionalRAPTOR, RoutePreference
        
        print("✅ 모듈 임포트 성공")
        
        # 기본 초기화 테스트
        raptor = TraditionalRAPTOR()
        print(f"✅ RAPTOR 시스템 초기화 성공")
        print(f"   - 정류장: {len(raptor.stops):,}개")
        print(f"   - 노선: {len(raptor.routes):,}개")
        
        return True
    
    except Exception as e:
        print(f"❌ RAPTOR 시스템 테스트 실패: {e}")
        return False

def run_streamlit_app():
    """Streamlit 애플리케이션 실행"""
    print("🚀 Streamlit 애플리케이션 시작 중...")
    
    try:
        # Streamlit 실행
        cmd = [sys.executable, '-m', 'streamlit', 'run', 'app.py']
        
        # 브라우저 자동 열기 설정
        env = os.environ.copy()
        env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        
        print("✅ 웹 애플리케이션이 시작되었습니다!")
        print("🌐 브라우저에서 http://localhost:8501 로 접속하세요.")
        print("⚠️  종료하려면 Ctrl+C를 누르세요.")
        
        subprocess.run(cmd, env=env)
    
    except KeyboardInterrupt:
        print("\n👋 애플리케이션이 종료되었습니다.")
    except Exception as e:
        print(f"❌ 애플리케이션 실행 실패: {e}")

def show_system_info():
    """시스템 정보 표시"""
    print("💻 시스템 정보:")
    print(f"   - OS: {platform.system()} {platform.release()}")
    print(f"   - Python: {sys.version.split()[0]}")
    print(f"   - 작업 디렉토리: {os.getcwd()}")

def main():
    """메인 함수"""
    print("=" * 60)
    print("🚇 OSM 기반 멀티모달 RAPTOR 시스템")
    print("=" * 60)
    
    # 시스템 정보 표시
    show_system_info()
    print()
    
    # 단계별 확인 및 설정
    steps = [
        ("Python 버전 확인", check_python_version),
        ("데이터 파일 확인", check_data_files),
        ("의존성 패키지 설치", install_dependencies),
        ("RAPTOR 시스템 테스트", test_raptor_system)
    ]
    
    for step_name, step_func in steps:
        print(f"📋 {step_name}...")
        if not step_func():
            print(f"\n❌ {step_name} 실패. 설정을 확인해주세요.")
            print("\n💡 도움말:")
            print("1. Python 3.8 이상이 설치되어 있는지 확인")
            print("2. 모든 데이터 파일이 올바른 위치에 있는지 확인")
            print("3. 인터넷 연결이 되어 있는지 확인")
            return
        print()
    
    print("🎉 모든 준비가 완료되었습니다!")
    print()
    
    # Streamlit 앱 실행
    run_streamlit_app()

if __name__ == "__main__":
    main()