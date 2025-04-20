<template>
    <div>
        <div class="max-w-4xl mx-auto p-4 card">
            <template v-if="type === 'ETUD'">
                <div class="flex items-center justify-between px-6">
                    <span class="text-2xl font-bold">Formulaire de candidature</span>
                    <span class="text-2xl">{{ formatTrimestre(trimestre) }}</span>
                </div>
            </template>
            <template v-else="type === 'GEST'">
                <div class="flex items-center justify-between gap-2 mb-4">
                    <span class="text-2xl font-bold">{{ getCandidatDialogTitle(candidatAction) }}</span>
                    <Button label="Annuler" icon="pi pi-times" variant="text" class="mb-4" @click="closeCandidatDialog" />
                </div>
            </template>
            <!-- Form divided into clear sections -->
            <div class="space-y-8">
                <!-- Section 1: Identification -->
                <section class="rounded-lg p-6">
                    <h2 class="text-xl font-bold mb-4 border-b pb-2">Informations d'identification</h2>
                    <div class="space-y-4">
                        <!-- Name inputs in a row -->
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                                    :disabled="candidatAction === 'EDIT'"
                                />
                            </div>
                            <!-- Email -->
                            <div>
                                <label for="email" class="block text-sm font-medium mb-1">Adresse courriel de l'UQO</label>
                                <InputText
                                    id="email"
                                    v-model="candidat.email"
                                    class="w-full"
                                    placeholder="doej01@uqo.ca"
                                    :invalid="candidatFormState.email"
                                    @change="candidatFormState.email = false"
                                    :disabled="type === 'ETUD' || candidatAction === 'EDIT'"
                                />
                            </div>
                            <div>
                                <label for="prenom" class="block text-sm font-medium mb-1">Prénom <span class="text-red-500">*</span></label>
                                <InputText id="prenom" v-model="candidat.prenom" class="w-full" :invalid="candidatFormState.prenom" @change="candidatFormState.prenom = false" />
                            </div>
                            <div>
                                <label for="nom" class="block text-sm font-medium mb-1">Nom <span class="text-red-500">*</span></label>
                                <InputText id="nom" v-model="candidat.nom" class="w-full" :invalid="candidatFormState.nom" @change="candidatFormState.nom = false" />
                            </div>
                        </div>

                        <!-- CV Upload/Download -->
                        <div class="pt-2">
                            <label class="block text-sm font-medium mb-2">Curriculum Vitae</label>
                            <Button v-if="type !== 'ETUD'" label="Télécharger CV actuel" icon="pi pi-download" class="w-full mb-2" outlined @click="downloadResume" />
                            <FileUpload
                                ref="fileupload"
                                class="w-full"
                                name="cv"
                                accept="application/pdf"
                                :maxFileSize="5000000"
                                chooseLabel="Téléverser CV"
                                :showUploadButton="false"
                                :showCancelButton="false"
                                :previewWidth="0"
                                :disabled="$refs.fileupload?.files?.length > 0"
                            >
                                <template #content="{ files, uploadedFiles, removeUploadedFileCallback, removeFileCallback, messages }">
                                    <div v-for="(file, index) of files" :key="file.name + file.type + file.size" class="p-3 rounded-border flex flex-row border justify-between border-surface items-center gap-4">
                                        <span class="font-semibold text-ellipsis max-w-60 whitespace-nowrap overflow-hidden">{{ file.name }}</span>
                                        <div>{{ formatSize(file.size) }}</div>
                                        <Button icon="pi pi-times" @click="onRemoveTemplatingFile(file, removeFileCallback, index)" outlined rounded severity="danger" />
                                    </div>
                                </template>
                            </FileUpload>
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
                    <!-- Course table -->
                    <DataTable :value="candidat.candidature" class="p-datatable-sm" responsiveLayout="scroll" stripedRows>
                        <template #header>
                            <div class="flex flex-wrap gap-2 items-center justify-between">
                                <h2 class="text-xl pt-2">Sélection des cours d'intérêt</h2>
                                <Button label="Ajouter un cours" icon="pi pi-plus" severity="secondary" class="mr-2" @click="openNewCandidature" />
                            </div>
                        </template>
                        <Column field="sigle" header="Sigle"></Column>
                        <Column field="titre" header="Titre du cours">
                            <template #body="slotProps">
                                <span class="">{{ getCourseTitle(slotProps.data.sigle) }}</span>
                            </template>
                        </Column>
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
                    <Button
                        v-if="candidatAction !== 'VIEW'"
                        :label="type === 'ETUD' ? 'Envoyer votre candidature' : 'Enregistrer'"
                        :icon="type === 'ETUD' ? 'pi pi-send' : 'pi pi-save'"
                        severity="success"
                        class="px-4 py-2"
                        @click="openConfirmCandidat(candidat)"
                    />
                </div>
            </div>
        </div>

        <!-- Candidatures -->
        <Dialog v-model:visible="candidatureDialog" :style="{ width: '450px' }" :header="candidatureAction === 'EDIT' ? 'Modification d\'une candidature' : 'Ajout d\'une candidature'" :modal="true">
            <div class="flex flex-col gap-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label for="sigle" class="block text-sm font-medium mb-1">Sigle</label>
                        <AutoComplete
                            v-model="candidature"
                            class="w-full mt-2"
                            type="text"
                            placeholder="Sigle"
                            forceSelection
                            dropdown
                            :suggestions="campagneCoursesResults"
                            optionLabel="sigle"
                            optionValue="sigle"
                            @complete="searchCourse"
                            :disabled="candidatureAction === 'EDIT'"
                        >
                            <template #option="slotProps">
                                <div class="flex items-center">
                                    <div>{{ slotProps.option.sigle }} - {{ slotProps.option.titre }}</div>
                                </div>
                            </template>
                        </AutoComplete>
                        <!-- <InputText v-model="candidature.sigle" class="w-full mt-2" type="text" placeholder="Sigle" maxlength="8" :disabled="candidatureAction === 'EDIT'" /> -->
                    </div>
                    <div v-if="candidature?.note !== undefined">
                        <label for="note" class="block text-sm font-medium mb-1">Note</label>
                        <Select v-model="candidature.note" class="w-full mt-2" :options="['A+', 'A', 'A-', 'B+', 'B', 'B-']" default="B+" type="text" placeholder="Note" />
                    </div>
                </div>
            </div>
            <template #footer>
                <Button label="Non" icon="pi pi-times" text @click="candidatureDialog = false" />
                <Button label="Oui" icon="pi pi-check" @click="confirmEditCandidature(candidature)" :disabled="candidature.sigle === undefined || candidature?.sigle?.length < 7" />
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
                    >Êtes-vous sûr de vouloir appliquer les modifications sur le candidat
                    <b
                        >{{ candidat.prenom + ' ' + candidat.nom }} <code>{{ '(' + candidat.code_permanent + ')' }}</code></b
                    >
                    ?</span
                >
                <span v-if="candidatAction === 'NEW'">
                    <template v-if="type === 'ETUD'">
                        Êtes-vous sûr de vouloir soumettre votre candidature pour le trimestre
                        <b>{{ formatTrimestre(trimestre) }}</b> ?
                    </template>
                    <template v-else>
                        Êtes-vous sûr de vouloir ajouter le candidat
                        <b
                            >{{ candidat.prenom + ' ' + candidat.nom }} <code>{{ '(' + candidat.code_permanent + ')' }}</code></b
                        >
                        ?
                    </template>
                </span>
            </div>
            <template #footer>
                <Button label="Non" icon="pi pi-times" text @click="confirmCandidatDialog = false" />
                <Button label="Oui" icon="pi pi-check" @click="saveCandidat(candidat)" />
            </template>
        </Dialog>
    </div>
