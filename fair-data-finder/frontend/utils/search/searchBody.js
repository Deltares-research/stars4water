import { buildFilter } from './filters.js'

export default function ({ collections, ...rest } = {}) {
  const body = {}
  const filter = buildFilter(rest)
  // Omit filter and filter-lang for an unfiltered search; sending an
  // always-true filter instead of no filter yields no results.
  if (filter) {
    body['filter-lang'] = 'cql2-json'
    body.filter = filter
  }
  if (Array.isArray(collections) && collections.length) {
    body.collections = collections.map(c => typeof c === 'string' ? c : c.id)
  }
  return body
}
