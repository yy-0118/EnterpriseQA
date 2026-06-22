/**
 * 企业知识库问答系统 - 路由配置
 * 根据用户角色动态控制页面访问权限
 */
import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

// 路由定义
const routes = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', noAuth: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', noAuth: true },
  },
  {
    path: '/home',
    name: 'UserHome',
    component: () => import('@/views/UserHome.vue'),
    meta: { title: '知识问答', role: 'user' },
  },
  {
    path: '/admin',
    name: 'AdminHome',
    component: () => import('@/views/AdminHome.vue'),
    meta: { title: '管理员后台', role: 'admin' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * 全局路由守卫 - 权限验证
 * 1. 未登录用户只能访问登录/注册页
 * 2. 普通用户不能访问管理员页面
 * 3. 管理员不能访问用户问答页面
 */
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 企业知识库` : '企业知识库问答系统'

  const token = localStorage.getItem('token')
  let user = null
  try {
    user = JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    user = null
  }

  // 不需要登录的页面（登录、注册）
  if (to.meta.noAuth) {
    // 已登录则跳转到对应首页
    if (token && user) {
      if (user.role === 'admin') {
        return next('/admin')
      }
      return next('/home')
    }
    return next()
  }

  // 需要登录但未登录
  if (!token) {
    ElMessage.warning('请先登录')
    return next('/login')
  }

  // 检查角色权限
  if (to.meta.role) {
    if (to.meta.role === 'admin' && user?.role !== 'admin') {
      ElMessage.error('需要管理员权限')
      return next('/home')
    }
    if (to.meta.role === 'user' && user?.role === 'admin') {
      return next('/admin')
    }
  }

  next()
})

export default router
