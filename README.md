# 통합 트레이딩 프로그램

야후 파이낸스 API를 활용한 주식 차트 분석 및 기술적 지표, 경제 지표를 통합적으로 볼 수 있는 트레이딩 프로그램입니다.

## 주요 기능

### 1. 주식 차트 분석
- **실시간 주식 데이터**: 야후 파이낸스 API를 통한 실시간 주가 데이터
- **캔들스틱 차트**: 직관적인 캔들스틱 차트로 주가 변동 확인
- **이동평균선**: MA20, MA50, MA200 자동 표시
- **기간/간격 설정**: 1일~최대 기간, 1분~월간 간격 선택 가능

### 2. 기술적 지표
- **RSI (Relative Strength Index)**: 과매수/과매도 구간 자동 분석
- **MACD**: 추세 전환 시그널 포착
- **Williams %R**: 모멘텀 지표를 통한 매매 타이밍 분석
- **볼린저 밴드**: 변동성 분석
- **신호 해석**: 각 지표별 매매 신호 자동 제공

### 3. 경제 지표
- **명목금리**: 미국 10년 만기 국채 수익률
- **실질금리**: 10년 만기 TIPS 수익률
- **Fear & Greed Index**: 시장 심리 지수 (참고용)
- **국가별 금리**: 확장 가능한 구조로 다양한 국가 금리 조회

## 설치 방법

### 1. 필수 요구사항
- Python 3.8 이상
- pip (Python 패키지 관리자)

### 2. 의존성 패키지 설치

```powershell
cd "d:\프로젝트\파이썬_주식차트"
pip install -r requirements.txt
```

### 3. FRED API 키 설정 (선택사항)

경제 지표(금리) 데이터를 사용하려면 FRED API 키가 필요합니다.

1. [FRED API 키 발급](https://fred.stlouisfed.org/docs/api/api_key.html) 페이지에서 무료 API 키 발급
2. `config.py` 파일을 열어 다음 부분 수정:

```python
FRED_API_KEY = "여기에_발급받은_API_키_입력"
```

> **참고**: FRED API 키 없이도 프로그램 사용 가능하며, 금리 데이터만 표시되지 않습니다.

## 사용 방법

### 1. 프로그램 실행

```powershell
python main.py
```

### 2. 주식 검색

1. **티커 심볼 입력**: 
   - 미국 주식: `AAPL` (애플), `TSLA` (테슬라), `MSFT` (마이크로소프트)
   - 한국 주식: `005930.KS` (삼성전자), `000660.KS` (SK하이닉스)
   - 일본 주식: `7203.T` (도요타), `9984.T` (소프트뱅크)

2. **기간 선택**: 1일(1d) ~ 최대(max)
3. **간격 선택**: 1분(1m) ~ 월간(1mo)
4. **검색 버튼 클릭**

### 3. 차트 분석

**차트 분석 탭**에서 다음을 확인할 수 있습니다:
- 캔들스틱 차트와 이동평균선
- RSI 지표 (과매수/과매도 구간 표시)
- MACD 지표 (추세 전환 신호)
- Williams %R (모멘텀 분석)

### 4. 기술적 지표 탭

- 각 지표의 현재 값
- 매매 신호 해석 (매수/매도/중립)
- 최근 10일간의 상세 데이터

### 5. 경제 지표 탭

- 미국 명목금리 및 실질금리
- Fear & Greed Index
- **새로고침 버튼**으로 최신 데이터 갱신

## 파일 구조

```
파이썬_주식차트/
│
├── main.py                    # 메인 프로그램 (GUI)
├── data_fetcher.py            # 데이터 수집 모듈
├── technical_analysis.py      # 기술적 분석 모듈
├── config.py                  # 설정 파일
├── requirements.txt           # 필수 패키지 목록
└── README.md                  # 사용 설명서
```

## 주요 모듈 설명

### data_fetcher.py
- `get_stock_data()`: 주식 데이터 수집
- `get_stock_info()`: 주식 기본 정보 수집
- `get_interest_rates()`: 금리 데이터 수집
- `get_fear_greed_index()`: Fear & Greed Index 수집

### technical_analysis.py
- `calculate_rsi()`: RSI 지표 계산
- `calculate_macd()`: MACD 지표 계산
- `calculate_williams_r()`: Williams %R 계산
- `calculate_all_indicators()`: 모든 지표 일괄 계산

### main.py
- PyQt5 기반 GUI 프로그램
- 멀티스레딩으로 비동기 데이터 로딩
- 3개 탭으로 구성된 통합 인터페이스

## 사용 예시

### 미국 주식 분석
```
티커: AAPL
기간: 1y
간격: 1d
→ 애플 주식의 최근 1년 일봉 차트 및 지표 분석
```

### 한국 주식 분석
```
티커: 005930.KS
기간: 6mo
간격: 1d
→ 삼성전자 주식의 최근 6개월 일봉 차트 및 지표 분석
```

### 단기 트레이딩 분석
```
티커: TSLA
기간: 5d
간격: 5m
→ 테슬라 주식의 최근 5일 5분봉 차트 (데이 트레이딩용)
```

## 지표 해석 가이드

### RSI (Relative Strength Index)
- **70 이상**: 과매수 구간 (매도 고려)
- **30 이하**: 과매도 구간 (매수 고려)
- **30~70**: 중립 구간

### MACD
- **MACD > Signal**: 강세 신호 (상승 추세)
- **MACD < Signal**: 약세 신호 (하락 추세)
- **골든 크로스**: MACD가 Signal을 상향 돌파 (매수 신호)
- **데드 크로스**: MACD가 Signal을 하향 돌파 (매도 신호)

### Williams %R
- **-20 이상**: 과매수 구간 (매도 고려)
- **-80 이하**: 과매도 구간 (매수 고려)
- **-20 ~ -80**: 중립 구간

## 문제 해결

### 주식 데이터를 가져올 수 없습니다
- 티커 심볼이 올바른지 확인
- 인터넷 연결 확인
- 야후 파이낸스에서 해당 주식이 지원되는지 확인

### FRED API 오류
- `config.py`에서 API 키가 올바르게 설정되었는지 확인
- API 키 발급: https://fred.stlouisfed.org/docs/api/api_key.html

### 패키지 설치 오류
```powershell
# 개별 패키지 설치
pip install yfinance pandas numpy matplotlib mplfinance PyQt5 ta requests fredapi

# 또는 최신 pip로 업그레이드 후 재시도
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 주의사항

1. **투자 결정의 보조 도구**: 이 프로그램은 투자 판단의 보조 도구일 뿐이며, 실제 투자 결정은 신중하게 하시기 바랍니다.
2. **데이터 지연**: 야후 파이낸스 데이터는 실시간이 아닐 수 있습니다.
3. **API 제한**: FRED API는 일일 사용량 제한이 있을 수 있습니다.
4. **네트워크 필요**: 모든 데이터는 온라인으로 수집되므로 인터넷 연결이 필요합니다.

## 라이선스

이 프로젝트는 개인 학습 및 연구 목적으로 사용하실 수 있습니다.

## 기여 및 문의

버그 리포트나 기능 제안은 이슈로 등록해 주세요.

---

**Happy Trading! 📈📊**
