import MarkdownIt from 'markdown-it'

// Turn a heading's text into a URL-friendly anchor id
export const slugify = (text) => text
  .toLowerCase()
  .trim()
  .replace(/[^a-z0-9\s-]/g, '')
  .replace(/\s+/g, '-')

// Creates a MarkdownIt instance configured for rendering the app's content
// files, with every heading given an id so it can be linked to (e.g. from a
// table of contents).
export function createMarkdownRenderer() {
  const md = new MarkdownIt({
    html: true,        // Enable HTML tags in source
    linkify: true,     // Autoconvert URL-like text to links
    breaks: true,      // Convert '\n' in paragraphs into <br>
  })

  md.renderer.rules.heading_open = (tokens, idx) => {
    const inline = tokens[idx + 1]
    const text = inline ? inline.content : ''
    return `<${tokens[idx].tag} id="${slugify(text)}">`
  }

  return md
}
