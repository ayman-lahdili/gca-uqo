import apiClient from '@/service/api'; // Adjust path if needed

export const UQOService = {
    async getCours() {
        const response = await apiClient.get(`/v1/uqo/cours?departement=DII`);
        return response.data;
    },

    getCoursDetails(sigle) {
        return { titre: 'Programmation Web' };
    },

    getProgramme(cycle) {
        return [
            {
                code: '7543',
                libelle: 'Baccalauréat en génie électrique',
                cycle: '1'
            },
            {
                code: '7833',
                libelle: 'Baccalauréat en informatique',
                cycle: '1'
            }
        ];
    }
};
