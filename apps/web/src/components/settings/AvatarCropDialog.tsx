import { useEffect, useLayoutEffect, useMemo, useRef, useState, type KeyboardEvent, type PointerEvent } from 'react'
import {
    clampZoom,
    computeMediaSize,
    cropDiameter,
    getCropArea,
    MAX_ZOOM,
    MIN_ZOOM,
    restrictPosition,
    zoomAtPoint,
    ZOOM_BUTTON_STEP,
    ZOOM_WHEEL_STEP,
    type CropArea,
    type Point,
    type Size,
} from '../../lib/avatarCrop.ts'
import { Icon } from '../ui/Icon.tsx'

type AvatarCropDialogProps = {
    src: string // a foto escolhida (URL local do arquivo)
    busy: boolean // enviando: trava os botões
    error: string | null // erro do envio, mostrado acima dos botões
    onCancel: () => void
    onChange: () => void // "Trocar": escolher outra foto
    onSave: (area: CropArea) => void // a área da foto original dentro do círculo
}

const KEY_STEP = 10 // px por seta

// Módulo: "Ajustar foto do perfil" (copiado do LexFlow, avatar-crop-modal.tsx): arrastar move, rolagem dá
// zoom no ponto do cursor, barra com −/slider/+. O cálculo fica em lib/avatarCrop.ts. Abre como <dialog>
// (por cima de Configurações); Esc e ✕ cancelam. Cores por var(--...): segue o tema.
export function AvatarCropDialog({ src, busy, error, onCancel, onChange, onSave }: AvatarCropDialogProps) {
    const dialog = useRef<HTMLDialogElement>(null)
    const area = useRef<HTMLDivElement>(null)
    const drag = useRef<{ x: number; y: number; start: Point } | null>(null)
    const [media, setMedia] = useState<Size>({ width: 0, height: 0 })
    const [container, setContainer] = useState<Size>({ width: 0, height: 0 })
    const [pos, setPos] = useState<Point>({ x: 0, y: 0 })
    const [zoom, setZoom] = useState(MIN_ZOOM)
    const [dragging, setDragging] = useState(false)

    const crop = cropDiameter(container)
    const size = useMemo(() => computeMediaSize(media, crop, zoom), [media, crop, zoom])
    const ready = media.width > 0 && container.width > 0
    // A área mudou de tamanho (celular girou, modal abriu): a foto continua cobrindo o círculo.
    const fitted = ready ? restrictPosition(pos, size, container, crop) : pos
    const zoomRef = useRef(zoom) // zoom atual para o listener de rolagem (registrado uma vez só)
    useLayoutEffect(() => {
        zoomRef.current = zoom
    }, [zoom])

    useLayoutEffect(() => {
        const element = dialog.current
        element?.showModal()
        return () => element?.close()
    }, [])

    // Foto nova (ou "Trocar"): mede e volta ao zoom 1, centralizada.
    useEffect(() => {
        const image = new Image()
        image.onload = () => {
            setMedia({ width: image.naturalWidth, height: image.naturalHeight })
            setPos({ x: 0, y: 0 })
            setZoom(MIN_ZOOM)
        }
        image.src = src
    }, [src])

    useEffect(() => {
        const element = area.current
        if (!element) return
        const measure = () => {
            const rect = element.getBoundingClientRect()
            setContainer({ width: rect.width, height: rect.height })
        }
        measure()
        const observer = new ResizeObserver(measure)
        observer.observe(element)
        return () => observer.disconnect()
    }, [])

    // Zoom (botões, slider, rolagem, teclado) mantendo parado o ponto indicado (padrão: o centro).
    function applyZoom(next: number, pointer?: Point) {
        const clamped = clampZoom(next)
        if (ready) {
            const anchor = pointer ?? { x: container.width / 2, y: container.height / 2 }
            setPos(zoomAtPoint(zoom, clamped, fitted, container, crop, media, anchor))
        }
        setZoom(clamped)
    }
    const applyZoomRef = useRef(applyZoom)
    useLayoutEffect(() => {
        applyZoomRef.current = applyZoom
    })

    // Rolagem: listener nativo (não passivo) para o preventDefault segurar a página.
    useEffect(() => {
        const element = area.current
        if (!element) return
        const onWheel = (event: WheelEvent) => {
            event.preventDefault()
            const rect = element.getBoundingClientRect()
            const delta = event.deltaY < 0 ? ZOOM_WHEEL_STEP : -ZOOM_WHEEL_STEP
            applyZoomRef.current(zoomRef.current + delta, {
                x: event.clientX - rect.left,
                y: event.clientY - rect.top,
            })
        }
        element.addEventListener('wheel', onWheel, { passive: false })
        return () => element.removeEventListener('wheel', onWheel)
    }, [])

    function onPointerDown(event: PointerEvent<HTMLDivElement>) {
        if (busy) return
        event.currentTarget.setPointerCapture(event.pointerId)
        drag.current = { x: event.clientX, y: event.clientY, start: fitted }
        setDragging(true)
    }
    function onPointerMove(event: PointerEvent<HTMLDivElement>) {
        const start = drag.current
        if (!start) return
        const next = { x: start.start.x + event.clientX - start.x, y: start.start.y + event.clientY - start.y }
        setPos(restrictPosition(next, size, container, crop))
    }
    function onPointerUp() {
        drag.current = null
        setDragging(false)
    }

    function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
        const moves: Record<string, Point> = {
            ArrowLeft: { x: -KEY_STEP, y: 0 },
            ArrowRight: { x: KEY_STEP, y: 0 },
            ArrowUp: { x: 0, y: -KEY_STEP },
            ArrowDown: { x: 0, y: KEY_STEP },
        }
        const move = moves[event.key]
        if (move) {
            event.preventDefault()
            setPos(restrictPosition({ x: fitted.x + move.x, y: fitted.y + move.y }, size, container, crop))
        } else if (event.key === '+' || event.key === '=') {
            applyZoom(zoom + ZOOM_BUTTON_STEP)
        } else if (event.key === '-') {
            applyZoom(zoom - ZOOM_BUTTON_STEP)
        }
    }

    function save() {
        if (!ready || busy) return
        onSave(getCropArea(media, container, crop, zoom, fitted))
    }

    const percent = Math.round(((zoom - MIN_ZOOM) / (MAX_ZOOM - MIN_ZOOM)) * 100)
    const mask = `radial-gradient(circle ${crop / 2}px at center, transparent 99.6%, black 100%)`

    return (
        <dialog
            ref={dialog}
            className="export-dialog crop-dialog"
            aria-label="Ajustar foto do perfil"
            onCancel={(event) => {
                event.preventDefault()
                if (!busy) onCancel()
            }}
        >
            <header className="crop-head">
                <button
                    className="iconbtn crop-ghost"
                    type="button"
                    aria-label="Cancelar"
                    disabled={busy}
                    onClick={onCancel}
                >
                    <Icon name="close" size={18} />
                </button>
                <div className="crop-title">
                    <strong>Ajustar foto do perfil</strong>
                    <span className="small muted">Arraste para mover · Scroll para zoom</span>
                </div>
                <button className="btn crop-change" type="button" disabled={busy} onClick={onChange}>
                    <Icon name="rotateCcw" size={16} />
                    Trocar
                </button>
            </header>

            <div
                ref={area}
                className={`crop-area${dragging ? ' dragging' : ''}`}
                tabIndex={0}
                aria-label="Foto: arraste ou use as setas para mover; + e − para zoom"
                onPointerDown={onPointerDown}
                onPointerMove={onPointerMove}
                onPointerUp={onPointerUp}
                onPointerCancel={onPointerUp}
                onKeyDown={onKeyDown}
            >
                {ready && (
                    <img
                        className="crop-image"
                        src={src}
                        alt=""
                        draggable={false}
                        style={{
                            width: size.width,
                            height: size.height,
                            transform: `translate(calc(-50% + ${fitted.x}px), calc(-50% + ${fitted.y}px))`,
                        }}
                    />
                )}
                <div className="crop-mask" style={{ WebkitMaskImage: mask, maskImage: mask }} />
                <div className="crop-ring" style={{ width: crop, height: crop }} />
            </div>

            <div className="crop-tools">
                <div className="crop-zoom">
                    <Icon name="zoomIn" size={16} />
                    <button
                        className="iconbtn crop-step"
                        type="button"
                        aria-label="Diminuir zoom"
                        disabled={busy || zoom <= MIN_ZOOM}
                        onClick={() => applyZoom(zoom - ZOOM_BUTTON_STEP)}
                    >
                        <Icon name="minus" size={16} />
                    </button>
                    <div className="crop-slider">
                        <input
                            type="range"
                            min={MIN_ZOOM}
                            max={MAX_ZOOM}
                            step={0.01}
                            value={zoom}
                            aria-label="Zoom"
                            disabled={busy}
                            onChange={(event) => applyZoom(Number(event.target.value))}
                        />
                        <span className="crop-percent">{percent}%</span>
                    </div>
                    <button
                        className="iconbtn crop-step"
                        type="button"
                        aria-label="Aumentar zoom"
                        disabled={busy || zoom >= MAX_ZOOM}
                        onClick={() => applyZoom(zoom + ZOOM_BUTTON_STEP)}
                    >
                        <Icon name="plus" size={16} />
                    </button>
                </div>
                {error && (
                    <p className="small profile-error" role="alert">
                        {error}
                    </p>
                )}
                <div className="crop-actions">
                    <button className="btn" type="button" disabled={busy} onClick={onCancel}>
                        Cancelar
                    </button>
                    <button className="btn btn-primary" type="button" disabled={busy || !ready} onClick={save}>
                        {busy ? (
                            'Salvando…'
                        ) : (
                            <>
                                <Icon name="check" size={16} />
                                Salvar foto
                            </>
                        )}
                    </button>
                </div>
            </div>
        </dialog>
    )
}
