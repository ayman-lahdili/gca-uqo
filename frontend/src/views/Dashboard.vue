<script>
import { sharedSelectState } from '@/layout/composables/sharedSelectedState';
import { CampagneService } from '@/service/CampagneService';
import { CandidatService } from '@/service/CandidatService';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';

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
            selectedSeance: null,
            selectedActivite: null,
            value: '',

            // Loading
            seanceTableLoading: false,
            confirmChangeLoading: false,

            // Seance
            seanceDialog: false,
            optionCandidates: [],
            confirmCancelDialog: false,
            changeDialog: false,
            seanceChanged: false,

            // Candidat
            candidateDialog: false,
            newCandidate: {
                prenom: '',
                nom: '',
                code_permanent: ''
            },
            candidatAction: 'EDIT',

            // Campagne Datatable
            filters: {
                global: { value: null, matchMode: FilterMatchMode.CONTAINS }
            },

            listCandidatCode: {},
            contrat: 0,

            // Contract
            totalSeance: 0,

            // Changes
            change: null,
            confirmChangeDialog: false,
            sigle: null,
            seance_id: null,

            // Distribution
            distribution: [],
            totalActivities: 0,
            totalCost: 0
        };
    },
    mounted() {
        this.fetchCampagneDetails();
        CandidatService.getCandidat().then((data) => {
            this.listCandidatCode = data.reduce((acc, candidat) => {
                acc[candidat.code_permanent] = candidat;
                return acc;
            }, {});
        });
    },
    computed: {
        // Create a computed property to make the shared state reactive within this component
        selectedTrimestre() {
            return this.sharedState.selectedValue;
        }
    },
    watch: {
        // Watch the computed property 'selectedTrimestre'
        selectedTrimestre(newValue, oldValue) {
            console.log(`Candidatures component detected trimestre change: ${newValue}`);
            if (newValue !== oldValue) {
                // Fetch data when the trimestre changes
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
                this.totalActivities = this.calculateTotalActivities(); // Initialize total activities
                this.totalCost = this.calculateTotalCost(); // Initialize total cost
            });
        },
        openEditSeance(seance, candidature) {
            this.seance = { ...seance };
            this.listeCandidature = candidature;
            this.optionCandidates = candidature.map((candidature) => {
                return {
                    id: candidature.etudiant.id,
                    label: candidature.etudiant.nom + ', ' + candidature.etudiant.prenom + ' (' + candidature.etudiant.code_permanent + ')'
                };
            });
            console.log('optionCandidates', this.optionCandidates);
            this.seanceDialog = true;
            this.seanceChanged = false;
        },
        openConfirmChange(seance, sigle) {
            this.sigle = sigle;
            this.seance = seance;
            this.confirmChangeDialog = true;
        },
        async confirmChange(seance) {
            this.confirmChangeLoading = true;

            await CampagneService.approveSeanceChange(this.selectedTrimestre, this.sigle, this.seance.groupe);

            this.confirmChangeLoading = false;
            this.fetchCampagneDetails();
            this.confirmChangeDialog = false;
        },
        openCandidateDialog(activite) {
            this.selectedActivite = { ...activite };
            this.candidateDialog = true;
        },
        saveCandidate() {
            if (this.newCandidate.prenom && this.newCandidate.nom && this.newCandidate.code_permanent) {
                this.candidateDialog = false;
                if (this.listeCandidature.find((value) => value.code_permanent === this.newCandidate.code_permanent)) {
                    console.log('Already exist');
                    this.toast.add({ severity: 'error', summary: 'Validation Error', detail: 'This candidate already exists.', life: 3000 });
                } else {
                    this.listeCandidature.push(this.newCandidate);
                    this.listCandidatCode[this.newCandidate.code_permanent] = this.newCandidate;
                    this.seance.activite.find((value) => value.id === this.selectedActivite.data.id).assistant = this.newCandidate;
                    this.calculateTotalSeance();
                    this.distribution = this.calculateDistribution(); // Update distribution
                    this.totalActivities = this.calculateTotalActivities(); // Update total activities
                    this.totalCost = this.calculateTotalCost(); // Update total cost
                    this.toast.add({ severity: 'success', summary: 'Candidate Created', detail: 'New candidate has been added.', life: 3000 });
                }

                this.newCandidate = { prenom: '', nom: '', code_permanent: '' }; // Reset fields
            } else {
                this.toast.add({ severity: 'error', summary: 'Validation Error', detail: 'All fields are required.', life: 3000 });
            }
        },
        getCandidat(codePermanent) {
            if (codePermanent.length < 12) return;

            const candidat = this.listCandidatCode[codePermanent];
            if (candidat !== undefined) {
                this.newCandidate = { ...candidat };
                this.candidatAction = 'EDIT';
            } else {
                this.newCandidate.prenom = '';
                this.newCandidate.nom = '';
                this.candidatAction = 'CREATE';
            }
        },
        confirmSaveSeance() {
            this.changeDialog = true;
        },
        saveSeance() {
            this.changeDialog = false;
            this.seanceDialog = false;
            this.toast.add({ severity: 'success', summary: 'Seance Saved', detail: 'Seance changes have been saved.', life: 3000 });
            this.distribution = this.calculateDistribution(); // Update distribution
            this.totalActivities = this.calculateTotalActivities(); // Update total activities
            this.totalCost = this.calculateTotalCost(); // Update total cost
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
            this.totalSeance = this.seance.activite.reduce((acc, activite) => {
                if (activite.assistant?.cycle !== undefined) {
                    return acc + activite.nombre_seance * this.campagne.salaire[activite.assistant.cycle - 1] * (activite.type === 'TD' ? 2 + 1 : 3 + 2);
                }
                return acc;
            }, 0);
        },
        calculateCourseContract(course) {
            return course.seance.reduce((acc, seance) => {
                return (
                    acc +
                    seance.activite.reduce((acc, activite) => {
                        if (activite.assistant?.cycle !== undefined) {
                            return acc + activite.nombre_seance * this.campagne.salaire[activite.assistant.cycle - 1] * (activite.type === 'TD' ? 2 + 1 : 3 + 2);
                        }
                        return acc;
                    }, 0)
                );
            }, 0);
        },
        calculateSeanceContract(seance) {
            return seance.activite.reduce((acc, activite) => {
                if (activite.assistant?.cycle !== undefined) {
                    return acc + activite.nombre_seance * this.campagne.salaire[activite.assistant.cycle - 1] * (activite.type === 'TD' ? 2 + 1 : 3 + 2);
                }
                return acc;
            }, 0);
        },
        countTDActivities(seance) {
            return seance.activite.filter((activite) => activite.type === 'Travaux dirigés').length;
        },
        countTPActivities(seance) {
            return seance.activite.filter((activite) => activite.type === 'Travaux pratiques').length;
        },
        openConfirmChangeActivity(activity, seance) {
            this.selectedSeance = seance;
            this.selectedActivite = activity;
            this.confirmChangeDialog = true;
        },
        confirmChangeActivity(activity) {
            const changeType = activity.change.type;

            if (changeType === 'C') {
                activity.change.status = 'C';
            } else if (changeType === 'D') {
                // Delete the activity from the seance
                this.selectedSeance.activite = this.selectedSeance.activite.filter((a) => a.id !== activity.id);
            }

            this.confirmChangeDialog = false;
            this.distribution = this.calculateDistribution(); // Update distribution
            this.totalActivities = this.calculateTotalActivities(); // Update total activities
            this.totalCost = this.calculateTotalCost(); // Update total cost
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
                        if (activite.type === 'TD' || activite.type === 'TP') {
                            totalActivities += 1;
                            if (activite.assistant && activite.assistant.cycle) {
                                distribution[activite.assistant.cycle - 1].value += 1;
                            }
                        }
                    });
                });
            });

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
                        if (activite.type === 'TD' || activite.type === 'TP') {
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
        }
    }
};

