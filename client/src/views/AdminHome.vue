<!--
  企业知识库问答系统 - 管理员后台主页
  包含: 数据统计图表、用户管理、知识库管理
-->
<template>
  <div class="main-layout">
    <!-- 左侧导航菜单 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <el-icon :size="24"><Setting /></el-icon>
        <span>管理员后台</span>
      </div>

      <div class="user-info">
        <el-avatar :size="32" :icon="UserFilled" />
        <div class="user-detail">
          <span class="name">{{ user?.username || '管理员' }}</span>
          <span class="role-tag">系统管理员</span>
        </div>
      </div>

      <!-- 导航菜单 -->
      <el-menu
        :default-active="activeMenu"
        background-color="transparent"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        @select="handleMenuSelect"
      >
        <el-menu-item index="dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据概览</span>
        </el-menu-item>
        <el-menu-item index="users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="documents">
          <el-icon><Document /></el-icon>
          <span>知识库管理</span>
        </el-menu-item>
        <el-menu-item index="qa-history">
          <el-icon><Clock /></el-icon>
          <span>问答记录</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-button text style="color: #fff" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon> 退出登录
        </el-button>
      </div>
    </div>

    <!-- 右侧内容区 -->
    <div class="content-area">
      <!-- ==================== 1. 数据概览 ==================== -->
      <div v-if="activeMenu === 'dashboard'" class="dashboard-page">
        <h2 class="page-title">数据概览</h2>

        <!-- 统计卡片 -->
        <el-row :gutter="16" class="stats-row">
          <el-col :span="6">
            <el-card class="stat-card hover-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-icon" style="background: #ecf5ff; color: #409eff">
                  <el-icon :size="28"><UserFilled /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ dashboard.user_count }}</div>
                  <div class="stat-label">用户总数</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card hover-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-icon" style="background: #f0f9eb; color: #67c23a">
                  <el-icon :size="28"><Document /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ dashboard.doc_count }}</div>
                  <div class="stat-label">知识文档数</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card hover-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-icon" style="background: #fdf6ec; color: #e6a23c">
                  <el-icon :size="28"><ChatDotSquare /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ dashboard.qa_count }}</div>
                  <div class="stat-label">问答总数</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card hover-card" shadow="hover">
              <div class="stat-content">
                <div class="stat-icon" style="background: #fef0f0; color: #f56c6c">
                  <el-icon :size="28"><Connection /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ dashboard.vector_chunks }}</div>
                  <div class="stat-label">向量块总数</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 图表区域 -->
        <el-row :gutter="16" style="margin-top: 16px">
          <!-- 近7天问答趋势(折线图) -->
          <el-col :span="14">
            <el-card shadow="hover">
              <template #header>
                <span class="chart-title">📈 近7天问答趋势</span>
              </template>
              <div ref="trendChartRef" style="height: 320px"></div>
            </el-card>
          </el-col>

          <!-- 知识分类分布(饼图) -->
          <el-col :span="10">
            <el-card shadow="hover">
              <template #header>
                <span class="chart-title">📊 知识分类分布</span>
              </template>
              <div ref="categoryChartRef" style="height: 320px"></div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 月度趋势和用户活跃度 -->
        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="14">
            <el-card shadow="hover">
              <template #header>
                <span class="chart-title">📅 近12个月问答趋势</span>
              </template>
              <div ref="monthlyChartRef" style="height: 300px"></div>
            </el-card>
          </el-col>
          <el-col :span="10">
            <el-card shadow="hover">
              <template #header>
                <span class="chart-title">🏆 用户活跃度排行 TOP10</span>
              </template>
              <div style="height: 300px; overflow-y: auto">
                <div
                  v-for="(item, index) in dashboard.user_activity"
                  :key="index"
                  class="rank-item"
                >
                  <span class="rank-num" :class="{ top: index < 3 }">{{ index + 1 }}</span>
                  <span class="rank-name">{{ item.username }}</span>
                  <el-progress
                    :percentage="getPercent(item.count, dashboard.user_activity)"
                    :color="getRankColor(index)"
                    :show-text="false"
                    style="flex:1; margin: 0 12px"
                  />
                  <span class="rank-count">{{ item.count }}次</span>
                </div>
                <el-empty v-if="!dashboard.user_activity?.length" description="暂无数据" />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- ==================== 2. 用户管理 ==================== -->
      <div v-if="activeMenu === 'users'" class="manage-page">
        <h2 class="page-title">用户管理</h2>
        <el-card>
          <div class="toolbar">
            <el-input
              v-model="userSearch"
              placeholder="搜索用户名或邮箱"
              :prefix-icon="Search"
              clearable
              style="width: 280px"
              @change="loadUsers"
            />
          </div>
          <el-table :data="userList" stripe style="width: 100%">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="用户名" width="140" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
            <el-table-column prop="role" label="角色" width="100">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
                  {{ row.role === 'admin' ? '管理员' : '普通用户' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="qa_count" label="问答数" width="80" />
            <el-table-column prop="doc_count" label="文档数" width="80" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
                  {{ row.status === 1 ? '正常' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="注册时间" width="160" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="warning" @click="openUserEdit(row)">
                  编辑
                </el-button>
                <el-popconfirm
                  title="确定删除该用户吗？"
                  @confirm="handleDeleteUser(row.id)"
                >
                  <template #reference>
                    <el-button size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrap">
            <el-pagination
              v-model:current-page="userPage"
              :page-size="userPageSize"
              :total="userTotal"
              layout="total, prev, pager, next"
              @current-change="loadUsers"
            />
          </div>
        </el-card>

        <!-- 用户编辑对话框 -->
        <el-dialog v-model="userEditVisible" title="编辑用户" width="450px">
          <el-form :model="userEditForm" label-width="80px">
            <el-form-item label="用户名">
              <el-input v-model="userEditForm.username" disabled />
            </el-form-item>
            <el-form-item label="角色">
              <el-radio-group v-model="userEditForm.role">
                <el-radio value="user">普通用户</el-radio>
                <el-radio value="admin">管理员</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="状态">
              <el-switch
                v-model="userEditForm.status"
                :active-value="1"
                :inactive-value="0"
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="userEditForm.email" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="userEditVisible = false">取消</el-button>
            <el-button type="primary" @click="handleUpdateUser">保存</el-button>
          </template>
        </el-dialog>
      </div>

      <!-- ==================== 3. 知识库管理 ==================== -->
      <div v-if="activeMenu === 'documents'" class="manage-page">
        <h2 class="page-title">知识库管理</h2>
        <el-card>
          <div class="toolbar">
            <el-input
              v-model="docKeyword"
              placeholder="搜索文档标题"
              :prefix-icon="Search"
              clearable
              style="width: 280px"
              @change="loadDocuments"
            />
            <el-button type="primary" :icon="Plus" @click="openDocAdd">上传文档</el-button>
            <el-button type="success" :icon="UploadFilled" @click="openFileUpload">上传文件</el-button>
          </div>
          <el-table :data="docList" stripe style="width: 100%">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="title" label="文档标题" min-width="200" />
            <el-table-column prop="file_type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag size="small">{{ row.file_type.toUpperCase() }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="chunk_count" label="向量块" width="80" />
            <el-table-column prop="uploader_name" label="上传者" width="100" />
            <el-table-column prop="created_at" label="上传时间" width="160" />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="openDocDetail(row)">查看</el-button>
                <el-popconfirm
                  title="确定删除该文档吗？将同时从向量库中移除"
                  @confirm="handleDeleteDoc(row.id)"
                >
                  <template #reference>
                    <el-button size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrap">
            <el-pagination
              v-model:current-page="docPage"
              :page-size="docPageSize"
              :total="docTotal"
              layout="total, prev, pager, next"
              @current-change="loadDocuments"
            />
          </div>
        </el-card>

        <!-- 文档上传对话框 -->
        <el-dialog v-model="docAddVisible" title="上传知识文档" width="600px">
          <el-form :model="docAddForm" label-width="80px">
            <el-form-item label="文档标题" required>
              <el-input v-model="docAddForm.title" placeholder="请输入文档标题" />
            </el-form-item>
            <el-form-item label="文档类型">
              <el-select v-model="docAddForm.file_type" style="width: 100%">
                <el-option label="纯文本 (txt)" value="txt" />
                <el-option label="Markdown (md)" value="md" />
              </el-select>
            </el-form-item>
            <el-form-item label="知识分类">
              <el-select v-model="docAddForm.category_id" placeholder="请选择分类" clearable style="width: 100%">
                <el-option
                  v-for="cat in flatCategories"
                  :key="cat.id"
                  :label="cat.name"
                  :value="cat.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="文档内容" required>
              <el-input
                v-model="docAddForm.content"
                type="textarea"
                :rows="10"
                placeholder="请输入文档完整内容..."
              />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="docAddVisible = false">取消</el-button>
            <el-button type="primary" :loading="docUploading" @click="handleAddDoc">
              {{ docUploading ? '上传中...' : '确认上传' }}
            </el-button>
          </template>
        </el-dialog>

        <!-- 文档详情对话框 -->
        <el-dialog v-model="docDetailVisible" title="文档详情" width="700px">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="标题">{{ docDetail.title }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ docDetail.file_type }}</el-descriptions-item>
            <el-descriptions-item label="向量块数">{{ docDetail.chunk_count }}</el-descriptions-item>
            <el-descriptions-item label="上传者">{{ docDetail.uploader_name }}</el-descriptions-item>
            <el-descriptions-item label="上传时间">{{ docDetail.created_at }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top: 16px">
            <h4 style="margin-bottom: 8px">文档内容预览</h4>
            <div class="doc-preview markdown-body" v-html="renderMarkdown(docDetail.content || '')" />
          </div>
        </el-dialog>

        <!-- 本地文件上传对话框 -->
        <el-dialog v-model="docFileUploadVisible" title="上传本地文件到知识库" width="500px">
          <el-form label-width="80px">
            <el-form-item label="选择文件" required>
              <div class="file-upload-area" @click="triggerFileInput">
                <el-icon :size="40" color="#409eff"><UploadFilled /></el-icon>
                <p v-if="!docFilePath" style="margin-top: 12px; color: #909399;">
                  点击选择 .txt 或 .md 文件
                </p>
                <p v-else style="margin-top: 12px; color: #67c23a; font-weight: 500;">
                  {{ docFilePath }}
                </p>
                <input
                  ref="docFileInputRef"
                  type="file"
                  accept=".txt,.md,.markdown"
                  style="display: none"
                  @change="handleFileChange"
                />
              </div>
            </el-form-item>
            <el-form-item label="知识分类">
              <el-select v-model="docFileCategory" placeholder="请选择分类（可选）" clearable style="width: 100%">
                <el-option
                  v-for="cat in flatCategories"
                  :key="cat.id"
                  :label="cat.name"
                  :value="cat.id"
                />
              </el-select>
            </el-form-item>
          </el-form>
          <el-alert
            type="info"
            :closable="false"
            show-icon
            title="支持 .txt / .md 文件，文件名将作为文档标题"
          />
          <template #footer>
            <el-button @click="docFileUploadVisible = false">取消</el-button>
            <el-button type="primary" :loading="docFileUploadLoading" :disabled="!docFilePath" @click="handleFileUpload">
              {{ docFileUploadLoading ? '上传中...' : '确 定' }}
            </el-button>
          </template>
        </el-dialog>
      </div>

      <!-- ==================== 4. 问答记录 ==================== -->
      <div v-if="activeMenu === 'qa-history'" class="manage-page">
        <h2 class="page-title">问答记录</h2>
        <el-card>
          <div class="toolbar">
            <el-input
              v-model="qaKeyword"
              placeholder="搜索问答内容"
              :prefix-icon="Search"
              clearable
              style="width: 280px"
              @change="loadQAHistory"
            />
          </div>
          <el-table :data="qaList" stripe style="width: 100%">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="用户" width="100" />
            <el-table-column prop="question" label="问题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="answer" label="回答" min-width="300" show-overflow-tooltip />
            <el-table-column prop="feedback" label="反馈" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.feedback === 1" type="success" size="small">满意</el-tag>
                <el-tag v-else-if="row.feedback === 0" type="danger" size="small">不满意</el-tag>
                <span v-else style="color:#c0c4cc">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="160" />
          </el-table>
          <div class="pagination-wrap">
            <el-pagination
              v-model:current-page="qaPage"
              :page-size="qaPageSize"
              :total="qaTotal"
              layout="total, prev, pager, next"
              @current-change="loadQAHistory"
            />
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 管理员后台主组件
 * 集成了数据统计面板、用户管理、知识库管理和问答记录查看
 */
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Setting, UserFilled, DataAnalysis, User, Document, Clock,
  SwitchButton, Plus, Search, ChatDotSquare, Connection, UploadFilled,
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { marked } from 'marked'
import {
  getDashboard, getUsers, updateUser, deleteUser,
  getDocuments, addDocument, deleteDocument, getCategories,
  getAllQAHistory, uploadFile,
} from '@/api'

const router = useRouter()

// 当前激活的菜单
const activeMenu = ref('dashboard')
// 用户信息
const user = ref(null)

// 图表引用
const trendChartRef = ref(null)
const categoryChartRef = ref(null)
const monthlyChartRef = ref(null)
let trendChart = null
let categoryChart = null
let monthlyChart = null

// ==================== 仪表盘数据 ====================
const dashboard = reactive({
  user_count: 0,
  doc_count: 0,
  qa_count: 0,
  today_qa_count: 0,
  vector_chunks: 0,
  trend_data: [],
  category_data: [],
  user_activity: [],
  monthly_trend: [],
})

// ==================== 用户管理数据 ====================
const userList = ref([])
const userTotal = ref(0)
const userPage = ref(1)
const userPageSize = ref(20)
const userSearch = ref('')
const userEditVisible = ref(false)
const userEditForm = reactive({ id: null, username: '', role: 'user', status: 1, email: '' })

// ==================== 知识库管理数据 ====================
const docList = ref([])
const docTotal = ref(0)
const docPage = ref(1)
const docPageSize = ref(20)
const docKeyword = ref('')
const docAddVisible = ref(false)
const docUploading = ref(false)
const docAddForm = reactive({ title: '', content: '', file_type: 'txt', category_id: null })
const docDetailVisible = ref(false)
const docDetail = ref({})
const docFileUploadVisible = ref(false)  // 文件上传对话框
const docFileUploadLoading = ref(false)  // 文件上传进度
const docFilePath = ref('')  // 选中的文件路径（用于显示）
const docFileCategory = ref(null)  // 文件上传所选分类
const docFileInputRef = ref(null)  // 隐藏的 input[type=file] 引用
const categories = ref([])
const flatCategories = ref([])

// ==================== 问答记录数据 ====================
const qaList = ref([])
const qaTotal = ref(0)
const qaPage = ref(1)
const qaPageSize = ref(20)
const qaKeyword = ref('')

/** 页面初始化 */
onMounted(async () => {
  try {
    const stored = localStorage.getItem('user')
    user.value = stored ? JSON.parse(stored) : null
  } catch { /* ignore */ }
  await loadDashboard()
})

/** ==================== 仪表盘方法 ==================== */

/** 加载仪表盘数据 */
const loadDashboard = async () => {
  try {
    const res = await getDashboard()
    Object.assign(dashboard, res.data)
    await nextTick()
    renderCharts()
  } catch { /* ignore */ }
}

/** 渲染ECharts图表 */
const renderCharts = () => {
  // 1. 近7天趋势折线图
  if (trendChartRef.value) {
    if (!trendChart) trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dashboard.trend_data?.map(d => d.date) || [],
      },
      yAxis: { type: 'value', minInterval: 1 },
      series: [{
        name: '问答数',
        type: 'line',
        smooth: true,
        data: dashboard.trend_data?.map(d => d.count) || [],
        areaStyle: { color: 'rgba(64,158,255,0.15)' },
        lineStyle: { color: '#409eff', width: 2 },
        itemStyle: { color: '#409eff' },
      }],
    })
  }

  // 2. 分类分布饼图
  if (categoryChartRef.value) {
    if (!categoryChart) categoryChart = echarts.init(categoryChartRef.value)
    categoryChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        type: 'pie',
        radius: ['45%', '75%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{d}%' },
        data: dashboard.category_data || [],
        color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#8e71c7'],
      }],
    })
  }

  // 3. 月度趋势柱状图
  if (monthlyChartRef.value) {
    if (!monthlyChart) monthlyChart = echarts.init(monthlyChartRef.value)
    monthlyChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: dashboard.monthly_trend?.map(d => d.month) || [],
        axisLabel: { rotate: 45 },
      },
      yAxis: { type: 'value', minInterval: 1 },
      series: [{
        name: '问答数',
        type: 'bar',
        data: dashboard.monthly_trend?.map(d => d.count) || [],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#409eff' },
            { offset: 1, color: '#79bbff' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      }],
    })
  }
}

