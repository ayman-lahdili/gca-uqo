<template>
    <div class="my-5">
        <!-- Show StudentLogin if not checked -->
        <StudentLogin v-if="!checked" v-model:checked="checked"></StudentLogin>

        <!-- Show CreateEditCandidature if checked -->
        <CreateEditCandidature v-else :candidat="candidat" candidatAction="NEW" :trimestre="trimestre" @save="handleSave" @close="checked = false" />
    </div>
    <Toast />
</template>

<script>
import CreateEditCandidature from '@/components/CreateEditCandidature.vue';
import { useToast } from 'primevue';
import { useRoute } from 'vue-router';
import StudentLogin from './StudentLogin.vue';

export default {
    components: {
        StudentLogin,
        CreateEditCandidature
    },
    data() {
        return {
            toast: useToast(),
            checked: false, // Tracks whether login is complete
            route: useRoute(),
            candidat: {
                code_permanent: '',
                email: '',
                nom: '',
                prenom: '',
                campus: 'gatineau',
                cycle: 1,
                programme: '',
                candidature: []
            },
            trimestre: ''
        };
    },
    mounted() {
        this.trimestre = this.$route.params.trimestre;
    },
    methods: {
        handleSave() {
            // Handle save logic here
        },
        handleClose() {
            // Handle close logic here
        }
    }
};
</script>
