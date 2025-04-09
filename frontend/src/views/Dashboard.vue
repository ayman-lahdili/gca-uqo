<script>
import { sharedSelectState } from '@/layout/composables/sharedSelectedState';
import { CampagneService } from '@/service/CampagneService';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';

const codePermanentRegex = /^[A-Z]{4}\d{8}$/;

export default {
    data() {
        return {
            toast: useToast(),
            sharedState: sharedSelectState,

            dt: null,
            campagne: {},
            seance: {},
            expandedRowGroups: null,
            expandedRows: {},
            selectedSeance: {},
            selectedActivite: null,
            value: '',

            // Loading
            seanceTableLoading: false,
            confirmChangeLoading: false,
            activiteTableLoading: false,

            // Seance
            seanceDialog: false,
            optionCandidates: [],
            confirmCancelDialog: false,
            changeDialog: false,
            seanceChanged: false,

            // Candidat
            candidatDialog: false,
            candidat: {
                prenom: '',
                nom: '',
                code_permanent: '',
                cycle: 1
            },
            candidatFormState: {
                code_permanent: false,
                email: false,
                nom: false,
                prenom: false,
                campus: false,
                cycle: false,
                programme: false,
                candidature: false
            },

            // Campagne Datatable
            filters: {
                global: { value: null, matchMode: FilterMatchMode.CONTAINS },
                sigle: { value: null, matchMode: FilterMatchMode.CONTAINS },
                titre: { value: null, matchMode: FilterMatchMode.CONTAINS },
                status: { value: null, matchMode: FilterMatchMode.STARTS_WITH }
            },

            contrat: 0,

            // Contrat
            totalSeance: 0,

            // Changes
            change: null,
            confirmChangeDialog: false,
            sigle: null,
            seance_id: null,

            // Distribution
            distribution: [],
            totalActivities: 0,
            totalCost: 0,
            totalCandidatures: 0,
            uniqueCandidates: 0
        };
    },
    mounted() {
        this.fetchCampagneDetails();
    },
    computed: {
        selectedTrimestre() {
            return this.sharedState.selectedValue;
        }
    },
    watch: {
        selectedTrimestre(newValue, oldValue) {
            console.log(`Candidatures component detected trimestre change: ${newValue}`);
            if (newValue !== oldValue) {
                this.fetchCampagneDetails();
            }
        }
    },
    methods: {
        async fetchCampagneDetails() {
            await CampagneService.getCampagne(this.selectedTrimestre).then((data) => {
                this.campagne = data;
                console.log(this.campagne);

                this.distribution = this.calculateDistribution();
                this.totalActivities = this.calculateTotalActivities();
                this.totalCost = this.calculateTotalCost();
                this.analyzeCandidatures();
            });
        },
        openEditSeance(cours, seance) {
            this.selectedCours = cours;
            this.selectedSeance = { ...seance };

            this.selectedSeance.activite = this.selectedSeance.activite.map((act) => {
                return {
                    ...act,
                    responsable_ids: act.responsable.map((value) => value.id_etudiant)
                };
            });

            this.optionCandidates = this.selectedCours.candidature.map((candidature) => {
                return {
                    id: candidature.etudiant.id,
                    label: candidature.etudiant.nom + ', ' + candidature.etudiant.prenom + ' (' + candidature.etudiant.code_permanent + ')'
                };
            });

            this.seanceChanged = false;
            this.seanceDialog = true;
        },
        openConfirmChange(seance, sigle) {
            this.sigle = sigle;
            this.selectedSeance = seance;
            this.confirmChangeDialog = true;
        },
        async confirmChange(seance) {
            this.confirmChangeLoading = true;

            await CampagneService.approveSeanceChange(this.selectedTrimestre, this.sigle, this.selectedSeance.groupe);

            this.confirmChangeLoading = false;
            this.fetchCampagneDetails();
            this.confirmChangeDialog = false;
        },
        analyzeCandidatures() {
            let totalCandidatures = 0;
            let campagneData = this.campagne;
            const uniqueCandidateIds = new Set(); // Using a Set to automatically handle uniqueness

            // Validate the basic structure needed
            if (!campagneData || !Array.isArray(campagneData.cours)) {
                console.error('Invalid or missing campagne data/cours array.');
                return { totalCandidatures: 0, uniqueCandidates: 0 };
            }

            // Iterate through each course in the campagne
            campagneData.cours.forEach((course) => {
                // Check if the course has a candidature array
                if (Array.isArray(course.candidature)) {
                    // Iterate through each candidature object within the course
                    course.candidature.forEach((candidature) => {
                        // Increment total count for every candidature found
                        totalCandidatures++;

                        // Add the student's ID to the Set.
                        // If the ID is already present, the Set ignores it.
                        // Check if id_etudiant exists and is valid
                        if (candidature && candidature.hasOwnProperty('id_etudiant')) {
                            uniqueCandidateIds.add(candidature.id_etudiant);
                        } else {
                            console.warn("Found a candidature entry without a valid 'id_etudiant':", candidature);
                        }
                    });
                }
            });

            this.totalCandidatures = totalCandidatures;
            this.uniqueCandidates = uniqueCandidateIds.size;
            // Return the results
            return {
                totalCandidatures: totalCandidatures,
                uniqueCandidates: uniqueCandidateIds.size // .size gives the count of unique elements in the Set
            };
        },
        openCandidateDialog() {
            this.candidatDialog = true;
        },
        async saveCandidat() {
            let isValid = true;

            if (this.candidat.nom === '') {
                this.candidatFormState.nom = true;
                isValid = false;
            }

            if (this.candidat.prenom === '') {
                this.candidatFormState.prenom = true;
                isValid = false;
            }

            if (!codePermanentRegex.test(this.candidat.code_permanent)) {
                this.candidatFormState.code_permanent = true;
                isValid = false;
            }

            if (!isValid) {
                this.toast.add({ severity: 'error', summary: 'Erreur de validation', detail: 'Certain champs son invalide.', life: 3000 });
                return;
            }

            try {
                let response = await CampagneService.addCandidatureToCours(this.selectedTrimestre, this.selectedCours.sigle, this.candidat);

                this.selectedCours = response;

                this.optionCandidates = this.selectedCours.candidature.map((candidature) => {
                    return {
                        id: candidature.etudiant.id,
                        label: candidature.etudiant.nom + ', ' + candidature.etudiant.prenom + ' (' + candidature.etudiant.code_permanent + ')'
                    };
                });

                this.candidatDialog = false;
            } catch (error) {
                console.log(error);
                this.toast.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: error?.response?.data?.detail || 'Une erreur est survenue.',
                    life: 3000
                });
            }
        },
        confirmSaveSeance() {
            this.changeDialog = true;
        },
        async saveSeance() {
            this.activiteTableLoading = true;

            let payload = {
                activite: this.selectedSeance.activite.map((act) => {
                    return {
                        id: act.id,
                        candidature: act.responsable_ids == null ? [] : act.responsable_ids,
                        nombre_seance: act.nombre_seance
                    };
                })
            };

            let response = await CampagneService.updateSeance(this.selectedTrimestre, this.selectedCours.sigle, this.selectedSeance.groupe, payload);

            this.selectedSeance.activite = response.activite.map((act) => {
                return {
                    ...act,
                    responsable_ids: act.responsable.map((value) => value.id_etudiant)
                };
            });

            this.fetchCampagneDetails();
            this.changeDialog = false;
            this.activiteTableLoading = false;
            this.toast.add({ severity: 'success', summary: 'Seance sauvegardée', detail: 'Vos changement ont été sauvegardés.', life: 3000 });
            this.distribution = this.calculateDistribution(); // Update distribution
            this.totalActivities = this.calculateTotalActivities(); // Update total activities
            this.totalCost = this.calculateTotalCost(); // Update total cost
            this.analyzeCandidatures();
        },
        confirmCancelSeance() {
            if (this.seanceChanged) {
                this.confirmCancelDialog = true;
            } else {
                this.seanceDialog = false;
            }
        },
        cancelSeance() {
            this.confirmCancelDialog = false;
            this.seanceDialog = false;
            this.toast.add({ severity: 'info', summary: 'Seance Cancelled', detail: 'All changes have been discarded.', life: 3000 });
        },
        async downloadCVs() {},
        async syncSchedules() {
            this.seanceTableLoading = true;
            await CampagneService.syncCampagne(this.selectedTrimestre).then((campagne) => (this.campagne = campagne));
            // Add your synchronization logic here
            this.toast.add({ severity: 'info', summary: 'Synchronization', detail: 'Les horaires de cours ont été synchronisés.', life: 3000 });
            this.seanceTableLoading = false;
        },
        formatCurrency(value) {
            return value.toLocaleString('en-CA', { style: 'currency', currency: 'CAD' });
        },
        calculateTotalSeance() {
            // Calculate total contrat
            this.totalSeance = this.selectedSeance.activite.reduce((acc, activite) => {
                if (activite.assistant?.cycle !== undefined) {
                    return acc + activite.nombre_seance * this.campagne.salaire[activite.assistant.cycle - 1] * (activite.type === 'TD' ? 2 + 1 : 3 + 2);
                }
                return acc;
            }, 0);
        },
        calculateCourseContract(course) {
            return course.seance.reduce((acc, seance) => {
                return acc + this.calculateSeanceContract(seance);
            }, 0);
        },
        calculateSeanceContract(seance) {
            let etudiant_contracts = {};

            seance.activite.forEach((act) => {
                act.responsable.forEach((resp) => {
                    if (etudiant_contracts?.[resp.id_etudiant]?.['total'] === undefined) {
                        etudiant_contracts[resp.id_etudiant] = { total: 0, nbr_cr_par_smn: 0 };
                    }
                    let hrs_prepa;
                    let hrs_trava;
                    etudiant_contracts[resp.id_etudiant]['nbr_cr_par_smn'] += 1;
                    if (etudiant_contracts[resp.id_etudiant]['nbr_cr_par_smn'] === 1) {
                        hrs_prepa = act.type === 'Travaux dirigés' ? 1 : 2;
                        etudiant_contracts[resp.id_etudiant]['total'] += act.nombre_seance * hrs_prepa * this.campagne.config.echelle_salariale[resp.etudiant.cycle - 1];
                    }
                    hrs_trava = act.type === 'Travaux dirigés' ? 2 : 3;

                    etudiant_contracts[resp.id_etudiant]['total'] += act.nombre_seance * hrs_trava * this.campagne.config.echelle_salariale[resp.etudiant.cycle - 1];
                });
            });

            console.log(etudiant_contracts);

            let tot = Object.values(etudiant_contracts).reduce((acc, obj) => acc + obj.total, 0);
            this.totalSeance = tot;

            console.log('etudiant_nombre_seance_par_semaine', etudiant_contracts);

            return tot;
        },
        countTDActivities(seance) {
            return seance.activite.filter((activite) => activite.type === 'Travaux dirigés').length;
        },
        countTPActivities(seance) {
            return seance.activite.filter((activite) => activite.type === 'Travaux pratiques').length;
        },
        openConfirmChangeActivity(activity) {
            this.selectedActivite = activity;
            this.confirmChangeDialog = true;
        },
        async confirmChangeActivity(activity) {
            this.confirmChangeLoading = true;

            let response = await CampagneService.approveActiviteChange(this.selectedTrimestre, this.selectedSeance.sigle, this.selectedSeance.groupe, activity.id);

            this.confirmChangeLoading = false;
            this.selectedSeance = response;
            this.selectedSeance.activite = response.activite.map((act) => {
                return {
                    ...act,
                    responsable_ids: act.responsable.map((value) => value.id_etudiant)
                };
            });
            this.fetchCampagneDetails();
            this.confirmChangeDialog = false;

            this.confirmChangeDialog = false;
            this.distribution = this.calculateDistribution(); // Update distribution
            this.totalActivities = this.calculateTotalActivities(); // Update total activities
            this.totalCost = this.calculateTotalCost(); // Update total cost
            this.analyzeCandidatures();
        },
        expandAll() {
            this.expandedRows = this.campagne.cours.reduce((acc, course) => (acc[course.sigle] = true) && acc, {});
        },
        collapseAll() {
            this.expandedRows = null;
        },
        calculateDistribution() {
            const distribution = [
                { label: 'Cycle 1', color: '#34d399', value: 0 },
                { label: 'Cycle 2', color: '#fbbf24', value: 0 },
                { label: 'Cycle 3', color: '#60a5fa', value: 0 }
            ];

            let totalActivities = 0;

            console.log(this.campagne);

            this.campagne.cours.forEach((course) => {
                course.seance.forEach((seance) => {
                    seance.activite.forEach((activite) => {
                        if (activite.type === 'Travaux dirigés' || activite.type === 'Travaux pratiques') {
                            totalActivities += 1;
                            // console.log('totalActivities', totalActivities);
                            activite.responsable.forEach((resp) => {
                                distribution[resp.etudiant.cycle - 1].value += 1;
                            });
                        }
                    });
                });
            });

            console.log(distribution);

            if (totalActivities !== 0) {
                distribution.forEach((item) => {
                    item.value = (item.value / totalActivities) * 100;
                });
            }

            return distribution;
        },
        calculateTotalActivities() {
            let totalActivities = 0;

            this.campagne.cours.forEach((course) => {
                course.seance.forEach((seance) => {
                    seance.activite.forEach((activite) => {
                        if (activite.type === 'Travaux dirigés' || activite.type === 'Travaux pratiques') {
                            totalActivities += 1;
                        }
                    });
                });
            });

            return totalActivities;
        },
        calculateTotalCost() {
            return this.campagne.cours.reduce((acc, course) => {
                return acc + this.calculateCourseContract(course);
            }, 0);
        },
        getCampusName(code) {
            switch (code) {
                case 'gatineau':
                    return 'Gatineau';
                case 'st-jerome':
                    return 'Saint-Jérôme';
                case 'non-specifie':
                    return 'Gatineau';
                default:
                    break;
            }
        },
        getCoursStatus(code) {
            switch (code) {
                case 'confirmee':
                    return 'Confirmé';
                case 'non_confirmee':
                    return 'Non-disponible';
                default:
                    break;
            }
        },
        hasAddedOrRemovedChange(dataObject) {
            if (!dataObject || !Array.isArray(dataObject.seance)) {
                return false; // No seance array to check
            }

            for (const seanceItem of dataObject.seance) {
                return this.hasSeanceAddedOrRemovedChange(seanceItem);
            }

            return false;
        },
        hasSeanceAddedOrRemovedChange(seanceItem) {
            const seanceChangeType = seanceItem?.change?.change_type;
            if (seanceChangeType === 'added' || seanceChangeType === 'removed') {
                return true; // Found the change in the seance item itself
            }

            if (Array.isArray(seanceItem?.activite)) {
                for (const activiteItem of seanceItem.activite) {
                    const activiteChangeType = activiteItem?.change?.change_type;
                    if (activiteChangeType === 'added' || activiteChangeType === 'removed') {
                        return true; // Found the change in an activite item
                    }
                }
            }
            return false;
        },
        formatTrimestre(value) {
            value = value + '';
            let season = value.charAt(4);
            let year = value.substring(0, 4);

            switch (season) {
                case '1':
                    return 'Hiver ' + year;
                case '2':
                    return 'Été ' + year;
                case '3':
                    return 'Automne ' + year;
                default:
                    break;
            }
        },
        formatHeure(heureInt) {
            // Basic validation for time range
            if (typeof heureInt !== 'number' || heureInt < 0 || heureInt > 2359) {
                console.warn('Heure invalide fournie:', heureInt);
                return ''; // Indicate invalid time
            }

            // Extract hours and minutes
            const heures = Math.floor(heureInt / 100);
            const minutes = heureInt % 100;

            // Ensure minutes are valid (0-59) - useful if input might be slightly off like 1680
            if (minutes > 59) {
                console.warn("Minutes invalides dans l'heure fournie:", heureInt);
                return '';
            }

            // Pad with leading zeros using padStart
            const heuresStr = String(heures).padStart(2, '0');
            const minutesStr = String(minutes).padStart(2, '0');

            // Use 'h' as the separator (common in French 24h format)
            return `${heuresStr}h${minutesStr}`;
        },
        formatJour(jour_num) {
            return ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][jour_num - 1];
        }
    }
};
</script>

