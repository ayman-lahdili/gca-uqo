import axios from 'axios';

// Retrieve the base URL from the environment variable
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

// Create an Axios instance
const apiClient = axios.create({
    baseURL: apiBaseUrl,
    headers: {
        'Content-Type': 'application/json'
        // Add any other default headers you need, like Authorization tokens if stored
    }
});

// Optional: Add interceptors for request or response handling (e.g., error handling, token injection)
// apiClient.interceptors.request.use(config => {
//   // Maybe add auth token here
//   return config;
// });

// apiClient.interceptors.response.use(response => {
//   return response;
// }, error => {
//   // Handle errors globally
//   console.error('API call error:', error);
//   return Promise.reject(error);
// });

export default apiClient;
