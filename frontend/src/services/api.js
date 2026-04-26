import axios from 'axios';

// If env exists → use it (dev)
// Else → use relative path (production via nginx)
const API_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 180000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const generateHealthcarePlan = async ({
  topic,
  location,
  locationMode = 'manual',
  latitude = null,
  longitude = null
}) => {
  try {
    const response = await apiClient.post('/generate-plan', {
      topic,
      location,
      location_mode: locationMode,
      latitude,
      longitude,
    });
    return response.data;
  } catch (error) {
    if (error.code === 'ECONNABORTED') {
      throw new Error('Request timed out while generating plan. Please retry in a moment.');
    }

    if (error.response) {
      throw new Error(
        error.response.data?.detail || 'Failed to generate healthcare plan'
      );
    } else if (error.request) {
      throw new Error('No response from server. Please ensure backend is running.');
    } else {
      throw new Error(error.message || 'An error occurred');
    }
  }
};

export default apiClient;