export const UQOService = {
    getMapCours(trimestre) {
        return {
            INF1163: {
                titre: 'Modélisation et conception orientée objet'
            },
            INF1563: {
                titre: 'Programmation I'
            },
            INF1573: {
                titre: 'Programmation II'
            },
            CYB1063: {
                titre: 'Communication et leadership en cybersécurité'
            }
        };
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