<template>
    <div class="relative overflow-hidden w-full min-h-screen">
        <!-- Pages Wrapper -->
        <div class="flex w-[200%] transition-transform duration-500" :class="{ '-translate-x-1/2': seanceDialog }">
            <!-- First Page -->
            <div class="w-1/2 flex-shrink-0 p-4">
                <div :style="seanceDialog ? { display: 'none' } : {}">
                    <div class="mb-3">
                        <Fieldset class="card" legend="Statistiques" :toggleable="true" :collapsed="false">
                            <div class="flex justify-between items-center">
                                <div class="flex items-center">
                                    <h1>{{ uniqueCandidates }}</h1>
                                    <span class="ml-1 mb-0 text-sm text-muted-color font-semibold">candidats</span>
                                </div>
                                <div class="flex items-center">
                                    <h1>{{ formatCurrency(totalCost) }}</h1>
                                    <span class="ml-4 mb-0 text-sm text-muted-color font-semibold">{{ formatTrimestre(selectedTrimestre) }}</span>
                                </div>
                            </div>
                            <MeterGroup :value="distribution">
                                <template #start="{ totalPercent }">
                                    <div class="flex justify-between mt-4 mb-2 relative">
                                        <span></span>
                                        <span :style="{ width: totalPercent + '%' }" class="absolute text-right">{{ totalPercent }}%</span>
                                        <span class="font-medium">{{ totalActivities }} séances de TD et TP</span>
                                    </div>
                                </template>
                            </MeterGroup>
                        </Fieldset>
                    </div>
                    <div class="card">
                        <DataTable
                            ref="dt"
                            :value="campagne.cours"
                            v-model:expandedRows="expandedRows"
                            dataKey="sigle"
                            removableSort
                            :loading="seanceTableLoading"
                            :filters="filters"
                            :globalFilterFields="['sigle', 'titre', 'status']"
                            :rowClass="
                                (rowData) => ({
                                    'no-expander': rowData.status === 'non_confirmee'
                                })
                            "
                        >
                            <template #header>
                                <div class="flex flex-wrap gap-2 items-center justify-between">
                                    <h4 class="m-0">Tableau de bord</h4>
                                    <IconField>
                                        <InputIcon>
                                            <i class="pi pi-search" />
                                        </InputIcon>
                                        <InputText v-model="filters['global'].value" placeholder="Recherche..." />
                                    </IconField>
                                    <div>
                                        <Button label="Synchroniser les horaires" icon="pi pi-sparkles" class="p-button-primary mr-2" @click="syncSchedules" />
                                        <Button icon="pi pi-refresh" class="mt-2" outlined @click="fetchCampagneDetails" />
                                    </div>
                                </div>
                                <div class="flex flex-wrap justify-start gap-2">
                                    <Button text icon="pi pi-plus" label="Agrandir tous" @click="expandAll" />
                                    <Button text icon="pi pi-minus" label="Tous réduire" @click="collapseAll" />
                                </div>
                            </template>
                            <Column expander />
                            <Column field="sigle" header="Sigle" class="font-semibold"></Column>
                            <Column field="titre" header="Titre" class="font-semibold"> </Column>
                            <Column field="status" header="Status" class="font-semibold">
                                <template #body="slotProps">
                                    {{ getCoursStatus(slotProps.data.status) }}
                                </template>
                            </Column>
                            <Column field="contrat" header="Contrat" class="font-semibold" sortable>
                                <template #body="slotProps">
                                    {{ formatCurrency(calculateCourseContract(slotProps.data)) }}
                                </template>
                            </Column>
                            <template #expansion="tableCampagne">
                                <div v-if="tableCampagne.data.status !== 'non_confirmee'" class="p-2">
                                    <DataTable
                                        :value="tableCampagne.data.seance"
                                        size="small"
                                        :rowClass="
                                            (rowData) => ({
                                                'danger-row': rowData.change !== null && rowData.change.change_type === 'removed',
                                                'success-row': rowData.change !== null && rowData.change.change_type === 'added',
                                                'change-row': rowData.change !== null && rowData.change.change_type !== 'added' && rowData.change.change_type !== 'removed' && hasSeanceAddedOrRemovedChange(rowData)
                                            })
                                        "
                                    >
                                        <Column :exportable="false" style="min-width: 4rem">
                                            <template #body="slotProps">
                                                <Button
                                                    v-if="slotProps.data.change !== null && slotProps.data.change.change_type === 'removed'"
                                                    icon="pi pi-exclamation-triangle"
                                                    severity="danger"
                                                    outlined
                                                    @click="openConfirmChange(slotProps.data, tableCampagne.data.sigle)"
                                                />
                                                <Button
                                                    v-if="slotProps.data.change !== null && slotProps.data.change.change_type === 'added'"
                                                    icon="pi pi-plus-circle"
                                                    severity="success"
                                                    @click="openConfirmChange(slotProps.data, tableCampagne.data.sigle)"
                                                />
                                            </template>
                                        </Column>
                                        <Column field="campus" header="Campus">
                                            <template #body="slotProps">
                                                <span class="mr-2">
                                                    {{ slotProps.data.campus.map((campus) => getCampusName(campus)).join(', ') }}
                                                </span>
                                            </template>
                                        </Column>
                                        <Column field="groupe" header="Gr"></Column>
                                        <Column field="ressource" header="Ressource d'enseignement">
                                            <template #body="slotProps">
                                                {{ slotProps.data.ressource[0].nom + ', ' + slotProps.data.ressource[0].prenom }}
                                            </template>
                                        </Column>
                                        <Column field="td_activities" header="Nombre de TD">
                                            <template #body="slotProps">
                                                {{ countTDActivities(slotProps.data) }}
                                            </template>
                                        </Column>
                                        <Column field="tp_activities" header="Nombre de TP">
                                            <template #body="slotProps">
                                                {{ countTPActivities(slotProps.data) }}
                                            </template>
                                        </Column>
                                        <Column field="contrat" header="Contrat">
                                            <template #body="slotProps">
                                                {{ formatCurrency(calculateSeanceContract(slotProps.data)) }}
                                            </template>
                                        </Column>
                                        <Column :exportable="false" style="min-width: 7rem">
                                            <template #body="slotProps">
                                                <template v-if="slotProps.data.change !== null && slotProps.data.change.change_type === 'unchanged'">
                                                    <Button icon="pi pi-pencil" :severity="hasSeanceAddedOrRemovedChange(slotProps.data) ? 'warn' : 'primary'" outlined rounded @click="openEditSeance(tableCampagne.data, slotProps.data)" />
                                                    <Button icon="pi pi-download" rounded outlined severity="secondary" class="ml-2" @click="downloadCVs" />
                                                </template>
                                            </template>
                                        </Column>
                                    </DataTable>
                                </div>
                            </template>
                        </DataTable>
                    </div>
                    <Dialog v-model:visible="confirmChangeDialog" :style="{ width: '450px' }" header="Confirmation" :modal="true">
                        <div class="flex items-center gap-4">
                            <i class="pi pi-exclamation-triangle !text-3xl" />
                            <span v-if="selectedActivite">
                                <span v-if="selectedActivite.change?.change_type === 'added'">Cette activité a été ajoutée dans l'horaire de l'UQO. Êtes-vous sûr de vouloir confirmer l'ajout de cette activité ?</span>
                                <span v-else-if="selectedActivite.change?.change_type === 'removed'">Cette activité a été retirée de l'horaire de l'UQO. Êtes-vous sûr de vouloir confirmer la suppréssion de cette activité ?</span>
                            </span>
                            <span v-else-if="selectedSeance">
                                <span v-if="selectedSeance.change?.change_type === 'added'">Cette séance a été ajoutée dans l'horaire de l'UQO. Êtes-vous sûr de vouloir confirmer l'ajout de cette séance ?</span>
                                <span v-else-if="selectedSeance.change?.change_type === 'removed'"
                                    >Cette séance a été retirée de l'horaire de l'UQO. Êtes-vous sûr de vouloir confirmer la suppréssion de cette séance ? Tous les informations sur les assignations des assistants seront supprimée.</span
                                >
                            </span>
                        </div>
                        <template #footer>
                            <Button v-if="selectedSeance.change?.change_type !== 'added'" label="Non, je veux m'assurer de ne pas perdre d'information" icon="pi pi-times" text @click="confirmChangeDialog = false" />
                            <Button label="Oui, confirmer" icon="pi pi-check" @click="selectedActivite ? confirmChangeActivity(selectedActivite) : confirmChange(selectedSeance)" :loading="confirmChangeLoading" />
                        </template>
                    </Dialog>
                </div>
            </div>
            <div class="w-1/2 flex-shrink-0">
                <div class="card mt-2" :style="!seanceDialog ? { display: 'none' } : {}">
                    <div class="flex justify-between px-2">
                        <h3>{{ selectedCours?.sigle + ' - ' + selectedSeance?.groupe + ' - ' + (selectedSeance?.campus === undefined ? '' : selectedSeance?.campus.map((campus) => getCampusName(campus)).join(', ')) }}</h3>
                        <Button icon="pi pi-times" variant="text" rounded severity="secondary" class="mb-4 mx-4" @click="confirmCancelSeance" />
                    </div>

                    <DataTable
                        :value="selectedSeance.activite"
                        :rowClass="
                            (rowData) => ({
                                'danger-row': rowData.change !== null && rowData.change.change_type === 'removed',
                                'success-row': rowData.change !== null && rowData.change.change_type === 'added'
                            })
                        "
                        :loading="activiteTableLoading"
                    >
                        <Column :exportable="false">
                            <template #body="tableActivite">
                                <Button v-if="tableActivite.data.change !== null && tableActivite.data.change.change_type === 'removed'" icon="pi pi-exclamation-triangle" severity="danger" @click="openConfirmChangeActivity(tableActivite.data)" />
                                <Button v-if="tableActivite.data.change !== null && tableActivite.data.change.change_type === 'added'" icon="pi pi-plus-circle" severity="success" @click="openConfirmChangeActivity(tableActivite.data)" />
                            </template>
                        </Column>
                        <Column field="type" header="Type">
                            <template #body="slotProps">
                                {{ slotProps.data.type }}
                            </template>
                        </Column>
                        <Column field="jour" header="Jour">
                            <template #body="slotProps">
                                {{ formatJour(slotProps.data.jour) }}
                            </template>
                        </Column>
                        <Column field="heur" header="Heures">
                            <template #body="slotProps">
                                {{ formatHeure(slotProps.data.hr_debut) + ' - ' + formatHeure(slotProps.data.hr_fin) }}
                            </template>
                        </Column>
                        <Column field="assistant" header="Assistant">
                            <template #body="tableActivite">
                                <MultiSelect
                                    v-model="tableActivite.data.responsable_ids"
                                    :options="optionCandidates"
                                    placeholder="Selectionner un candidat"
                                    optionValue="id"
                                    optionLabel="label"
                                    class="md:w-56"
                                    showClear
                                    @update:modelValue="calculateSeanceContract(selectedSeance)"
                                    style="min-width: 20rem"
                                    filter
                                    :disabled="tableActivite.data.change !== null && tableActivite.data.change.change_type === 'added'"
                                >
                                    <template #header>
                                        <div class="p-3">
                                            <Button label="Ajouter un nouveau candidat" fluid severity="secondary" text size="small" icon="pi pi-plus" @click="openCandidateDialog" />
                                        </div>
                                    </template>
                                </MultiSelect>
                            </template>
                        </Column>
                        <Column field="nombre_seance" header="Nombre de séance">
                            <template #body="slotProps">
                                <InputNumber
                                    v-model="slotProps.data.nombre_seance"
                                    :min="0"
                                    :max="15"
                                    mode="decimal"
                                    showButtons
                                    fluid
                                    @update:modelValue="calculateSeanceContract(selectedSeance)"
                                    :disabled="slotProps.data.change !== null && slotProps.data.change.change_type === 'added'"
                                />
                            </template>
                        </Column>
                    </DataTable>
                    <div class="flex flex-row-reverse">
                        <Button label="Sauvegarder" icon="pi pi-check" variant="text" class="mt-4" @click="confirmSaveSeance" />
                    </div>
                </div>
                <Dialog v-model:visible="candidatDialog" header="Ajouter une nouvelle candidature" :modal="true" :style="{ width: '450px' }" :closable="true" @hide="candidatFormState = {}">
                    <div class="p-1 space-y-4">
                        <div>
                            <label for="codePermanent" class="block text-xs font-medium mb-1"> Code Permanent <span class="text-red-500">*</span> </label>
                            <InputText
                                id="codePermanent"
                                v-model="candidat.code_permanent"
                                maxlength="12"
                                placeholder="EX: ABCD12345678"
                                class="w-full p-inputtext-sm"
                                :class="{ 'p-invalid': candidatFormState.code_permanent }"
                                @input="
                                    candidatFormState.code_permanent = false;
                                    candidat.code_permanent = candidat.code_permanent.toUpperCase();
                                "
                            />
                            <small v-if="candidatFormState.code_permanent" class="p-error text-xs"> Le code permanent est requis et doit suivre le format AAAA12345678. </small>
                        </div>

                        <template v-if="candidat.code_permanent && candidat.code_permanent.length === 12 && !candidatFormState.code_permanent">
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <div>
                                    <label for="prenom" class="block text-xs font-medium mb-1"> Prénom <span class="text-red-500">*</span> </label>
                                    <InputText id="prenom" v-model="candidat.prenom" class="w-full p-inputtext-sm" :class="{ 'p-invalid': candidatFormState.prenom }" @input="candidatFormState.prenom = false" />
                                    <small v-if="candidatFormState.prenom" class="p-error text-xs"> Le prénom est requis. </small>
                                </div>

                                <div>
                                    <label for="nom" class="block text-xs font-medium mb-1"> Nom <span class="text-red-500">*</span> </label>
                                    <InputText id="nom" v-model="candidat.nom" class="w-full p-inputtext-sm" :class="{ 'p-invalid': candidatFormState.nom }" @input="candidatFormState.nom = false" />
                                    <small v-if="candidatFormState.nom" class="p-error text-xs"> Le nom est requis. </small>
                                </div>
                            </div>

                            <div>
                                <label for="cycle" class="block text-xs font-medium mb-1"> Cycle d'étude <span class="text-red-500">*</span> </label>
                                <Select
                                    id="cycle"
                                    v-model="candidat.cycle"
                                    size="small"
                                    :options="[1, 2, 3]"
                                    class="w-full p-inputtext-sm"
                                    placeholder="Sélectionnez un cycle"
                                    :class="{ 'p-invalid': candidatFormState.cycle }"
                                    @change="candidatFormState.cycle = false"
                                />
                                <small v-if="candidatFormState.cycle" class="p-error text-xs"> Le cycle est requis. </small>
                            </div>
                        </template>
                        <template v-else>
                            <p class="text-xs text-gray-500 text-center mt-4">Veuillez entrer un code permanent valide (4 lettres, 8 chiffres) pour continuer.</p>
                        </template>
                    </div>

                    <template #footer>
                        <Button label="Annuler" icon="pi pi-times" text class="p-button-sm" @click="candidatDialog = false" />
                        <Button label="Suivant" icon="pi pi-check" class="p-button-sm" :disabled="!candidat.code_permanent || candidat.code_permanent.length !== 12 || candidatFormState.code_permanent" @click="saveCandidat" />
                    </template>
                </Dialog>

                <Dialog v-model:visible="changeDialog" :style="{ width: '450px' }" header="Confirmation" :modal="true">
                    <div class="flex items-center gap-4">
                        <i class="pi pi-exclamation-triangle !text-3xl" />
                        <span>Êtes-vous sûr de vouloir enregistrer les modifications apportées à cette séance ?</span>
                    </div>
                    <template #footer>
                        <Button label="No" icon="pi pi-times" text @click="changeDialog = false" />
                        <Button label="Yes" icon="pi pi-check" @click="saveSeance" />
                    </template>
                </Dialog>
                <Dialog v-model:visible="confirmCancelDialog" :style="{ width: '450px' }" header="Confirmation" :modal="true">
                    <div class="flex items-center gap-4">
                        <i class="pi pi-exclamation-triangle !text-3xl" />
                        <span>Êtes-vous sûr de vouloir annuler les modifications apportées à cette séance ? Toutes les modifications seront perdues.</span>
                    </div>
                    <template #footer>
                        <Button label="No" icon="pi pi-times" text @click="confirmCancelDialog = false" />
                        <Button label="Yes" icon="pi pi-check" @click="cancelSeance" />
                    </template>
                </Dialog>
            </div>
        </div>
    </div>
</template>

<style>
.p-datatable-tbody > tr.danger-row {
    background: var(--p-button-outlined-danger-hover-background);
    color: var(--p-button-text-danger-color);
}

.p-datatable-tbody > tr.success-row {
    background: var(--p-button-outlined-success-hover-background);
    color: var(--p-button-text-success-color);
}

.p-datatable-tbody > tr.change-row {
    background: var(--p-button-outlined-warn-hover-background);
    color: var(--p-button-text-warn-color);
}

.p-datatable-table .p-datatable-tbody > tr.no-expander > td .p-datatable-row-toggle-button {
    display: none;
}
</style>
