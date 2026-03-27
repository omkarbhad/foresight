import service from './index'

export const createSimulation = (scenarios, config = {}) =>
  service.post('/api/simulations', { scenarios, config })

export const getSimulation = (simulationId) =>
  service.get(`/api/simulations/${simulationId}`)

export const listSimulations = (limit = 10) => {
  const params = { limit }
  return service.get('/api/simulations', { params })
}

export const getTaskStatus = (taskId) =>
  service.get(`/api/tasks/${taskId}`)

export const cancelTask = (taskId) =>
  service.post(`/api/tasks/${taskId}/cancel`)
