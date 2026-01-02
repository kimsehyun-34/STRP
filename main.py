import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QComboBox, QTextEdit, QTabWidget, QScrollArea,
                             QGridLayout, QGroupBox, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QPen
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd

# 한글 폰트 설정
try:
    plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
    plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
except:
    try:
        plt.rcParams['font.family'] = 'AppleGothic'  # Mac
        plt.rcParams['axes.unicode_minus'] = False
    except:
        pass  # 폰트 설정 실패해도 프로그램은 계속 실행

from data_fetcher import DataFetcher
from technical_analysis import TechnicalAnalysis
import config

class DataLoadThread(QThread):
    """데이터 로딩을 위한 스레드"""
    finished = pyqtSignal(object, object)
    error = pyqtSignal(str)
    
    def __init__(self, symbol, period, interval):
        super().__init__()
        self.symbol = symbol
        self.period = period
        self.interval = interval
    
    def run(self):
        try:
            fetcher = DataFetcher()
            data = fetcher.get_stock_data(self.symbol, self.period, self.interval)
            info = fetcher.get_stock_info(self.symbol)
            
            if data is None:
                error_msg = f"주식 데이터를 가져올 수 없습니다.\n\n"
                error_msg += f"입력한 심볼: {self.symbol}\n"
                error_msg += f"기간: {self.period}, 간격: {self.interval}\n\n"
                error_msg += "가능한 원인:\n"
                error_msg += "1. 잘못된 티커 심볼\n"
                error_msg += "2. 기간/간격 조합이 지원되지 않음\n"
                error_msg += "   (예: 분봉은 최근 1개월만 가능)\n"
                error_msg += "3. 네트워크 연결 문제\n\n"
                error_msg += "한국 주식은 .KS 추가 (예: 005930.KS)"
                self.error.emit(error_msg)
            else:
                self.finished.emit(data, info)
        except Exception as e:
            self.error.emit(f"데이터 로딩 중 오류 발생:\n{type(e).__name__}: {str(e)}")


