<script setup lang="ts">
import { BarChart3, Eye, Heart, MapPin, MessageCircle, RefreshCw, Star, TrendingUp } from '@lucide/vue'
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import { Bar, Doughnut, Line } from 'vue-chartjs'
import { computed, onMounted, ref } from 'vue'
import { getApiErrorMessage } from '@/services/api'
import { fetchDashboard } from '@/services/dashboard'
import type { CategorySlice, DashboardData } from '@/types'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, PointElement, LineElement, Filler, Tooltip, Legend)

const dashboard = ref<DashboardData | null>(null)
const loading = ref(true)
const error = ref('')

const palette = ['#3b82f6', '#fe9c00', '#8b5cf6', '#ef4444', '#10b981', '#f59e0b', '#06b6d4', '#ec4899', '#64748b']
const monthlyColors = ['#3b82f6', '#fe9c00', '#8b5cf6', '#ef4444']

const monthlyData = computed<ChartData<'bar'>>(() => ({
  labels: dashboard.value?.monthly_category.labels || [],
  datasets: (dashboard.value?.monthly_category.series || []).map((series, index) => ({
    label: series.name,
    data: series.data,
    backgroundColor: monthlyColors[index % monthlyColors.length],
    borderRadius: 6,
    borderSkipped: false,
    maxBarThickness: 34,
  })),
}))

const monthlyOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, padding: 20 } },
    tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${context.parsed.y}건` } },
  },
  scales: {
    x: { stacked: true, grid: { display: false }, border: { display: false } },
    y: { stacked: true, beginAtZero: true, ticks: { precision: 0 }, grid: { color: 'rgba(56,38,15,.07)' }, border: { display: false } },
  },
}

const distributionOptions: ChartOptions<'doughnut'> = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '66%',
  plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => `${context.label}: ${context.parsed}건` } } },
}

const weeklyData = computed<ChartData<'line'>>(() => ({
  labels: dashboard.value?.weekly_trend.labels || [],
  datasets: [
    {
      label: '조회수',
      data: dashboard.value?.weekly_trend.views || [],
      borderColor: '#fe9c00',
      backgroundColor: 'rgba(254,156,0,.12)',
      pointBackgroundColor: '#fe9c00',
      pointRadius: 4,
      pointHoverRadius: 6,
      borderWidth: 2.5,
      tension: .35,
      fill: false,
    },
    {
      label: '좋아요',
      data: dashboard.value?.weekly_trend.likes || [],
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,.10)',
      pointBackgroundColor: '#3b82f6',
      pointRadius: 4,
      pointHoverRadius: 6,
      borderWidth: 2.5,
      tension: .35,
      fill: false,
    },
  ],
}))

const weeklyOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, padding: 20 } },
    tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${context.parsed.y}회` } },
  },
  scales: {
    x: { grid: { display: false }, border: { display: false } },
    y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: 'rgba(56,38,15,.07)' }, border: { display: false } },
  },
}

const maxRegionScore = computed(() => Math.max(1, ...(dashboard.value?.popular_regions.map((item) => item.score) || [1])))
const maxLocationScore = computed(() => Math.max(1, ...(dashboard.value?.popular_locations.map((item) => item.score) || [1])))

function distributionData(items: CategorySlice[]): ChartData<'doughnut'> {
  return {
    labels: items.map((item) => item.label),
    datasets: [{
      data: items.map((item) => item.count),
      backgroundColor: items.map((_, index) => palette[index % palette.length]),
      borderWidth: 3,
      borderColor: '#ffffff',
      hoverOffset: 5,
    }],
  }
}

function totalCount(items: CategorySlice[]): number {
  return items.reduce((sum, item) => sum + item.count, 0)
}

function percentage(item: CategorySlice, items: CategorySlice[]): number {
  const total = totalCount(items)
  return total ? Math.round((item.count / total) * 100) : 0
}

