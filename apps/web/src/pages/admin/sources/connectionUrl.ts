import type { DatabaseConnector } from '../../../types/index.ts'

// Módulo: a URL de conexão colada no topo do formulário vira os campos. Sem React (connectionUrl.test.ts).

export type ParsedConnection = {
    connector: DatabaseConnector
    host: string
    port: number | null
    database: string
    user: string
    password: string
    ssl: boolean | null // null = a URL não diz
}

const SCHEMES: Record<string, DatabaseConnector> = {
    'postgres:': 'postgres',
    'postgresql:': 'postgres',
    'mysql:': 'mysql',
}

// 'postgresql://user:senha@db.x.com:5432/banco?sslmode=require' -> campos; o que não é URL de banco = null.
export function parseConnectionUrl(text: string): ParsedConnection | null {
    let url: URL
    try {
        url = new URL(text.trim())
    } catch {
        return null
    }
    const connector = SCHEMES[url.protocol]
    if (!connector || !url.hostname) return null
    const decode = (v: string) => {
        try {
            return decodeURIComponent(v)
        } catch {
            return v
        }
    }
    const sslParam = (url.searchParams.get('sslmode') ?? url.searchParams.get('ssl-mode') ?? '').toLowerCase()
    return {
        connector,
        host: url.hostname.replace(/^\[|\]$/g, ''),
        port: url.port ? Number(url.port) : null,
        database: decode(url.pathname.replace(/^\//, '')),
        user: decode(url.username),
        password: decode(url.password),
        ssl: sslParam ? !['disable', 'disabled', 'false', 'off'].includes(sslParam) : null,
    }
}

export const DEFAULT_PORT: Record<DatabaseConnector, number> = { postgres: 5432, mysql: 3306 }

// O SQL que a TI manda para o cliente criar o usuário só de leitura (passo "Como pedir o acesso").
export function readOnlySql(connector: DatabaseConnector, database: string, egressIp: string | null): string {
    const db = database.trim() || 'banco_da_operacao'
    if (connector === 'mysql') {
        const host = egressIp ?? 'IP_DO_LEXHUB'
        return [
            `CREATE USER 'lexhub_leitura'@'${host}' IDENTIFIED BY 'troque-esta-senha';`,
            `GRANT SELECT, SHOW VIEW ON \`${db}\`.* TO 'lexhub_leitura'@'${host}';`,
        ].join('\n')
    }
    return [
        "CREATE USER lexhub_leitura WITH PASSWORD 'troque-esta-senha';",
        `GRANT CONNECT ON DATABASE "${db}" TO lexhub_leitura;`,
        'GRANT USAGE ON SCHEMA public TO lexhub_leitura;',
        'GRANT SELECT ON ALL TABLES IN SCHEMA public TO lexhub_leitura;',
        'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO lexhub_leitura;',
        "ALTER USER lexhub_leitura SET statement_timeout = '60s';",
    ].join('\n')
}
