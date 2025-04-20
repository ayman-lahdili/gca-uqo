<script>
import AppConfigurator from './AppConfigurator.vue';
import AppMenuItem from './AppMenuItem.vue';

export default {
    components: {
        AppConfigurator,
        AppMenuItem
    },
    data() {
        return {
            model: [
                {
                    items: [
                        { label: 'Tableau de bord', icon: 'pi pi-fw pi-home', to: '/' },
                        { label: 'Campagnes', icon: 'pi pi-fw pi-list', to: '/campagnes' },
                        { label: 'Candidatures', icon: 'pi pi-fw pi-pen-to-square', to: '/candidatures' },
                        {
                            label: 'Sécurité',
                            icon: 'pi pi-fw pi-lock',
                            items: [
                                { label: 'Journaux', icon: 'pi pi-fw pi-file', to: '/logs' },
                                { label: 'Utilisateurs', icon: 'pi pi-fw pi-users', to: '/users' }
                            ]
                        }
                    ]
                }
            ],
            visible: false,
            currentUser: null
        };
    },
    mounted() {
        this.currentUser = localStorage.getItem('email');
    },
    methods: {
        disconnect() {
            console.log('User disconnected');
            localStorage.clear();
            window.location.replace('/login');
        }
    }
};
</script>

<template>
    <ul class="layout-menu flex flex-col h-full">
        <template v-for="(item, i) in model" :key="item">
            <app-menu-item v-if="!item.separator" :item="item" :index="i"></app-menu-item>
        </template>
        <div class="mt-auto">
            <Button icon="pi pi-cog" class="w-full" :label="currentUser" severity="contrast" variant="text" @click="visible = true" />

            <hr class="border-t border-surface-200 dark:border-surface-700" />

            <Button class="w-full mb-2" severity="danger" variant="text" icon="pi pi-sign-out" label="Déconnexion" @click="disconnect" />
        </div>
    </ul>
    <Dialog v-model:visible="visible" modal header="Paramètre utilisateur" class="w-100">
        <span class="text-surface-500 dark:text-surface-400 block mb-8">Syle d'affichage</span>
        <AppConfigurator></AppConfigurator>
        <div class="flex justify-end gap-2">
            <Button type="button" label="Annuler" severity="secondary" @click="visible = false"></Button>
            <Button type="button" label="Save" @click="visible = false"></Button>
        </div>
    </Dialog>
</template>

<style lang="scss" scoped></style>
