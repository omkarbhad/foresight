import service from './index'

export const getTrends = (monitorId, days = 30) =>
  service.get(`/api/analysis/trends/${monitorId}`, { params: { days } })

export const getDashboard = (monitorId) =>
  service.get(`/api/analysis/dashboard/${monitorId}`)

export const compareCompetitors = (monitorIds, days = 30) =>
  service.get('/api/analysis/competitors', { params: { monitor_ids: monitorIds, days } })

export const submitWhatIf = (monitorId, scenario) =>
  service.post('/api/analysis/whatif', { monitor_id: monitorId, scenario })
