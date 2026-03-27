import service from './index'

export const listAlerts = (params = {}) =>
  service.get('/api/alerts', { params })

export const acknowledgeAlert = (eventId) =>
  service.post(`/api/alerts/${eventId}/acknowledge`)
