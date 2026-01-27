const http = require('http');

class PythonBridge {
  constructor() {
    this.baseURL = 'http://127.0.0.1:8000';
    this.healthCheckInterval = null;
  }

  async checkHealth() {
    return new Promise((resolve, reject) => {
      const req = http.get(`${this.baseURL}/health`, (res) => {
        let data = '';
        res.on('data', (chunk) => {
          data += chunk;
        });
        res.on('end', () => {
          try {
            const result = JSON.parse(data);
            resolve({ status: 'ok', ...result });
          } catch (e) {
            resolve({ status: 'error', message: '解析响应失败' });
          }
        });
      });

      req.on('error', (error) => {
        resolve({ status: 'error', message: error.message });
      });

      req.setTimeout(2000, () => {
        req.destroy();
        resolve({ status: 'timeout', message: '连接超时' });
      });
    });
  }

  startHealthCheck(callback, interval = 5000) {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }

    this.healthCheckInterval = setInterval(async () => {
      const health = await this.checkHealth();
      if (callback) {
        callback(health);
      }
    }, interval);
  }

  stopHealthCheck() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
  }
}

module.exports = { PythonBridge };
