// 币安量化交易监控 - 前端JavaScript

class TradingMonitor {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.isMonitoring = false;
        this.lastSignals = [];

        this.init();
    }

    init() {
        this.initializeSocket();
        this.bindEvents();
        this.updateUI();
    }

    initializeSocket() {
        try {
            // 初始化Socket.IO连接
            this.socket = io();

            // 连接事件
            this.socket.on('connect', () => {
                this.isConnected = true;
                this.updateConnectionStatus(true);
                this.addLog('✅ 服务器连接成功', 'success');
            });

            // 断开连接事件
            this.socket.on('disconnect', () => {
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.addLog('❌ 服务器连接断开', 'error');
            });

            // 状态更新
            this.socket.on('status', (data) => {
                this.handleStatusUpdate(data);
            });

            // 市场数据更新
            this.socket.on('market_update', (data) => {
                this.handleMarketUpdate(data);
            });

        } catch (error) {
            console.error('Socket初始化失败:', error);
            this.addLog('❌ Socket初始化失败: ' + error.message, 'error');
        }
    }

    bindEvents() {
        // 开始监控按钮
        document.getElementById('start-btn').addEventListener('click', () => {
            this.startMonitoring();
        });

        // 停止监控按钮
        document.getElementById('stop-btn').addEventListener('click', () => {
            this.stopMonitoring();
        });

        // 刷新数据按钮
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.refreshData();
        });

        // 清空日志按钮
        document.getElementById('clear-log-btn').addEventListener('click', () => {
            this.clearLog();
        });

        // 设置按钮
        document.getElementById('settings-btn').addEventListener('click', () => {
            this.openSettingsModal();
        });

        // 模态框事件
        document.getElementById('close-modal').addEventListener('click', () => {
            this.closeSettingsModal();
        });

        document.getElementById('cancel-settings-btn').addEventListener('click', () => {
            this.closeSettingsModal();
        });

        document.getElementById('save-settings-btn').addEventListener('click', () => {
            this.saveSettings();
        });

        document.getElementById('load-default-btn').addEventListener('click', () => {
            this.loadDefaultSettings();
        });

        // 点击模态框外部关闭
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('settings-modal');
            if (event.target === modal) {
                this.closeSettingsModal();
            }
        });
    }

    startMonitoring() {
        if (this.isConnected && !this.isMonitoring) {
            this.socket.emit('start_monitoring');
            this.addLog('🚀 开始监控...', 'info');
        } else if (!this.isConnected) {
            this.addLog('❌ 未连接到服务器', 'error');
        }
    }

    stopMonitoring() {
        if (this.isConnected && this.isMonitoring) {
            this.socket.emit('stop_monitoring');
            this.addLog('⏹️ 停止监控...', 'info');
        }
    }

    refreshData() {
        if (this.isConnected) {
            // 通过API获取当前数据
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    this.handleMarketUpdate(data);
                    this.addLog('🔄 数据已刷新', 'info');
                })
                .catch(error => {
                    this.addLog('❌ 数据刷新失败: ' + error.message, 'error');
                });
        } else {
            this.addLog('❌ 未连接到服务器', 'error');
        }
    }

    handleStatusUpdate(data) {
        this.isMonitoring = data.monitoring_active;
        this.updateMonitoringStatus(this.isMonitoring);

        if (data.message) {
            this.addLog('📋 ' + data.message, 'info');
        }
    }

    handleMarketUpdate(data) {
        try {
            // 更新时间戳
            if (data.timestamp) {
                document.getElementById('last-update').textContent = data.timestamp;
            }

            // 更新BTC数据
            if (data.btc) {
                this.updateBTCData(data.btc);
            }

            // 更新DOGE数据
            if (data.doge) {
                this.updateDOGEData(data.doge);
            }

            // 更新信号
            if (data.signals) {
                this.updateSignals(data.signals);
            }

            // 记录更新日志
            this.addLog(`📊 数据更新 - BTC: $${data.btc?.price?.toLocaleString() || 'N/A'}, DOGE: $${data.doge?.price?.toFixed(6) || 'N/A'}`, 'info');

        } catch (error) {
            console.error('处理市场数据失败:', error);
            this.addLog('❌ 数据处理失败: ' + error.message, 'error');
        }
    }

    updateBTCData(btcData) {
        try {
            // 更新价格
            if (btcData.price !== undefined) {
                document.getElementById('btc-price').textContent = btcData.price.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }

            // 更新涨跌幅
            if (btcData.change_percent !== undefined) {
                const changeElement = document.getElementById('btc-change');
                const changeValue = btcData.change_percent;

                changeElement.textContent = (changeValue > 0 ? '+' : '') + changeValue.toFixed(2) + '%';
                changeElement.className = 'change ' + (changeValue >= 0 ? 'positive' : 'negative');
            }

            // 更新条件状态
            if (btcData.conditions) {
                const statusElement = document.getElementById('btc-condition-status');
                statusElement.textContent = btcData.valid ? '✅ 满足' : '❌ 不满足';
                statusElement.className = 'condition-status ' + (btcData.valid ? 'satisfied' : 'not-satisfied');

                // 更新详细数据
                if (btcData.conditions['24h_conditions']) {
                    const volatility = btcData.conditions['24h_conditions'].volatility;
                    if (volatility !== undefined) {
                        document.getElementById('btc-volatility').textContent = (volatility * 100).toFixed(2) + '%';
                    }
                }

                if (btcData.conditions['kdj_conditions']) {
                    const kdj4h = btcData.conditions['kdj_conditions'].kdj_4h;
                    const kdj1h = btcData.conditions['kdj_conditions'].kdj_1h;

                    // 这些KDJ值是旧的显示方式，现在使用详细的indicators数据
                    // 暂时注释掉，避免错误
                    /*
                    if (kdj4h !== undefined) {
                        document.getElementById('btc-kdj-4h').textContent = kdj4h.toFixed(1);
                    }
                    if (kdj1h !== undefined) {
                        document.getElementById('btc-kdj-1h').textContent = kdj1h.toFixed(1);
                    }
                    */
                }
            }

            // 更新详细技术指标
            if (btcData.indicators) {
                this.updateBTCIndicators(btcData.indicators);
            }

        } catch (error) {
            console.error('更新BTC数据失败:', error);
        }
    }

    updateBTCIndicators(indicators) {
        try {
            // 更新市场统计
            if (indicators.market_stats) {
                const stats = indicators.market_stats;

                if (stats.amplitude_24h !== undefined) {
                    document.getElementById('btc-volatility').textContent = stats.amplitude_24h.toFixed(3) + '%';
                }
                if (stats.growth_24h !== undefined) {
                    document.getElementById('btc-growth').textContent = (stats.growth_24h > 0 ? '+' : '') + stats.growth_24h.toFixed(3) + '%';
                }
            }

            // 更新4小时BOLL指标
            if (indicators.boll_4h) {
                const boll4h = indicators.boll_4h;
                document.getElementById('btc-boll-4h-upper').textContent = '$' + boll4h.upper.toLocaleString();
                document.getElementById('btc-boll-4h-middle').textContent = '$' + boll4h.middle.toLocaleString();
                document.getElementById('btc-boll-4h-lower').textContent = '$' + boll4h.lower.toLocaleString();
            }

            // 更新4小时KDJ指标
            if (indicators.kdj_4h) {
                const kdj4h = indicators.kdj_4h;
                document.getElementById('btc-kdj-4h-k').textContent = kdj4h.k.toFixed(2);
                document.getElementById('btc-kdj-4h-d').textContent = kdj4h.d.toFixed(2);
                document.getElementById('btc-kdj-4h-j').textContent = kdj4h.j.toFixed(2);
            }

            // 更新1小时BOLL指标
            if (indicators.boll_1h) {
                const boll1h = indicators.boll_1h;
                document.getElementById('btc-boll-1h-upper').textContent = '$' + boll1h.upper.toLocaleString();
                document.getElementById('btc-boll-1h-middle').textContent = '$' + boll1h.middle.toLocaleString();
                document.getElementById('btc-boll-1h-lower').textContent = '$' + boll1h.lower.toLocaleString();
            }

            // 更新1小时KDJ指标
            if (indicators.kdj_1h) {
                const kdj1h = indicators.kdj_1h;
                document.getElementById('btc-kdj-1h-k').textContent = kdj1h.k.toFixed(2);
                document.getElementById('btc-kdj-1h-d').textContent = kdj1h.d.toFixed(2);
                document.getElementById('btc-kdj-1h-j').textContent = kdj1h.j.toFixed(2);
            }

        } catch (error) {
            console.error('更新BTC指标失败:', error);
        }
    }

    updateDOGEData(dogeData) {
        try {
            // 更新价格
            if (dogeData.price !== undefined) {
                document.getElementById('doge-price').textContent = dogeData.price.toFixed(6);
            }

            // 更新涨跌幅
            if (dogeData.change_percent !== undefined) {
                const changeElement = document.getElementById('doge-change');
                const changeValue = dogeData.change_percent;

                changeElement.textContent = (changeValue > 0 ? '+' : '') + changeValue.toFixed(2) + '%';
                changeElement.className = 'change ' + (changeValue >= 0 ? 'positive' : 'negative');
            }

            // 更新详细技术指标
            if (dogeData.indicators) {
                this.updateDOGEIndicators(dogeData.indicators);
            }

        } catch (error) {
            console.error('更新DOGE数据失败:', error);
        }
    }

    updateDOGEIndicators(indicators) {
        try {
            // 更新市场统计
            if (indicators.market_stats) {
                const stats = indicators.market_stats;

                if (stats.amplitude_24h !== undefined) {
                    document.getElementById('doge-volatility').textContent = stats.amplitude_24h.toFixed(3) + '%';
                }
                if (stats.growth_24h !== undefined) {
                    document.getElementById('doge-growth').textContent = (stats.growth_24h > 0 ? '+' : '') + stats.growth_24h.toFixed(3) + '%';
                }
            }

            // 更新1小时BOLL指标
            if (indicators.boll_1h) {
                const boll1h = indicators.boll_1h;
                document.getElementById('doge-boll-1h-upper').textContent = '$' + boll1h.upper.toFixed(6);
                document.getElementById('doge-boll-1h-middle').textContent = '$' + boll1h.middle.toFixed(6);
                document.getElementById('doge-boll-1h-lower').textContent = '$' + boll1h.lower.toFixed(6);
            }

            // 更新1小时KDJ指标
            if (indicators.kdj_1h) {
                const kdj1h = indicators.kdj_1h;
                document.getElementById('doge-kdj-1h-k').textContent = kdj1h.k.toFixed(2);
                document.getElementById('doge-kdj-1h-d').textContent = kdj1h.d.toFixed(2);
                document.getElementById('doge-kdj-1h-j').textContent = kdj1h.j.toFixed(2);

                // 添加颜色指示
                this.setKDJColor('doge-kdj-1h-k', kdj1h.k);
                this.setKDJColor('doge-kdj-1h-d', kdj1h.d);
                this.setKDJColor('doge-kdj-1h-j', kdj1h.j);
            }

            // 更新15分钟BOLL指标
            if (indicators.boll_15m) {
                const boll15m = indicators.boll_15m;
                document.getElementById('doge-boll-15m-upper').textContent = '$' + boll15m.upper.toFixed(6);
                document.getElementById('doge-boll-15m-middle').textContent = '$' + boll15m.middle.toFixed(6);
                document.getElementById('doge-boll-15m-lower').textContent = '$' + boll15m.lower.toFixed(6);
            }

            // 更新15分钟KDJ指标
            if (indicators.kdj_15m) {
                const kdj15m = indicators.kdj_15m;
                document.getElementById('doge-kdj-15m-k').textContent = kdj15m.k.toFixed(2);
                document.getElementById('doge-kdj-15m-d').textContent = kdj15m.d.toFixed(2);
                document.getElementById('doge-kdj-15m-j').textContent = kdj15m.j.toFixed(2);

                // 添加颜色指示
                this.setKDJColor('doge-kdj-15m-k', kdj15m.k);
                this.setKDJColor('doge-kdj-15m-d', kdj15m.d);
                this.setKDJColor('doge-kdj-15m-j', kdj15m.j);
            }

            // 更新1分钟BOLL指标
            if (indicators.boll_1m) {
                const boll1m = indicators.boll_1m;
                document.getElementById('doge-boll-1m-upper').textContent = '$' + boll1m.upper.toFixed(6);
                document.getElementById('doge-boll-1m-middle').textContent = '$' + boll1m.middle.toFixed(6);
                document.getElementById('doge-boll-1m-lower').textContent = '$' + boll1m.lower.toFixed(6);
            }

            // 更新1分钟KDJ指标
            if (indicators.kdj_1m) {
                const kdj1m = indicators.kdj_1m;
                document.getElementById('doge-kdj-1m-k').textContent = kdj1m.k.toFixed(2);
                document.getElementById('doge-kdj-1m-d').textContent = kdj1m.d.toFixed(2);
                document.getElementById('doge-kdj-1m-j').textContent = kdj1m.j.toFixed(2);

                // 添加颜色指示
                this.setKDJColor('doge-kdj-1m-k', kdj1m.k);
                this.setKDJColor('doge-kdj-1m-d', kdj1m.d);
                this.setKDJColor('doge-kdj-1m-j', kdj1m.j);
            }

        } catch (error) {
            console.error('更新DOGE指标失败:', error);
        }
    }

    setKDJColor(elementId, value) {
        const element = document.getElementById(elementId);
        if (!element) return;

        // 移除现有的颜色类
        element.classList.remove('indicator-value', 'oversold', 'overbought', 'neutral');

        // 添加基础类
        element.classList.add('indicator-value');

        // 根据KDJ值设置颜色
        if (value <= 20) {
            element.classList.add('oversold');  // 超卖 - 绿色
        } else if (value >= 80) {
            element.classList.add('overbought');  // 超买 - 红色
        } else {
            element.classList.add('neutral');  // 中性 - 橙色
        }
    }

    updateSignals(signalsData) {
        try {
            // 更新信号计数
            const count = signalsData.count || 0;
            document.getElementById('signal-count').textContent = count;

            // 更新信号列表
            const signalList = document.getElementById('signal-list');

            if (count === 0) {
                signalList.innerHTML = '<p class="no-signals">暂无信号</p>';
            } else {
                let signalsHtml = '';

                signalsData.list.forEach((signal, index) => {
                    const signalType = signal.type || 'unknown';
                    const signalId = signal.signal_id || index + 1;
                    const timestamp = new Date().toLocaleTimeString();

                    signalsHtml += `
                        <div class="signal-item ${signalType} new">
                            <div class="signal-header">
                                ${signalType === 'buy' ? '🟢 买入信号' : '🔴 卖出信号'} ${signalId}
                            </div>
                            <div class="signal-time">${timestamp}</div>
                        </div>
                    `;
                });

                signalList.innerHTML = signalsHtml;

                // 检查是否有新信号
                if (signalsData.list.length > this.lastSignals.length) {
                    this.addLog(`🚨 新信号触发! 当前有 ${count} 个信号`, 'success');

                    // 可以添加声音提醒
                    this.playNotificationSound();
                }

                this.lastSignals = signalsData.list;
            }

        } catch (error) {
            console.error('更新信号数据失败:', error);
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        statusElement.textContent = connected ? '已连接' : '未连接';
        statusElement.className = 'status ' + (connected ? 'connected' : 'disconnected');
    }

    updateMonitoringStatus(monitoring) {
        const statusElement = document.getElementById('monitoring-status');
        statusElement.textContent = monitoring ? '监控中' : '已停止';
        statusElement.className = 'status ' + (monitoring ? 'running' : 'stopped');
    }

    updateUI() {
        // 初始化UI状态
        this.updateConnectionStatus(false);
        this.updateMonitoringStatus(false);

        // 显示初始日志
        this.addLog('💻 系统初始化完成', 'info');
        this.addLog('🔌 正在连接服务器...', 'info');
    }

    addLog(message, type = 'info') {
        const logContent = document.getElementById('log-content');
        const timestamp = new Date().toLocaleTimeString();

        const logEntry = document.createElement('p');
        logEntry.className = `log-entry ${type}`;
        logEntry.textContent = `[${timestamp}] ${message}`;

        logContent.appendChild(logEntry);

        // 保持滚动到底部
        logContent.scrollTop = logContent.scrollHeight;

        // 限制日志条数（保留最新100条）
        const entries = logContent.getElementsByClassName('log-entry');
        if (entries.length > 100) {
            logContent.removeChild(entries[0]);
        }
    }

    clearLog() {
        const logContent = document.getElementById('log-content');
        logContent.innerHTML = '';
        this.addLog('📝 日志已清空', 'info');
    }

    playNotificationSound() {
        // 简单的提示音（可选）
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmEaBDmr5fO6eSwGJXzH7NaJOQgZaLvr45xNEwtLpe3Zo2AcBzwEFgAA');
            audio.volume = 0.3;
            audio.play().catch(() => {
                // 忽略播放失败
            });
        } catch (error) {
            // 忽略音频错误
        }
    }

    // 设置相关方法
    openSettingsModal() {
        // 加载当前设置
        this.loadCurrentSettings();

        // 显示模态框
        document.getElementById('settings-modal').style.display = 'block';

        this.addLog('⚙️ 打开策略设置', 'info');
    }

    closeSettingsModal() {
        document.getElementById('settings-modal').style.display = 'none';
    }

    loadCurrentSettings() {
        // 从服务器获取当前设置
        fetch('/api/settings')
            .then(response => response.json())
            .then(settings => {
                this.populateSettingsForm(settings);
            })
            .catch(error => {
                this.addLog('❌ 加载设置失败: ' + error.message, 'error');
            });
    }

    populateSettingsForm(settings) {
        try {
            // BTC条件设置
            if (settings.btc_conditions) {
                document.getElementById('volatility-threshold').value = (settings.btc_conditions.volatility_threshold * 100).toFixed(2);
                document.getElementById('growth-threshold').value = (settings.btc_conditions.growth_threshold * 100).toFixed(2);
                document.getElementById('kdj-threshold').value = settings.btc_conditions.kdj_threshold;
            }

            // DOGE信号设置
            if (settings.doge_thresholds) {
                const oversold = settings.doge_thresholds.oversold || [10, 15, 20, 20];
                document.getElementById('oversold-1').value = oversold[0] || 10;
                document.getElementById('oversold-2').value = oversold[1] || 15;
                document.getElementById('oversold-3').value = oversold[2] || 20;
                document.getElementById('oversold-4').value = oversold[3] || 20;
                document.getElementById('overbought').value = settings.doge_thresholds.overbought || 90;
            }

            // 监控设置
            if (settings.monitoring) {
                document.getElementById('update-interval').value = settings.monitoring.update_interval || 5;
            }

        } catch (error) {
            this.addLog('❌ 填充设置表单失败: ' + error.message, 'error');
        }
    }

    saveSettings() {
        try {
            // 收集表单数据
            const settings = {
                btc_conditions: {
                    volatility_threshold: parseFloat(document.getElementById('volatility-threshold').value) / 100,
                    growth_threshold: parseFloat(document.getElementById('growth-threshold').value) / 100,
                    kdj_threshold: parseFloat(document.getElementById('kdj-threshold').value)
                },
                doge_thresholds: {
                    oversold: [
                        parseFloat(document.getElementById('oversold-1').value),
                        parseFloat(document.getElementById('oversold-2').value),
                        parseFloat(document.getElementById('oversold-3').value),
                        parseFloat(document.getElementById('oversold-4').value)
                    ],
                    overbought: parseFloat(document.getElementById('overbought').value)
                },
                monitoring: {
                    update_interval: parseInt(document.getElementById('update-interval').value)
                }
            };

            // 发送到服务器
            fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    this.addLog('✅ 设置保存成功！', 'success');
                    this.closeSettingsModal();

                    // 如果更新了监控间隔，提示重启监控
                    if (settings.monitoring.update_interval !== this.lastUpdateInterval) {
                        this.addLog('🔄 监控间隔已更新，重启监控以生效', 'info');
                        this.lastUpdateInterval = settings.monitoring.update_interval;
                    }
                } else {
                    this.addLog('❌ 保存设置失败: ' + result.error, 'error');
                }
            })
            .catch(error => {
                this.addLog('❌ 保存设置失败: ' + error.message, 'error');
            });

        } catch (error) {
            this.addLog('❌ 收集设置数据失败: ' + error.message, 'error');
        }
    }

    loadDefaultSettings() {
        // 加载默认设置
        const defaultSettings = {
            btc_conditions: {
                volatility_threshold: 3.0,   // 3%
                growth_threshold: 1.0,       // 1%
                kdj_threshold: 50
            },
            doge_thresholds: {
                oversold: [10, 15, 20, 20],
                overbought: 90
            },
            monitoring: {
                update_interval: 5
            }
        };

        this.populateSettingsForm(defaultSettings);
        this.addLog('🔄 已恢复默认设置（未保存）', 'info');
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.tradingMonitor = new TradingMonitor();
});

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (window.tradingMonitor && window.tradingMonitor.socket) {
        window.tradingMonitor.socket.disconnect();
    }
});