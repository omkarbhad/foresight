import service from './index'

export const generateDigest = (monitorId) =>
  service.post('/api/digests/generate', { monitor_id: monitorId })

export const listDigests = (monitorId, limit = 20) =>
  service.get(`/api/digests/${monitorId}`, { params: { limit } })
