<script>
import CreateEditCampagne from '@/components/CreateEditCampagne.vue';
import StatisticsChart from '@/components/StatisticsChart.vue';
import { sharedSelectState } from '@/layout/composables/sharedSelectedState';
import { CampagneService } from '@/service/CampagneService';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';

export default {
    components: {
        StatisticsChart,
        CreateEditCampagne
    },
    data() {
        return {
            toast: useToast(),
            campagnes: [],
            campagneDialog: false,
            concludeCampagneDialog: false,
            reactivateCampagneDialog: false,
            campagne: {
                trimestre: '',
                config: {
                    echelle_salariale: [18.85, 24.49, 26.48],
                    activite_heure: {
                        'Travaux dirigés': {
                            preparation: 1.0,
                            travail: 2.0
                        },
                        'Travaux pratiques': {
                            preparation: 2.0,
                            travail: 3.0
                        }
                    }
                },
                cours: []
            },
            selectedCampagne: null,
            campagneAction: '', // NEW, EDIT
            filters: {
                global: { value: null, matchMode: FilterMatchMode.CONTAINS }
            },
            statuses: [
                { label: 'en_cours', value: 'En cours' },
                { label: 'cloturee', value: 'Clôturée' },
                { label: 'annulee', value: 'Annulée' }
            ],
            loading: false,
            sharedState: sharedSelectState
        };
    },
    mounted() {
        this.fetchCampagnes();
    },
    methods: {
        async fetchCampagnes() {
            this.loading = true; // Set loading to true
            try {
                const campagnes = await CampagneService.getCampagnes();
                this.campagnes = campagnes;

                const fetchedTrimestres = [...new Set(campagnes.map((c) => c.trimestre))];

                fetchedTrimestres.forEach((trimestre) => {
                    // Use the method from the imported shared state
                    this.sharedState.updateTrimestreOptions(trimestre);
                });
                this.sharedState.validateSelection();
            } catch (error) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: 'Impossible de charger les campagnes', life: 3000 });
            } finally {
                this.loading = false; // Set loading to false
            }
        },
        async saveCampagne() {
            this.loading = true; // Set loading to true
            try {
                let savedTrimestre = this.campagne.trimestre;
                if (this.campagneAction === 'NEW') {
                    const result = await CampagneService.createCampagne({
                        trimestre: this.campagne.trimestre,
                        config: this.campagne.config,
                        cours: this.campagne.cours.map((c) => {
                            return { sigle: c.sigle, titre: c.titre };
                        })
                    });

                    if (result) {
                        // Use shared state methods AFTER successful creation
                        this.sharedState.updateTrimestreOptions(savedTrimestre);
                        this.sharedState.setSelectedValue(savedTrimestre); // Optionally select the new one
                    }
                } else if (this.campagneAction === 'EDIT') {
                    let data = {
                        status: this.campagne.status,
                        config: this.campagne.config,
                        cours: this.campagne.cours.map((c) => {
                            return { sigle: c.sigle, titre: c.titre };
                        })
                    };
                    await CampagneService.updateCampagne(this.campagne.trimestre, data);
                }
                this.toast.add({ severity: 'success', summary: 'Succès', detail: 'Campagne sauvegardée', life: 3000 });
                await this.fetchCampagnes(); // Reload the table
            } catch (error) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: 'Impossible de sauvegarder la campagne', life: 3000 });
            } finally {
                this.loading = false; // Set loading to false
            }
            this.campagneDialog = false;
            this.resetCampagne();
        },
        openNewCampagne() {
            this.campagneAction = 'NEW';
            this.campagneDialog = true;
            this.campagne = {
                trimestre: '',
                config: {
                    echelle_salariale: [18.85, 24.49, 26.48],
                    activite_heure: {
                        'Travaux dirigés': {
                            preparation: 1.0,
                            travail: 2.0
                        },
                        'Travaux pratiques': {
                            preparation: 2.0,
                            travail: 3.0
                        }
                    }
                },
                cours: []
            };
        },
        openEditCampagne(campagne) {
            this.campagne = campagne;
            this.campagneAction = 'EDIT';
            this.campagneDialog = true;
        },
        openConcludeCampagneDialog(campagne) {
            this.campagne = { ...campagne };
            this.concludeCampagneDialog = true;
        },
        openReactivateCampagneDialog(campagne) {
            this.campagne = { ...campagne };
            this.reactivateCampagneDialog = true;
        },
        async closeCreateEditCampagne() {
            this.selectedCampagne = null;
            this.campagneDialog = false;
            await this.fetchCampagnes();
        },
        resetCampagne() {
            this.campagne = {
                trimestre: '',
                config: {
                    echelle_salariale: [18.85, 24.49, 26.48],
                    activite_heure: {
                        'Travaux dirigés': {
                            preparation: 1.0,
                            travail: 2.0
                        },
                        'Travaux pratiques': {
                            preparation: 2.0,
                            travail: 3.0
                        }
                    }
                },
                cours: []
            };
        },
        async concludeCampagne() {
            this.loading = true; // Set loading to true
            try {
                await CampagneService.updateCampagne(this.campagne.trimestre, { status: 'cloturee' });
                this.toast.add({ severity: 'success', summary: 'Succès', detail: 'Campagne clôturée', life: 3000 });
                await this.fetchCampagnes(); // Reload the table
                this.selectedCampagne = null;
            } catch (error) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: 'Impossible de clôturer la campagne', life: 3000 });
            } finally {
                this.loading = false; // Set loading to false
            }
            this.concludeCampagneDialog = false;
        },
        async reactivateCampagne() {
            this.loading = true; // Set loading to true
            try {
                await CampagneService.updateCampagne(this.campagne.trimestre, { status: 'en_cours' });
                this.toast.add({ severity: 'success', summary: 'Succès', detail: 'Campagne réactivée', life: 3000 });
                await this.fetchCampagnes(); // Reload the table
                this.selectedCampagne = null;
            } catch (error) {
                this.toast.add({ severity: 'error', summary: 'Erreur', detail: 'Impossible de réactiver la campagne', life: 3000 });
            } finally {
                this.loading = false; // Set loading to false
            }
            this.reactivateCampagneDialog = false;
        },

        // UTILS
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
        formatCurrency(value) {
            return value.toLocaleString('en-CA', { style: 'currency', currency: 'CAD' });
        },
        openCampagneFormulaire(trimestre) {
            const routeUrl = this.$router.resolve({ name: 'StudentForm', params: { trimestre: trimestre } });
            window.open(routeUrl.href, '_blank');
        }
    }
};
</script>

