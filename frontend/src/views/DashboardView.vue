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
import { useI18n } from 'vue-i18n'
import { getApiErrorMessage } from '@/services/api'
import { fetchDashboard } from '@/services/dashboard'
import type { CategorySlice, DashboardData } from '@/types'
import { formatRegionLabel, translateCategory, translateRegion } from '@/i18n-helpers'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, PointElement, LineElement, Filler, Tooltip, Legend)

const { t, locale } = useI18n()
const dashboard = ref<DashboardData | null>(null)
const loading = ref(true)
const error = ref('')

const palette = ['#3b82f6', '#fe9c00', '#8b5cf6', '#ef4444', '#10b981', '#f59e0b', '#06b6d4', '#ec4899', '#64748b']
const monthlyColors = ['#3b82f6', '#fe9c00', '#8b5cf6', '#ef4444']

const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const weekdayNames: Record<string, string> = { '월': 'Mon', '화': 'Tue', '수': 'Wed', '목': 'Thu', '금': 'Fri', '토': 'Sat', '일': 'Sun' }

function translateMonthLabel(value: string): string {
  if (locale.value !== 'en') return value
  const match = value.match(/^(\d{1,2})월$/)
  if (!match) return value
  return monthNames[Number(match[1]) - 1] || value
}

function translateWeekdayLabel(value: string): string {
  return locale.value === 'en' ? (weekdayNames[value] || value) : value
}

const monthlyData = computed<ChartData<'bar'>>(() => ({
  labels: (dashboard.value?.monthly_category.labels || []).map(translateMonthLabel),
  datasets: (dashboard.value?.monthly_category.series || []).map((series, index) => ({
    label: translateCategory(t, series.name),
    data: series.data,
    backgroundColor: monthlyColors[index % monthlyColors.length],
    borderRadius: 6,
    borderSkipped: false,
    maxBarThickness: 34,
  })),
}))

const monthlyOptions = computed<ChartOptions<'bar'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, padding: 20 } },
    tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${context.parsed.y}${t('dashboard.unitItems')}` } },
  },
  scales: {
    x: { stacked: true, grid: { display: false }, border: { display: false } },
    y: { stacked: true, beginAtZero: true, ticks: { precision: 0 }, grid: { color: 'rgba(56,38,15,.07)' }, border: { display: false } },
  },
}))

const distributionOptions = computed<ChartOptions<'doughnut'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  cutout: '66%',
  plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => `${context.label}: ${context.parsed}${t('dashboard.unitItems')}` } } },
}))

const weeklyData = computed<ChartData<'line'>>(() => ({
  labels: (dashboard.value?.weekly_trend.labels || []).map(translateWeekdayLabel),
  datasets: [
    {
      label: t('dashboard.viewsDataset'),
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
      label: t('dashboard.likesDataset'),
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

const weeklyOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, padding: 20 } },
    tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${context.parsed.y}${t('dashboard.unitTimes')}` } },
  },
  scales: {
    x: { grid: { display: false }, border: { display: false } },
    y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: 'rgba(56,38,15,.07)' }, border: { display: false } },
  },
}))

const maxRegionScore = computed(() => Math.max(1, ...(dashboard.value?.popular_regions.map((item) => item.score) || [1])))
const maxLocationScore = computed(() => Math.max(1, ...(dashboard.value?.popular_locations.map((item) => item.score) || [1])))

