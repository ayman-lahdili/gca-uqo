import apiClient from '@/service/api'; // Adjust path if needed

export const CandidatService = {
    async getCandidatures(trimestre) {
        const response = await apiClient.get(`/v1/${trimestre}/candidature`, { params: { trimestre } });
        return response.data;
    },

    async createCandidature(trimestre, studentData, resumeFile) {
        const formData = new FormData();

        // Add all student data fields to the form
        Object.keys(studentData).forEach((key) => {
            if (key !== 'courses') {
                // Handle courses separately
                formData.append(key, studentData[key]);
            }
        });

        // Convert courses array to JSON string and add to form
        if (studentData.courses) {
            formData.append('courses_json', JSON.stringify(studentData.courses));
        } else {
            formData.append('courses_json', '[]');
        }

        // Add the resume file
        if (resumeFile !== undefined) {
            formData.append('resume', resumeFile);
        }

        const response = await apiClient.post(`/v1/${trimestre}/candidature`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return response.data;
    },

    async updateCandidature(trimestre, studentId, studentData, resumeFile = null) {
        // Create a FormData object for the update
        const formData = new FormData();

        // Add all student data fields to the form
        Object.keys(studentData).forEach((key) => {
            if (key !== 'courses') {
                // Handle courses separately
                formData.append(key, studentData[key]);
            }
        });

        // Convert courses array to JSON string and add to form
        if (studentData.courses) {
            formData.append('courses_json', JSON.stringify(studentData.courses));
        } else {
            formData.append('courses_json', '[]');
        }

        // Add the resume file if provided
        console.log('resumeFile', resumeFile);
        if (resumeFile !== undefined && resumeFile !== null) {
            formData.append('resume', resumeFile);
        }

        const response = await apiClient.put(`/v1/${trimestre}/candidature/${studentId}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        return response.data;
    },

    async deleteCandidature(studentId, trimestre) {
        const response = await apiClient.delete(`/v1/${trimestre}/candidature/${studentId}`);
        return response.data;
    },

    async downloadResume(studentId, trimestre) {
        const response = await apiClient
            .get(`/v1/${trimestre}/candidature/${studentId}/resume`, {
                responseType: 'blob' // Important for file downloads
            })
            .catch((error) => {
                return null;
            });

        return response === null ? response : response.data;
    }
};