/** 监听菜单切换，重新渲染图表 */
watch(activeMenu, async (val) => {
  if (val === 'dashboard') {
    await loadDashboard()
  }
})

/** ==================== 用户管理方法 ==================== */

const loadUsers = async () => {
  try {
    const res = await getUsers({ page: userPage.value, page_size: userPageSize.value, keyword: userSearch.value })
    userList.value = res.data.list
    userTotal.value = res.data.total
  } catch { /* ignore */ }
}

const openUserEdit = (row) => {
  Object.assign(userEditForm, {
    id: row.id,
    username: row.username,
    role: row.role,
    status: row.status,
    email: row.email || '',
  })
  userEditVisible.value = true
}

const handleUpdateUser = async () => {
  try {
    await updateUser(userEditForm.id, {
      role: userEditForm.role,
      status: userEditForm.status,
      email: userEditForm.email,
    })
    ElMessage.success('更新成功')
    userEditVisible.value = false
    loadUsers()
  } catch { /* ignore */ }
}

const handleDeleteUser = async (id) => {
  try {
    await deleteUser(id)
    ElMessage.success('删除成功')
    loadUsers()
    loadDashboard()
  } catch { /* ignore */ }
}

/** ==================== 知识库管理方法 ==================== */

const flattenCategories = (cats, prefix = '') => {
  const result = []
  for (const cat of cats) {
    result.push({ id: cat.id, name: prefix + cat.name })
    if (cat.children?.length) {
      result.push(...flattenCategories(cat.children, prefix + '  └ '))
    }
  }
  return result
}

