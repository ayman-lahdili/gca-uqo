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
    }
};
