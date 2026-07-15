<template>
  <div class="page-container not-found-page">
    <h1>{{ $t('notFound.title') }}</h1>
    <p>{{ $t('notFound.description') }}</p>
    <RouterLink to="/" class="button button-primary">{{ $t('notFound.home') }}</RouterLink>
  </div>
</template>
