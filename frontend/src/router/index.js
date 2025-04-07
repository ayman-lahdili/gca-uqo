import AppLayout from '@/layout/AppLayout.vue';
import { CampagneService } from '@/service/CampagneService';
import { createRouter, createWebHistory } from 'vue-router';

// Simple flag to avoid fetching on every navigation
let initialCampagneCheckPerformed = false;
let userHasCampagnes = false;

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/login',
            name: 'Login',
            component: () => import('@/views/pages/auth/Login.vue'),
            meta: { requiresAuth: false } // Pas d'authentification requise pour la page de login
        },
        {
            path: '/premiere-visite',
            name: 'CreateFirstCampagne',
            component: () => import('@/views/pages/CreateFirstCampagnePage.vue'),
            meta: { requiresAuth: false }
        },
        {
            path: '/',
            component: AppLayout,
            meta: { requiresAuth: true }, // Authentification requise pour les pages sous Layout
            children: [
                {
                    path: '/',
                    name: 'dashboard',
                    component: () => import('@/views/Dashboard.vue')
                },
                {
                    path: '/campagnes',
                    name: 'campagnes',
                    component: () => import('@/views/pages/Campagnes.vue')
                },
                {
                    path: '/candidatures',
                    name: 'candidatures',
                    component: () => import('@/views/pages/Candidatures.vue')
                },
                {
                    path: '/logs',
                    name: 'logs',
                    component: () => import('@/views/pages/Logs.vue')
                },
                {
                    path: '/users',
                    name: 'users',
                    component: () => import('@/views/pages/Users.vue')
                }
            ]
        }
    ]
});

export function resetCampagneCheckFlag() {
    initialCampagneCheckPerformed = false;
    userHasCampagnes = false;
    // Also clear relevant localStorage if you used it instead of variables
}

// Vérification de l'authentification avant chaque navigation
router.beforeEach(async (to, from, next) => {
    const isAuthenticated = !!localStorage.getItem('email'); // Use a more robust auth check if possible

    if (to.meta.requiresAuth) {
        if (!isAuthenticated) {
            // User is not logged in, redirect to login
            resetCampagneCheckFlag(); // Reset flag if redirecting to login
            next({ name: 'Login', query: { redirect: to.fullPath } }); // Optional: redirect back after login
        } else {
            // User is logged in, check for campagnes IF NOT already checked
            if (!initialCampagneCheckPerformed) {
                try {
                    const campagnes = await CampagneService.getCampagnes();
                    userHasCampagnes = campagnes && campagnes.length > 0;
                    initialCampagneCheckPerformed = true; // Mark check as done for this session
                } catch (error) {
                    console.error('Failed initial campagne check:', error);
                    // Decide how to handle errors - maybe let them proceed? Or show error page?
                    // For now, let's assume error means proceed to dashboard cautiously
                    userHasCampagnes = true; // Or false depending on desired error behavior
                    initialCampagneCheckPerformed = true;
                }
            }

            // Now perform the redirect check based on the fetched status
            if (!userHasCampagnes && to.name !== 'CreateFirstCampagne') {
                // If user has no campagnes and is trying to access any authenticated page *other* than the creation page, redirect them.
                next({ name: 'CreateFirstCampagne' });
            } else if (userHasCampagnes && to.name === 'CreateFirstCampagne') {
                // If user *has* campagnes, don't let them go back to the 'create first' page, send to dashboard.
                next({ name: 'dashboard' });
            } else {
                // User has campagnes, or is going to the creation page when they have none: Allow navigation
                next();
            }
        }
    } else {
        // Route does not require authentication (e.g., Login page)
        // Optional: If user is already logged in and tries to access Login page, redirect them to dashboard
        if (isAuthenticated && to.name === 'Login') {
            next({ name: 'dashboard' });
        } else {
            next();
        }
    }
});

export default router;
