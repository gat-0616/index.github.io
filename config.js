// 后端 API 地址（部署在同一域名时用 /api，本地开发用完整地址）
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:5000/api'
  : '/api'