const loadDocuments = async () => {
  try {
    const res = await getDocuments({ page: docPage.value, page_size: docPageSize.value, keyword: docKeyword.value })
    docList.value = res.data.list
    docTotal.value = res.data.total
  } catch { /* ignore */ }
}

const loadCategories = async () => {
  try {
    const res = await getCategories()
    categories.value = res.data.categories || []
    flatCategories.value = flattenCategories(categories.value)
  } catch { /* ignore */ }
}

const openDocAdd = () => {
  Object.assign(docAddForm, { title: '', content: '', file_type: 'txt', category_id: null })
  docAddVisible.value = true
  loadCategories()
}

const handleAddDoc = async () => {
  if (!docAddForm.title.trim() || !docAddForm.content.trim()) {
    ElMessage.warning('标题和内容不能为空')
    return
  }
  docUploading.value = true
  try {
    await addDocument({
      title: docAddForm.title.trim(),
      content: docAddForm.content.trim(),
      file_type: docAddForm.file_type,
      category_id: docAddForm.category_id,
    })
    ElMessage.success('文档上传成功')
    docAddVisible.value = false
    loadDocuments()
    loadDashboard()
  } catch { /* ignore */ }
  docUploading.value = false
}

/** 打开文件上传对话框 */
const openFileUpload = () => {
  docFilePath.value = ''
  docFileCategory.value = null
  docFileUploadVisible.value = true
  loadCategories()
}

