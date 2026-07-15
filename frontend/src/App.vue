<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'
import ChatWidget from '@/components/ChatWidget.vue'
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <main class="main-content">
      <RouterView />
    </main>
    <footer class="site-footer">
      <div class="page-container footer-inner">
        <div>
          <strong>LocalHub</strong>
          <p>서울·경기 지역정보 공유 커뮤니티</p>
        </div>
        <p class="footer-note">한국관광공사 TourAPI 4.0 · 공공누리 제3유형</p>
      </div>
    </footer>
    <ChatWidget />
  </div>
</template>
