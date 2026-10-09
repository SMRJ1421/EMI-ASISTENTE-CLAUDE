import type { MascotaEstado } from '../types'

// Cómo habla Emi y qué estado le toca a cada herramienta: funciones puras, sin `$`.

export const NOMBRE = 'Emi'

export const ESTADOS: readonly MascotaEstado[] = [
  'nueva',
  'pensando',
  'responde',
  'leyendo',
  'escribiendo',
  'necesita',
  'falla',
  'para',
  'terminado',
  'baile',
  'hula',
  'duerme',
]

export const FRASES: Record<MascotaEstado, readonly string[]> = {
  nueva: ['¡hola! conversación nueva', '¡empezamos!', '¿qué hacemos hoy?'],
  pensando: ['cavilando…', 'rumiando…', 'dándole vueltas…', 'maquinando…', 'atando cabos…', 'cocinando una idea…'],
  responde: ['redactando…', 'ya casi lo tengo…', 'contándotelo…'],
  leyendo: ['hojeando archivos…', 'curioseando…', 'leyendo con lupa…', 'devorando líneas…'],
  escribiendo: ['tecleando…', 'picando código…', 'manos a la obra…', 'cocinando comandos…'],
  necesita: ['¡te necesito!', '¿me echas una mano?', 'mira esto, porfa'],
  falla: ['uy, algo se atascó…', 'vaya, un tropiezo…', 'reintentando…'],
  para: ['me he mareado…', 'Claude se ha parado', 'necesito un respiro'],
  terminado: ['¡terminado!', '¡listo!', '¡misión cumplida!'],
  baile: ['¡a bailar, que acabamos!', '¡gran trabajo!', '¡fiesta!'],
  hula: ['de guardia', 'aquí estoy', 'vigilando'],
  duerme: ['zzz…', 'descansando…', 'en modo siesta'],
}

export const COLORES: Record<MascotaEstado, string> = {
  nueva: '#b79ae0',
  pensando: '#7aa7ff',
  responde: '#7aa7ff',
  leyendo: '#6fcf97',
  escribiendo: '#f2c94c',
  necesita: '#f2994a',
  falla: '#eb5757',
  para: '#eb5757',
  terminado: '#bb6bd9',
  baile: '#bb6bd9',
  hula: '#b79ae0',
  duerme: '#8a8aa0',
}

// La carita de la versión compacta (una sola línea).
export const CARAS: Record<MascotaEstado, string> = {
  nueva: '(＾▽＾)',
  pensando: '(•_•)',
  responde: '(•ᴗ•)',
  leyendo: '(•_•)📖',
  escribiendo: '(•̀ᴗ•́)⌨',
  necesita: '(°o°)❗',
  falla: '(°△°)?',
  para: '(@_@)',
  terminado: '\\(＾▽＾)/🎉',
  baile: '♪(´▽｀)♪',
  hula: '(•ᴗ•)🌺',
  duerme: '(－_－)zzZ',
}

// Cuánto dura cada estado pasajero antes de volver a la guardia (ms).
export const DURACION: Partial<Record<MascotaEstado, number>> = {
  nueva: 6000,
  terminado: 9000,
  baile: 12000,
  para: 15000,
  falla: 5000,
}

export const SIESTA = 5 * 60000

export function frase(estado: MascotaEstado, desde: number, ahora: number): string {
  const lista = FRASES[estado]
  const vuelta = Math.floor(Math.max(0, ahora - desde) / 7000)
  return lista[(Math.floor(desde / 1000) + vuelta) % lista.length] ?? ''
}

const LEE = new Set([
  'Read',
  'Glob',
  'Grep',
  'WebFetch',
  'WebSearch',
  'NotebookRead',
  'ToolSearch',
  'ListMcpResourcesTool',
  'ReadMcpResourceTool',
  'ReadMcpResourceDirTool',
])
const ESCRIBE = new Set(['Edit', 'Write', 'NotebookEdit', 'Bash', 'PowerShell'])
const ESCRIBE_MCP = /(create|update|delete|write|post|send|set|add|upload|buy|stage|run|kill|patch|put|reply|forward|label|trash|move|share|copy|apply|publish|assign|start|stop|restore|retry|invalidate)/i

export function estadoDeHerramienta(tool: string): MascotaEstado {
  if (tool === 'AskUserQuestion' || tool === 'ExitPlanMode') {
    return 'necesita'
  }
  if (LEE.has(tool)) {
    return 'leyendo'
  }
  if (ESCRIBE.has(tool)) {
    return 'escribiendo'
  }
  if (tool.startsWith('mcp__')) {
    const accion = tool.split('__').slice(2).join('__')
    return ESCRIBE_MCP.test(accion) ? 'escribiendo' : 'leyendo'
  }
  return 'pensando'
}

export function cortar(texto: string, max: number): string {
  const una = texto.replace(/\s+/g, ' ').trim()
  return una.length > max ? `${una.slice(0, max - 1)}…` : una
}

const ultimo = (ruta: string) => ruta.split(/[\\/]/).filter(Boolean).pop() ?? ruta

// Una pista corta de lo que hace la herramienta: el archivo, el patrón, el comando.
export function detalleDe(tool: string, e: Record<string, unknown>): string {
  const texto = (k: string) => (typeof e[k] === 'string' ? (e[k] as string) : '')
  const archivo = texto('file_path') || texto('notebook_path') || texto('path')
  if (['Read', 'Edit', 'Write', 'NotebookEdit'].includes(tool) && archivo) {
    return `${tool} ${cortar(ultimo(archivo), 40)}`
  }
  if (tool === 'Grep' && texto('pattern')) {
    return `Grep «${cortar(texto('pattern'), 36)}»`
  }
  if (tool === 'Glob' && texto('pattern')) {
    return `Glob ${cortar(texto('pattern'), 40)}`
  }
  if ((tool === 'Bash' || tool === 'PowerShell') && texto('command')) {
    return `${tool} ${cortar(texto('command'), 44)}`
  }
  if (tool === 'WebFetch' && texto('url')) {
    return `WebFetch ${cortar(texto('url').replace(/^https?:\/\//, ''), 40)}`
  }
  if (tool === 'WebSearch' && texto('query')) {
    return `WebSearch «${cortar(texto('query'), 36)}»`
  }
  if (tool === 'AskUserQuestion') {
    return 'tiene una pregunta para ti'
  }
  if (tool === 'ExitPlanMode') {
    return 'te pide aprobar el plan'
  }
  if (tool.startsWith('mcp__')) {
    return cortar(tool.split('__').slice(1).join(' · ').replace(/_/g, ' '), 48)
  }
  return tool
}
