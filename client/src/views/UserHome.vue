<!--
  企业知识库问答系统 - 用户主页(Q&A聊天界面)
  提供基于RAG的智能问答对话功能
-->
<template>
  <div class="main-layout">
    <!-- 左侧边栏 - 问答历史 -->
    <div class="sidebar">
      <!-- Logo区域 -->
      <div class="sidebar-header">
        <el-icon :size="24"><Reading /></el-icon>
        <span>企业知识库问答</span>
      </div>

      <!-- 用户信息 -->
      <div class="user-info">
        <el-avatar :size="32" :icon="UserFilled" />
        <div class="user-detail">
          <span class="name">{{ user?.username || '用户' }}</span>
          <span class="role-tag">普通用户</span>
        </div>
      </div>

      <!-- 新对话按钮 -->
      <div class="sidebar-actions">
        <el-button type="primary" style="width: 100%" @click="startNewChat">
          <el-icon><Plus /></el-icon> 新对话
        </el-button>
      </div>

      <!-- 历史记录列表 -->
      <div class="history-list">
        <div
          v-for="item in historyList"
          :key="item.id"
          class="history-item"
          :class="{ active: currentHistoryId === item.id }"
          @click="loadHistory(item)"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span class="history-question">{{ truncateText(item.question, 20) }}</span>
          <span class="history-time">{{ formatTime(item.created_at) }}</span>
        </div>
        <el-empty
          v-if="historyList.length === 0"
          description="暂无问答记录"
          :image-size="60"
        />
      </div>

      <!-- 底部操作 -->
      <div class="sidebar-footer">
        <el-button text style="color: #fff" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon> 退出登录
        </el-button>
      </div>
    </div>

    <!-- 右侧内容区 - 聊天界面 -->
    <div class="content-area">
      <div class="chat-container">
        <!-- 聊天头部 -->
        <div class="chat-header">
          <h3>智能知识问答</h3>
          <span class="chat-hint">基于RAG技术，从企业内部知识库中检索答案</span>
        </div>

        <!-- 聊天消息区域 -->
        <div class="chat-messages" ref="messagesContainer">
          <!-- 欢迎提示 -->
          <div v-if="messages.length === 0" class="welcome-section">
            <div class="welcome-icon">
              <el-icon :size="64" color="#409eff"><ChatLineSquare /></el-icon>
            </div>
            <h2>你好！我是企业知识库助手</h2>
            <p>可以问我关于公司制度、技术文档、产品手册等问题</p>
            <div class="suggest-questions">
              <span class="suggest-label">试试这些问题：</span>
              <el-tag
                v-for="q in suggestQuestions"
                :key="q"
                class="suggest-tag"
                @click="sendMessage(q)"
              >
                {{ q }}
              </el-tag>
            </div>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="message-item fade-in-up"
            :class="msg.role"
          >
            <div class="message-avatar">
              <el-avatar v-if="msg.role === 'user'" :size="36" :icon="UserFilled" />
              <el-avatar v-else :size="36" :icon="Reading" style="background: #409eff" />
            </div>
            <div class="message-content">
              <div class="message-role">{{ msg.role === 'user' ? '我' : 'AI助手' }}</div>
              <!-- AI消息使用Markdown渲染 -->
              <div v-if="msg.role === 'assistant'" class="message-text markdown-body" v-html="renderMarkdown(msg.content)" />
              <div v-else class="message-text">{{ msg.content }}</div>

              <!-- 参考来源 -->
              <div v-if="msg.sources && msg.sources.length > 0" class="message-sources">
                <span class="sources-label">📚 参考来源：</span>
                <el-tag
                  v-for="(src, si) in msg.sources"
                  :key="si"
                  size="small"
                  type="success"
                  effect="plain"
                  style="margin-right: 6px"
                >
                  {{ src.title }} ({{ (src.score * 100).toFixed(0) }}%)
                </el-tag>
              </div>

              <!-- 反馈按钮(仅AI消息) -->
              <div v-if="msg.role === 'assistant' && msg.historyId" class="feedback-btns">
                <el-button
                  text
                  size="small"
                  :type="msg.feedback === 1 ? 'success' : 'default'"
                  @click="handleFeedback(msg, 1)"
                >
                  <el-icon><Select /></el-icon> 满意
                </el-button>
                <el-button
                  text
                  size="small"
                  :type="msg.feedback === 0 ? 'danger' : 'default'"
                  @click="handleFeedback(msg, 0)"
                >
                  <el-icon><CloseBold /></el-icon> 不满意
                </el-button>
              </div>
            </div>
          </div>

          <!-- 加载动画 -->
          <div v-if="isLoading" class="message-item assistant fade-in-up">
            <div class="message-avatar">
              <el-avatar :size="36" :icon="Reading" style="background: #409eff" />
            </div>
            <div class="message-content">
              <div class="message-role">AI助手</div>
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入你的问题，按Enter发送（Shift+Enter换行）..."
            resize="none"
            :disabled="isLoading"
            @keydown.enter.exact="sendMessage()"
          />
          <el-button
            type="primary"
            :icon="Promotion"
            :loading="isLoading"
            :disabled="!inputText.trim()"
            @click="sendMessage()"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 用户主页组件 - Q&A聊天界面
 * 实现智能问答对话、历史记录查看、反馈提交等功能
 */
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Reading, UserFilled, Plus, ChatDotRound, ChatLineSquare,
  SwitchButton, Promotion, Select, CloseBold,
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import { getUserInfo, askQuestion, getQAHistory, submitFeedback } from '@/api'