<template>
    <div class="relative overflow-hidden w-full">
        <!-- Pages Wrapper -->
        <div class="flex w-[200%] transition-transform duration-500" :class="{ '-translate-x-1/2': campagneDialog }">
            <!-- First Page -->
            <div class="w-1/2 flex-shrink-0">
                <div :style="campagneDialog ? { display: 'none' } : {}">
                    <div class="mb-3">
                        <Fieldset class="card" legend="Statistiques" :toggleable="true" :collapsed="false">
                            <StatisticsChart :campagnes="campagnes" />
                        </Fieldset>
                    </div>
                    <div class="card">
                        <DataTable ref="dt" v-model:selection="selectedCampagne" selectionMode="single" :value="campagnes" dataKey="id" :rows="50" :filters="filters" removableSort :loading="loading">
                            <template #header>
                                <div class="flex flex-wrap gap-2 items-center justify-between">
                                    <h3 class="m-0">Campagnes</h3>
                                    <div>
                                        <template v-if="selectedCampagne">
                                            <Button v-if="selectedCampagne.status === 'en_cours'" label="Clôturer" icon="pi pi-stop-circle" class="mr-2 mt-2" outlined severity="danger" @click="openConcludeCampagneDialog(selectedCampagne)" />
                                            <Button
                                                v-else-if="selectedCampagne && selectedCampagne.status === 'cloturee'"
                                                label="Réactiver"
                                                icon="pi pi-play-circle"
                                                class="mr-2 mt-2"
                                                outlined
                                                severity="success"
                                                @click="openReactivateCampagneDialog(selectedCampagne)"
                                            />
                                            <Button label="Modifier" icon="pi pi-pencil" class="mr-2" outlined @click="openEditCampagne(selectedCampagne)" />
                                        </template>
                                        <Button label="Créer une nouvelle campagne" class="mr-2 mt-2" icon="pi pi-plus" severity="primary" @click="openNewCampagne" />
                                        <Button icon="pi pi-refresh" class="mt-2" outlined @click="fetchCampagnes" />
                                    </div>
                                </div>
                            </template>

                            <Column field="trimestre" header="Trimestre" sortable style="min-width: 12rem">
                                <template #body="slotProps">
                                    {{ formatTrimestre(slotProps.data.trimestre) }}
                                </template>
                            </Column>
                            <Column field="cout_total" header="Coût total" :sortable="true" style="min-width: 8rem">
                                <template #body="slotProps">
                                    {{ formatCurrency(slotProps.data.stats.cout_total) }}
                                </template>
                            </Column>
                            <Column field="status" header="Statut" sortable style="min-width: 3rem">
                                <template #body="slotProps">
                                    <Tag :value="statuses.find((s) => s.label === slotProps.data.status)?.value" :severity="slotProps.data.status === 'cloturee' ? 'warn' : 'success'" />
                                </template>
                            </Column>
                            <Column :exportable="false" style="max-width: 3rem" header="Formulaire">
                                <template #body="slotProps">
                                    <Button icon="pi pi-arrow-right" outlined rounded severity="secondary" @click="openCampagneFormulaire(slotProps.data.trimestre)" :disabled="slotProps.data.status === 'cloturee'" />
                                </template>
                            </Column>
                        </DataTable>
                    </div>
                </div>

                <Dialog v-model:visible="concludeCampagneDialog" :style="{ width: '450px' }" header="Confirmation" :modal="true">
                    <div class="flex items-center gap-4">
                        <i class="pi pi-exclamation-triangle !text-3xl" />
                        <span v-if="campagne"
                            >Êtes-vous sûr de vouloir clôturer la campagne du trimestre <b>{{ campagne.trimestre }}</b> ?</span
                        >
                    </div>
                    <template #footer>
                        <Button label="Non" icon="pi pi-times" text @click="concludeCampagneDialog = false" />
                        <Button label="Oui" icon="pi pi-check" @click="concludeCampagne" />
                    </template>
                </Dialog>

                <Dialog v-model:visible="reactivateCampagneDialog" :style="{ width: '450px' }" header="Confirmation" :modal="true">
                    <div class="flex items-center gap-4">
                        <i class="pi pi-exclamation-triangle !text-3xl" />
                        <span v-if="campagne"
                            >Êtes-vous sûr de vouloir réactiver la campagne du trimestre <b>{{ campagne.trimestre }}</b> ?</span
                        >
                    </div>
                    <template #footer>
                        <Button label="Non" icon="pi pi-times" text @click="reactivateCampagneDialog = false" />
                        <Button label="Oui" icon="pi pi-check" @click="reactivateCampagne" />
                    </template>
                </Dialog>
            </div>
            <div class="w-1/2 flex-shrink-0 overflow-hidden">
                <div class="card" :style="!campagneDialog ? { display: 'none' } : {}">
                    <CreateEditCampagne v-if="campagneDialog" v-model:campagne="campagne" :campagne-action="campagneAction" @save="saveCampagne" @close="closeCreateEditCampagne" />
                </div>
            </div>
        </div>
    </div>
</template>
