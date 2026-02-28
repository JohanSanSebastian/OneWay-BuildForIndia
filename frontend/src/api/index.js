import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Auth API
export const authApi = {
  register: (data) =>
    api.post('/auth/register', data),
  login: (identifier, identifierType) =>
    api.post('/auth/login', { identifier, identifierType }),
}

// Utilities API
export const utilitiesApi = {
  getServices: () => api.get('/utilities/services'),
  fetchBill: (serviceType, consumerId, numberPlate = null) => {
    const body = { service_type: serviceType, consumer_id: consumerId }
    if (numberPlate) body.number_plate = numberPlate
    return api.post('/utilities/fetch-bill', body)
  },
  getHistory: (serviceType, consumerId) =>
    api.get(`/utilities/history/${serviceType}/${consumerId}`),
  getProfileSummary: (profileId) =>
    api.get(`/utilities/summary/${profileId}`),
  getChartData: (accounts, billData) =>
    api.post('/utilities/chart-data', { accounts, bill_data: billData }),
}

// Profiles API
export const profilesApi = {
  getAll: () => api.get('/profiles/'),
  create: (profile) => api.post('/profiles/', profile),
  get: (profileId) => api.get(`/profiles/${profileId}`),
  delete: (profileId) => api.delete(`/profiles/${profileId}`),
  addAccount: (profileId, account) =>
    api.post(`/profiles/${profileId}/accounts`, account),
  getAccounts: (profileId) =>
    api.get(`/profiles/${profileId}/accounts`),
  removeAccount: (profileId, accountId) =>
    api.delete(`/profiles/${profileId}/accounts/${accountId}`),
}

// Payments API
export const paymentsApi = {
  initiate: (accountId, serviceType, consumerId) =>
    api.post('/payments/initiate', {
      account_id: accountId,
      service_type: serviceType,
      consumer_id: consumerId
    }),
  checkStatus: (sessionId) =>
    api.get(`/payments/status/${sessionId}`),
  confirm: (sessionId) =>
    api.post(`/payments/confirm/${sessionId}`),
}

// Sentinel API (Motor Violation Assistant)
export const sentinelApi = {
  // Violation Reporting
  analyzeViolation: (imageBase64, deviceLatitude = null, deviceLongitude = null) =>
    api.post('/sentinel/analyze', { 
      image_base64: imageBase64,
      device_latitude: deviceLatitude,
      device_longitude: deviceLongitude
    }),
  getReports: () =>
    api.get('/sentinel/reports'),
  updateReportStatus: (reportId, status) =>
    api.patch(`/sentinel/reports/${reportId}/status`, { status }),
  sendToMVD: (reportId) =>
    api.post(`/sentinel/reports/${reportId}/send-mvd`),
  
  // Parking Assistant
  parkingAssist: (plateNumber) =>
    api.post('/sentinel/parking-assist', { plate_number: plateNumber }),
  
  // Vehicle Registry
  getRegistry: () =>
    api.get('/sentinel/registry'),
  addToRegistry: (plateNumber, ownerName, ownerPhone) =>
    api.post('/sentinel/registry', { 
      plate_number: plateNumber, 
      owner_name: ownerName, 
      owner_phone: ownerPhone 
    }),
  lookupPlate: (plateNumber) =>
    api.get(`/sentinel/registry/${plateNumber}`),
  deleteFromRegistry: (entryId) =>
    api.delete(`/sentinel/registry/${entryId}`),
}

// Disaster & Infrastructure Sentinel API
export const disasterApi = {
  // Incident Reporting
  analyzeIncident: (imageBase64, deviceLatitude = null, deviceLongitude = null, userDescription = null) =>
    api.post('/disaster/analyze', {
      image_base64: imageBase64,
      device_latitude: deviceLatitude,
      device_longitude: deviceLongitude,
      user_description: userDescription
    }),
  
  getIncidents: (activeOnly = false) =>
    api.get(`/disaster/incidents?active_only=${activeOnly}`),
  
  getIncident: (incidentId) =>
    api.get(`/disaster/incidents/${incidentId}`),
  
  updateIncidentStatus: (incidentId, status, authoritiesNotified = []) =>
    api.patch(`/disaster/incidents/${incidentId}/status`, { 
      status, 
      authorities_notified: authoritiesNotified 
    }),
  
  notifyAuthorities: (incidentId) =>
    api.post(`/disaster/incidents/${incidentId}/notify`),
  
  // Map & Statistics
  getMapData: () =>
    api.get('/disaster/map-data'),
  
  getStats: () =>
    api.get('/disaster/stats'),
  
  getDistrictIncidents: (district) =>
    api.get(`/disaster/districts/${district}/incidents`),
  
  // Authority Directory
  getAllAuthorities: () =>
    api.get('/disaster/authorities'),
  
  searchAuthorities: (query) =>
    api.get(`/disaster/authorities/search?q=${encodeURIComponent(query)}`),
  
  getAuthoritiesForIncident: (incidentId) =>
    api.get(`/disaster/authorities/for-incident/${incidentId}`),
  
  // Call Script
  getCallScript: (incidentId) =>
    api.get(`/disaster/incidents/${incidentId}/call-script`),
}

export default api
