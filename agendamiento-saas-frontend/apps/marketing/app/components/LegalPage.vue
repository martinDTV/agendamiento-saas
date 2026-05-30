<script setup>
defineProps({
  title: { type: String, required: true },
  updated: { type: String, default: '' }
})
</script>

<template>
  <UContainer class="py-16 sm:py-24">
    <div class="mx-auto max-w-3xl">
      <h1 class="text-3xl font-medium tracking-tight text-highlighted sm:text-4xl">
        {{ title }}
      </h1>
      <p v-if="updated" class="mt-3 text-sm text-muted">
        Última actualización: {{ updated }}
      </p>

      <!-- Long-form legal copy. `prose`-like spacing via utility classes on a
           scoped wrapper so headings/paragraphs read comfortably. -->
      <div class="legal mt-10 text-default">
        <slot />
      </div>
    </div>
  </UContainer>
</template>

<style scoped>
.legal :deep(h2) {
  margin-top: 2.5rem;
  margin-bottom: 0.75rem;
  font-size: 1.25rem;
  font-weight: 500;
  letter-spacing: -0.01em;
  color: var(--ui-text-highlighted, #131D2E);
}
.legal :deep(h3) {
  margin-top: 1.75rem;
  margin-bottom: 0.5rem;
  font-size: 1.05rem;
  font-weight: 500;
}
.legal :deep(p) {
  margin-bottom: 1rem;
  line-height: 1.75;
  max-width: 70ch;
}
.legal :deep(ul) {
  margin: 0.5rem 0 1.25rem;
  padding-left: 1.25rem;
  list-style: disc;
}
.legal :deep(li) {
  margin-bottom: 0.4rem;
  line-height: 1.7;
}
.legal :deep(a) {
  color: var(--ui-primary, #274C77);
  text-decoration: underline;
  text-underline-offset: 2px;
}
.legal :deep(.placeholder) {
  background: color-mix(in oklch, var(--color-warning, #EAB308) 18%, transparent);
  border-radius: 4px;
  padding: 0 4px;
  font-weight: 500;
}
</style>
