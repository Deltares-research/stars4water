<template>
  <div class="pa-8">
    <v-container fluid>
      <v-row>
        <v-col
          cols="12"
          md="3"
          class="d-none d-md-block"
        >
          <nav
            v-if="tocItems.length"
            class="toc-sidebar"
          >
            <div class="text-subtitle-2 font-weight-bold mb-2">
              On this page
            </div>
            <ul class="toc-list">
              <li
                v-for="item in tocItems"
                :key="item.id"
                :class="`toc-level-${item.level}`"
              >
                <a :href="`#${item.id}`">{{ item.text }}</a>
              </li>
            </ul>
          </nav>
        </v-col>
        <v-col
          cols="12"
          md="9"
          lg="8"
        >
          <div
            v-if="renderedMarkdown"
            class="about-content"
            v-html="renderedMarkdown"
          />
          <div v-else>
            Loading...
          </div>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup>
  import { computed } from 'vue'
  import { fetchMarkdownContent } from '~/requests/content.js'
  import { createMarkdownRenderer, slugify } from '~/composables/useMarkdownRenderer'

  const md = createMarkdownRenderer()

  // Fetch the markdown file
  const markdownContent = await fetchMarkdownContent('stars4water/about.md')

  // Render the markdown to HTML
  const renderedMarkdown = computed(() => 
    markdownContent ? md.render(markdownContent) : ''
  )

  // Build a clickable table of contents from the H2/H3 headings
  const tocItems = computed(() => {
    if (!markdownContent) return []

    const tokens = md.parse(markdownContent, {})
    const items = []

    tokens.forEach((token, idx) => {
      if (token.type === 'heading_open' && (token.tag === 'h2' || token.tag === 'h3')) {
        const inline = tokens[idx + 1]
        const text = inline ? inline.content : ''
        items.push({
          level: Number(token.tag.slice(1)),
          text,
          id: slugify(text),
        })
      }
    })

    return items
  })
</script>

<style>
  html {
    scroll-behavior: smooth;
  }

  .about-content h1,
  .about-content h2,
  .about-content h3 {
    scroll-margin-top: 88px;
  }

  .about-content ul,
  .about-content ol {
    margin-left: 1.5rem;
    padding-left: 1.5rem;
    list-style-position: outside;
  }
  
  .about-content li {
    margin: 0.25rem 0;
  }
  
  .about-content ul ul,
  .about-content ol ol,
  .about-content ul ol,
  .about-content ol ul {
    margin-left: 1.5rem;
  }

  .toc-sidebar {
    position: sticky;
    top: 88px;
  }

  .toc-list {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .toc-list li {
    margin: 0.25rem 0;
  }

  .toc-list a {
    text-decoration: none;
    color: inherit;
  }

  .toc-list a:hover {
    text-decoration: underline;
  }

  .toc-level-3 {
    padding-left: 1rem;
    font-size: 0.9em;
  }

  .about-content .funding-banner {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .about-content .funding-logo {
    max-height: 64px;
    width: auto;
    flex-shrink: 0;
  }

  .about-content .funding-text {
    margin: 0;
    font-size: 0.85em;
    color: rgba(0, 0, 0, 0.7);
  }
  </style>
  