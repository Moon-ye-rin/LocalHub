<script setup lang="ts">
import { MapPin, MessageCircle, Sparkles } from '@lucide/vue'
</script>

<template>
  <section class="hero-card">
    <div class="hero-copy">
      <div class="eyebrow"><Sparkles :size="15" /> 서울·경기 지역정보를 한곳에</div>
      <h1>동네의 발견을<br />함께 나누는 <span>LocalHub</span></h1>
      <p>서울·경기 공공 관광정보를 찾고, 지역 생활 후기를 회원가입 없이 익명으로 공유하세요.</p>
      <div class="hero-actions">
        <RouterLink to="/locations" class="button button-primary button-large"><MapPin :size="18" /> 공공데이터 보기</RouterLink>
        <RouterLink to="/board" class="button button-secondary button-large"><MessageCircle :size="18" /> 커뮤니티 참여</RouterLink>
      </div>
    </div>
    <div class="hero-visual" aria-hidden="true">
      <div class="map-orbit orbit-one"></div>
      <div class="map-orbit orbit-two"></div>
      <div class="hero-pin pin-seoul"><span>서울</span></div>
      <div class="hero-pin pin-gyeonggi"><span>경기</span></div>
      <div class="hero-place-card">
        <small>실제 데이터 연동</small>
        <strong>TourAPI 12,512건</strong>
      </div>
    </div>
  </section>
</template>
