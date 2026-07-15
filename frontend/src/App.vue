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
          <p>{{ $t('footer.description') }}</p>
        </div>
        <p class="footer-note">{{ $t('footer.license') }}</p>
      </div>
    </footer>
    <ChatWidget />
  </div>
</template>
