import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, WilliamsRIndicator
from ta.trend import MACD
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import OnBalanceVolumeIndicator

class TechnicalAnalysis:
    def __init__(self, data):
        self.data = data.copy()
    
    def calculate_rsi(self, period=14):
        rsi_indicator = RSIIndicator(close=self.data['Close'], window=period)
        return rsi_indicator.rsi()
    
    def calculate_macd(self, fast=12, slow=26, signal=9):
        macd_indicator = MACD(
            close=self.data['Close'],
            window_slow=slow,
            window_fast=fast,
            window_sign=signal
        )
        
        macd_line = macd_indicator.macd()
        signal_line = macd_indicator.macd_signal()
        histogram = macd_indicator.macd_diff()
        
        return macd_line, signal_line, histogram
    
    def calculate_williams_r(self, period=14):
        williams_r_indicator = WilliamsRIndicator(
            high=self.data['High'],
            low=self.data['Low'],
            close=self.data['Close'],
            lbp=period
        )
        return williams_r_indicator.williams_r()
    
    def calculate_moving_averages(self, periods=[20, 50, 200]):
        mas = {}
        for period in periods:
            mas[f'MA{period}'] = self.data['Close'].rolling(window=period).mean()
        return mas
    
    def calculate_bollinger_bands(self, period=20, std_dev=2):
        bb_indicator = BollingerBands(
            close=self.data['Close'],
            window=period,
            window_dev=std_dev
        )
        
        upper_band = bb_indicator.bollinger_hband()
        middle_band = bb_indicator.bollinger_mavg()
        lower_band = bb_indicator.bollinger_lband()
        
        return upper_band, middle_band, lower_band
    
    def calculate_atr(self, period=14):
        atr_indicator = AverageTrueRange(
            high=self.data['High'],
            low=self.data['Low'],
            close=self.data['Close'],
            window=period
        )
        return atr_indicator.average_true_range()
    
    def calculate_obv(self):
        obv_indicator = OnBalanceVolumeIndicator(
            close=self.data['Close'],
            volume=self.data['Volume']
        )
        return obv_indicator.on_balance_volume()
    
    def calculate_volume_ma(self, period=20):
        return self.data['Volume'].rolling(window=period).mean()
    
    def get_latest_rsi_signal(self, rsi_value):
        if pd.isna(rsi_value):
            return "데이터 부족"
        elif rsi_value >= 70:
            return "과매수 (매도 고려)"
        elif rsi_value <= 30:
            return "과매도 (매수 고려)"
        else:
            return "중립"
    
    def get_latest_williams_r_signal(self, wr_value):
        if pd.isna(wr_value):
            return "데이터 부족"
        elif wr_value >= -20:
            return "과매수 (매도 고려)"
        elif wr_value <= -80:
            return "과매도 (매수 고려)"
        else:
            return "중립"
    
    def get_macd_signal(self, macd_value, signal_value):
        if pd.isna(macd_value) or pd.isna(signal_value):
            return "데이터 부족"
        
        diff = macd_value - signal_value
        
        if diff > 0:
            return "강세 (MACD > Signal)"
        elif diff < 0:
            return "약세 (MACD < Signal)"
        else:
            return "중립"
    
    def calculate_all_indicators(self):
        result_df = self.data.copy()
        
        result_df['ATR'] = self.calculate_atr()
        result_df['OBV'] = self.calculate_obv()
        result_df['Volume_MA'] = self.calculate_volume_ma()
        
        result_df['RSI'] = self.calculate_rsi()
        
        macd_line, signal_line, histogram = self.calculate_macd()
        result_df['MACD'] = macd_line
        result_df['MACD_Signal'] = signal_line
        result_df['MACD_Histogram'] = histogram
        
        result_df['Williams_R'] = self.calculate_williams_r()
        
        mas = self.calculate_moving_averages()
        for key, value in mas.items():
            result_df[key] = value
        
        upper_bb, middle_bb, lower_bb = self.calculate_bollinger_bands()
        result_df['BB_Upper'] = upper_bb
        result_df['BB_Middle'] = middle_bb
        result_df['BB_Lower'] = lower_bb
        
        return result_df
