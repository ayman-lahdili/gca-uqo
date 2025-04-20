<script setup>
import { useLayout } from '@/layout/composables/layout';
import { sharedSelectState } from '@/layout/composables/sharedSelectedState';
import { computed } from 'vue';

const { toggleMenu } = useLayout();
const formattedTrimestreOptions = computed(() => {
    return sharedSelectState.trimestreOptions.map((value) => ({
        label: formatTrimestre(value), // Use your existing formatting logic
        value: value // Keep the original numeric value
    }));
});

// Formatting function (can be moved to a utils file)
function formatTrimestre(value) {
    if (value === null || value === undefined) return '';
    const stringValue = String(value);
    const season = stringValue.charAt(4);
    const year = stringValue.substring(0, 4);
    switch (season) {
        case '1':
            return `Hiver ${year}`;
        case '2':
            return `Été ${year}`;
        case '3':
            return `Automne ${year}`;
        default:
            return stringValue; // Fallback
    }
}

function updateSelectedTrimestre() {
    sharedSelectState.setSelectedValue(sharedSelectState.selectedValue);
}
</script>

<template>
    <div class="layout-topbar">
        <div class="layout-topbar-logo-container">
            <button class="layout-menu-button layout-topbar-action" @click="toggleMenu">
                <i class="pi pi-bars"></i>
            </button>
            <router-link to="/" class="layout-topbar-logo">
                <svg version="1.1" viewBox="0 0 2048 858" xmlns="http://www.w3.org/2000/svg">
                    <path
                        transform="translate(954,40)"
                        d="m0 0h45l25 2 36 7 24 7 21 8 20 9 23 12 16 10 18 13 11 9 11 10 8 7 10 10 7 8 11 13 11 15 10 15 10 17 8 16 10 22 11 33 7 30 4 31v57l-4 30-6 26-6 20-10 27-13 27-12 20-8 12-9 12-11 14-12 13-14 14-8 7-12 10-15 11-15 10-15 9-4 3-4-2-36-27-19-14-12-9-21-16-14-10-13-10-19-14-14-10-7-4 1-2 25-2 17-3 20-6 18-8 17-10 16-12 10-9 10-10 13-17 9-15 8-17 7-21 5-24 1-13v-20l-2-16-4-20-8-22-8-16-8-14-10-13-11-12-9-9-13-10-11-7-12-7-16-7-17-6-18-4-24-2h-10l-24 2-18 4-22 8-16 8-15 9-13 10-15 14-11 13-11 16-11 21-7 19-5 21-2 10v43l5 23 5 16 8 19 10 17 12 16 9 10 9 9 17 13 13 10 38 28 20 15 19 14 21 16 14 10 21 16 19 14 16 12 38 28 16 12 19 14 20 15 19 14 13 10 19 14 21 16 15 10v3l-16 4-37 11-23 7-17 5-14 4-5 2-8 2-14 3-12 1h-11l-9-1-6-1-11-1-2-2-12-2-8-3-19-8-22-12-16-11-28-21-38-28-13-10-18-13-21-16-11-8-19-14-21-16-19-14-16-12-11-9-14-12-14-14-9-11-10-12-13-18-13-21-14-27-11-28-8-26-5-23-4-26-2-22v-25l2-22 2-16 5-26 7-25 9-25 13-28 10-18 14-21 12-16 13-15 12-13 13-12 11-9 10-8 20-14 22-13 27-13 29-11 25-7 19-4 22-3z"
                        fill="var(--primary-color)"
                    />
                    <path
                        transform="translate(1664,39)"
                        d="m0 0h39l28 3 22 4 25 6 24 8 28 12 24 13 21 14 16 12 13 11 13 12 11 11 7 8 10 12 11 15 10 15 10 17 13 26 9 24 7 22 6 26 4 27v14l1 2v38l-1 6v9l-4 26-6 27-12 36-12 26-10 19-11 17-13 18-9 11-11 12-25 25-11 9-18 13-15 10-18 10-27 13-24 9-17 5-25 6-25 4-21 2h-38l-9-2h-9l-31-5-27-7-31-11-33-16-20-12-17-12-14-11-14-12-23-23-9-11-14-18-10-15-11-19-12-24-10-26-8-26-6-29-2-14-2-19v-39l1-2 1-20 5-28 4-18 8-26 10-24 9-19 13-22 10-15 12-16 13-15 7-8 4-4h2l1-3 8-7 12-11 17-13 24-16 18-10 23-11 21-8 18-6 8-2 14-3 21-4zm4 156-21 3-16 4-21 8-15 8-15 10-10 8-13 12-14 16-12 18-8 16-8 20-5 18-3 27-2 8 2 9 3 28 8 26 8 18 8 14 10 14 11 12 17 17 19 13 16 9 16 7 18 5 15 3 19 2 3 1h11l3-1 27-3 18-5 16-6 16-8 12-7 11-8 10-9 3-2v-2l4-2 1-3h2l7-8 8-10 7-10 12-23 6-16 6-23 2-17v-28l-2-19-7-25-6-15-8-16-9-14-8-10-9-10-13-13-15-11-13-8-16-8-16-6-10-3-12-3-18-2z"
                        fill="var(--primary-color)"
                    />
                    <path
                        transform="translate(54,81)"
                        d="m0 0h139l17 1 1 1 1 344 1 16 5 25 8 20 10 15 11 12 11 9 15 9 20 8 13 3 12 1h23l11-1 17-4 15-6 14-8 9-7 10-9 9-11 9-15 6-15 4-18 2-14 1-356h155l3 1v326l-1 28-2 23-1 4-2 19-4 21-8 27-9 20-13 24-11 16-9 12-13 15-17 17-11 9-14 11-19 12-20 11-19 8-20 7-22 6-22 4-20 2-26 1-19-1-7-2-15-1-6-2-12-2-15-4-18-6-19-8-16-8-14-8-12-8-16-12-15-13-17-17-11-14-9-12-12-19-12-23-7-16-5-16-4-16-4-25-3-27-2-28v-335z"
                        fill="var(--primary-color)"
                    />
                </svg>

                <!-- <span>GCA-UQO</span> -->
            </router-link>
            <span class="mx-5 text-sm text-muted-color font-semibold"> Département d'informatique et d'ingénierie </span>
        </div>

        <div class="layout-topbar-actions">
            <div class="layout-topbar-menu hidden lg:block">
                <div class="layout-topbar-menu-content">
                    <Select
                        v-if="sharedSelectState.trimestreOptions.length > 0"
                        v-model="sharedSelectState.selectedValue"
                        @change="updateSelectedTrimestre"
                        :options="formattedTrimestreOptions"
                        optionLabel="label"
                        optionValue="value"
                        placeholder="Selectionner un trimestre"
                        class="w-full md:w-70"
                    />
                    <span v-else>Loading... {{ $router.push('/premiere-visite') }}</span>
                </div>
            </div>
        </div>
    </div>
</template>
