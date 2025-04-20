<script>
import { sharedSelectState } from '@/layout/composables/sharedSelectedState';
import { CandidatService } from '@/service/CandidatService';
import { UQOService } from '@/service/UQOService';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';

const emailUQORegex = /^[a-zA-Z0-9._%+-]+@uqo.ca$/;
const codePermanentRegex = /^[A-Z]{4}\d{8}$/;

export default {
    data() {
        return {
            toast: useToast(),

            // Candidat
            selectedCandidat: null,
            candidatDialog: false,
            deleteCandidatDialog: false,
            candidat: {},
            candidatFormState: {},
            confirmCandidatDialog: false,
            candidatAction: '', // VIEW, NEW, EDIT, DELETE
            dt: null,
            candidats: [],
            filters: {
                global: { value: null, matchMode: FilterMatchMode.CONTAINS },
                prenom: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
                nom: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
                code_permanent: { value: null, matchMode: FilterMatchMode.STARTS_WITH }
            },

            // Candidature
            candidatureDialog: false,
            candidature: {},
            deleteCandidatureDialog: false,
            candidatureAction: '', // VIEW, NEW, EDIT, DELETE

            // MISC
            programmes: [],
            trimestre: new Date().getFullYear() * 10 + Math.ceil((new Date().getMonth() + 1) / 4), // Current trimestre
            loading: false,
            sharedState: sharedSelectState,
            courses: [],
            programmeLoading: false // Add loading state for program list
        };
    },
    mounted() {
        UQOService.getCours().then((courses) => (this.courses = courses));
        this.fetchCandidatures();
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
                this.fetchCandidatures();
            }
        }
    },
    methods: {
        async fetchCandidatures() {
            const currentTrimestre = this.selectedTrimestre;
            if (currentTrimestre === null) {
                this.candidats = []; // Clear data if no trimestre
                return;
            }

            this.loading = true;
            try {
                console.log(this.trimestre);
                const data = await CandidatService.getCandidatures(currentTrimestre);
                this.candidats = data;
            } catch (error) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: 'Impossible de charger les candidatures', life: 3000 });
            } finally {
                this.loading = false;
            }
        },
        async saveCandidat(candidat) {
            this.loading = true;
            try {
                await this.fetchCandidatures();
            } catch (error) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: 'Impossible de sauvegarder le candidat', life: 3000 });
            } finally {
                this.loading = false;
            }
            this.confirmCandidatDialog = false;
            this.candidatDialog = false;
        },
        async deleteCandidat() {
            this.loading = true;
            try {
                await CandidatService.deleteCandidature(this.candidat.id);
                this.toast.add({ severity: 'success', summary: 'Succès', detail: 'Candidat supprimé', life: 3000 });
                await this.fetchCandidatures();
            } catch (error) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: 'Impossible de supprimer le candidat', life: 3000 });
            } finally {
                this.loading = false;
            }
            this.deleteCandidatDialog = false;
        },
        openViewCandidat(candidat) {
            this.candidat = candidat;

            this.candidatDialog = true;
            this.candidatAction = 'VIEW';
        },
        openNewCandidat() {
            this.candidat = {
                code_permanent: '',
                email: '',
                nom: '',
                prenom: '',
                campus: 'gatineau',
                cycle: 1,
                programme: '',
                candidature: []
            };
            this.candidatFormState = {
                code_permanent: false,
                email: false,
                nom: false,
                prenom: false,
                campus: false,
                cycle: false,
                programme: false,
                candidature: false
            };
            this.getListProgramme(this.candidat.cycle);
            this.selectedCandidat = null;
            this.candidatDialog = true;

            this.candidatAction = 'NEW';
        },
        openEditCandidat(candidat) {
            this.candidat = { ...candidat };

            this.getListProgramme(this.candidat.cycle);
            this.selectedCandidat = candidat;
            this.candidatDialog = true;
            this.candidatAction = 'EDIT';
        },
        openConfirmCandidat(candidat) {
            let isValid = true;

            if (candidat.nom === '') {
                this.candidatFormState.nom = true;
                isValid = false;
            }

            if (candidat.prenom === '') {
                this.candidatFormState.prenom = true;
                isValid = false;
            }

            if (!codePermanentRegex.test(candidat.code_permanent)) {
                this.candidatFormState.code_permanent = true;
                isValid = false;
            }

            if (candidat.email !== '' && !emailUQORegex.test(candidat.email)) {
                this.candidatFormState.email = true;
                isValid = false;
            }

            if (!isValid) {
                this.toast.add({ severity: 'error', summary: 'Validation Error', detail: 'Certain champs son invalide.', life: 3000 });
                return;
            }

            this.confirmCandidatDialog = true;
        },
        confirmDeleteCandidat(candidat) {
            this.candidat = candidat;
            this.deleteCandidatDialog = true;
        },
        getCandidatDialogTitle(candidatAction) {
            switch (candidatAction) {
                case 'EDIT':
                    return "Modification des informations d'un candidat";
                case 'NEW':
                    return "Ajout d'un nouveau candidat";
                case 'VIEW':
                    return "Visionnement les informations d'un candidat";
                default:
                    break;
            }
        },

        // Candidature
        openNewCandidature() {
            this.candidature = {
                sigle: '',
                titre: '',
                note: 'B+'
            };
            this.candidatureAction = 'NEW';
            this.candidatureDialog = true;
        },
        openEditCandidature(candidature) {
            this.candidature = { ...candidature };
            this.candidatureAction = 'EDIT';
            this.candidatureDialog = true;
        },
        confirmDeleteCandidature(candidature) {
            this.candidature = candidature;
            this.deleteCandidatureDialog = true;
        },
        confirmEditCandidature(candidature) {
            console.log(this.candidature, candidature == candidature, candidature === candidature, this.candidatAction);
            if (this.candidatureAction === 'NEW') {
                if (this.candidat.candidature.find((val) => val.sigle === candidature.sigle) !== undefined) {
                    this.toast.add({ severity: 'warn', summary: 'Attention', detail: 'Une candidature pour ce cours existe déjà pour ce candidat', life: 2000 });
                    return;
                }
                let title = 'Cours introuvable';
                console.log(this.courses);
                const foundCourse = this.courses.find((course) => course.sigle === this.candidature.sigle);
                if (foundCourse) {
                    title = foundCourse.titre;
                }
                this.candidature.titre = title;
                console.log(this.candidature);
                this.candidat.candidature.push(this.candidature);
                this.candidatureDialog = false;
            } else if (this.candidatureAction === 'EDIT') {
                const index = this.candidat.candidature.findIndex((c) => c.sigle === candidature.sigle);
                if (index !== -1) {
                    this.candidat.candidature.splice(index, 1, candidature);
                }
                this.candidatureDialog = false;
            }
        },
        deleteCandidature() {
            this.candidat.candidature = this.candidat.candidature.filter((c) => c.sigle !== this.candidature.sigle);
            this.deleteCandidatureDialog = false;
            this.toast.add({ severity: 'success', summary: 'Successful', detail: 'Candidature supprimée', life: 3000 });
        },

        // Datatable
        exportCSV() {
            this.dt.exportCSV();
        },
        async downloadResume(student) {
            try {
                const id = student.id;
                const codePermanent = student.code_permanent;
                const filename = `${this.trimestre}_${codePermanent || id}_CV.pdf`;

                const response = await CandidatService.downloadResume(id, this.trimestre);

                // Create a blob URL directly from the response data
                const blob = new Blob([response]);
                const url = window.URL.createObjectURL(blob);

                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', filename);
                document.body.appendChild(link);
                link.click();

                // Clean up
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(link);
                }, 100);
            } catch (error) {
                console.error('Error downloading resume:', error);
                this.toast.add({
                    severity: 'error',
                    summary: 'Erreur',
                    detail: "Aucun CV n'a été enregistré pour ce candidat ou erreur de téléchargement",
                    life: 3000
                });
            }
        },

        // File upload
        upload() {
            this.$refs.fileupload.upload();
        },
        onUpload() {
            this.toast.add({ severity: 'info', summary: 'Succès', detail: 'Fichier Téléversé', life: 3000 });
        },

        // MISC
        async getListProgramme(cycle) {
            this.programmeLoading = true; // Start loading
            try {
                const programmes = await UQOService.getProgramme(cycle);
                this.programmes = programmes;
            } catch (error) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: 'Impossible de charger les programmes', life: 3000 });
            } finally {
                this.programmeLoading = false; // End loading
            }
        }
    }
};
</script>

