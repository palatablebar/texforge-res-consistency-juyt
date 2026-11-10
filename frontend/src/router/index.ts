import { createRouter, createWebHistory } from 'vue-router'
import { installGuards } from './guards'
import LoginPage from '../pages/LoginPage.vue'
import RecipesPage from '../pages/RecipesPage.vue'
import RecipeEditorPage from '../pages/RecipeEditorPage.vue'
import PreviewPage from '../pages/PreviewPage.vue'
import VariantsPage from '../pages/VariantsPage.vue'
import PacksPage from '../pages/PacksPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/recipes' },
    { path: '/login', component: LoginPage },
    { path: '/recipes', component: RecipesPage },
    { path: '/recipes/:id/editor', component: RecipeEditorPage, props: true },
    { path: '/preview', component: PreviewPage },
    { path: '/variants', component: VariantsPage },
    { path: '/packs', component: PacksPage },
    { path: '/:pathMatch(.*)*', redirect: '/recipes' },
  ],
})

installGuards(router)

export default router