const router = useRouter()

// 用户信息
const user = ref(null)
// 是否正在生成回答
const isLoading = ref(false)
// 输入框文本
const inputText = ref('')
// 消息列表
const messages = ref([])
// 历史记录
const historyList = ref([])
// 当前历史记录ID
const currentHistoryId = ref(null)
// 消息容器引用
const messagesContainer = ref(null)

// 推荐问题
const suggestQuestions = [
  '公司的考勤制度是什么？',
  '如何报销差旅费用？',
  'React组件命名规范是什么？',
  '新员工入职需要准备什么？',
  'Python代码有哪些命名规范？',
]

/** 页面初始化 */
onMounted(async () => {
  try {
    const stored = localStorage.getItem('user')
    user.value = stored ? JSON.parse(stored) : null

    const res = await getUserInfo()
    user.value = res.data.user

    // 加载历史记录
    await loadHistoryList()
  } catch {
    // 错误处理
  }
})

/** 加载问答历史列表 */
const loadHistoryList = async () => {
  try {
    const res = await getQAHistory({ page: 1, page_size: 50 })
    historyList.value = res.data.list || []
  } catch {
    // 忽略加载失败
  }
}

/** 发送消息 */
const sendMessage = async (text) => {
  const question = (text || inputText.value).trim()
  if (!question || isLoading.value) return

  // 将用户消息添加到消息列表
  messages.value.push({
    role: 'user',
    content: question,
  })
  inputText.value = ''
  await scrollToBottom()

  // 调用RAG问答API
  isLoading.value = true
  try {
    const res = await askQuestion(question)
    messages.value.push({
      role: 'assistant',
      content: res.data.answer,
      sources: res.data.sources || [],
      historyId: res.data.history_id,
      feedback: null,
    })

    // 刷新历史记录
    await loadHistoryList()
    currentHistoryId.value = res.data.history_id
  } catch {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，问答服务暂时不可用，请稍后重试。',
      sources: [],
    })
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

/** 开始新对话 */
const startNewChat = () => {
  messages.value = []
  currentHistoryId.value = null
}

/** 加载历史问答记录 */
const loadHistory = (item) => {
  currentHistoryId.value = item.id
  messages.value = [
    { role: 'user', content: item.question },
    {
      role: 'assistant',
      content: item.answer,
      sources: item.sources || [],
      historyId: item.id,
      feedback: item.feedback,
    },
  ]
}

/** 提交反馈 */
const handleFeedback = async (msg, value) => {
  if (!msg.historyId) return
  try {
    await submitFeedback(msg.historyId, value)
    msg.feedback = value
    ElMessage.success(value === 1 ? '感谢您的反馈！' : '我们会继续改进')
  } catch {
    // 错误处理
  }
}

/** 滚动到消息底部 */
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

/** Markdown渲染 */
const renderMarkdown = (text) => {
  if (!text) return ''
  return marked(text, { breaks: true })
}

/** 截断文本 */
const truncateText = (text, maxLen) => {
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}

/** 格式化时间 */
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const min = d.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hour}:${min}`
}

/** 退出登录 */
const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
/* 侧边栏 */
.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.user-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-detail .name {
  font-size: 14px;
}

.user-detail .role-tag {
  font-size: 11px;
  color: #a0aec0;
}

.sidebar-actions {
  padding: 12px 16px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 13px;
}

.history-item:hover, .history-item.active {
  background: rgba(255,255,255,0.1);
}

.history-question {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  font-size: 11px;
  color: #a0aec0;
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(255,255,255,0.1);
}

/* 聊天区域 */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 900px;
  margin: 0 auto;
}

.chat-header {
  text-align: center;
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
}

.chat-header h3 {
  font-size: 18px;
  color: #303133;
}

.chat-hint {
  font-size: 12px;
  color: #909399;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fafbfc;
}

/* 欢迎区域 */
.welcome-section {
  text-align: center;
  padding: 60px 20px;
}

.welcome-section h2 {
  font-size: 24px;
  color: #303133;
  margin: 20px 0 10px;
}

.welcome-section p {
  color: #909399;
  font-size: 14px;
}

.suggest-questions {
  margin-top: 24px;
}

.suggest-label {
  display: block;
  font-size: 13px;
  color: #909399;
  margin-bottom: 10px;
}

.suggest-tag {
  cursor: pointer;
  margin: 4px 6px;
}

.suggest-tag:hover {
  background: #409eff;
  color: #fff;
}

/* 消息样式 */
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 75%;
}

.message-role {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.message-item.user .message-role {
  text-align: right;
}

.message-text {
  background: #fff;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.message-item.user .message-text {
  background: #409eff;
  color: #fff;
}

.message-sources {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f0f9eb;
  border-radius: 8px;
  font-size: 12px;
}

.sources-label {
  color: #67c23a;
  font-weight: 500;
  margin-right: 4px;
}

.feedback-btns {
  margin-top: 6px;
  display: flex;
  gap: 8px;
}

/* 输入区域 */
.chat-input {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #e4e7ed;
}

.chat-input .el-textarea {
  flex: 1;
}

.chat-input .el-button {
  align-self: flex-end;
  height: 40px;
}

/* 打字动画 */
.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 12px 16px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #909399;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-5px); }
}
</style>
