<template>
    <div>
        <div class="flex justify-between p-4">
            <h3>{{ getCampagneDialogTitle(campagneAction) }}</h3>
            <Button icon="pi pi-times" variant="text" rounded severity="secondary" class="mb-4" @click="closeCampagneDialog" />
        </div>
        <div class="flex flex-col gap-4">
            <!-- Config Section -->
            <Fieldset legend="Configuration de la campagne" toggleable>
                <div class="flex flex-row gap-4 items-center justify-center">
                    <div>
                        <h4>Échelle salariale</h4>
                        <div class="flex flex-col gap-2 pt-1">
                            <div v-for="n in 3">
                                <label class="text-sm mb-1 block">Cycle {{ n }}</label>
                                <InputNumber v-model="campagne.config.echelle_salariale[n - 1]" mode="decimal" :min="0" :placeholder="'Cycle ' + n" />
                            </div>
                        </div>
                    </div>
                    <div class="flex flex-col items-center justify-center">
                        <h4>Heure par activité</h4>
                        <div v-for="(values, activity) in campagne.config.activite_heure" :key="activity" class="flex flex-col gap-2 items-center justify-center">
                            <label class="text mb-1 block">{{ activity }}</label>
                            <div class="flex gap-4 mb-5">
                                <div>
                                    <label class="text-sm mb-1 block">Heures de préparation</label>
                                    <InputNumber v-model="values.preparation" mode="decimal" :min="0" placeholder="Préparation" />
                                </div>
                                <div>
                                    <label class="text-sm mb-1 block">Durée de la scéance</label>
                                    <InputNumber v-model="values.travail" mode="decimal" :min="0" placeholder="Travail" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </Fieldset>
            <Button v-if="campagneAction === 'EDIT' && campagne.status === 'en_cours'" label="Conclure" icon="pi pi-stop-circle" class="mx-2" outlined severity="danger" @click="campagne.status = 'cloturee'" />
            <Button v-else-if="campagneAction === 'EDIT' && campagne.status === 'cloturee'" label="Réactiver" icon="pi pi-play-circle" class="mx-2" outlined severity="success" @click="campagne.status = 'en_cours'" />
            <div class="flex justify-between mx-2">
                <div class="flex gap-4 justify-between">
                    <Select v-if="campagneAction === 'NEW'" id="trimestre" v-model="campagne.trimestre" :options="optionTrimestre" optionLabel="value" placeholder="Sélectionner un trimestre" :disabled="campagne.trimestre !== ''" />
                    <div v-if="campagne.trimestre !== ''">
                        <InputText v-model="sigle" type="text" placeholder="Sigle" maxlength="8" style="border-start-end-radius: 0; border-end-end-radius: 0" @keyup.enter="addCourse(sigle)" />
                        <Button label="Ajouter" @click="addCourse(sigle)" :disabled="sigle.length < 7" style="border-start-start-radius: 0; border-end-start-radius: 0" :loading="isSearchingCourse" />
                    </div>
                </div>
                <Button v-if="campagne.trimestre !== '' && campagneAction === 'NEW'" label="Commencer la campagne" icon="pi pi-arrow-right" iconPos="right" variant="text" class="" @click="openConfirmCampagne" />
                <Button v-if="campagne.trimestre !== '' && campagneAction === 'EDIT'" label="Enregistrer" icon="pi pi-save" iconPos="right" variant="text" class="" @click="openConfirmCampagne" />
            </div>
            <template v-if="campagne.trimestre !== ''">
                <DataTable :value="campagne.cours" tableStyle="min-width: 50rem" class="card">
                    <Column field="sigle" header="Sigle"></Column>
                    <Column field="titre" header="Titre"></Column>
                    <Column field="status" header="Statut">
                        <template #body="slotProps">
                            <Tag :value="slotProps.data.status === 'CONFIRME' ? 'Confirmé' : 'Non confirmé'" :severity="slotProps.data.status === 'CONFIRME' ? 'success' : 'warn'" />
                        </template>
                    </Column>
                    <Column :exportable="false" style="max-width: 1rem">
                        <template #body="slotProps">
                            <Button icon="pi pi-trash" outlined rounded severity="danger" @click="removeCourse(slotProps.data.sigle)" />
                        </template>
                    </Column>
                </DataTable>
            </template>
        </div>

        <Dialog v-model:visible="confirmCampagneDialog" :style="{ width: '450px' }" header="Confirmation" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span v-if="campagneAction === 'EDIT'">
                    Êtes-vous sûr de vouloir appliquer les modifications sur le trimestre
                    <b>{{ formatTrimestre(campagne.trimestre) }}</b> ?
                </span>
                <span v-if="campagneAction === 'NEW'">
                    Êtes-vous sûr de vouloir créer une campagne pour le trimestre
                    <b>{{ formatTrimestre(campagne.trimestre.label) }}</b> ?
                </span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="confirmCampagneDialog = false" />
                <Button label="Yes" icon="pi pi-check" @click="saveCampagne(campagne)" />
            </template>
        </Dialog>

        <Dialog v-model:visible="showWarningDialog" :style="{ width: '450px' }" header="Confirmation" :modal="true">
            <div class="flex items-center gap-4">
                <i class="pi pi-exclamation-triangle !text-3xl" />
                <span>Êtes-vous sûr de vouloir quitter ? Les modifications non enregistrées seront perdues.</span>
            </div>
            <template #footer>
                <Button label="No" icon="pi pi-times" text @click="showWarningDialog = false" />
                <Button label="Yes" icon="pi pi-check" @click="confirmCloseCampagneDialog" />
            </template>
        </Dialog>
    </div>
