import service from './index'

export const listMentions = (monitorId, params = {}) =>
  service.get(`/api/mentions/${monitorId}`, { params })

export const getMention = (mentionId) =>
  service.get(`/api/mentions/detail/${mentionId}`)

export const getAmplifyQueue = (params = {}) =>
  service.get('/api/mentions/amplify', { params })