/** 触发文件选择框 */
const triggerFileInput = () => {
  if (docFileInputRef.value) {
    docFileInputRef.value.click()
  }
}

/** 文件选择变更 */
const handleFileChange = (event) => {
  const file = event.target.files?.[0]
  if (!file) {
    docFilePath.value = ''
    return
  }
  docFilePath.value = file.name
  // 保存文件引用供上传使用
  event.target._selectedFile = file
}

/** 上传本地文件到知识库 */
const handleFileUpload = async () => {
  const file = docFileInputRef.value?._selectedFile
  if (!file) {
    ElMessage.warning('请先选择文件')
    return
  }
  docFileUploadLoading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    if (docFileCategory.value) {
      formData.append('category_id', docFileCategory.value)
    }
    await uploadFile(formData)
    ElMessage.success('文件上传成功')
    docFileUploadVisible.value = false
    loadDocuments()
    loadDashboard()
  } catch {
    // 错误已在拦截器处理
  }
  docFileUploadLoading.value = false
  // 重置input以便重复选同一文件
  if (docFileInputRef.value) {
    docFileInputRef.value.value = ''
    docFileInputRef.value._selectedFile = null
  }
}

const openDocDetail = (row) => {
  docDetail.value = row
  docDetailVisible.value = true
}

const handleDeleteDoc = async (id) => {
  try {
    await deleteDocument(id)
    ElMessage.success('删除成功')
    loadDocuments()
    loadDashboard()
  } catch { /* ignore */ }
}

