<template>
  <v-dialog
    v-model="showDisclaimer"
    persistent
    scrollable
    max-width="700"
  >
    <v-card>
      <v-card-title class="d-flex flex-column align-center pt-4">
        <v-img
          src="/images/about/stars4water-logo.png"
          alt="STARS4Water"
          height="40"
          width="40"
          class="flex-grow-0 mb-2"
        />
        <span class="text-h6">Disclaimer</span>
      </v-card-title>
      <v-divider />
      <v-card-text
        v-if="renderedDisclaimer"
        class="disclaimer-content"
        v-html="renderedDisclaimer"
      />
      <v-card-actions>
        <v-spacer />
        <v-btn
          color="primary"
          variant="flat"
          @click="showDisclaimer = false"
        >
          OK
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
  import { computed, onMounted, ref } from 'vue'
  import { fetchMarkdownContent } from '~/requests/content.js'
  import { createMarkdownRenderer } from '~/composables/useMarkdownRenderer'

  // Shown automatically on every page load; can only be closed via the OK button.
  const showDisclaimer = ref(true)

  const md = createMarkdownRenderer()

  // Reuse the exact same content as the "Disclaimer S4W metadata portal"
  // section of the About page, so both stay in sync. Fetched on mount (rather
  // than via a top-level await) so this component keeps a synchronous setup,
  // since it is rendered outside of a page-level Suspense boundary.
  const markdownContent = ref('')

  onMounted(async () => {
    markdownContent.value = await fetchMarkdownContent('stars4water/about.md')
  })

  const disclaimerMarkdown = computed(() => {
    if (!markdownContent.value) return ''

    const heading = markdownContent.value.match(/^## Disclaimer S4W metadata portal\s*$/m)
    if (!heading) return ''

    const bodyStart = markdownContent.value.indexOf('\n', heading.index) + 1
    return markdownContent.value.slice(bodyStart)
  })

  const renderedDisclaimer = computed(() => (
    disclaimerMarkdown.value ? md.render(disclaimerMarkdown.value) : ''
  ))
</script>

<style scoped>
  .disclaimer-content :deep(ul),
  .disclaimer-content :deep(ol) {
    margin-left: 1.5rem;
    padding-left: 1.5rem;
    list-style-position: outside;
  }

  .disclaimer-content :deep(li) {
    margin: 0.25rem 0;
  }
</style>
