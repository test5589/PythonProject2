# 📈 監控與可觀察性

## 指標收集系統

### 應用指標
```python
from prometheus_client import Counter, Histogram, Gauge

class MetricsCollector:
    \"\"\"指標收集器\"\"\"

    # 業務指標
    trades_total = Counter('trades_total', 'Total number of trades', ['symbol', 'type'])
    api_requests_total = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])

    # 性能指標
    request_duration = Histogram('request_duration_seconds', 'Request duration', ['endpoint'])

    # 系統指標
    active_connections = Gauge('active_connections', 'Number of active connections')

    @staticmethod
    def record_trade(symbol: str, trade_type: str):
        \"\"\"記錄交易\"\"\"
        MetricsCollector.trades_total.labels(symbol=symbol, type=trade_type).inc()

    @staticmethod
    def record_api_request(endpoint: str, status: str):
        \"\"\"記錄API請求\"\"\"
        MetricsCollector.api_requests_total.labels(endpoint=endpoint, status=status).inc()
```

## 健康檢查系統

### 系統健康檢查
```python
class HealthChecker:
    \"\"\"健康檢查器\"\"\"

    def __init__(self):
        self.checks = []

    def add_check(self, name: str, check_func):
        \"\"\"添加健康檢查\"\"\"
        self.checks.append((name, check_func))

    def run_checks(self) -> Dict[str, bool]:
        \"\"\"運行所有檢查\"\"\"
        results = {}
        for name, check_func in self.checks:
            try:
                results[name] = check_func()
            except Exception as e:
                results[name] = False
        return results

    def is_healthy(self) -> bool:
        \"\"\"檢查系統是否健康\"\"\"
        results = self.run_checks()
        return all(results.values())
```

## 日誌系統優化

### 結構化日誌記錄
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    \"\"\"結構化日誌記錄器\"\"\"

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_logger()

    def _setup_logger(self):
        \"\"\"設置日誌格式\"\"\"
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_trade(self, symbol: str, action: str, amount: float, price: float):
        \"\"\"記錄交易操作\"\"\"
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'trade',
            'symbol': symbol,
            'action': action,
            'amount': amount,
            'price': price
        }
        self.logger.info(f"Trade executed: {json.dumps(log_data)}")

    def log_api_request(self, endpoint: str, status: int, duration: float):
        \"\"\"記錄API請求\"\"\"
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'api_request',
            'endpoint': endpoint,
            'status': status,
            'duration': duration
        }
        self.logger.info(f"API request: {json.dumps(log_data)}")

    def log_error(self, error_type: str, message: str, context: dict = None):
        \"\"\"記錄錯誤\"\"\"
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'error',
            'error_type': error_type,
            'message': message,
            'context': context or {}
        }
        self.logger.error(f"Error occurred: {json.dumps(log_data)}")
```

## 監控儀表板建議

### 📊 關鍵指標監控
1. **API性能指標**
   - 請求響應時間
   - 成功/失敗率
   - 速率限制觸發次數

2. **系統資源指標**
   - CPU 使用率
   - 記憶體使用量
   - 磁盤 I/O
   - 網路流量

3. **業務指標**
   - 數據獲取量
   - 權重測試結果
   - 錯誤發生率
   - 用戶操作統計

4. **品質指標**
   - 測試覆蓋率
   - 代碼複雜度
   - 技術債指標

### 📈 可視化建議
- **Grafana**: 建立監控儀表板
- **Prometheus**: 指標收集和告警
- **ELK Stack**: 日誌分析和可視化
- **APM工具**: 應用性能監控

## 告警系統

### ⚠️ 告警規則建議
```yaml
# Prometheus 告警規則示例
groups:
  - name: trading_bot_alerts
    rules:
      - alert: HighAPIErrorRate
        expr: rate(api_requests_total{status="error"}[5m]) / rate(api_requests_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API 錯誤率過高"
          description: "API 錯誤率在過去 5 分鐘內超過 10%"

      - alert: WeightBelowThreshold
        expr: weight_value < 0.8
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "權重值過低"
          description: "權重值已降至安全閾值以下，需要手動檢查"
```

---

*最後更新: 2025-11-13*