/** ==================== 问答记录方法 ==================== */

const loadQAHistory = async () => {
  try {
    const res = await getAllQAHistory({ page: qaPage.value, page_size: qaPageSize.value, keyword: qaKeyword.value })
    qaList.value = res.data.list
    qaTotal.value = res.data.total
  } catch { /* ignore */ }
}

/** ==================== 菜单切换 ==================== */
const handleMenuSelect = (index) => {
  activeMenu.value = index
  if (index === 'users') loadUsers()
  else if (index === 'documents') loadDocuments()
  else if (index === 'qa-history') loadQAHistory()
}

/** ==================== 工具方法 ==================== */

const getPercent = (count, arr) => {
  if (!arr?.length) return 0
  const max = arr[0]?.count || 1
  return Math.round((count / max) * 100)
}

const getRankColor = (index) => {
  const colors = ['#f56c6c', '#e6a23c', '#409eff', '#909399']
  return colors[index] || '#c0c4cc'
}

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked(text, { breaks: true })
}

/** 退出登录 */
const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
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

.user-detail { display: flex; flex-direction: column; gap: 2px; }
.user-detail .name { font-size: 14px; }
.user-detail .role-tag { font-size: 11px; color: #a0aec0; }

/* Element Plus菜单覆写 */
.el-menu {
  border-right: none !important;
}

.sidebar-footer {
  margin-top: auto;
  padding: 12px 16px;
  border-top: 1px solid rgba(255,255,255,0.1);
}

/* 页面通用 */
.page-title {
  font-size: 20px;
  color: #303133;
  padding: 20px 24px 12px;
}

.dashboard-page, .manage-page {
  padding: 0 24px 24px;
}

/* 统计卡片 */
.stats-row { margin-bottom: 8px; }

.stat-card { cursor: default; }

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
}

/* 图表标题 */
.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

/* 排行项 */
.rank-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.rank-num {
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  border-radius: 50%;
  background: #f0f2f5;
  color: #909399;
  font-size: 12px;
  font-weight: bold;
  margin-right: 8px;
}

.rank-num.top { background: #fdf6ec; color: #e6a23c; }

.rank-name {
  width: 80px;
  font-size: 13px;
  color: #606266;
}

.rank-count {
  font-size: 13px;
  color: #909399;
  width: 40px;
  text-align: right;
}

/* 工具栏和分页 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 文档预览 */
.doc-preview {
  max-height: 400px;
  overflow-y: auto;
  padding: 12px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.7;
}

/* 文件上传区域 */
.file-upload-area {
  width: 100%;
  height: 160px;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.file-upload-area:hover {
  border-color: #409eff;
  background: #ecf5ff;
}
</style>
