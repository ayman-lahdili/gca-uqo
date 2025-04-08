<template>
    <div class="relative overflow-hidden w-full min-h-screen">
        <div class="flex w-[200%] transition-transform duration-500" :class="{ '-translate-x-1/2': createCampagneDialog }">
            <!-- First Page -->
            <div class="w-1/2 flex-shrink-0 min-h-screen flex items-center justify-center">
                <div class="text-center">
                    <div class="m-auto">
                        <h3>On dirait que c'est votre première visite . . .</h3>
                        <div class="flex flex-row-reverse">
                            <Button label="Créer une nouvelle campagne" class="mr-2" icon="pi pi-arrow-right" severity="primary" iconPos="right" outlined @click="createCampagneDialog = true" />
                        </div>
                    </div>
                </div>
            </div>
            <div class="w-1/2 flex-shrink-0 overflow-hidden">
                <div class="max-w-4xl mx-auto p-4 m-4">
                    <CreateEditCampagne v-model:campagne="campagne" campagneAction="NEW" :open="showCreateCampagne" @close="closeCampagneCreation" @save="saveCampagne(campagne)" />
                </div>
            </div>
        </div>
    </div>
    <Toast />
</template>

<script>
import CreateEditCampagne from '@/components/CreateEditCampagne.vue';
import { sharedSelectState } from '@/layout/composables/sharedSelectedState';
import { CampagneService } from '@/service/CampagneService';

import { useLayout } from '@/layout/composables/layout';

export default {
    components: {
        CreateEditCampagne
    },
    data() {
        return {
            showCreateCampagne: false,
            createCampagneDialog: false,
            outsideClickListener: null,
            layoutConfig: {},
            layoutState: {},
            isSidebarActive: false,
            campagne: {
                trimestre: '',
                status: 'INPROGRESS',
                cours: []
            }
        };
    },
    created() {
        // Initialize layout properties from the composable
        const layout = useLayout();
        this.layoutConfig = layout.layoutConfig;
        this.layoutState = layout.layoutState;
        this.isSidebarActive = layout.isSidebarActive;
        this.toggleMenu = layout.toggleMenu;
        this.toggleDarkMode = layout.toggleDarkMode;
        this.isDarkTheme = layout.isDarkTheme;
    },
    computed: {
        containerClass() {
            return {
                'layout-overlay': this.layoutConfig.menuMode === 'overlay',
                'layout-static': this.layoutConfig.menuMode === 'static',
                'layout-static-inactive': this.layoutState.staticMenuDesktopInactive && this.layoutConfig.menuMode === 'static',
                'layout-overlay-active': this.layoutState.overlayMenuActive,
                'layout-mobile-active': this.layoutState.staticMenuMobileActive
            };
        }
    },
    watch: {
        isSidebarActive(newVal) {
            if (newVal) {
                this.bindOutsideClickListener();
            } else {
                this.unbindOutsideClickListener();
            }
        }
    },
    methods: {
        bindOutsideClickListener() {
            if (!this.outsideClickListener) {
                this.outsideClickListener = (event) => {
                    if (this.isOutsideClicked(event)) {
                        this.layoutState.overlayMenuActive = false;
                        this.layoutState.staticMenuMobileActive = false;
                        this.layoutState.menuHoverActive = false;
                    }
                };
                document.addEventListener('click', this.outsideClickListener);
            }
        },
        unbindOutsideClickListener() {
            if (this.outsideClickListener) {
                document.removeEventListener('click', this.outsideClickListener);
                this.outsideClickListener = null;
            }
        },
        isOutsideClicked(event) {
            const sidebarEl = document.querySelector('.layout-sidebar');
            const topbarEl = document.querySelector('.layout-menu-button');

            return !(sidebarEl.isSameNode(event.target) || sidebarEl.contains(event.target) || topbarEl.isSameNode(event.target) || topbarEl.contains(event.target));
        },
        closeCampagneCreation() {
            this.createCampagneDialog = false;
            this.campagne = {
                trimestre: '',
                cours: []
            };
        },
        async saveCampagne(campagne) {
            const result = await CampagneService.createCampagne({
                trimestre: campagne.trimestre,
                cours: campagne.cours.map((c) => {
                    return { sigle: c.sigle, titre: c.titre };
                })
            });

            if (result) {
                sharedSelectState.updateTrimestreOptions(campagne.trimestre);
                sharedSelectState.setSelectedValue(campagne.trimestre);
                this.$router.push('/');
            } else {
                console.error('Erreur lors de la création de la campagne');
            }
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
        }
    },
    mounted() {
        // Check if there are any trimestres
        const trimestres = [];
        if (trimestres.length === 0) {
            this.showCreateCampagne = true;
        }
    },
    beforeUnmount() {
        // Clean up event listener when component is destroyed
        this.unbindOutsideClickListener();
    }
};
</script>
