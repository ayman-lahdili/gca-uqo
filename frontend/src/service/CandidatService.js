import apiClient from '@/service/api'; // Adjust path if needed

export const CandidatService = {
    getData() {
        return [
            {
                id: 1,
                email: 'test1@uqo.ca',
                code_permanent: 'ABCD87300300',
                nom: 'Doe',
                prenom: 'Jacob',
                campus: 'GAT',
                cycle: 1,
                programme: 'Informatique',
                candidature: [
                    {
                        id: 1,
                        cours_id: 1,
                        note: 'A+',
                        has_exp: false,
                        sigle: 'INF3214',
                        titre: 'Génie logicielle'
                    }
                ]
            },
            {
                id: 2,
                email: 'test1@uqo.ca',
                code_permanent: 'ABCD87300400',
                nom: 'Doe',
                prenom: 'Frank',
                campus: 'GAT',
                cycle: 2,
                programme: 'Informatique',
                candidature: [
                    {
                        id: 1,
                        cours_id: 1,
                        note: 'A+',
                        has_exp: false,
                        sigle: 'INF3214',
                        titre: 'Génie logicielle'
                    }
                ]
            }
        ];
    },

    getCandidat() {
        return Promise.resolve(this.getData());
    },

    async getCandidatures(trimestre) {
        const response = await apiClient.get(`/v1/candidature`, { params: { trimestre } });
        return response.data;
    },

    async createCandidature(payload) {
        const response = await apiClient.post(`/v1/candidature`, payload);
        return response.data;
    },

    async updateCandidature(studentId, payload) {
        const response = await apiClient.put(`/v1/candidature/${studentId}`, payload);
        return response.data;
    },

    async deleteCandidature(studentId) {
        const response = await apiClient.delete(`/v1/candidature/${studentId}`);
        return response.data;
    }
};
