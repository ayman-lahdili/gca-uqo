<script>
import CreateEditCampagne from '@/components/CreateEditCampagne.vue';
import { useLayout } from '@/layout/composables/layout';
import { sharedSelectState } from '@/layout/composables/sharedSelectedState';
import AppFooter from './AppFooter.vue';
import AppSidebar from './AppSidebar.vue';
import AppTopbar from './AppTopbar.vue';

export default {
    components: {
        CreateEditCampagne,
        AppFooter,
        AppSidebar,
        AppTopbar
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
        },
        sharedValueFromGlobalState() {
            return sharedSelectState.selectedValue;
        }
    },
    watch: {
        isSidebarActive(newVal) {
            if (newVal) {
                this.bindOutsideClickListener();
            } else {
                this.unbindOutsideClickListener();
            }
        },
        // Watch the computed property that tracks the shared state
        sharedValueFromGlobalState(newValue, oldValue) {
            // You can trigger actions here when the value changes, e.g., automatically fetch data
            // this.fetchData();
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
        }
    },
    mounted() {
        // Check if there are any trimestres
        const trimestres = [20241];
        if (trimestres.length === 0) {
            this.showCreateCampagne = true;
        }
    },
    beforeUnmount() {
        // Clean up event listener when component is destroyed
        this.unbindOutsideClickListener();
    },
    saveCampagne(campagne) {
        if (this.campagneAction === 'NEW') {
            this.campagnes.push(campagne);
        }
        this.campagneDialog = false;
        this.campagne = {};
        this.selectedCampagne = null;
    }
};
</script>

<template>
    <div class="layout-wrapper" :class="containerClass">
        <app-topbar></app-topbar>
        <app-sidebar></app-sidebar>
        <div class="layout-main-container">
            <div class="layout-main">
                <router-view v-if="sharedValueFromGlobalState"></router-view>
                <template v-else>
                    <div class="text-center">
                        <div class="m-auto">
                            <h3>On dirait que c'est votre première visite . . .</h3>
                            <div class="flex flex-row-reverse">
                                <Button label="Créer une nouvelle campagne" class="mr-2" icon="pi pi-arrow-right" severity="primary" iconPos="right" outlined @click="createCampagneDialog = true" />
                            </div>
                        </div>
                    </div>
                </template>
            </div>
            <app-footer></app-footer>
        </div>
        <div class="layout-mask animate-fadein"></div>
    </div>
    <Toast />
</template>