<template>
    <div class="relative overflow-hidden w-full">
        <!-- Pages Wrapper -->
        <div class="flex w-[200%] transition-transform duration-500" :class="{ '-translate-x-1/2': candidatDialog }">
            <!-- First Page -->
            <div class="w-1/2 flex-shrink-0">
                <div class="card" :style="candidatDialog ? { display: 'none' } : {}">
                    <DataTable
                        ref="dt"
                        :value="candidats"
                        dataKey="id"
                        :paginator="true"
                        :rows="25"
                        :filters="filters"
                        :globalFilterFields="['prenom', 'nom', 'code_permanent']"
                        removableSort
                        paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                        :rowsPerPageOptions="[25, 50]"
                        currentPageReportTemplate="Affichage de {first} à {last} sur {totalRecords} candidats"
                    >
                        <template #header>
                            <div class="flex flex-wrap gap-2 items-center justify-between">
                                <h4 class="m-0">Gestion des candidats</h4>
                                <IconField>
                                    <InputIcon>
                                        <i class="pi pi-search" />
                                    </InputIcon>
                                    <InputText v-model="filters['global'].value" placeholder="Recherche..." />
                                </IconField>
                                <div class="flex gap-2">
                                    <Button label="Ajouter" icon="pi pi-plus" severity="primary" class="mr-2" @click="openNewCandidat" />
                                    <Button icon="pi pi-refresh" class="mr-2" outlined @click="fetchCandidatures" />
                                </div>
                            </div>
                        </template>

                        <Column field="code_permanent" header="Code permanent" style="max-width: 6rem">
                            <template #body="slotProps">
                                <code>{{ slotProps.data.code_permanent }}</code>
                            </template>
                        </Column>

                        <Column field="nom_complet" header="Nom complet">
                            <template #body="slotProps">
                                {{ slotProps.data.nom + ', ' + slotProps.data.prenom }}
                            </template>
                        </Column>

                        <Column field="cycle" header="Cycle" sortable>
                            <template #body="slotProps">
                                {{ slotProps.data.cycle }}
                            </template>
                        </Column>
                        <Column :exportable="false" style="max-width: 5rem">
                            <template #body="slotProps">
                                <Button icon="pi pi-pencil" rounded @click="openEditCandidat(slotProps.data)" />
                                <Button icon="pi pi-download" rounded severity="secondary" class="ml-2" @click="downloadResume(slotProps.data)" />
                                <Button icon="pi pi-trash" rounded severity="danger" class="ml-2" @click="confirmDeleteCandidat(slotProps.data)" />
                            </template>
                        </Column>
                    </DataTable>

                    <Dialog v-model:visible="deleteCandidatDialog" :style="{ width: '450px' }" header="Confirmation" :modal="true">
                        <div class="flex items-center gap-4">
                            <i class="pi pi-exclamation-triangle !text-3xl" />
                            <span v-if="candidat"
                                >Êtes-vous sûr de vouloir supprimer la candidature de <b>{{ candidat.prenom + ' ' + candidat.nom + ' (' + candidat.email + ')' }}</b> ?</span
                            >
                        </div>
                        <template #footer>
                            <Button label="Non" icon="pi pi-times" text @click="deleteCandidatDialog = false" />
                            <Button label="Oui" icon="pi pi-check" @click="deleteCandidat" />
                        </template>
                    </Dialog>
                </div>
            </div>

            <!-- Second Page -->
            <div class="w-1/2 flex-shrink-0">
                <div class="card" :style="!candidatDialog ? { display: 'none' } : {}">
                    <CreateEditCandidature v-if="candidatDialog" v-model:candidat="candidat" v-model:trimestre="selectedTrimestre" :candidat-action="candidatAction" @save="saveCandidat" @close="candidatDialog = false" />
                </div>
            </div>
        </div>
    </div>
</template>
