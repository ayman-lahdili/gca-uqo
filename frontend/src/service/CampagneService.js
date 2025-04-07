import apiClient from '@/service/api'; // Adjust path if needed

export const CampagneService = {
    async getCampagnes() {
        const response = await apiClient.get(`/v1/campagne`);
        return response.data;
    },

    async getCampagne(trimestre) {
        const response = await apiClient.get(`/v1/campagne?trimestre=` + trimestre);
        return response.data;
    },

    async createCampagne(payload) {
        const response = await apiClient.post(`/v1/campagne`, payload);
        return response.data;
    },

    async updateCampagne(trimestre, payload) {
        const response = await apiClient.put(`/v1/campagne/${trimestre}`, payload);
        return response.data;
    },

    async getListTrimestre() {
        let listTrimestre = await this.getCampagnes();
        let res = listTrimestre.map((value) => value.trimestre);
        return res;
    }
};
