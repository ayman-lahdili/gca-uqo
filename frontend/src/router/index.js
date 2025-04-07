import AppLayout from '@/layout/AppLayout.vue';
import { createRouter, createWebHistory } from 'vue-router';

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
            meta: { requiresAuth: true }
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

// Vérification de l'authentification avant chaque navigation
router.beforeEach((to, from, next) => {
    const isAuthenticated = localStorage.getItem('email'); // Vérifier si l'utilisateur est "authentifié"

    if (to.meta.requiresAuth && !isAuthenticated) {
        next({ name: 'Login' }); // Rediriger vers la page de login si non authentifié
    } else {
        next();
    }
});

export default router;