function distributionData(items: CategorySlice[]): ChartData<'doughnut'> {
  return {
    labels: items.map((item) => translateCategory(t, item.label)),
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
  catch (caught) { error.value = getApiErrorMessage(caught, t('errors.dashboardLoad')) }
  finally { loading.value = false }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="page-container dashboard-page">
    <section class="dashboard-heading">
      <div>
        <span class="eyebrow"><BarChart3 :size="14" /> DASHBOARD</span>
        <h1>{{ $t('dashboard.title') }}</h1>
        <p>{{ $t('dashboard.description') }}</p>
      </div>
      <button type="button" class="button button-secondary" :disabled="loading" @click="loadDashboard">
        <RefreshCw :size="16" :class="{ spinning: loading }" /> {{ $t('dashboard.refresh') }}
      </button>
    </section>

    <div v-if="loading" class="dashboard-loading">
      <div v-for="item in 4" :key="item" class="dashboard-card skeleton-card"></div>
    </div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>

    <template v-else-if="dashboard">
      <section class="dashboard-card monthly-chart-card">
        <header class="dashboard-card-heading">
          <div><BarChart3 :size="18" /><h2>{{ $t('dashboard.monthly') }}</h2></div>
          <small>{{ $t('dashboard.recentMonths') }}</small>
        </header>
        <div class="chart-large"><Bar :data="monthlyData" :options="monthlyOptions" /></div>
      </section>

      <div class="dashboard-middle-grid">
        <section class="dashboard-card distribution-card">
          <header class="dashboard-card-heading">
            <div><BarChart3 :size="18" /><h2>{{ $t('dashboard.distribution') }}</h2></div>
            <small>{{ $t('dashboard.comparison') }}</small>
          </header>

          <div class="distribution-grid">
            <article
              v-for="group in [
                { title: $t('common.all'), items: dashboard.category_distribution.total },
                { title: $t('common.seoul'), items: dashboard.category_distribution.seoul },
                { title: $t('common.gyeonggi'), items: dashboard.category_distribution.gyeonggi },
              ]"
              :key="group.title"
              class="distribution-panel"
            >
              <div class="distribution-title"><strong>{{ group.title }}</strong><span>{{ totalCount(group.items) }}{{ $t('dashboard.unitItems') }}</span></div>
              <div v-if="group.items.length" class="donut-wrap">
                <Doughnut :data="distributionData(group.items)" :options="distributionOptions" />
                <div class="donut-center"><strong>{{ totalCount(group.items) }}</strong><small>{{ $t('dashboard.posts') }}</small></div>
              </div>
              <div v-else class="chart-empty">{{ $t('dashboard.noPosts') }}</div>
              <ul v-if="group.items.length" class="distribution-legend">
                <li v-for="(item, index) in group.items" :key="item.label">
                  <span class="legend-dot" :style="{ backgroundColor: palette[index % palette.length] }"></span>
                  <span>{{ translateCategory(t, item.label) }}</span>
                  <strong>{{ percentage(item, group.items) }}%</strong>
                </li>
              </ul>
            </article>
          </div>
        </section>

        <section class="dashboard-card popular-region-card">
          <header class="dashboard-card-heading">
            <div><MapPin :size="18" /><h2>{{ $t('dashboard.popularRegions') }}</h2></div>
          </header>

          <ol v-if="dashboard.popular_regions.length" class="region-ranking">
            <li v-for="(item, index) in dashboard.popular_regions" :key="`${item.region}-${item.district}`">
              <div class="rank-row">
                <span class="rank-number">{{ index + 1 }}</span>
                <strong>{{ formatRegionLabel(t, locale, item.region, item.district) }}</strong>
                <b>{{ $t('common.score', { score: item.score }) }}</b>
              </div>
              <div class="rank-bar"><span :style="{ width: `${Math.max(4, item.score / maxRegionScore * 100)}%` }"></span></div>
              <div class="rank-detail">
                <span>{{ $t('dashboard.postCount', { count: item.post_count }) }}</span>
                <span>{{ $t('dashboard.commentCount', { count: item.comment_count }) }}</span>
                <span>{{ $t('dashboard.likeCount', { count: item.like_count }) }}</span>
                <span>{{ $t('dashboard.viewCount', { count: item.view_count }) }}</span>
              </div>
            </li>
          </ol>
          <div v-else class="chart-empty region-empty"><MessageCircle :size="22" />{{ $t('dashboard.noRegions') }}</div>
        </section>
      </div>

      <div class="location-ranking-grid">
        <section class="dashboard-card location-ranking-card">
          <header class="dashboard-card-heading">
            <div><MapPin :size="18" /><h2>{{ $t('dashboard.popularLocations') }}</h2></div>
            <small>{{ $t('dashboard.reactionBased') }}</small>
          </header>
          <ol v-if="dashboard.popular_locations.length" class="location-content-ranking">
            <li v-for="(item, index) in dashboard.popular_locations" :key="item.contentid">
              <RouterLink :to="{ path: `/locations/${item.contentid}`, query: { region: item.region } }">
                <span class="rank-number">{{ index + 1 }}</span>
                <img :src="item.firstimage || ''" :alt="item.title" />
                <div class="location-rank-copy">
                  <strong>{{ item.title }}</strong>
                  <small>{{ translateRegion(t, item.region) }}</small>
                  <div class="rank-bar"><span :style="{ width: `${Math.max(4, item.score / maxLocationScore * 100)}%` }"></span></div>
                  <div class="rank-detail compact-rank-detail">
                    <span><MessageCircle :size="13" /> {{ item.comment_count }}</span>
                    <span><Heart :size="13" /> {{ item.like_count }}</span>
                    <span><Eye :size="13" /> {{ item.view_count }}</span>
                  </div>
                </div>
                <b>{{ $t('common.score', { score: item.score }) }}</b>
              </RouterLink>
            </li>
          </ol>
          <div v-else class="chart-empty region-empty">{{ $t('dashboard.noPopularLocations') }}</div>
        </section>

        <section class="dashboard-card location-ranking-card">
          <header class="dashboard-card-heading">
            <div><Star :size="18" /><h2>{{ $t('dashboard.topRated') }}</h2></div>
            <small>{{ $t('dashboard.ratingAverage') }}</small>
          </header>
          <ol v-if="dashboard.top_rated_locations.length" class="location-content-ranking rated-location-ranking">
            <li v-for="(item, index) in dashboard.top_rated_locations" :key="item.contentid">
              <RouterLink :to="{ path: `/locations/${item.contentid}`, query: { region: item.region } }">
                <span class="rank-number">{{ index + 1 }}</span>
                <img :src="item.firstimage || ''" :alt="item.title" />
                <div class="location-rank-copy">
                  <strong>{{ item.title }}</strong>
                  <small>{{ translateRegion(t, item.region) }} · {{ $t('dashboard.commentCount', { count: item.comment_count }) }}</small>
                  <div class="dashboard-star-row">
                    <Star v-for="score in 5" :key="score" :size="14" :fill="score <= Math.round(item.average_rating) ? 'currentColor' : 'none'" :class="{ active: score <= Math.round(item.average_rating) }" />
                  </div>
                </div>
                <b>{{ item.average_rating.toFixed(1) }}<small>/5</small></b>
              </RouterLink>
            </li>
          </ol>
          <div v-else class="chart-empty region-empty">{{ $t('dashboard.noRatings') }}</div>
        </section>
      </div>

      <section class="dashboard-card weekly-chart-card">
        <header class="dashboard-card-heading">
          <div><TrendingUp :size="18" /><h2>{{ $t('dashboard.weeklyTrend') }}</h2></div>
          <small>{{ $t('dashboard.thisWeek') }}</small>
        </header>
        <div class="chart-large weekly-chart"><Line :data="weeklyData" :options="weeklyOptions" /></div>
      </section>
    </template>
  </div>
</template>
