import apiClient from '@/service/api'; // Adjust path if needed

export const CampagneService = {
    async getCampagnes() {
        const response = await apiClient.get(`/v1/campagne`);
        return response.data;
    },

    async getCampagne(trimestre) {
        const response = await apiClient.get(`/v1/campagne/${trimestre}`);
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
    },

    async syncCampagne(trimestre) {
        const response = await apiClient.post(`/v1/campagne/${trimestre}/sync`);
        return response.data;
    },

    async approveSeanceChange(trimestre, sigle, groupe) {
        const response = await apiClient.patch(`/v1/campagne/${trimestre}/${sigle}/${groupe}/changes/approve`);
        return response.data;
    },

    async approveActiviteChange(trimestre, sigle, groupe, activite_id) {
        const response = await apiClient.patch(`/v1/campagne/${trimestre}/${sigle}/${groupe}/${activite_id}/changes/approve`);
        return response.data;
    },

    async updateSeance(trimestre, sigle, groupe, payload) {
        console.log('service', groupe);
        const response = await apiClient.put(`/v1/campagne/${trimestre}/${sigle}/${groupe}`, payload);
        return response.data;
    },

    async addCandidatureToCours(trimestre, sigle, payload) {
        const response = await apiClient.post(`/v1/cours/${trimestre}/${sigle}/candidature`, payload);
        return response.data;
    }
};
