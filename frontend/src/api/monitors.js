import service from './index'

export const listMonitors = (activeOnly = false) =>
  service.get('/api/monitors', { params: { active_only: activeOnly } })

export const getMonitor = (id) =>
  service.get(`/api/monitors/${id}`)

export const createMonitor = (data) =>
  service.post('/api/monitors', data)

export const updateMonitor = (id, data) =>
  service.put(`/api/monitors/${id}`, data)

export const deleteMonitor = (id) =>
  service.delete(`/api/monitors/${id}`)
