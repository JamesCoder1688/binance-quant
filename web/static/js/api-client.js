// 币安量化交易监控 - REST API 客户端

class APITradingMonitor {
    constructor() {
        this.isMonitoring = false;
        this.updateInterval = 3000; // 3秒更新一次
        this.intervalId = null;
        this.lastUpdate = null;

        this.init();
    }

    init() {
        this.bindEvents();
        this.updateUI();
        this.startAutoRefresh();
    }

    bindEvents() {
        // 开始监控按钮
        const startBtn = document.getElementById('start-btn');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startMonitoring());
        }

        // 停止监控按钮
        const stopBtn = document.getElementById('stop-btn');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopMonitoring());
        }

        // 刷新数据按钮
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        // 策略设置按钮
        const settingsBtn = document.getElementById('settings-btn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.openSettings());
        }

        // 清空日志按钮
        const clearLogBtn = document.getElementById('clear-log-btn');
        if (clearLogBtn) {
            clearLogBtn.addEventListener('click', () => this.clearLog());
        }

        // 模态框关闭
        const closeModal = document.getElementById('close-modal');
        if (closeModal) {
            closeModal.addEventListener('click', () => this.closeSettings());
        }

        // 点击模态框外部关闭
        const modal = document.getElementById('settings-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeSettings();
                }
            });
        }
    }

    updateUI() {
        this.updateConnectionStatus(true);
        this.updateMonitoringStatus(this.isMonitoring);
    }

    startAutoRefresh() {
        this.addLog('🔄 启动自动刷新 (每3秒)', 'info');
        this.refreshData(); // 立即刷新一次

        this.intervalId = setInterval(() => {
            if (this.isMonitoring) {
                this.refreshData();
            }
        }, this.updateInterval);
    }

    stopAutoRefresh() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            this.addLog('⏹️ 停止自动刷新', 'info');
        }
    }

    async refreshData() {
        try {
            this.updateLastUpdate();

            // 并行获取BTC和DOGE数据
            const [btcData, dogeData] = await Promise.all([
                this.fetchBTCData(),
                this.fetchDOGEData()
            ]);

            if (btcData && !btcData.error) {
                this.updateBTCData(btcData);
                this.addLog('📊 BTC数据更新成功', 'success');
            } else {
                this.addLog('❌ BTC数据获取失败', 'error');
            }

            if (dogeData && !dogeData.error) {
                this.updateDOGEData(dogeData);
                this.addLog('🐕 DOGE数据更新成功', 'success');
            } else {
                this.addLog('❌ DOGE数据获取失败', 'error');
            }

        } catch (error) {
            console.error('数据刷新失败:', error);
            this.addLog('❌ 数据刷新失败: ' + error.message, 'error');
        }
    }

    async fetchBTCData() {
        try {
            const response = await fetch('/api/btc-data');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('获取BTC数据失败:', error);
            return { error: error.message };
        }
    }

    async fetchDOGEData() {
        try {
            const response = await fetch('/api/doge-data');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('获取DOGE数据失败:', error);
            return { error: error.message };
        }
    }

    updateBTCData(data) {
        try {
            // 更新价格
            const priceElement = document.getElementById('btc-price');
            if (priceElement && data.price) {
                priceElement.textContent = data.price.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }

            // 更新涨跌幅
            const changeElement = document.getElementById('btc-change');
            if (changeElement && data.change !== undefined) {
                const changeText = (data.change >= 0 ? '+' : '') + data.change.toFixed(2) + '%';
                changeElement.textContent = changeText;
                changeElement.className = data.change >= 0 ? 'positive' : 'negative';
            }

            // 更新24h数据
            this.updateElement('btc-volatility', data.amplitude_24h?.toFixed(3) + '%');
            this.updateElement('btc-growth', data.growth_24h?.toFixed(2) + '%');

            // 更新技术指标
            if (data.indicators) {
                this.updateBTCIndicators(data.indicators);
            }

        } catch (error) {
            console.error('更新BTC数据失败:', error);
        }
    }

    updateDOGEData(data) {
        try {
            // 更新价格
            const priceElement = document.getElementById('doge-price');
            if (priceElement && data.price) {
                priceElement.textContent = data.price.toFixed(6);
            }

            // 更新涨跌幅
            const changeElement = document.getElementById('doge-change');
            if (changeElement && data.change !== undefined) {
                const changeText = (data.change >= 0 ? '+' : '') + data.change.toFixed(2) + '%';
                changeElement.textContent = changeText;
                changeElement.className = data.change >= 0 ? 'positive' : 'negative';
            }

            // 更新24h数据
            this.updateElement('doge-volatility', data.amplitude_24h?.toFixed(3) + '%');
            this.updateElement('doge-growth', data.growth_24h?.toFixed(2) + '%');

            // 更新技术指标
            if (data.indicators) {
                this.updateDOGEIndicators(data.indicators);
            }

        } catch (error) {
            console.error('更新DOGE数据失败:', error);
        }
    }

    updateBTCIndicators(indicators) {
        // 4小时指标
        if (indicators['4h']) {
            const boll4h = indicators['4h'].boll;
            const kdj4h = indicators['4h'].kdj;

            if (boll4h) {
                this.updateElement('btc-boll-4h-upper', '$' + boll4h.UP?.toLocaleString());
                this.updateElement('btc-boll-4h-middle', '$' + boll4h.MB?.toLocaleString());
                this.updateElement('btc-boll-4h-lower', '$' + boll4h.DN?.toLocaleString());
            }

            if (kdj4h) {
                this.updateElement('btc-kdj-4h-k', kdj4h.K?.toFixed(1));
                this.updateElement('btc-kdj-4h-d', kdj4h.D?.toFixed(1));
                this.updateElement('btc-kdj-4h-j', kdj4h.J?.toFixed(1));
            }
        }

        // 1小时指标
        if (indicators['1h']) {
            const boll1h = indicators['1h'].boll;
            const kdj1h = indicators['1h'].kdj;

            if (boll1h) {
                this.updateElement('btc-boll-1h-upper', '$' + boll1h.UP?.toLocaleString());
                this.updateElement('btc-boll-1h-middle', '$' + boll1h.MB?.toLocaleString());
                this.updateElement('btc-boll-1h-lower', '$' + boll1h.DN?.toLocaleString());
            }

            if (kdj1h) {
                this.updateElement('btc-kdj-1h-k', kdj1h.K?.toFixed(1));
                this.updateElement('btc-kdj-1h-d', kdj1h.D?.toFixed(1));
                this.updateElement('btc-kdj-1h-j', kdj1h.J?.toFixed(1));
            }
        }
    }

    updateDOGEIndicators(indicators) {
        const timeframes = ['1h', '15m', '1m'];

        timeframes.forEach(tf => {
            if (indicators[tf]) {
                const boll = indicators[tf].boll;
                const kdj = indicators[tf].kdj;

                if (boll) {
                    this.updateElement(`doge-boll-${tf}-upper`, '$' + boll.UP?.toFixed(6));
                    this.updateElement(`doge-boll-${tf}-middle`, '$' + boll.MB?.toFixed(6));
                    this.updateElement(`doge-boll-${tf}-lower`, '$' + boll.DN?.toFixed(6));
                }

                if (kdj) {
                    this.updateElement(`doge-kdj-${tf}-k`, kdj.K?.toFixed(1));
                    this.updateElement(`doge-kdj-${tf}-d`, kdj.D?.toFixed(1));
                    this.updateElement(`doge-kdj-${tf}-j`, kdj.J?.toFixed(1));
                }
            }
        });
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element && value !== undefined && value !== 'undefined') {
            element.textContent = value;
        }
    }

    startMonitoring() {
        this.isMonitoring = true;
        this.updateMonitoringStatus(true);
        this.addLog('▶️ 开始监控', 'success');
    }

    stopMonitoring() {
        this.isMonitoring = false;
        this.updateMonitoringStatus(false);
        this.addLog('⏸️ 停止监控', 'warning');
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = connected ? '已连接' : '未连接';
            statusElement.className = 'status ' + (connected ? 'connected' : 'disconnected');
        }
    }

    updateMonitoringStatus(monitoring) {
        const statusElement = document.getElementById('monitoring-status');
        if (statusElement) {
            statusElement.textContent = monitoring ? '监控中' : '已停止';
            statusElement.className = 'status ' + (monitoring ? 'active' : 'stopped');
        }
    }

    updateLastUpdate() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('zh-CN', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        const updateElement = document.getElementById('last-update');
        if (updateElement) {
            updateElement.textContent = timeString;
        }

        this.lastUpdate = now;
    }

    addLog(message, type = 'info') {
        const logContent = document.getElementById('log-content');
        if (logContent) {
            const timestamp = new Date().toLocaleTimeString('zh-CN', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });

            const logEntry = document.createElement('p');
            logEntry.className = `log-entry ${type}`;
            logEntry.textContent = `[${timestamp}] ${message}`;

            logContent.appendChild(logEntry);
            logContent.scrollTop = logContent.scrollHeight;

            // 限制日志条数
            const entries = logContent.querySelectorAll('.log-entry');
            if (entries.length > 100) {
                entries[0].remove();
            }
        }
    }

    clearLog() {
        const logContent = document.getElementById('log-content');
        if (logContent) {
            logContent.innerHTML = '<p class="log-entry">日志已清空</p>';
        }
    }

    openSettings() {
        const modal = document.getElementById('settings-modal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    closeSettings() {
        const modal = document.getElementById('settings-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.tradingMonitor = new APITradingMonitor();
});