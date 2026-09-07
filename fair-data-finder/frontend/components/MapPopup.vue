<template>
  <div style="display: none;">
    <!-- This component doesn't render anything, it just manages the Mapbox popup -->
  </div>
</template>

<script setup>
  import { watch, onBeforeUnmount, ref, unref, nextTick } from 'vue'
  import { useMap } from '@studiometa/vue-mapbox-gl'
  import mapboxgl from 'mapbox-gl'
  import { formatDate, firstAssetHref } from '~/utils/helpers'

  const props = defineProps({
    selectedFeature: {
      type: Object,
      default: null,
    },
    coordinates: {
      type: Array,
      default: null,
      validator: (value) => {
        if (!value) return true
        return Array.isArray(value) && value.length === 2
      },
    },
    anchor: {
      type: [String, Array],
      default: undefined, // Changed: undefined lets Mapbox auto-position
    },
    offset: {
      type: Array,
      default: () => [0, 0], // Changed: neutral offset, let Mapbox handle positioning
    },
    maxWidth: {
      type: String,
      default: '420px',
    },
    closeButton: {
      type: Boolean,
      default: false,
    },
    closeOnClick: {
      type: Boolean,
      default: true,
    },
    closeOnMove: {
      type: Boolean,
      default: false,
    },
  })

  const emit = defineEmits(['close'])

  const { map } = useMap()
  const popupInstance = ref(null)

  function createPopupHTML(feature) {
    if (!feature) return ''

    const title = feature.properties?.title || feature.id || 'Untitled'
    const description = feature.properties?.description || 'No description.'
    const assetHref = firstAssetHref(feature)
    const date = formatDate(feature)
    const viewDetailsUrl = `/register/${feature.id}/view`

    return `
      <div class="popup-content">
        <div class="popup-title">${escapeHtml(title)}</div>
        <div class="popup-body">
          <p class="description">${escapeHtml(description)}</p>
          <p class="asset-link">
            ${assetHref ? `<a href="${escapeHtml(assetHref)}" target="_blank" rel="noopener noreferrer">${escapeHtml(assetHref)}</a>` : '—'}
          </p>
          <p class="view-details">
            <a href="${escapeHtml(viewDetailsUrl)}">View details</a>
          </p>
          <p class="date">${escapeHtml(date)}</p>
        </div>
      </div>
    `
  }

  function escapeHtml(text) {
    if (!text) return ''
    if (typeof text !== 'string') {
      text = String(text)
    }
    // Simple HTML escaping
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
  }

  function removePopup() {
    if (popupInstance.value) {
      popupInstance.value.remove()
      popupInstance.value = null
    }
    detachReclampListeners()
  }

  // Upper-bound popup dimensions, kept in sync with the CSS below
  // (max-width on .mapboxgl-popup-content / max-height on the popup content)
  const POPUP_WIDTH_ESTIMATE = 420
  const POPUP_HEIGHT_ESTIMATE = 400

  // Container padding kept between the popup and the map container edges.
  const CONTAINER_EDGE_PADDING = 12

  // Fallback size of the little triangular popup arrow, used when it can't
  // be measured yet.
  const DEFAULT_ARROW_SIZE = 10

  // Pick whichever side of the point has more room, so the popup grows into
  // the larger available space instead of a side that may not fit it at all
  // (e.g. a point close to the top of a map container that only occupies
  // half the screen, near the app bar).
  function computeAnchor(clientWidth, clientHeight, point) {
    const vertical = point.y > clientHeight / 2 ? 'bottom' : 'top'
    const horizontal =
      point.x < POPUP_WIDTH_ESTIMATE / 2
        ? 'left'
        : point.x > clientWidth - POPUP_WIDTH_ESTIMATE / 2
          ? 'right'
          : ''

    return horizontal ? `${vertical}-${horizontal}` : vertical
  }

  // Cap the popup's scrollable content to the space actually available
  // between the point and the container edge it grows towards, so the
  // popup can never extend past the map container's own top/bottom (which
  // would otherwise be clipped invisibly by mapbox's `overflow: hidden`,
  // e.g. disappearing behind a page header/app bar sitting above the map).
  function clampPopupHeight(popup, mapInstance, point) {
    const popupElement = popup.getElement()
    if (!popupElement) return

    const contentElement = popupElement.querySelector('.mapboxgl-popup-content')
    if (!contentElement) return

    const { clientHeight } = mapInstance.getContainer()
    const anchor = popup.options.anchor || ''
    const growsDownward = anchor === '' || anchor.startsWith('top')
    const arrowElement = popupElement.querySelector('.mapboxgl-popup-tip')
    const arrowSize = arrowElement ? arrowElement.offsetHeight : DEFAULT_ARROW_SIZE

    const availableVertical = growsDownward
      ? clientHeight - point.y - arrowSize - CONTAINER_EDGE_PADDING
      : point.y - arrowSize - CONTAINER_EDGE_PADDING

    const clampedHeight = Math.max(120, Math.min(availableVertical, POPUP_HEIGHT_ESTIMATE))
    contentElement.style.maxHeight = `${clampedHeight}px`
  }

  // Measure the popup's actual rendered box against the map container's
  // actual box and nudge it back in bounds (via the popup offset) if it
  // still overflows horizontally. Vertical overflow is handled separately
  // by clampPopupHeight, since a horizontal shift can't fix a popup that's
  // simply too tall for the available space.
  function clampPopupToContainer(popup, mapInstance) {
    const popupElement = popup.getElement()
    const containerElement = mapInstance.getContainer()
    if (!popupElement || !containerElement) return

    const popupRect = popupElement.getBoundingClientRect()
    const containerRect = containerElement.getBoundingClientRect()

    let dx = 0

    if (popupRect.left < containerRect.left + CONTAINER_EDGE_PADDING) {
      dx = containerRect.left + CONTAINER_EDGE_PADDING - popupRect.left
    } else if (popupRect.right > containerRect.right - CONTAINER_EDGE_PADDING) {
      dx = containerRect.right - CONTAINER_EDGE_PADDING - popupRect.right
    }

    if (dx !== 0) {
      const currentOffset = popup.options.offset
      const [baseX, baseY] = Array.isArray(currentOffset) ? currentOffset : [0, 0]
      popup.setOffset([baseX + dx, baseY])
    }
  }

  // Tracks the currently attached map listener so it can be removed when the
  // popup closes or is replaced. Without this, a popup left open across a
  // pan/zoom (closeOnMove is false) keeps the clamping computed for its
  // *original* screen position, and can drift back out of the container
  // (e.g. behind the app bar or the left results panel) as the map moves.
  let reclampMapInstance = null
  let reclampHandler = null

  function detachReclampListeners() {
    if (reclampMapInstance && reclampHandler) {
      reclampMapInstance.off('move', reclampHandler)
      reclampMapInstance.off('zoom', reclampHandler)
      reclampMapInstance.off('resize', reclampHandler)
    }
    reclampMapInstance = null
    reclampHandler = null
  }

  function attachReclampListeners(popup, mapInstance) {
    detachReclampListeners()

    reclampHandler = () => {
      if (!popupInstance.value || popupInstance.value !== popup) return
      const currentPoint = mapInstance.project(popup.getLngLat())
      clampPopupHeight(popup, mapInstance, currentPoint)
      clampPopupToContainer(popup, mapInstance)
    }
    reclampMapInstance = mapInstance

    mapInstance.on('move', reclampHandler)
    mapInstance.on('zoom', reclampHandler)
    mapInstance.on('resize', reclampHandler)
  }

  function createPopup() {
    const mapInstance = unref(map)
    if (!mapInstance || !props.selectedFeature || !props.coordinates) {
      return
    }

    // Remove existing popup first
    removePopup()

    const [lng, lat] = props.coordinates
    const point = mapInstance.project([lng, lat])
    const { clientWidth, clientHeight } = mapInstance.getContainer()

    // Cap the popup width to the map container's own size so it never
    // attempts to be wider than the space actually available to it.
    const maxWidthPx = parseInt(props.maxWidth, 10) || POPUP_WIDTH_ESTIMATE
    const clampedMaxWidth = Math.min(maxWidthPx, clientWidth - CONTAINER_EDGE_PADDING * 2)

    // Build popup options - only include anchor if specified
    const popupOptions = {
      closeButton: props.closeButton,
      closeOnClick: props.closeOnClick,
      closeOnMove: props.closeOnMove,
      maxWidth: `${clampedMaxWidth}px`,
    }

    // Only override anchor if explicitly provided, otherwise compute it
    // based on the point's pixel position so the popup stays fully visible.
    popupOptions.anchor = props.anchor !== undefined
      ? props.anchor
      : computeAnchor(clientWidth, clientHeight, point)

    // Only add offset if provided and not default
    if (props.offset && (props.offset[0] !== 0 || props.offset[1] !== 0)) {
      popupOptions.offset = props.offset
    }

    const html = createPopupHTML(props.selectedFeature)

    popupInstance.value = new mapboxgl.Popup(popupOptions)
      .setLngLat([lng, lat])
      .setHTML(html)
      .addTo(mapInstance)

    // Attach immediately (not deferred to nextTick) so it's already active
    // before any zoom-to-extent animation for the newly selected feature
    // (e.g. MapControlsZoom's fitBounds) starts firing move/zoom events -
    // otherwise the popup would keep the clamping computed for its
    // pre-animation position and could drift out of bounds again.
    attachReclampListeners(popupInstance.value, mapInstance)

    // Listen for close event
    popupInstance.value.on('close', () => {
      emit('close')
      popupInstance.value = null
      detachReclampListeners()
    })

    // Reset scroll position to top and clamp position within the map
    // container once the popup has actually rendered (so its real size is
    // known).
    nextTick(() => {
      if (popupInstance.value) {
        const popupElement = popupInstance.value.getElement()
        if (popupElement) {
          const scrollContainer = popupElement.querySelector('.mapboxgl-popup-content')
          if (scrollContainer) {
            scrollContainer.scrollTop = 0
          }
        }
        clampPopupHeight(popupInstance.value, mapInstance, point)
        clampPopupToContainer(popupInstance.value, mapInstance)
      }
    })
  }

  // Watch for changes to selectedFeature or coordinates
  watch(
    () => [props.selectedFeature, props.coordinates],
    () => {
      if (props.selectedFeature && props.coordinates) {
        createPopup()
      } else {
        removePopup()
      }
    },
    { immediate: true, deep: true }
  )

  // Cleanup on unmount
  onBeforeUnmount(() => {
    removePopup()
  })
</script>

<style>
  .mapboxgl-popup-content {
    width: 100%;
    max-width: 420px;
    max-height: 400px;
    overflow-y: auto;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    padding: 0;
  }

  .popup-content {
    padding: 0;
  }

  .popup-title {
    font-size: 1.25rem;
    font-weight: 500;
    line-height: 2rem;
    padding: 16px 16px 0 16px;
    word-wrap: break-word;
  }

  .popup-body {
    padding: 16px;
  }

  .popup-body p {
    margin: 0 0 12px 0;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .popup-body p:last-child {
    margin-bottom: 0;
  }

  .description {
    margin-bottom: 12px;
  }

  .asset-link {
    margin-bottom: 12px;
  }

  .asset-link a {
    color: #1976d2;
    text-decoration: underline;
    word-break: break-all;
  }

  .view-details {
    margin-bottom: 12px;
  }

  .view-details a {
    color: #1976d2;
    text-decoration: underline;
    cursor: pointer;
  }

  .date {
    color: #666;
  }
</style>
