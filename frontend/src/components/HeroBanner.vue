<script setup lang="ts">
import { MapPin, MessageCircle, Sparkles } from '@lucide/vue'
</script>

<template>
  <section class="hero-banner">
    <div class="hero-copy">
      <div class="eyebrow"><Sparkles :size="15" /> {{ $t('hero.eyebrow') }}</div>
      <h1>{{ $t('hero.line1') }}<br />{{ $t('hero.line2') }} <span>LocalHub</span></h1>
      <p>{{ $t('hero.description') }}</p>
      <div class="hero-actions">
        <RouterLink to="/locations" class="button button-primary button-large"><MapPin :size="18" /> {{ $t('hero.dataButton') }}</RouterLink>
        <RouterLink to="/board" class="button button-secondary button-large"><MessageCircle :size="18" /> {{ $t('hero.communityButton') }}</RouterLink>
      </div>
    </div>
    <div class="hero-visual" aria-hidden="true">
      <div class="hero-map-outline"></div>
      <div class="hero-pin pin-seoul"><span>{{ $t('common.seoul') }}</span></div>
      <div class="hero-pin pin-gyeonggi"><span>{{ $t('common.gyeonggi') }}</span></div>
      <div class="hero-place-card">
        <small>{{ $t('hero.linked') }}</small>
        <strong>{{ $t('hero.count') }}</strong>
      </div>
    </div>
  </section>
</template>
