<template>
    <div>
        <div class="max-w-4xl mx-auto p-4 card">
            <h3>{{ getCandidatDialogTitle(candidatAction) }}</h3>
            <Button label="Cancel" icon="pi pi-times" variant="text" class="mb-4" @click="closeCandidatDialog" />
            <!-- Form divided into clear sections -->
            <div class="space-y-8">
                <!-- Section 1: Identification -->
                <section class="rounded-lg p-6">
                    <h2 class="text-xl font-bold mb-4 border-b pb-2">Informations d'identification</h2>
                    <div class="space-y-4">
                        <!-- Name inputs in a row -->
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label for="prenom" class="block text-sm font-medium mb-1">Prénom <span class="text-red-500">*</span></label>
                                <InputText id="prenom" v-model="candidat.prenom" class="w-full" :invalid="candidatFormState.prenom" @change="candidatFormState.prenom = false" />
                            </div>
                            <div>
                                <label for="nom" class="block text-sm font-medium mb-1">Nom <span class="text-red-500">*</span></label>
                                <InputText id="nom" v-model="candidat.nom" class="w-full" :invalid="candidatFormState.nom" @change="candidatFormState.nom = false" />
                            </div>
                            <!-- Code permanent - highlighted as important -->
                            <div>
                                <label for="code_permanent" class="block text-sm font-medium mb-1"> Code permanent <span class="text-red-500">*</span> </label>
                                <InputText
                                    id="code_permanent"
                                    v-model="candidat.code_permanent"
                                    class="w-full"
                                    placeholder="DOEJ12345678"
                                    maxlength="12"
                                    :invalid="candidatFormState.code_permanent"
                                    @change="candidatFormState.code_permanent = false"
                                />
                            </div>
                            <!-- Email -->
                            <div>
                                <label for="email" class="block text-sm font-medium mb-1">Adresse courriel de l'UQO</label>
                                <InputText id="email" v-model="candidat.email" class="w-full" placeholder="doej01@uqo.ca" :invalid="candidatFormState.email" @change="candidatFormState.email = false" />
                            </div>
                        </div>

                        <!-- CV Upload/Download -->
                        <div class="pt-2">
                            <label class="block text-sm font-medium mb-2">Curriculum Vitae</label>
                            <div class="flex flex-col sm:flex-row gap-2 justify-between">
                                <Button label="Télécharger CV actuel" icon="pi pi-download" class="flex-1" outlined />
                                <FileUpload ref="fileupload" mode="basic" name="cv" url="/" accept="application/pdf" :maxFileSize="5000000" @upload="onUpload" chooseLabel="Téléverser CV" class="flex-1" />
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Section 2: Academic Information -->
                <section class="rounded-lg p-6">
                    <h2 class="text-xl font-bold mb-4 border-b pb-2">Informations académiques</h2>
                    <div class="space-y-4">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <!-- Study cycle -->
                            <div>
                                <label for="cycle" class="block text-sm font-medium mb-1">Cycle d'étude <span class="text-red-500">*</span></label>
                                <Select id="cycle" v-model="candidat.cycle" :options="[1, 2, 3]" class="w-full" placeholder="Sélectionnez un cycle" @change="getListProgramme(candidat.cycle)" />
                            </div>

                            <!-- Campus selection -->
                            <div>
                                <label for="campus" class="block text-sm font-medium mb-1">Campus d'admission</label>
                                <Select
                                    id="campus"
                                    v-model="candidat.campus"
                                    :options="[
                                        { label: 'Gatineau', value: 'gatineau' },
                                        { label: 'Saint-Jérôme', value: 'st-jerome' }
                                    ]"
                                    optionLabel="label"
                                    optionValue="value"
                                    class="w-full"
                                    placeholder="Sélectionnez un campus"
                                />
                            </div>
                        </div>

                        <!-- Study program - only shown when cycle is selected -->
                        <div v-if="candidat.cycle">
                            <label for="programme" class="block text-sm font-medium mb-1">Programme d'étude</label>
                            <Select id="programme" v-model="candidat.programme" :options="programmes" optionLabel="label" optionValue="sigle" class="w-full" placeholder="Sélectionnez un programme" :loading="programmeLoading" />
                        </div>
                    </div>
                </section>

                <!-- Section 3: Course Selection -->
                <section class="rounded-lg p-6">
                    <h2 class="text-xl font-bold mb-4 border-b pb-2">Sélection des cours d'intérêt</h2>

                    <!-- Course table -->
                    <DataTable :value="candidat.candidature" class="p-datatable-sm" responsiveLayout="scroll" stripedRows>
                        <template #header>
                            <div class="flex flex-wrap gap-2 items-center justify-between">
                                <h4 class="m-0">Candidatures</h4>
                                <Button label="Ajouter un cours" icon="pi pi-plus" severity="secondary" class="mr-2" @click="openNewCandidature" />
                            </div>
                        </template>
                        <Column field="sigle" header="Sigle"></Column>
                        <Column field="titre" header="Titre du cours"></Column>
                        <Column field="note" header="Note" style="max-width: 3rem"></Column>
                        <Column :exportable="false" style="min-width: 10rem">
                            <template #body="slotProps">
                                <Button icon="pi pi-pencil" rounded class="mr-2" outlined @click="openEditCandidature(slotProps.data)" />
                                <Button icon="pi pi-trash" rounded severity="danger" @click="confirmDeleteCandidature(slotProps.data)" />
                            </template>
                        </Column>
                    </DataTable>
                </section>

                <!-- Save button - only shown in edit mode -->
                <div class="flex justify-end">
                    <Button v-if="candidatAction !== 'VIEW'" label="Enregistrer" icon="pi pi-save" severity="success" class="px-4 py-2" @click="openConfirmCandidat(candidat)" />
                </div>
            </div>
        </div>

        <!-- Candidatures -->
        <Dialog v-model:visible="candidatureDialog" :style="{ width: '450px' }" :header="candidatureAction === 'EDIT' ? 'Modification d\'une candidature' : 'Ajout d\'une candidature'" :modal="true">
            <div class="flex flex-col gap-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label for="sigle" class="block text-sm font-medium mb-1">Sigle</label>
                        <InputText v-model="candidature.sigle" class="w-full mt-2" type="text" placeholder="Sigle" maxlength="8" :disabled="candidatureAction === 'EDIT'" />
                    </div>
                    <div>
                        <label for="note" class="block text-sm font-medium mb-1">Note</label>
                        <Select v-model="candidature.note" class="w-full mt-2" :options="['A+', 'A', 'A-', 'B+', 'B', 'B-']" type="text" placeholder="Note" />
                    </div>
                </div>
            </div>
            <template #footer>
                <Button label="Non" icon="pi pi-times" text @click="candidatureDialog = false" />
                <Button label="Oui" icon="pi pi-check" @click="confirmEditCandidature(candidature)" :disabled="candidature.sigle.length < 7" />
            </template>
        </Dialog>
        <Dialog v-model:visible="deleteCandidatureDialog" :style="{ width: '450px' }" header="Confirmation" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="candidat"
                    >Êtes-vous sûr de vouloir supprimer la candidature pour le cours de <b>{{ candidature.sigle + ' ' + candidature.titre }}</b> ?</span
                >
            </div>
            <template #footer>
                <Button label="Non" icon="pi pi-times" text @click="deleteCandidatureDialog = false" />
                <Button label="Oui" icon="pi pi-check" @click="deleteCandidature" />
            </template>
        </Dialog>

        <!-- Candidat -->
        <Dialog v-model:visible="confirmCandidatDialog" :style="{ width: '450px' }" header="Confirmation" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="candidatAction === 'EDIT'"
                    >Êtes-vous sûr de vouloir appliquer les modifications sur le candidat <b>{{ candidat.prenom + ' ' + candidat.nom + ' (' + candidat.email + ')' }}</b> ?</span
                >
                <span v-if="candidatAction === 'NEW'"
                    >Êtes-vous sûr de vouloir ajouter le candidat <b>{{ candidat.prenom + ' ' + candidat.nom + ' (' + candidat.email + ')' }}</b> ?</span
                >
            </div>
            <template #footer>
                <Button label="Non" icon="pi pi-times" text @click="confirmCandidatDialog = false" />
                <Button label="Oui" icon="pi pi-check" @click="saveCandidat(candidat)" />
            </template>
        </Dialog>
    </div>
