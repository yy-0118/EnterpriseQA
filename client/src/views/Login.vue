<!--
  企业知识库问答系统 - 登录页面
  支持管理员和普通用户登录
-->
<template>
  <div class="page-container">
    <div class="login-wrapper">
      <!-- 系统标题 -->
      <div class="system-title">
        <el-icon :size="48" color="#fff"><Reading /></el-icon>
        <h1>企业知识库智能问答系统</h1>
        <p>基于RAG技术的企业内部知识管理与智能检索平台</p>
      </div>

      <!-- 登录卡片 -->
      <el-card class="auth-card">
        <h2 class="card-title">用户登录</h2>
        <el-form
          ref="formRef"
          :model="loginForm"
          :rules="rules"
          size="large"
          @keyup.enter="handleLogin"
        >
          <!-- 用户名 -->
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
            />
          </el-form-item>

          <!-- 密码 -->
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <!-- 登录按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              style="width: 100%"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 底部链接 -->
        <div class="form-footer">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册</router-link>
        </div>

        <!-- 测试账号提示 -->
        <el-alert
          title="测试账号: admin / 123456 (管理员)  |  zhangsan / 123456 (普通用户)"
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 16px"
        />
      </el-card>
    </div>
  </div>
</template>

<script setup>
/**
 * 登录页面组件
 * 提供用户名密码登录，登录成功根据角色跳转不同页面
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { login } from '@/api'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: '',
})

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3-50个字符之间', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' },
  ],
}

/** 处理登录提交 */
const handleLogin = async () => {
  if (!formRef.value) return

  // 表单验证
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await login({
      username: loginForm.username,
      password: loginForm.password,
    })

    // 保存token和用户信息到localStorage
    const { token, user } = res.data
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))

    ElMessage.success(`欢迎回来，${user.username}！`)

    // 根据用户角色跳转不同页面
    if (user.role === 'admin') {
      router.push('/admin')
    } else {
      router.push('/home')
    }
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
}

.system-title {
  text-align: center;
  margin-bottom: 30px;
  color: #fff;
}

.system-title h1 {
  font-size: 28px;
  margin: 16px 0 8px;
  letter-spacing: 2px;
}

.system-title p {
  font-size: 14px;
  opacity: 0.85;
}

.card-title {
  text-align: center;
  font-size: 22px;
  color: #303133;
  margin-bottom: 24px;
}

.form-footer {
  text-align: center;
  font-size: 14px;
  color: #909399;
}

.form-footer a {
  color: #409eff;
  text-decoration: none;
  margin-left: 4px;
}

.form-footer a:hover {
  text-decoration: underline;
}
</style>
