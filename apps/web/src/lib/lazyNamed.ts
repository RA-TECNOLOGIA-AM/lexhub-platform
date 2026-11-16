import { lazy, type ComponentType } from 'react'

// Carrega sob demanda um componente exportado com nome (o React.lazy só aceita `export default`).
// Uso: const MembersPage = lazyNamed(() => import('./MembersPage.tsx'), 'MembersPage')
// O arquivo vira um chunk separado e só é baixado na 1ª vez que o componente aparece na tela;
// enquanto baixa, o <Suspense> mais próximo mostra o fallback.
export function lazyNamed<M, K extends keyof M>(loader: () => Promise<M>, name: K) {
    return lazy(async () => ({ default: (await loader())[name] as ComponentType }))
}