</template>

<script>
import { CampagneService } from '@/service/CampagneService';
import { UQOService } from '@/service/UQOService';
import { useToast } from 'primevue/usetoast';

export default {
    props: {
        campagne: {
            type: Object,
            required: true,
            default: () => ({
                trimestre: '',
                status: 'en_cours',
                config: {
                    echelle_salariale: [18.85, 24.49, 26.48],
                    activite_heure: {
                        'Travaux dirigés': { preparation: 1.0, travail: 2.0 },
                        'Travaux pratiques': { preparation: 2.0, travail: 3.0 }
                    }
                },
                cours: []
            })
        },
        campagneAction: {
            type: String,
            required: true,
            validator: (value) => ['NEW', 'EDIT', 'VIEW'].includes(value)
        }
    },
    emits: ['save', 'close', 'update:campagne'],
    data() {
        return {
            toast: useToast(),
            sigle: '',
            confirmCampagneDialog: false,
            showWarningDialog: false,
            hasUnsavedChanges: false,
            optionTrimestre: [],
            trimestres: [],
            isSearchingCourse: false // New loading state
        };
    },
    mounted() {
        CampagneService.getListTrimestre()
            .then((trimestres) => (this.trimestres = trimestres))
            .then(() => {
                this.setOptionTrimestre();
            });
    },
    methods: {
        setOptionTrimestre() {
            const currentDate = new Date();
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth();
            let session;

            if (month < 6) {
                session = 1;
            } else if (month < 9) {
                session = 2;
            } else {
                session = 3;
            }

            let current = year * 10 + session;
            let sequence = [];
            const n = 3;

            for (let i = 0; i <= n; i++) {
                sequence.push({
                    label: current,
                    value: this.formatTrimestre(current)
                });

                // Increment by 1 for the first three numbers, then jump by 8
                if ((i + 1) % 3 === 0) {
                    current += 8;
                } else {
                    current += 1;
                }
            }

            // Assuming you pass the existing campagnes from parent component
            console.log(this.trimestres);
            this.optionTrimestre = sequence.filter((val) => !this.trimestres.includes(val.label));
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
        getCampagneDialogTitle(candidatAction) {
            switch (candidatAction) {
                case 'EDIT':
                    return "Modification des configurations d'une campagne";
                case 'NEW':
                    return "Création d'une nouvelle campagne";
                case 'VIEW':
                    return "Visionnement des configuration d'une campagne";
                default:
                    break;
            }
        },
        async addCourse(sigle) {
            if (sigle.length < 7) {
                this.toast.add({ severity: 'warn', summary: 'Attention', detail: 'Le sigle doit contenir 7 caractères', life: 2000 });
                return;
            }

            if (this.campagne.cours.find((val) => val.sigle === sigle) !== undefined) {
                this.toast.add({ severity: 'warn', summary: 'Attention', detail: 'Vous avez déjà ajouter ce cours', life: 2000 });
                return;
            }

            this.isSearchingCourse = true; // Start loading
            try {
                const cours = await UQOService.getCours();

                let title = 'Cours introuvable';
                const foundCourse = cours.find((course) => course.sigle === sigle);
                if (foundCourse) {
                    title = foundCourse.titre;
                }

                this.campagne.cours.push({
                    sigle: sigle,
                    titre: title,
                    status: foundCourse ? 'CONFIRME' : 'NONCONFIRME'
                });
                this.hasUnsavedChanges = true;
                this.$emit('update:campagne', this.campagne);
            } catch (error) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: 'Erreur lors de la recherche du cours', life: 3000 });
            } finally {
                this.isSearchingCourse = false; // End loading
            }
        },
        removeCourse(sigle) {
            this.campagne.cours = this.campagne.cours.filter((val) => val.sigle !== sigle);
            this.hasUnsavedChanges = true;
            this.$emit('update:campagne', this.campagne);
        },
        closeCampagneDialog() {
            if (this.hasUnsavedChanges) {
                this.showWarningDialog = true;
            } else {
                this.$emit('close');
            }
        },
        confirmCloseCampagneDialog() {
            this.showWarningDialog = false;
            this.$emit('close');
        },
        openConfirmCampagne() {
            this.confirmCampagneDialog = true;
        },
        saveCampagne(campagne) {
            // Trimestre needs to be processed if it's a new campagne
            if (this.campagneAction === 'NEW') {
                campagne.trimestre = campagne.trimestre.label;
            }

            this.confirmCampagneDialog = false;
            this.hasUnsavedChanges = false;
            this.$emit('save', campagne);
        }
    }
};
</script>
