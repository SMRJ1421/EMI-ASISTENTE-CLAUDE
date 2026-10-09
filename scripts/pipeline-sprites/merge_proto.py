BASE = "C:/Users/Admin0011/.claude/dev-mods/da5e8c78-c252-4d1c-9f43-47016e40a9d5/mascota-lab/hooks/"
proto = open(BASE + "proto.tsx", encoding="utf-8").read()
reg = open(BASE + "register.tsx", encoding="utf-8").read()

# 1) bloque de módulo del prototipo: desde «const PROTO» hasta antes de iniciarProto
a = proto.index("const PROTO = 'emiproto'")
b = proto.index("// El laboratorio llama a esto desde su único hook")
bloque = proto[a:b]
bloque = bloque.replace("let carpeta = ''\n", "")
bloque = bloque.replace("function informe() {", "function informeProto() {")

# 2) lo que va dentro de register: los dos hooks (command.run y ui.render)
c = proto.index("  on('command.run', { command: 'emiproto' }")
cuerpo = proto[c:]
cuerpo = cuerpo.rstrip()
assert cuerpo.endswith("}")
cuerpo = cuerpo[:-1].rstrip() + "\n"          # quita la llave de cierre de register
cuerpo = cuerpo.replace("informe()", "informeProto()")

# 3) lo que va dentro de session.start
inicio_proto = '''    await $.command.register({
      name: 'emiproto',
      description: 'Prototipo de animación de Emi: /emiproto atomo | blit | fluido | bench | off',
      argumentHint: '[atomo | blit | fluido | bench | off]',
      immediate: true,
    })
    // Medición automática de una sola vez: si auto.txt contiene «bench», compara las tres formas de animar y deja bench.json.
    if (carpeta) {
      const marcaBench = await $.fs.read(`${carpeta}/auto.txt`).catch(() => '')
      if (typeof marcaBench === 'string' && marcaBench.trim() === 'bench') {
        await $.fs.write(`${carpeta}/auto.txt`, 'hecho').catch(() => undefined)
        void bench($)
      }
    }
'''

# 4) montar
reg = reg.replace("import { iniciarProto, register as registrarProto } from './proto'\n", "import { indiceEn } from './animacion'\nimport type { Perfil } from './animacion'\nimport { celdas2 } from './celdas2'\n", 1)
reg = reg.replace("import { celdas, fotograma, medidas, planPanel, TEXTO_COLUMNAS, TEXTO_FILAS } from './dibujo'", "import { celdas, filasDe, fotograma, fotogramas, indice, medidas, planPanel, TEXTO_COLUMNAS, TEXTO_FILAS } from './dibujo'", 1)
assert "export const register: Register = (on, options) => {\n  registrarProto(on, options)\n" in reg
reg = reg.replace("export const register: Register = (on, options) => {\n  registrarProto(on, options)\n", bloque + "\nexport const register: Register = on => {\n" + cuerpo + "\n", 1)
assert "    await iniciarProto($)\n" in reg
reg = reg.replace("    await iniciarProto($)\n", inicio_proto, 1)
open(BASE + "register.tsx", "w", encoding="utf-8").write(reg)
open(BASE + "proto.tsx", "w", encoding="utf-8").write("// El prototipo de animación vive ahora dentro de register.tsx: el motor no admite pasar `$` entre archivos ni dos session.start sin filtro.\nexport {}\n")
print("fusionado:", len(reg), "caracteres")
