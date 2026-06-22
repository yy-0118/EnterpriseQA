/**
 * 企业知识库问答系统 - API接口层
 * 封装所有后端API请求，统一管理请求拦截和错误处理
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',    // 后端API基础路径（通过Vite代理转发）
  timeout: 60000,     // 请求超时60秒（RAG问答可能较慢）
})

/**
 * 请求拦截器 - 自动添加JWT Token
 */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

/**
 * 响应拦截器 - 统一处理错误
 */
api.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端返回的code不为200时，显示错误消息
    if (res.code && res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message))
    }
    return res
  },
  (error) => {
    // HTTP状态码错误处理
    if (error.response) {
      const { status } = error.response
      if (status === 401) {
        ElMessage.error('登录已过期，请重新登录')
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      } else if (status === 403) {
        ElMessage.error('权限不足')
      } else if (status === 500) {
        ElMessage.error('服务器内部错误')
      } else {
        ElMessage.error(error.response.data?.message || '网络请求失败')
      }
    } else {
      ElMessage.error('网络连接异常，请检查网络')
    }
    return Promise.reject(error)
  }
)

// ==================== 认证相关API ====================

/** 用户登录 */
export const login = (data) => api.post('/auth/login', data)

/** 用户注册 */
export const register = (data) => api.post('/auth/register', data)

/** 获取当前用户信息 */
export const getUserInfo = () => api.get('/auth/userinfo')

// ==================== 智能问答API ====================

/** RAG智能问答 */
export const askQuestion = (question) => api.post('/qa/ask', { question })

/** 获取问答历史 */
export const getQAHistory = (params) => api.get('/qa/history', { params })

/** 提交问答反馈 */
export const submitFeedback = (historyId, feedback) =>
  api.post(`/qa/feedback/${historyId}`, { feedback })

// ==================== 知识库管理API ====================

/** 获取文档列表 */
export const getDocuments = (params) => api.get('/kb/documents', { params })

/** 获取单个文档详情 */
export const getDocument = (id) => api.get(`/kb/documents/${id}`)

/** 上传文档 */
export const addDocument = (data) => api.post('/kb/documents', data)

/** 上传本地文件到知识库 */
export const uploadFile = (formData) =>
  api.post('/kb/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

/** 更新文档 */
export const updateDocument = (id, data) => api.put(`/kb/documents/${id}`, data)

/** 删除文档 */
export const deleteDocument = (id) => api.delete(`/kb/documents/${id}`)

/** 获取分类列表 */
export const getCategories = () => api.get('/kb/categories')

/** 添加分类 */
export const addCategory = (data) => api.post('/kb/categories', data)

// ==================== 管理员API ====================

/** 获取仪表盘统计数据 */
export const getDashboard = () => api.get('/admin/dashboard')

/** 获取用户列表 */
export const getUsers = (params) => api.get('/admin/users', { params })

/** 更新用户信息 */
export const updateUser = (id, data) => api.put(`/admin/users/${id}`, data)

/** 删除用户 */
export const deleteUser = (id) => api.delete(`/admin/users/${id}`)

/** 获取所有问答历史（管理员） */
export const getAllQAHistory = (params) => api.get('/admin/qa/history', { params })

export default api