</template>

<script>
import { CandidatService } from '@/service/CandidatService';
import { UQOService } from '@/service/UQOService';
import { useToast } from 'primevue/usetoast';

const emailUQORegex = /^[a-zA-Z0-9._%+-]+@uqo.ca$/;
const codePermanentRegex = /^[A-Z]{4}\d{8}$/;

export default {
    props: {
        candidat: {
            type: Object,
            required: true,
            default: () => ({
                code_permanent: '',
                email: '',
                nom: '',
                prenom: '',
                campus: 'gatineau',
                cycle: 1,
                programme: '',
                candidature: []
            })
        },
        candidatAction: {
            type: String,
            required: true,
            validator: (value) => ['NEW', 'EDIT', 'VIEW'].includes(value)
        },
        trimestre: {
            type: String,
            required: true
        }
    },
    emits: ['save', 'close'],
    data() {
        return {
            toast: useToast(),
            showWarningDialog: false,
            hasUnsavedChanges: false,
            courses: [],
            programmes: [],
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
            candidature: {},
            candidatureAction: false,
            candidatureDialog: false,
            deleteCandidatureDialog: false,
            confirmCandidatDialog: false,
            programmeLoading: false
        };
    },
    mounted() {
        UQOService.getCours().then((courses) => (this.courses = courses));
        this.getListProgramme(this.candidat.cycle);
    },
    methods: {
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
        closeCandidatDialog() {
            if (this.hasUnsavedChanges) {
                this.showWarningDialog = true;
            } else {
                this.$emit('close');
            }
        },
        onUpload() {
            this.toast.add({ severity: 'info', summary: 'Succès', detail: 'Fichier Téléversé', life: 3000 });
        },
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
        },
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
        async saveCandidat(candidat) {
            this.loading = true;
            try {
                if (this.candidatAction === 'NEW') {
                    await CandidatService.createCandidature({
                        code_permanent: candidat.code_permanent,
                        email: candidat.email,
                        nom: candidat.nom,
                        prenom: candidat.prenom,
                        cycle: candidat.cycle,
                        campus: candidat.campus,
                        programme: candidat.programme, // Send the code
                        trimestre: this.trimestre,
                        courses: candidat.candidature.map((c) => ({
                            sigle: c.sigle,
                            titre: c.titre,
                            note: c.note
                        }))
                    });
                } else if (this.candidatAction === 'EDIT') {
                    await CandidatService.updateCandidature(candidat.id, {
                        code_permanent: candidat.code_permanent,
                        email: candidat.email,
                        nom: candidat.nom,
                        prenom: candidat.prenom,
                        cycle: candidat.cycle,
                        campus: candidat.campus,
                        programme: candidat.programme, // Send the code
                        trimestre: candidat.trimestre,
                        courses: candidat.candidature.map((c) => ({
                            sigle: c.sigle,
                            titre: c.titre,
                            note: c.note
                        }))
                    });
                }
                this.$emit('save', candidat);
                this.toast.add({ severity: 'success', summary: 'Succès', detail: 'Candidat sauvegardé', life: 3000 });
            } catch (error) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: error?.response?.data?.detail || 'Impossible de sauvegarder le candidat', life: 3000 });
            } finally {
                this.loading = false;
            }
            this.confirmCandidatDialog = false;
            this.candidatDialog = false;
        }
    }
};
</script>
