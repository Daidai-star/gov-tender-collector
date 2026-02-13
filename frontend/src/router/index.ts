import { createRouter, createWebHistory } from 'vue-router';

import DashboardPage from '../pages/DashboardPage.vue';
import LoginPage from '../pages/LoginPage.vue';
import NoticeDetailPage from '../pages/NoticeDetailPage.vue';
import NoticesPage from '../pages/NoticesPage.vue';
import SitesPage from '../pages/SitesPage.vue';
import UsersPage from '../pages/UsersPage.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginPage },
    { path: '/', component: DashboardPage },
    { path: '/notices', component: NoticesPage },
    { path: '/notices/:id', component: NoticeDetailPage },
    { path: '/sites', component: SitesPage },
    { path: '/users', component: UsersPage }
  ]
});

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token');
  if (!token && to.path !== '/login') {
    next('/login');
    return;
  }
  if (token && to.path === '/login') {
    next('/');
    return;
  }
  next();
});

export default router;
