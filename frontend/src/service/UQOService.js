import apiClient from '@/service/api'; // Adjust path if needed

export const UQOService = {
    async getCours() {
        const response = await apiClient.get(`/v1/uqo/cours?departement=DII`);
        return response.data;
    },

    async getProgramme(cycle) {
        const response = await apiClient.get(`/v1/uqo/programmes?departement=INFOR&cycle=${cycle}`);
        return response.data;
    }
};
