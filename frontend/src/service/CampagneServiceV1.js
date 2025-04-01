export const CampagneService = {
    getCampagneData() {
        return [
            {
                id: 7,
                trimestre: 20251,
                status: 'INPROGRESS',
                salaire_1: 18.85,
                salaire_2: 24.49,
                salaire_3: 26.48,
                cout_total: 15000.0,
                nbr_candidature_cycle1: 30,
                nbr_candidature_cycle2: 10,
                nbr_candidature_cycle3: 3,
                nbr_assistant_cycle1: 12,
                nbr_assistant_cycle2: 5,
                nbr_assistant_cycle3: 2,
                nbr_cours: 20,
                nbr_td_total: 100,
                nbr_tp_total: 50
            },
            {
                id: 6,
                trimestre: 20243,
                status: 'COMPLETED',
                salaire_1: 18.85,
                salaire_2: 24.49,
                salaire_3: 26.48,
                cout_total: 15000.0,
                nbr_candidature_cycle1: 30,
                nbr_candidature_cycle2: 10,
                nbr_candidature_cycle3: 3,
                nbr_assistant_cycle1: 12,
                nbr_assistant_cycle2: 5,
                nbr_assistant_cycle3: 2,
                nbr_cours: 20,
                nbr_td_total: 100,
                nbr_tp_total: 50
            },
            {
                id: 5,
                trimestre: 20242,
                status: 'COMPLETED',
                salaire_1: 18.85,
                salaire_2: 24.49,
                salaire_3: 26.48,
                cout_total: 15000.0,
                nbr_candidature_cycle1: 30,
                nbr_candidature_cycle2: 10,
                nbr_candidature_cycle3: 3,
                nbr_assistant_cycle1: 12,
                nbr_assistant_cycle2: 5,
                nbr_assistant_cycle3: 2,
                nbr_cours: 20,
                nbr_td_total: 100,
                nbr_tp_total: 50
            },
            {
                id: 4,
                trimestre: 20241,
                status: 'COMPLETED',
                salaire_1: 18.85,
                salaire_2: 24.49,
                salaire_3: 26.48,
                cout_total: 15000.0,
                nbr_candidature_cycle1: 30,
                nbr_candidature_cycle2: 10,
                nbr_candidature_cycle3: 3,
                nbr_assistant_cycle1: 12,
                nbr_assistant_cycle2: 5,
                nbr_assistant_cycle3: 2,
                nbr_cours: 20,
                nbr_td_total: 100,
                nbr_tp_total: 50
            },
            {
                id: 3,
                trimestre: 20233,
                status: 'COMPLETED',
                salaire_1: 18.85,
                salaire_2: 24.49,
                salaire_3: 26.48,
                cout_total: 15000.0,
                nbr_candidature_cycle1: 30,
                nbr_candidature_cycle2: 10,
                nbr_candidature_cycle3: 3,
                nbr_assistant_cycle1: 12,
                nbr_assistant_cycle2: 5,
                nbr_assistant_cycle3: 2,
                nbr_cours: 20,
                nbr_td_total: 100,
                nbr_tp_total: 50
            },
            {
                id: 2,
                trimestre: 20232,
                status: 'COMPLETED',
                salaire_1: 18.85,
                salaire_2: 24.49,
                salaire_3: 26.48,
                cout_total: 15000.0,
                nbr_candidature_cycle1: 30,
                nbr_candidature_cycle2: 10,
                nbr_candidature_cycle3: 3,
                nbr_assistant_cycle1: 12,
                nbr_assistant_cycle2: 5,
                nbr_assistant_cycle3: 2,
                nbr_cours: 20,
                nbr_td_total: 100,
                nbr_tp_total: 50
            },
            {
                id: 1,
                trimestre: 20231,
                status: 'COMPLETED',
                salaire_1: 17.58,
                salaire_2: 23.1,
                salaire_3: 24.98,
                cout_total: 15000.0,
                nbr_candidature_cycle1: 30,
                nbr_candidature_cycle2: 10,
                nbr_candidature_cycle3: 3,
                nbr_assistant_cycle1: 12,
                nbr_assistant_cycle2: 5,
                nbr_assistant_cycle3: 2,
                nbr_cours: 20,
                nbr_td_total: 100,
                nbr_tp_total: 50
            }
        ];
    },

    getCampagneWithCoursesData() {
        return [
            {
                id: 7,
                trimestre: 20251,
                status: 'INPROGRESS',
                salaire: [18.85, 24.49, 26.48],
                lien: 'https://example.com/1231232',
                cout_total: 15000.0,
                nbr_candidature_cycle1: 30,
                nbr_candidature_cycle2: 10,
                nbr_candidature_cycle3: 3,
                nbr_assistant_cycle1: 12,
                nbr_assistant_cycle2: 5,
                nbr_assistant_cycle3: 2,
                nbr_cours: 20,
                nbr_td_total: 29,
                nbr_tp_total: 9,
                cours: [
                    {
                        id: 2,
                        campagne_id: 7,
                        sigle: 'CYB1063',
                        titre: 'Communication et leadership en cybersécurité',
                        status: 'NONCONFIRME',
                        candidature: [
                            {
                                id: 1,
                                code_permanent: 'ABCD87300300',
                                nom: 'Doe',
                                prenom: 'John',
                                campus: 'GAT',
                                cycle: 1
                            },
                            {
                                id: 2,
                                code_permanent: 'EFGH87300300',
                                nom: 'Smith',
                                prenom: 'Jane',
                                campus: 'GAT',
                                cycle: 1
                            },
                            {
                                id: 3,
                                code_permanent: 'IJKL87300300',
                                nom: 'Doe',
                                prenom: 'Jane',
                                campus: 'GAT',
                                cycle: 1
                            }
                        ],
                        seance: [
                            {
                                campus: 'Gatineau, St-Jérôme',
                                ressource: [
                                    {
                                        id: 1,
                                        email: 'abdel.hamou-lhadj@uqo.ca',
                                        nom: 'Hamou Lhadj',
                                        prenom: 'Abdel'
                                    }
                                ],
                                activite: [
                                    {
                                        id: 1,
                                        type: 'TP',
                                        mode: 'NPRES',
                                        jour: 'vendredi',
                                        hr_debut: 830,
                                        hr_fin: 1130,
                                        assistant: {
                                            id: 1,
                                            code_permanent: 'ABCD87300300',
                                            nom: 'Doe',
                                            prenom: 'John',
                                            campus: 'GAT',
                                            cycle: 1
                                        },
                                        nombre_seance: 0,
                                        changement: null
                                    },
                                    {
                                        id: 2,
                                        type: 'TD',
                                        mode: 'NPRES',
                                        jour: 'lundi',
                                        hr_debut: 830,
                                        hr_fin: 1130,
                                        assistant: null,
                                        nombre_seance: 0,
                                        changement: null
                                    }
                                ],
                                changement: null,
                                id: 1
                            },
                            {
                                campus: 'Gatineau, St-Jérôme',
                                ressource: [
                                    {
                                        id: 1,
                                        email: 'ayman.lahdili@uqo.ca',
                                        nom: 'Lahdili',
                                        prenom: 'Ayman'
                                    }
                                ],
                                activite: [
                                    {
                                        id: 1,
                                        type: 'TP',
                                        mode: 'NPRES',
                                        jour: 'vendredi',
                                        hr_debut: 830,
                                        hr_fin: 1130,
                                        assistant: {
                                            id: 1,
                                            code_permanent: 'ABCD87300300',
                                            nom: 'Doe',
                                            prenom: 'John',
                                            campus: 'GAT',
                                            cycle: 1
                                        },
                                        nombre_seance: 0,
                                        changement: {
                                            type: 'D',
                                            status: 'NC'
                                        }
                                    },
                                    {
                                        id: 2,
                                        type: 'TD',
                                        mode: 'NPRES',
                                        jour: 'lundi',
                                        hr_debut: 830,
                                        hr_fin: 1130,
                                        assistant: null,
                                        nombre_seance: 0,
                                        changement: {
                                            type: 'C',
                                            status: 'NC'
                                        }
                                    }
                                ],
                                changement: {
                                    type: 'D',
                                    status: 'NC'
                                },
                                id: 2
                            }
                        ]
                    },
                    {
                        id: 3,
                        campagne_id: 7,
                        sigle: 'INF1573',
                        titre: 'Programmation II',
                        status: 'CONFIRME',
                        candidature: [
                            {
                                id: 1,
                                code_permanent: 'ABCD87300300',
                                nom: 'Doe',
                                prenom: 'John',
                                campus: 'GAT',
                                cycle: 1
                            },
                            {
                                id: 2,
                                code_permanent: 'EFGH87300300',
                                nom: 'Smith',
                                prenom: 'Jane',
                                campus: 'GAT',
                                cycle: 1
                            },
                            {
                                id: 3,
                                code_permanent: 'IJKL87300300',
                                nom: 'Doe',
                                prenom: 'Jane',
                                campus: 'GAT',
                                cycle: 1
                            }
                        ],
                        seance: [
                            {
                                campus: 'Gatineau',
                                ressource: [
                                    {
                                        id: 2,
                                        email: 'ilham.benyahia@uqo.ca',
                                        nom: 'Benyahia',
                                        prenom: 'Ilham'
                                    }
                                ],
                                activite: [
                                    {
                                        id: 1,
                                        type: 'TD',
                                        mode: 'NPRES',
                                        jour: 'lundi',
                                        hr_debut: 1600,
                                        hr_fin: 1800,
                                        assistant: {},
                                        nombre_seance: 0,
                                        changement: null
                                    },
                                    {
                                        id: 2,
                                        type: 'TD',
                                        mode: 'NPRES',
                                        jour: 'vendredi',
                                        hr_debut: 900,
                                        hr_fin: 1100,
                                        assistant: {},
                                        nombre_seance: 0,
                                        changement: null
                                    }
                                ],
                                changement: {
                                    type: 'C',
                                    status: 'NC'
                                },
                                id: 1
                            },
                            {
                                campus: 'St-Jérôme',
                                ressource: [
                                    {
                                        id: 3,
                                        email: 'etienne.st-onge@uqo.ca',
                                        nom: 'St-Onge',
                                        prenom: 'Etienne'
                                    }
                                ],
                                activite: [
                                    {
                                        id: 1,
                                        type: 'TD',
                                        mode: 'NPRES',
                                        jour: 'lundi',
                                        hr_debut: 1600,
                                        hr_fin: 1800,
                                        assistant: {},
                                        nombre_seance: 0,
                                        changement: null
                                    },
                                    {
                                        id: 2,
                                        type: 'TD',
                                        mode: 'NPRES',
                                        jour: 'vendredi',
                                        hr_debut: 900,
                                        hr_fin: 1100,
                                        assistant: {},
                                        nombre_seance: 0,
                                        changement: null
                                    }
                                ],
                                changement: null,
                                id: 2
                            }
                        ]
                    }
                ]
            },
            {
                id: 6,
                trimestre: 20243,
                status: 'CONCLUDED',
                salaire: [18.85, 24.49, 26.48],
                cout_total: 16000.0,
                nbr_candidature_cycle1: 36,
                nbr_candidature_cycle2: 10,
                nbr_candidature_cycle3: 3,
                nbr_assistant_cycle1: 15,
                nbr_assistant_cycle2: 8,
                nbr_assistant_cycle3: 1,
                nbr_cours: 20,
                nbr_td_total: 30,
                nbr_tp_total: 10
            },
            {
                id: 5,
                trimestre: 20242,
                status: 'CONCLUDED',
                salaire: [18.85, 24.49, 26.48],
                cout_total: 13000.0,
                nbr_candidature_cycle1: 24,
                nbr_candidature_cycle2: 7,
                nbr_candidature_cycle3: 1,
                nbr_assistant_cycle1: 12,
                nbr_assistant_cycle2: 5,
                nbr_assistant_cycle3: 2,
                nbr_cours: 17,
                nbr_td_total: 25,
                nbr_tp_total: 7
            }
        ];
    },

    getCampagneWithCourses() {
        return Promise.resolve(this.getCampagneWithCoursesData());
    },

    getCampagnes() {
        return Promise.resolve(this.getCampagneData());
    },

    getCampagne(trimestre) {
        return Promise.resolve(this.getCampagneWithCoursesData()[0]);
    }
};
