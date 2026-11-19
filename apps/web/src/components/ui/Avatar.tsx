import { useState } from 'react'
import { dataClient } from '../../services/client.ts'
import type { User } from '../../types/index.ts'

type AvatarProps = {
    user: Pick<User, 'name' | 'initials' | 'avatar_path'>
    className?: string // classe do círculo (ex.: 'av' da barra lateral, 'profile-av' do cartão)
}

// Módulo: o círculo do usuário. Com foto (avatar_path), mostra a foto; sem foto ou se ela não carregar,
// as iniciais. Quem decide tamanho e cor é a classe de quem usa.
export function Avatar({ user, className = 'av' }: AvatarProps) {
    const [broken, setBroken] = useState<string | null>(null) // caminho que falhou ao carregar
    const path = user.avatar_path
    if (!path || broken === path) return <span className={className}>{user.initials}</span>
    return (
        <span className={`${className} has-photo`}>
            <img src={dataClient.avatarUrl(path)} alt="" onError={() => setBroken(path)} />
        </span>
    )
}
