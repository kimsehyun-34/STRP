import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from fredapi import Fred
import config
import time

class DataFetcher:
    def __init__(self):
        self.fred = None
        if config.FRED_API_KEY != "b6e11573d0679dafc29142db963c4025":
            try:
                self.fred = Fred(api_key=config.FRED_API_KEY)
            except:
                print("FRED API 초기화 실패")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        self.session.proxies = {}
        self.session.verify = True
    
    def get_stock_data(self, symbol, period="1y", interval="1d"):
        try:
            print(f"데이터 요청: {symbol}, period={period}, interval={interval}")
            
            intraday_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h']
            short_periods = ['1d', '5d']
            
            if interval in intraday_intervals and period not in short_periods + ['1mo']:
                print(f"경고: {interval} 간격은 짧은 기간(1d, 5d, 1mo)에서만 사용 가능합니다. 1mo로 변경합니다.")
                period = '1mo'
            
            time.sleep(1.5)
            
            stock = yf.Ticker(symbol)
            
            max_retries = 2
            retry_delay = 3
            
            for attempt in range(max_retries):
                try:
                    print(f"데이터 다운로드 시도 {attempt + 1}/{max_retries}...")
                    
                    df = stock.history(
                        period=period, 
                        interval=interval
                    )
                    
                    if not df.empty:
                        print(f"받은 데이터: {len(df)} 행")
                        
                        if len(df) < 2:
                            print(f"데이터가 너무 적음: {len(df)} 행")
                            return None
                        
                        return df
                    else:
                        print(f"빈 데이터프레임 반환됨 - 심볼: {symbol} (시도 {attempt + 1}/{max_retries})")
                        
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (attempt + 1)
                            print(f"{wait_time}초 대기 후 재시도...")
                            time.sleep(wait_time)
                        else:
                            print(f"❌ {symbol}: 유효하지 않은 심볼이거나 데이터가 없습니다.")
                            return None
                
                except Exception as inner_e:
                    error_str = str(inner_e)
                    print(f"시도 {attempt + 1}/{max_retries} 실패: {error_str}")
                    
                    if '429' in error_str or 'Too Many Requests' in error_str:
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (attempt + 2)  # 5초, 15초
                            print(f"⚠️ Rate Limit 감지! {wait_time}초 대기 후 재시도...")
                            time.sleep(wait_time)
                        else:
                            print("❌ 야후 파이낸스 접근 제한. 잠시 후 다시 시도하세요.")
                            return None
                    else:
                        if attempt < max_retries - 1:
                            print(f"{retry_delay}초 대기 후 재시도...")
                            time.sleep(retry_delay)
                        else:
                            raise
            
            return None
            
        except Exception as e:
            print(f"주식 데이터 가져오기 실패 [{symbol}]: {type(e).__name__} - {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_stock_info(self, symbol):
        try:
            time.sleep(1)
            
            stock = yf.Ticker(symbol)
            
            try:
                stock_info = stock.info
                info = {
                    'symbol': symbol,
                    'longName': stock_info.get('longName', stock_info.get('shortName', symbol)),
                    'currentPrice': stock_info.get('currentPrice', stock_info.get('regularMarketPrice', 'N/A')),
                    'regularMarketPrice': stock_info.get('regularMarketPrice', 'N/A'),
                    'currency': stock_info.get('currency', 'USD'),
                    'marketCap': stock_info.get('marketCap', 'N/A')
                }
                return info
            except:
                print(f"⚠️ {symbol} 상세 정보를 가져올 수 없습니다. 기본 정보만 표시합니다.")
                return {
                    'symbol': symbol,
                    'longName': symbol,
                    'currentPrice': 'N/A',
                    'regularMarketPrice': 'N/A',
                    'currency': 'USD',
                    'marketCap': 'N/A'
                }
            
        except Exception as e:
            print(f"주식 정보 가져오기 실패: {e}")
            return {
                'symbol': symbol,
                'longName': symbol,
                'regularMarketPrice': 'N/A',
                'currency': 'USD'
            }
    
    def get_interest_rates(self):
        result = {
            'nominal_rate': None,
            'real_rate': None,
            'kr_base_rate': None,
            'error': None
        }
        
        if self.fred:
            try:
                nominal_rate_series = self.fred.get_series('DGS10', 
                                                           observation_start=datetime.now() - timedelta(days=30))
                result['nominal_rate'] = nominal_rate_series.iloc[-1] if not nominal_rate_series.empty else None
                
                real_rate_series = self.fred.get_series('DFII10', 
                                                         observation_start=datetime.now() - timedelta(days=30))
                result['real_rate'] = real_rate_series.iloc[-1] if not real_rate_series.empty else None
            except Exception as e:
                result['error'] = f'미국 금리 데이터 가져오기 실패: {str(e)}'
        else:
            result['error'] = 'FRED API 키가 설정되지 않았습니다.'
        
        try:
            kr_bond = yf.Ticker("KR10YT=X")
            kr_info = kr_bond.info
            if 'regularMarketPrice' in kr_info:
                result['kr_base_rate'] = kr_info['regularMarketPrice']
            else:
                kr_data = kr_bond.history(period="5d")
                if not kr_data.empty:
                    result['kr_base_rate'] = kr_data['Close'].iloc[-1]
                else:
                    result['kr_base_rate'] = 3.25
        except:
            result['kr_base_rate'] = 3.25
        
        return result
    
    def get_fear_greed_index(self):
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    fng_data = data['data'][0]
                    return {
                        'value': int(fng_data['value']),
                        'classification': fng_data['value_classification'],
                        'timestamp': fng_data['timestamp'],
                        'note': '암호화폐 Fear & Greed Index (참고용)',
                        'error': None
                    }
            
            return {
                'value': None,
                'classification': None,
                'error': 'Fear & Greed Index를 가져올 수 없습니다.'
            }
        except Exception as e:
            return {
                'value': None,
                'classification': None,
                'error': f'Fear & Greed Index 가져오기 실패: {str(e)}'
            }
    
    def get_country_rates(self, country_code):
        if not self.fred:
            return {
                'rate': None,
                'error': 'FRED API 키가 설정되지 않았습니다.'
            }
        
        series_map = {
            'US': 'DGS10',
            'KR': 'IRLTLT01KRM156N',
            'JP': 'IRLTLT01JPM156N',
            'GB': 'IRLTLT01GBM156N',
            'DE': 'IRLTLT01DEM156N'
        }
        
        series_code = series_map.get(country_code.upper())
        
        if not series_code:
            return {
                'rate': None,
                'error': f'{country_code} 국가의 금리 데이터를 사용할 수 없습니다.'
            }
        
        try:
            rate_series = self.fred.get_series(series_code, 
                                               observation_start=datetime.now() - timedelta(days=90))
            rate = rate_series.iloc[-1] if not rate_series.empty else None
            
            return {
                'rate': rate,
                'series_code': series_code,
                'error': None
            }
        except Exception as e:
            return {
                'rate': None,
                'error': f'금리 데이터 가져오기 실패: {str(e)}'
            }
