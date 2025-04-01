export const CourseService = {
    getCoursesData() {
        return [
            {
                "sigle": "CYB1063",
                "titre": "Communication et leadership en cybersécurité",
                "nom": "hamou-lhadj",
                "prenom": "abdel",
                "enseignant": "abdel.hamou-lhadj@uqo.ca",
                "campus": ["Gatineau", "St-Jérôme"],
                "mode": "NPRES",
                "jour": "vendredi",
                "heure_debut": 1230,
                "heure_fin": 1530,
            },
            {
                "sigle": "CYB1093",
                "titre": "Gestion de projets et cybersécurité",
                "enseignant": "david.caissy@uqo.ca",
                "nom": "caissy",
                "prenom": "david",
                "campus": ["Gatineau"],
                "jour": "lundi",
                "mode": "PRES",
                "heure_debut": 1230,
                "heure_fin": 1530,
            },
            {
                "sigle": "CYB1093",
                "titre": "Gestion de projets et cybersécurité",
                "enseignant": "david.caissy@uqo.ca",
                "nom": "caissy",
                "prenom": "david",
                "campus": ["Gatineau"],
                "mode": "PRES",
                "jour": "vendredi",
                "heure_debut": 1230,
                "heure_fin": 1530,
            },
            {
                "sigle": "CYB1103",
                "titre": "Gouvernance en cybersécurité et gestion de risque",
                "enseignant": "dhaou.said@uqo.ca",
                "nom": "said",
                "prenom": "dhaou",
                "campus": ["Gatineau", "St-Jérôme"],
                "mode": "NPRES",
                "jour": "mercredi",
                "heure_debut": 1230,
                "heure_fin": 1530,
            }
        ]
    },

    getCourses(trimestre, departement) {
        return Promise.resolve(this.getCoursesData());
    },
};