</template>

<script>
import { CampagneService } from '@/service/CampagneService';
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
            type: [Number, String],
            required: true
        },
        type: {
            type: String,
            required: false,
            default: 'GEST',
            validator: (value) => ['GEST', 'ETUD'].includes(value)
        }
    },
    emits: ['save', 'close'],
    data() {
        return {
            toast: useToast(),
            showWarningDialog: false,
            hasUnsavedChanges: false,
            courses: [],
            campagneCourses: [],
            campagneCoursesResults: [],
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
        CampagneService.getCours(this.trimestre).then((campagneCourses) => (this.campagneCourses = campagneCourses.map((course) => ({ ...course, note: 'B+' }))));
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
        getCourseTitle(sigle) {
            const foundCourse = this.courses.find((c) => c.sigle === sigle);
            return foundCourse ? foundCourse.titre : 'Cours introuvable';
        },
        onUpload() {
            console.log('Fichier téléversé');
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

            if (this.type === 'ETUD' && this.$refs.fileupload.files.length === 0) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: "Aucun CV n'a été téléversé", life: 3000 });
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
                    await CandidatService.createCandidature(
                        {
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
                        },
                        this.$refs.fileupload.files?.[0]
                    );
                } else if (this.candidatAction === 'EDIT') {
                    await CandidatService.updateCandidature(
                        candidat.id,
                        {
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
                        },
                        this.$refs.fileupload.files?.[0]
                    );
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
        formatSize(bytes) {
            const k = 1024;
            const dm = 3;
            const sizes = this.$primevue.config.locale.fileSizeTypes;

            if (bytes === 0) {
                return `0 ${sizes[0]}`;
            }

            const i = Math.floor(Math.log(bytes) / Math.log(k));
            const formattedSize = parseFloat((bytes / Math.pow(k, i)).toFixed(dm));

            return `${formattedSize} ${sizes[i]}`;
        },
        onRemoveTemplatingFile(file, removeFileCallback, index) {
            removeFileCallback(index);
            this.totalSize -= parseInt(this.formatSize(file.size));
            this.totalSizePercent = this.totalSize / 10;
        },
        searchCourse(event) {
            const query = event.query.toLowerCase();
            this.campagneCoursesResults = this.campagneCourses.filter((course) => course.sigle.toLowerCase().includes(query) || course.titre.toLowerCase().includes(query));
        },
        deleteCandidature() {
            this.candidat.candidature = this.candidat.candidature.filter((c) => c.sigle !== this.candidature.sigle);
            this.deleteCandidatureDialog = false;
            this.toast.add({ severity: 'success', summary: 'Successful', detail: 'Candidature supprimée', life: 3000 });
        },
        async downloadResume() {
            try {
                // Get a direct reference to the file from the API
                const response = await CandidatService.downloadResume(this.candidat.id, this.trimestre);

                if (response === null) {
                    this.toast.add({ severity: 'error', summary: 'Erreur', detail: "Aucun CV n'a été enregistré pour ce candidat", life: 3000 });
                    return;
                }

                // Create a blob URL for the file
                const blob = new Blob([response], { type: 'application/pdf' });
                const url = window.URL.createObjectURL(blob);

                // Create and click a download link
                const link = document.createElement('a');
                link.href = url;

                // Set a descriptive filename
                const filename = `${this.trimestre}_${this.candidat.code_permanent || this.candidat.id}_CV.pdf`;
                link.setAttribute('download', filename);

                // Trigger download
                document.body.appendChild(link);
                link.click();

                // Clean up
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(link);
                }, 100);
            } catch (error) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: 'Aucun CV de retrouver', life: 3000 });
                return;
            }
        }
    }
};
</script>