// TODO: add a unamed column for each row that will contain a button for when there are changes that occured that need to be treated
// List all the type of differences that can occure and how they should be stored and treated (graphically)
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
                                    <h1>120</h1>
                                    <span class="ml-1 mb-0 text-sm text-muted-color font-semibold">candidats</span>
                                </div>
                                <div class="flex items-center">
                                    <h1>{{ formatCurrency(totalCost) }}</h1>
                                    <span class="ml-4 mb-0 text-sm text-muted-color font-semibold">Hiver 2025</span>
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
                            :loading="seanceTableLoading"
                            :rowClass="
                                (rowData) => ({
                                    'change-row': rowData.change !== null && hasAddedOrRemovedChange(rowData),
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
                                        <Button label="Synchroniser les horaires" icon="pi pi-refresh" class="p-button-primary mr-2" @click="syncSchedules" />
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
                            <Column field="contract" header="Contract ($)">
                                <template #body="slotProps">
                                    {{ formatCurrency(calculateCourseContract(slotProps.data)) }}
                                </template>
                            </Column>
                            <template #expansion="slotProps1">
                                <div v-if="slotProps1.data.status !== 'non_confirmee'" class="p-2">
                                    <DataTable
                                        :value="slotProps1.data.seance"
                                        size="small"
                                        :rowClass="
                                            (rowData) => ({
                                                'danger-row': rowData.change !== null && rowData.change.change_type === 'removed',
                                                'success-row': rowData.change !== null && rowData.change.change_type === 'added'
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
                                                    @click="openConfirmChange(slotProps.data, slotProps1.data.sigle)"
                                                />
                                                <Button
                                                    v-if="slotProps.data.change !== null && slotProps.data.change.change_type === 'added'"
                                                    icon="pi pi-plus-circle"
                                                    severity="success"
                                                    @click="openConfirmChange(slotProps.data, slotProps1.data.sigle)"
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
                                        <Column field="contract" header="Contract ($)">
                                            <template #body="slotProps">
                                                {{ formatCurrency(calculateSeanceContract(slotProps.data)) }}
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
                                        <Column :exportable="false" style="min-width: 7rem">
                                            <template #body="slotProps">
                                                <template v-if="slotProps.data.change !== null && slotProps.data.change.change_type === 'unchanged'">
                                                    <Button icon="pi pi-pencil" rounded @click="openEditSeance(slotProps.data, slotProps1.data.candidature)" />
                                                    <Button icon="pi pi-download" rounded severity="secondary" class="ml-2" @click="downloadCVs" />
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
                            <span v-else-if="seance">
                                <span v-if="seance.change?.change_type === 'added'">Cette séance a été ajoutée dans l'horaire de l'UQO. Êtes-vous sûr de vouloir confirmer l'ajout de cette séance ?</span>
                                <span v-else-if="seance.change?.change_type === 'removed'"
                                    >Cette séance a été retirée de l'horaire de l'UQO. Êtes-vous sûr de vouloir confirmer la suppréssion de cette séance ? Tous les informations sur les assignations des assistants seront supprimée.</span
                                >
                            </span>
                        </div>
                        <template #footer>
                            <Button v-if="seance.change?.change_type !== 'added'" label="Non, je veux m'assurer de ne pas perdre d'information" icon="pi pi-times" text @click="confirmChangeDialog = false" />
                            <Button label="Oui, confirmer" icon="pi pi-check" @click="selectedActivite ? confirmChangeActivity(selectedActivite) : confirmChange(seance)" :loading="confirmChangeLoading" />
                        </template>
                    </Dialog>
                </div>
            </div>
            <div class="w-1/2 flex-shrink-0">
                <div class="card mt-2" :style="!seanceDialog ? { display: 'none' } : {}">
                    <div class="flex">
                        <Button icon="pi pi-times" variant="text" rounded severity="secondary" class="mb-4 mx-4" @click="confirmCancelSeance" />
                    </div>

                    <DataTable
                        :value="seance.activite"
                        :rowClass="
                            (rowData) => ({
                                'danger-row': rowData.change !== null && rowData.change.status === 'NC' && rowData.change.type === 'D',
                                'success-row': rowData.change !== null && rowData.change.status === 'NC' && rowData.change.type === 'C'
                            })
                        "
                    >
                        <Column :exportable="false">
                            <template #body="slotProps">
                                <Button
                                    v-if="slotProps.data.change !== null && slotProps.data.change.type === 'D' && slotProps.data.change.status === 'NC'"
                                    icon="pi pi-exclamation-triangle"
                                    severity="danger"
                                    raised
                                    outlined
                                    @click="openConfirmChangeActivity(slotProps.data, seance)"
                                />
                                <Button
                                    v-if="slotProps.data.change !== null && slotProps.data.change.type === 'C' && slotProps.data.change.status === 'NC'"
                                    icon="pi pi-plus-circle"
                                    severity="success"
                                    raised
                                    outlined
                                    @click="openConfirmChangeActivity(slotProps.data, seance)"
                                />
                            </template>
                        </Column>
                        <Column field="type" header="Type">
                            <template #body="slotProps">
                                {{ slotProps.data.type }}
                            </template>
                        </Column>
                        <Column field="assistant" header="Assistant">
                            <template #body="activite">
                                <MultiSelect
                                    v-model="activite.data.assistant"
                                    :options="optionCandidates"
                                    placeholder="Selectionner un candidat"
                                    optionValue="id"
                                    optionLabel="label"
                                    class="md:w-56"
                                    showClear
                                    @update:modelValue="calculateTotalSeance"
                                    style="min-width: 20rem"
                                    filter
                                >
                                    <template #header>
                                        <div class="p-3">
                                            <Button label="Ajouter un nouveau candidat" fluid severity="secondary" text size="small" icon="pi pi-plus" @click="openCandidateDialog(activite)" />
                                        </div>
                                    </template>
                                </MultiSelect>
                            </template>
                        </Column>
                        <Column field="nombre_seance" header="Nombre de séance">
                            <template #body="slotProps">
                                <InputNumber v-model="slotProps.data.nombre_seance" :min="0" :max="15" mode="decimal" showButtons fluid @update:modelValue="calculateTotalSeance" />
                            </template>
                        </Column>
                        <Column field="contrat" header="Contrat ($)">
                            <template #body="slotProps">
                                {{ formatCurrency(slotProps.data.assistant?.cycle !== undefined ? slotProps.data.nombre_seance * campagne.salaire[slotProps.data.assistant.cycle - 1] * (slotProps.data.type === 'TD' ? 2 : 3) : 0) }}
                            </template>
                        </Column>
                        <ColumnGroup type="footer">
                            <Row>
                                <Column footer="Total :" :colspan="3" footerStyle="text-align:right" />
                                <Column :footer="formatCurrency(totalSeance)" />
                            </Row>
                        </ColumnGroup>
                    </DataTable>
                    <div class="flex flex-row-reverse">
                        <Button label="Sauvegarder" icon="pi pi-check" variant="text" class="mt-4" @click="confirmSaveSeance" />
                    </div>
                </div>
                <Dialog v-model:visible="candidateDialog" header="Nouveau Candidat" modal :closable="false">
                    <div class="p-fluid">
                        <div class="field">
                            <label for="codePermanent">Code Permanent</label>
                            <InputText id="codePermanent" v-model="newCandidate.code_permanent" @input="getCandidat(newCandidate.code_permanent)" />
                        </div>
                        <template v-if="newCandidate.code_permanent.length >= 12">
                            <div class="field">
                                <label for="prenom">Prénom</label>
                                <InputText id="prenom" v-model="newCandidate.prenom" :disabled="candidatAction === 'EDIT'" />
                            </div>
                            <div class="field">
                                <label for="nom">Nom</label>
                                <InputText id="nom" v-model="newCandidate.nom" :disabled="candidatAction === 'EDIT'" />
                            </div>
                        </template>
                    </div>
                    <template #footer>
                        <Button label="Annuler" icon="pi pi-times" text @click="candidateDialog = false" />
                        <Button label="Sauvegarder" icon="pi pi-check" @click="saveCandidate" />
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