async function loadDashboard(): Promise<void> {
  loading.value = true
  error.value = ''
  try { dashboard.value = await fetchDashboard() }
  catch (caught) { error.value = getApiErrorMessage(caught, '대시보드 데이터를 불러오지 못했습니다.') }
  finally { loading.value = false }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="page-container dashboard-page">
    <section class="dashboard-heading">
      <div>
        <span class="eyebrow"><BarChart3 :size="14" /> DASHBOARD</span>
        <h1>서울·경기 커뮤니티 대시보드</h1>
        <p>게시글, 댓글, 좋아요, 조회 기록을 실시간으로 집계합니다.</p>
      </div>
      <button type="button" class="button button-secondary" :disabled="loading" @click="loadDashboard">
        <RefreshCw :size="16" :class="{ spinning: loading }" /> 새로고침
      </button>
    </section>

    <div v-if="loading" class="dashboard-loading">
      <div v-for="item in 4" :key="item" class="dashboard-card skeleton-card"></div>
    </div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>

    <template v-else-if="dashboard">
      <section class="dashboard-card monthly-chart-card">
        <header class="dashboard-card-heading">
          <div><BarChart3 :size="18" /><h2>월별 카테고리 게시글 현황</h2></div>
          <small>최근 7개월 · 누적 막대</small>
        </header>
        <div class="chart-large"><Bar :data="monthlyData" :options="monthlyOptions" /></div>
      </section>

      <div class="dashboard-middle-grid">
        <section class="dashboard-card distribution-card">
          <header class="dashboard-card-heading">
            <div><BarChart3 :size="18" /><h2>카테고리별 분포</h2></div>
            <small>전체·서울·경기 비교</small>
          </header>

          <div class="distribution-grid">
            <article
              v-for="group in [
                { title: '전체', items: dashboard.category_distribution.total },
                { title: '서울', items: dashboard.category_distribution.seoul },
                { title: '경기', items: dashboard.category_distribution.gyeonggi },
              ]"
              :key="group.title"
              class="distribution-panel"
            >
              <div class="distribution-title"><strong>{{ group.title }}</strong><span>{{ totalCount(group.items) }}건</span></div>
              <div v-if="group.items.length" class="donut-wrap">
                <Doughnut :data="distributionData(group.items)" :options="distributionOptions" />
                <div class="donut-center"><strong>{{ totalCount(group.items) }}</strong><small>게시글</small></div>
              </div>
              <div v-else class="chart-empty">집계할 게시글이 없습니다.</div>
              <ul v-if="group.items.length" class="distribution-legend">
                <li v-for="(item, index) in group.items" :key="item.label">
                  <span class="legend-dot" :style="{ backgroundColor: palette[index % palette.length] }"></span>
                  <span>{{ item.label }}</span>
                  <strong>{{ percentage(item, group.items) }}%</strong>
                </li>
              </ul>
            </article>
          </div>
        </section>

        <section class="dashboard-card popular-region-card">
          <header class="dashboard-card-heading">
            <div><MapPin :size="18" /><h2>인기 지역 순위</h2></div>
          </header>

          <ol v-if="dashboard.popular_regions.length" class="region-ranking">
            <li v-for="(item, index) in dashboard.popular_regions" :key="`${item.region}-${item.district}`">
              <div class="rank-row">
                <span class="rank-number">{{ index + 1 }}</span>
                <strong>{{ item.label }}</strong>
                <b>{{ item.score }}점</b>
              </div>
              <div class="rank-bar"><span :style="{ width: `${Math.max(4, item.score / maxRegionScore * 100)}%` }"></span></div>
              <div class="rank-detail">
                <span>게시글 {{ item.post_count }}</span>
                <span>댓글 {{ item.comment_count }}</span>
                <span>좋아요 {{ item.like_count }}</span>
                <span>조회 {{ item.view_count }}</span>
              </div>
            </li>
          </ol>
          <div v-else class="chart-empty region-empty"><MessageCircle :size="22" />지역을 선택해 게시글을 작성하면 순위가 집계됩니다.</div>
        </section>
      </div>

      <div class="location-ranking-grid">
        <section class="dashboard-card location-ranking-card">
          <header class="dashboard-card-heading">
            <div><MapPin :size="18" /><h2>인기 지역정보</h2></div>
            <small>사용자 반응 기반</small>
          </header>
          <ol v-if="dashboard.popular_locations.length" class="location-content-ranking">
            <li v-for="(item, index) in dashboard.popular_locations" :key="item.contentid">
              <RouterLink :to="{ path: `/locations/${item.contentid}`, query: { region: item.region } }">
                <span class="rank-number">{{ index + 1 }}</span>
                <img :src="item.firstimage || ''" :alt="item.title" />
                <div class="location-rank-copy">
                  <strong>{{ item.title }}</strong>
                  <small>{{ item.region }}</small>
                  <div class="rank-bar"><span :style="{ width: `${Math.max(4, item.score / maxLocationScore * 100)}%` }"></span></div>
                  <div class="rank-detail compact-rank-detail">
                    <span><MessageCircle :size="13" /> {{ item.comment_count }}</span>
                    <span><Heart :size="13" /> {{ item.like_count }}</span>
                    <span><Eye :size="13" /> {{ item.view_count }}</span>
                  </div>
                </div>
                <b>{{ item.score }}점</b>
              </RouterLink>
            </li>
          </ol>
          <div v-else class="chart-empty region-empty">지역정보에 댓글·좋아요·조회 기록이 쌓이면 순위가 표시됩니다.</div>
        </section>

        <section class="dashboard-card location-ranking-card">
          <header class="dashboard-card-heading">
            <div><Star :size="18" /><h2>평점 높은 지역정보</h2></div>
            <small>댓글 별점 평균순</small>
          </header>
          <ol v-if="dashboard.top_rated_locations.length" class="location-content-ranking rated-location-ranking">
            <li v-for="(item, index) in dashboard.top_rated_locations" :key="item.contentid">
              <RouterLink :to="{ path: `/locations/${item.contentid}`, query: { region: item.region } }">
                <span class="rank-number">{{ index + 1 }}</span>
                <img :src="item.firstimage || ''" :alt="item.title" />
                <div class="location-rank-copy">
                  <strong>{{ item.title }}</strong>
                  <small>{{ item.region }} · 댓글 {{ item.comment_count }}개</small>
                  <div class="dashboard-star-row">
                    <Star v-for="score in 5" :key="score" :size="14" :fill="score <= Math.round(item.average_rating) ? 'currentColor' : 'none'" :class="{ active: score <= Math.round(item.average_rating) }" />
                  </div>
                </div>
                <b>{{ item.average_rating.toFixed(1) }}<small>/5</small></b>
              </RouterLink>
            </li>
          </ol>
          <div v-else class="chart-empty region-empty">지역정보 댓글에 별점을 등록하면 순위가 표시됩니다.</div>
        </section>
      </div>

      <section class="dashboard-card weekly-chart-card">
        <header class="dashboard-card-heading">
          <div><TrendingUp :size="18" /><h2>주간 조회수 · 좋아요 트렌드</h2></div>
          <small>이번 주 월요일~일요일</small>
        </header>
        <div class="chart-large weekly-chart"><Line :data="weeklyData" :options="weeklyOptions" /></div>
      </section>
    </template>
  </div>
</template>
