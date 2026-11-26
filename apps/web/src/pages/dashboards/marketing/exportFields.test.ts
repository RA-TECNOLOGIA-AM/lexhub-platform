import { describe, expect, it } from 'vitest'
import { allSlugs } from '../../../lib/exportFields.ts'
import { marketingExport } from '../marketing-lexpre/exportFields.ts'
import { marketingNgExport } from './exportFields.ts'

describe('Marketing (banco NG): relatórios', () => {
    it('Leads = os do Marketing (LexPre) com a Base na frente; Facebook Ads igual', () => {
        const [leads, facebook] = marketingNgExport
        expect(leads.key).toBeNull()
        expect(allSlugs(leads.groups)).toEqual(['base', ...allSlugs(marketingExport[0].groups)])
        expect(facebook).toEqual(marketingExport[1])
    })
})