class ChartCanvas(FigureCanvas):
    """차트를 표시하는 캔버스"""
    
    def __init__(self, parent=None, width=10, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
        self.data = None
        self.symbol = None
        self.indicators_data = None
        self.main_ax = None
        self.sub_axes = []
        self.hover_line = None
        self.hover_annotation = None
        
        self.mpl_connect('motion_notify_event', self.on_hover)
    
    def plot_candlestick(self, data, symbol, indicators_data=None):
        """캔들스틱 차트와 기술적 지표 그리기"""
        self.fig.clear()
        
        if data is None or len(data) == 0:
            return
        
        self.data = data
        self.symbol = symbol
        self.indicators_data = indicators_data
        
        # 서브플롯 구성 - GridSpec으로 높이 비율 조정
        if indicators_data is not None:
            # 메인 차트를 더 크게 (3:1:1:1 비율)
            gs = GridSpec(4, 1, figure=self.fig, height_ratios=[3, 1, 1, 1], hspace=0.3)
            ax1 = self.fig.add_subplot(gs[0])
            ax2 = self.fig.add_subplot(gs[1], sharex=ax1)
            ax3 = self.fig.add_subplot(gs[2], sharex=ax1)
            ax4 = self.fig.add_subplot(gs[3], sharex=ax1)
            
            self.main_ax = ax1
            self.sub_axes = [ax2, ax3, ax4]
            
            ax1.clear()
            
            for idx in range(len(data)):
                open_price = data['Open'].iloc[idx]
                close_price = data['Close'].iloc[idx]
                high = data['High'].iloc[idx]
                low = data['Low'].iloc[idx]
                
                if close_price >= open_price:
                    body_color = 'red'
                else:
                    body_color = 'blue'
                
                ax1.plot([idx, idx], [low, high], color='black', linewidth=0.8, zorder=1)
                
                body_height = abs(close_price - open_price)
                body_bottom = min(open_price, close_price)
                
                if body_height > 0:
                    rect = plt.Rectangle((idx - 0.3, body_bottom), 0.6, body_height,
                                        facecolor=body_color, edgecolor='black', 
                                        linewidth=0.5, zorder=2)
                    ax1.add_patch(rect)
                else:
                    ax1.plot([idx - 0.3, idx + 0.3], [open_price, open_price], 
                           color=body_color, linewidth=1.5, zorder=2)
            
            if 'MA20' in indicators_data.columns:
                ax1.plot(range(len(indicators_data)), indicators_data['MA20'].values, 
                        label='MA20', linewidth=1.5, alpha=0.8, color='orange')
            if 'MA50' in indicators_data.columns:
                ax1.plot(range(len(indicators_data)), indicators_data['MA50'].values, 
                        label='MA50', linewidth=1.5, alpha=0.8, color='green')
            
            if 'BB_Upper' in indicators_data.columns and 'BB_Lower' in indicators_data.columns:
                ax1.plot(range(len(indicators_data)), indicators_data['BB_Upper'].values, 
                        '--', label='BB Upper', linewidth=1, alpha=0.5, color='gray')
                ax1.plot(range(len(indicators_data)), indicators_data['BB_Middle'].values, 
                        '--', label='BB Middle', linewidth=1, alpha=0.5, color='purple')
                ax1.plot(range(len(indicators_data)), indicators_data['BB_Lower'].values, 
                        '--', label='BB Lower', linewidth=1, alpha=0.5, color='gray')
                ax1.fill_between(range(len(indicators_data)), 
                               indicators_data['BB_Upper'].values,
                               indicators_data['BB_Lower'].values,
                               alpha=0.1, color='purple')
            
            ax1.set_title(f'{symbol} Stock Price (마우스를 차트 위에 올려보세요)', 
                         fontsize=13, fontweight='bold')
            ax1.set_ylabel('Price ($)', fontsize=10)
            ax1.legend(loc='upper left', fontsize=8, ncol=2)
            ax1.grid(True, alpha=0.3, linestyle='--')
            ax1.set_xlim(-1, len(data))
            ax1.tick_params(labelbottom=False)
            
            # RSI
            ax2.clear()
            ax2.plot(range(len(indicators_data)), indicators_data['RSI'].values, 
                    label='RSI', color='purple', linewidth=1.5)
            ax2.axhline(y=70, color='r', linestyle='--', linewidth=1, alpha=0.5)
            ax2.axhline(y=30, color='g', linestyle='--', linewidth=1, alpha=0.5)
            ax2.fill_between(range(len(indicators_data)), 70, 100, alpha=0.1, color='red')
            ax2.fill_between(range(len(indicators_data)), 0, 30, alpha=0.1, color='green')
            ax2.set_ylabel('RSI', fontsize=10)
            ax2.set_ylim(0, 100)
            ax2.legend(loc='upper left', fontsize=8)
            ax2.grid(True, alpha=0.3, linestyle='--')
            ax2.set_xlim(-1, len(indicators_data))
            ax2.tick_params(labelbottom=False)
            
            # MACD
            ax3.clear()
            ax3.plot(range(len(indicators_data)), indicators_data['MACD'].values, 
                    label='MACD', color='blue', linewidth=1.5)
            ax3.plot(range(len(indicators_data)), indicators_data['MACD_Signal'].values, 
                    label='Signal', color='red', linewidth=1.5)
            
            colors = ['green' if val >= 0 else 'red' 
                     for val in indicators_data['MACD_Histogram'].values]
            ax3.bar(range(len(indicators_data)), indicators_data['MACD_Histogram'].values,
                   label='Histogram', color=colors, alpha=0.3, width=0.8)
            ax3.axhline(y=0, color='black', linewidth=0.8)
            ax3.set_ylabel('MACD', fontsize=10)
            ax3.legend(loc='upper left', fontsize=8)
            ax3.grid(True, alpha=0.3, linestyle='--')
            ax3.set_xlim(-1, len(indicators_data))
            ax3.tick_params(labelbottom=False)
            
            # Williams %R
            ax4.clear()
            ax4.plot(range(len(indicators_data)), indicators_data['Williams_R'].values, 
                    label='Williams %R', color='orange', linewidth=1.5)
            ax4.axhline(y=-20, color='r', linestyle='--', linewidth=1, alpha=0.5)
            ax4.axhline(y=-80, color='g', linestyle='--', linewidth=1, alpha=0.5)
            ax4.fill_between(range(len(indicators_data)), -20, 0, alpha=0.1, color='red')
            ax4.fill_between(range(len(indicators_data)), -100, -80, alpha=0.1, color='green')
            ax4.set_ylabel('Williams %R', fontsize=10)
            ax4.set_xlabel('Days', fontsize=10)
            ax4.set_ylim(-100, 0)
            ax4.legend(loc='upper left', fontsize=8)
            ax4.grid(True, alpha=0.3, linestyle='--')
            ax4.set_xlim(-1, len(indicators_data))
            
        else:

            ax = self.fig.add_subplot(111)
            ax.clear()
            
            self.main_ax = ax
            self.sub_axes = []
            
            for idx in range(len(data)):
                open_price = data['Open'].iloc[idx]
                close_price = data['Close'].iloc[idx]
                high = data['High'].iloc[idx]
                low = data['Low'].iloc[idx]
                
                if close_price >= open_price:
                    color = 'red'
                else:
                    color = 'blue'
                
                ax.plot([idx, idx], [low, high], color='black', linewidth=0.8, zorder=1)
                
                body_height = abs(close_price - open_price)
                body_bottom = min(open_price, close_price)
                
                if body_height > 0:
                    rect = plt.Rectangle((idx - 0.3, body_bottom), 0.6, body_height,
                                        facecolor=color, edgecolor='black', 
                                        linewidth=0.5, zorder=2)
                    ax.add_patch(rect)
                else:
                    ax.plot([idx - 0.3, idx + 0.3], [open_price, open_price], 
                           color=color, linewidth=1.5, zorder=2)
            
            ax.set_title(f'{symbol} Stock Price (마우스를 차트 위에 올려보세요)', 
                        fontsize=14, fontweight='bold')
            ax.set_ylabel('Price ($)', fontsize=11)
            ax.set_xlabel('Days', fontsize=11)
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_xlim(-1, len(data))
        
        self.fig.tight_layout()
        self.draw()
    
    def on_hover(self, event):
        """마우스 호버 이벤트 처리"""
        if event.inaxes != self.main_ax or self.data is None:
            if self.hover_line:
                self.hover_line.remove()
                self.hover_line = None
            if self.hover_annotation:
                self.hover_annotation.remove()
                self.hover_annotation = None
            self.draw_idle()
            return
        
        x_pos = event.xdata
        if x_pos is None:
            return
        
        idx = int(round(x_pos))
        if idx < 0 or idx >= len(self.data):
            return
        
        date = self.data.index[idx]
        open_price = self.data['Open'].iloc[idx]
        high = self.data['High'].iloc[idx]
        low = self.data['Low'].iloc[idx]
        close = self.data['Close'].iloc[idx]
        volume = self.data['Volume'].iloc[idx]
        
        date_str = date.strftime('%Y-%m-%d %H:%M') if hasattr(date, 'strftime') else str(date)
        
        if self.hover_line:
            self.hover_line.remove()
        if self.hover_annotation:
            self.hover_annotation.remove()
        
        self.hover_line = self.main_ax.axvline(x=idx, color='gray', linestyle='--', 
                                                linewidth=1, alpha=0.7, zorder=10)
        
        change = close - open_price
        change_pct = (change / open_price) * 100 if open_price != 0 else 0
        change_color = 'red' if change >= 0 else 'blue'
        
        info_text = f'{date_str}\n'
        info_text += f'시가: ${open_price:.2f}\n'
        info_text += f'고가: ${high:.2f}\n'
        info_text += f'저가: ${low:.2f}\n'
        info_text += f'종가: ${close:.2f}\n'
        info_text += f'변화: ${change:+.2f} ({change_pct:+.2f}%)\n'
        info_text += f'거래량: {volume:,.0f}'
        
        bbox_props = dict(boxstyle='round,pad=0.5', facecolor='wheat', 
                         alpha=0.9, edgecolor=change_color, linewidth=2)
        
        x_range = self.main_ax.get_xlim()
        if idx < (x_range[1] - x_range[0]) / 2:
            x_offset = 50
            ha = 'left'
        else:
            x_offset = -50
            ha = 'right'
        
        self.hover_annotation = self.main_ax.annotate(
            info_text,
            xy=(idx, high),
            xytext=(x_offset, 20),
            textcoords='offset points',
            bbox=bbox_props,
            fontsize=9,
            ha=ha,
            va='bottom',
            zorder=20
        )
        
        self.draw_idle()


class FearGreedGauge(QWidget):
    """Fear & Greed Index 게이지 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 50
        self.classification = "Neutral"
        self.setMinimumHeight(150)
    
    def set_value(self, value, classification):
        """값 설정"""
        self.value = value if value is not None else 50
        self.classification = classification if classification else "N/A"
        self.update()
    
    def paintEvent(self, event):
        """게이지 그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        bar_height = 40
        bar_y = (height - bar_height) // 2
        bar_margin = 50
        bar_width = width - (bar_margin * 2)
        
        segment_width = bar_width // 5
        colors = [
            (QColor(200, 50, 50), "Extreme Fear"),
            (QColor(255, 150, 50), "Fear"),
            (QColor(255, 220, 100), "Neutral"),
            (QColor(150, 220, 100), "Greed"),
            (QColor(50, 200, 50), "Extreme Greed")
        ]
        
        for i, (color, label) in enumerate(colors):
            x = bar_margin + (i * segment_width)
            painter.fillRect(x, bar_y, segment_width, bar_height, color)
            
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setFont(QFont('Arial', 8))
            painter.drawText(x, bar_y + bar_height + 20, segment_width, 20,
                           Qt.AlignCenter, label)
        
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRect(bar_margin, bar_y, bar_width, bar_height)
        
        if 0 <= self.value <= 100:
            marker_x = bar_margin + int((self.value / 100) * bar_width)
            
            painter.setBrush(QColor(0, 0, 0))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            points = [
                (marker_x, bar_y - 10),
                (marker_x - 8, bar_y - 25),
                (marker_x + 8, bar_y - 25)
            ]
            from PyQt5.QtCore import QPoint
            painter.drawPolygon(*[QPoint(x, y) for x, y in points])
            
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setFont(QFont('Arial', 12, QFont.Bold))
            text = f"{int(self.value)}"
            painter.drawText(marker_x - 20, bar_y - 30, 40, 20,
                           Qt.AlignCenter, text)


class TradingApp(QMainWindow):
    """메인 트레이딩 애플리케이션"""
    
    def __init__(self):
        super().__init__()
        self.data_fetcher = DataFetcher()
        self.current_data = None
        self.current_info = None
        self.current_symbol = None
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle('통합 트레이딩 프로그램')
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        input_panel = self.create_input_panel()
        main_layout.addWidget(input_panel)
        
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        self.chart_tab = QWidget()
        self.tab_widget.addTab(self.chart_tab, "차트 분석")
        self.setup_chart_tab()
        
        self.indicators_tab = QWidget()
        self.tab_widget.addTab(self.indicators_tab, "기술적 지표")
        self.setup_indicators_tab()
        
        self.economic_tab = QWidget()
        self.tab_widget.addTab(self.economic_tab, "경제 지표")
        self.setup_economic_tab()
        
        self.status_label = QLabel("준비")
        main_layout.addWidget(self.status_label)
    
    def create_input_panel(self):
        """입력 패널 생성"""
        group_box = QGroupBox("주식 검색")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("티커 심볼:"))
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("예: AAPL, TSLA, 005930.KS")
        self.symbol_input.setMinimumWidth(200)
        layout.addWidget(self.symbol_input)
        
        layout.addWidget(QLabel("기간:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'])
        self.period_combo.setCurrentText('1y')
        layout.addWidget(self.period_combo)
        
        layout.addWidget(QLabel("간격:"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(['1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo'])
        self.interval_combo.setCurrentText('1d')
        layout.addWidget(self.interval_combo)
        
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.search_stock)
        layout.addWidget(self.search_button)
        
        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.clicked.connect(self.refresh_economic_data)
        layout.addWidget(self.refresh_button)
        
        layout.addStretch()
        
        group_box.setLayout(layout)
        return group_box
    
    def setup_chart_tab(self):
        """차트 탭 설정"""
        layout = QVBoxLayout(self.chart_tab)
        
        self.stock_info_label = QLabel("주식 정보가 여기에 표시됩니다")
        self.stock_info_label.setStyleSheet("font-size: 12pt; padding: 10px;")
        layout.addWidget(self.stock_info_label)
        
        self.chart_canvas = ChartCanvas(self, width=12, height=8)
        layout.addWidget(self.chart_canvas)
    
    def setup_economic_tab(self):
        """경제 지표 탭 설정"""
        layout = QVBoxLayout(self.economic_tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        interest_group = QGroupBox("미국 금리 정보")
        interest_layout = QGridLayout()
        
        interest_layout.addWidget(QLabel("<b>명목금리 (10Y Treasury):</b>"), 0, 0)
        self.nominal_rate_label = QLabel("-")
        interest_layout.addWidget(self.nominal_rate_label, 0, 1)
        
        interest_layout.addWidget(QLabel("<b>실질금리 (10Y TIPS):</b>"), 1, 0)
        self.real_rate_label = QLabel("-")
        interest_layout.addWidget(self.real_rate_label, 1, 1)
        
        interest_group.setLayout(interest_layout)
        scroll_layout.addWidget(interest_group)
        
        kr_interest_group = QGroupBox("한국 금리 정보")
        kr_interest_layout = QGridLayout()
        
        kr_interest_layout.addWidget(QLabel("<b>기준금리:</b>"), 0, 0)
        self.kr_base_rate_label = QLabel("-")
        kr_interest_layout.addWidget(self.kr_base_rate_label, 0, 1)
        
        kr_interest_group.setLayout(kr_interest_layout)
        scroll_layout.addWidget(kr_interest_group)
        
        fng_group = QGroupBox("Fear & Greed Index (CNN)")
        fng_layout = QVBoxLayout()
        
        self.fng_gauge = FearGreedGauge()
        fng_layout.addWidget(self.fng_gauge)
        
        fng_info_layout = QGridLayout()
        fng_info_layout.addWidget(QLabel("<b>현재 지수:</b>"), 0, 0)
        self.fng_value_label = QLabel("-")
        self.fng_value_label.setFont(QFont('Arial', 12, QFont.Bold))
        fng_info_layout.addWidget(self.fng_value_label, 0, 1)
        
        fng_info_layout.addWidget(QLabel("<b>분류:</b>"), 1, 0)
        self.fng_class_label = QLabel("-")
        self.fng_class_label.setFont(QFont('Arial', 11))
        fng_info_layout.addWidget(self.fng_class_label, 1, 1)
        
        fng_layout.addLayout(fng_info_layout)
        fng_group.setLayout(fng_layout)
        scroll_layout.addWidget(fng_group)
        
        self.economic_text = QTextEdit()
        self.economic_text.setReadOnly(True)
        self.economic_text.setMinimumHeight(200)
        scroll_layout.addWidget(self.economic_text)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
    
    def setup_indicators_tab(self):
        """기술적 지표 탭 설정"""
        layout = QVBoxLayout(self.indicators_tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.indicators_group = QGroupBox("현재 지표 값")
        indicators_layout = QGridLayout()
        
        indicators_layout.addWidget(QLabel("<b>RSI:</b>"), 0, 0)
        self.rsi_value_label = QLabel("-")
        indicators_layout.addWidget(self.rsi_value_label, 0, 1)
        self.rsi_signal_label = QLabel("-")
        indicators_layout.addWidget(self.rsi_signal_label, 0, 2)
        
        indicators_layout.addWidget(QLabel("<b>MACD:</b>"), 1, 0)
        self.macd_value_label = QLabel("-")
        indicators_layout.addWidget(self.macd_value_label, 1, 1)
        self.macd_signal_label = QLabel("-")
        indicators_layout.addWidget(self.macd_signal_label, 1, 2)
        
        indicators_layout.addWidget(QLabel("<b>Williams %R:</b>"), 2, 0)
        self.wr_value_label = QLabel("-")
        indicators_layout.addWidget(self.wr_value_label, 2, 1)
        self.wr_signal_label = QLabel("-")
        indicators_layout.addWidget(self.wr_signal_label, 2, 2)
        
        indicators_layout.addWidget(QLabel("<b>MA20:</b>"), 3, 0)
        self.ma20_label = QLabel("-")
        indicators_layout.addWidget(self.ma20_label, 3, 1)
        
        indicators_layout.addWidget(QLabel("<b>MA50:</b>"), 4, 0)
        self.ma50_label = QLabel("-")
        indicators_layout.addWidget(self.ma50_label, 4, 1)
        
        indicators_layout.addWidget(QLabel("<b>MA200:</b>"), 5, 0)
        self.ma200_label = QLabel("-")
        indicators_layout.addWidget(self.ma200_label, 5, 1)
        
        # 볼린저 밴드
        indicators_layout.addWidget(QLabel("<b>Bollinger Bands:</b>"), 6, 0)
        self.bb_label = QLabel("-")
        indicators_layout.addWidget(self.bb_label, 6, 1)
        
        # ATR (변동성)
        indicators_layout.addWidget(QLabel("<b>ATR (14일 변동성):</b>"), 7, 0)
        self.atr_label = QLabel("-")
        indicators_layout.addWidget(self.atr_label, 7, 1)
        
        # OBV (거래량 지표)
        indicators_layout.addWidget(QLabel("<b>OBV:</b>"), 8, 0)
        self.obv_label = QLabel("-")
        indicators_layout.addWidget(self.obv_label, 8, 1)
        
        # 거래량 비율
        indicators_layout.addWidget(QLabel("<b>거래량 (vs 20일 평균):</b>"), 9, 0)
        self.volume_ratio_label = QLabel("-")
        indicators_layout.addWidget(self.volume_ratio_label, 9, 1)
        
        self.indicators_group.setLayout(indicators_layout)
        scroll_layout.addWidget(self.indicators_group)
        
        self.indicators_text = QTextEdit()
        self.indicators_text.setReadOnly(True)
        self.indicators_text.setMinimumHeight(300)
        scroll_layout.addWidget(self.indicators_text)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
    
    def search_stock(self):
        """주식 검색"""
        symbol = self.symbol_input.text().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "경고", "티커 심볼을 입력하세요.")
            return
        
        period = self.period_combo.currentText()
        interval = self.interval_combo.currentText()
        
        self.current_symbol = symbol
        self.status_label.setText(f"데이터 로딩 중: {symbol}...")
        self.search_button.setEnabled(False)
        
        self.load_thread = DataLoadThread(symbol, period, interval)
        self.load_thread.finished.connect(self.on_data_loaded)
        self.load_thread.error.connect(self.on_data_error)
        self.load_thread.start()
    
    def on_data_loaded(self, data, info):
        """데이터 로딩 완료"""
        self.current_data = data
        self.current_info = info
        
        ta = TechnicalAnalysis(data)
        indicators_data = ta.calculate_all_indicators()
        
        self.chart_canvas.plot_candlestick(data, self.current_symbol, indicators_data)
        
        self.update_stock_info()
        self.update_indicators(indicators_data, ta)
        self.refresh_economic_data()
        
        self.status_label.setText(f"완료: {self.current_symbol}")
        self.search_button.setEnabled(True)
    
    def on_data_error(self, error_msg):
        """데이터 로딩 오류"""
        QMessageBox.critical(self, "오류", error_msg)
        self.status_label.setText("오류 발생")
        self.search_button.setEnabled(True)
    
    def update_stock_info(self):
        """주식 정보 업데이트"""
        if self.current_info:
            name = self.current_info.get('longName', self.current_symbol)
            price = self.current_info.get('currentPrice', self.current_info.get('regularMarketPrice', 'N/A'))
            currency = self.current_info.get('currency', 'USD')
            market_cap = self.current_info.get('marketCap', 'N/A')
            
            info_text = f"<b>{name}</b> ({self.current_symbol})<br>"
            info_text += f"현재가: {price} {currency}"
            
            if market_cap != 'N/A':
                info_text += f" | 시가총액: {market_cap:,}"
            
            self.stock_info_label.setText(info_text)
    
    def update_indicators(self, indicators_data, ta):
        """기술적 지표 업데이트"""
        latest = indicators_data.iloc[-1]
        
        rsi_val = latest['RSI']
        self.rsi_value_label.setText(f"{rsi_val:.2f}" if not pd.isna(rsi_val) else "N/A")
        self.rsi_signal_label.setText(ta.get_latest_rsi_signal(rsi_val))
        
        macd_val = latest['MACD']
        signal_val = latest['MACD_Signal']
        self.macd_value_label.setText(
            f"MACD: {macd_val:.2f}, Signal: {signal_val:.2f}" 
            if not pd.isna(macd_val) else "N/A"
        )
        self.macd_signal_label.setText(ta.get_macd_signal(macd_val, signal_val))
        
        wr_val = latest['Williams_R']
        self.wr_value_label.setText(f"{wr_val:.2f}" if not pd.isna(wr_val) else "N/A")
        self.wr_signal_label.setText(ta.get_latest_williams_r_signal(wr_val))
        
        ma20 = latest.get('MA20', None)
        ma50 = latest.get('MA50', None)
        ma200 = latest.get('MA200', None)
        
        self.ma20_label.setText(f"{ma20:.2f}" if not pd.isna(ma20) else "N/A")
        self.ma50_label.setText(f"{ma50:.2f}" if not pd.isna(ma50) else "N/A")
        self.ma200_label.setText(f"{ma200:.2f}" if not pd.isna(ma200) else "N/A")
        
        bb_upper = latest.get('BB_Upper', None)
        bb_middle = latest.get('BB_Middle', None)
        bb_lower = latest.get('BB_Lower', None)
        close_price = latest['Close']
        
        if not pd.isna(bb_upper) and not pd.isna(bb_lower):
            bb_width = ((bb_upper - bb_lower) / bb_middle) * 100 if bb_middle != 0 else 0
            bb_position = "상단 근처" if close_price > bb_middle else "하단 근처"
            self.bb_label.setText(f"U: {bb_upper:.2f}, M: {bb_middle:.2f}, L: {bb_lower:.2f} (폭: {bb_width:.1f}%, {bb_position})")
        else:
            self.bb_label.setText("N/A")
        
        atr_val = latest.get('ATR', None)
        if not pd.isna(atr_val):
            atr_pct = (atr_val / close_price) * 100 if close_price != 0 else 0
            volatility = "높음" if atr_pct > 3 else "중간" if atr_pct > 1.5 else "낮음"
            self.atr_label.setText(f"{atr_val:.2f} ({atr_pct:.2f}% - {volatility})")
        else:
            self.atr_label.setText("N/A")
        
        obv_val = latest.get('OBV', None)
        if not pd.isna(obv_val):
            obv_formatted = f"{obv_val:,.0f}"
            self.obv_label.setText(obv_formatted)
        else:
            self.obv_label.setText("N/A")
        
        volume = latest['Volume']
        volume_ma = latest.get('Volume_MA', None)
        if not pd.isna(volume_ma) and volume_ma != 0:
            volume_ratio = (volume / volume_ma) * 100
            volume_status = "매우 높음" if volume_ratio > 150 else "높음" if volume_ratio > 120 else "보통"
            self.volume_ratio_label.setText(f"{volume:,.0f} ({volume_ratio:.0f}% - {volume_status})")
        else:
            self.volume_ratio_label.setText(f"{volume:,.0f}")
        
        detail_text = "=== 최근 10일 데이터 ===\n\n"
        available_cols = ['Close', 'RSI', 'MACD', 'Williams_R', 'Volume']
        if 'ATR' in indicators_data.columns:
            available_cols.insert(-1, 'ATR')
        detail_text += indicators_data[available_cols].tail(10).to_string()
        self.indicators_text.setPlainText(detail_text)
    
    def refresh_economic_data(self):
        """경제 지표 새로고침"""
        interest_data = self.data_fetcher.get_interest_rates()
        
        if interest_data['error']:
            self.nominal_rate_label.setText(interest_data['error'])
            self.real_rate_label.setText("")
        else:
            nominal = interest_data['nominal_rate']
            real = interest_data['real_rate']
            
            self.nominal_rate_label.setText(
                f"{nominal:.2f}%" if nominal is not None else "N/A"
            )
            self.real_rate_label.setText(
                f"{real:.2f}%" if real is not None else "N/A"
            )
        
        kr_rate = interest_data.get('kr_base_rate', None)
        if kr_rate and kr_rate != 'N/A':
            self.kr_base_rate_label.setText(f"{kr_rate:.2f}%")
        else:
            self.kr_base_rate_label.setText("N/A")
        
        fng_data = self.data_fetcher.get_fear_greed_index()
        
        if fng_data['error']:
            self.fng_value_label.setText(fng_data['error'])
            self.fng_class_label.setText("")
            self.fng_gauge.set_value(50, "N/A")
        else:
            self.fng_value_label.setText(str(fng_data['value']))
            self.fng_class_label.setText(fng_data['classification'])
            self.fng_gauge.set_value(fng_data['value'], fng_data['classification'])
        
        detail_text = "=== 경제 지표 상세 정보 ===\n\n"
        detail_text += "[ 미국 금리 정보 ]\n"
        detail_text += f"명목금리: {interest_data.get('nominal_rate', 'N/A')}\n"
        detail_text += f"실질금리: {interest_data.get('real_rate', 'N/A')}\n\n"
        detail_text += "[ 한국 금리 정보 ]\n"
        detail_text += f"기준금리: {interest_data.get('kr_base_rate', 'N/A')}\n\n"
        detail_text += "[ Fear & Greed Index ]\n"
        detail_text += f"지수: {fng_data.get('value', 'N/A')}\n"
        detail_text += f"분류: {fng_data.get('classification', 'N/A')}\n"
        
        if 'note' in fng_data:
            detail_text += f"참고: {fng_data['note']}\n"
        
        self.economic_text.setPlainText(detail_text)


def main():
    app = QApplication(sys.argv)
    window = TradingApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
