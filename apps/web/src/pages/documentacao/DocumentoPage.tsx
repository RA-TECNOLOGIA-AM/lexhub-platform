import { useParams } from 'react-router'
import { StateMessage } from '../../components/states/StateMessage.tsx'
import { PageTransitionLink } from '../../components/page_transition/PageTransitionLink.tsx'
import { DOC_ENTRIES } from './docRegistry.ts'
import { DOC_PAGES } from './docPages.ts'

// Rota /:org/documentacao/:slug: procura o guia no registro e mostra o conteúdo dele.
export function DocumentoPage() {
    const { org = '', slug = '' } = useParams()
    const entry = DOC_ENTRIES.find((d) => d.slug === slug)
    const Content = DOC_PAGES[slug]

    if (!entry || !Content) {
        return (
            <StateMessage
                icon="book"
                title={entry ? `${entry.title}: em construção` : 'Documentação não encontrada'}
                action={
                    <PageTransitionLink className="btn" to={`/${org}/documentacao`}>
                        Ver todas as documentações
                    </PageTransitionLink>
                }
            >
                {entry ? 'Este guia ainda está sendo trazido da v1.' : 'Confira o endereço ou volte à lista.'}
            </StateMessage>
        )
    }
    return <Content />
}
