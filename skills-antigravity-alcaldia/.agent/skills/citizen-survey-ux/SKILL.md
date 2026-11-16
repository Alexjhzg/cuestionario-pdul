---
name: citizen-survey-ux
description: >-
  Diseña e implementa experiencias de usuario (UI/UX) accesibles, mobile-first y de
  baja carga cognitiva para que ciudadanos y encuestadores de campo completen
  encuestas municipales y cuestionarios extensos (como la Encuesta Origen-Destino PDUL)
  de forma sencilla, rápida y sin pérdida de datos. Úsala cuando construyas o mejores
  la interfaz de llenado de encuestas, asistentes paso a paso (wizards), captura móvil
  de grillas de viajes/residentes, validación amigable (:user-invalid), accesibilidad
  (WCAG AA) o autoguardado offline. No la uses para analítica SQL (usa postgres-jsonb-dba)
  ni endpoints backend (usa fastapi-survey-backend).
---

# Especialista UI/UX para Encuestas Ciudadanas y Trabajo de Campo (Mobile-First & Accesible)

## Descripción General
Esta skill transforma cuestionarios técnicos o extensos (como las **8 secciones de la Encuesta Origen-Destino del PDUL**) en experiencias digitales intuitivas, rápidas y tolerantes a fallos de conexión, pensadas tanto para ciudadanos desde teléfonos móviles de gama media/baja como para encuestadores de campo bajo condiciones reales (sol directo, operación con una sola mano y conectividad intermitente).

## Dependencias y Coordinación con Otras Skills
- **Sistema de Diseño ([DESIGN.md](./references/DESIGN.md))**: Fuente única de verdad para tokens de color (`--color-snow-canvas`, `--color-lavender-wash`, `--color-midnight-ink`, `--color-royal-signal`, `--color-azure-focus`), tipografía (`Inter` + `Roboto Mono`), radios de borde (`12px` en inputs, `8px`/`16px` en tarjetas, `9999px` tipo píldora en botones) y sombras suaves multicapa.
- **`formio-survey-architect`**: Traduce las reglas ergonómicas (selección de controles, textos de ayuda, paginación `wizard` y tarjetas `editgrid`) al esquema JSON de `@formio/js`.
- **`municipal-gis-dashboard`**: Comparte el sistema de diseño en **Vue 3 (`<script setup>`) + PrimeVue v3** y los tokens de [DESIGN.md](./references/DESIGN.md), manteniendo separada la vista pública de participación ciudadana de la vista administrativa de mapas y analítica.
- **`fastapi-survey-backend`**: Se integra con el envío idempotente (`client_submission_id`) y los mensajes de error estructurados del backend.

## Flujo de Trabajo Paso a Paso

### 1. Arquitectura de Información y Reducción de Carga Cognitiva
1. **Fragmentación Progresiva (Wizard Paso a Paso):**
   - Nunca muestres más de **5 a 7 preguntas** simultáneamente en pantalla si la encuesta supera las 10 preguntas.
   - Agrupa cuestionarios largos (ej. las 8 secciones del PDUL) en pasos con una barra de progreso semántica (`<nav aria-label="Progreso de la encuesta">` + `<ol>` con `aria-current="step"`) que indique el título de la sección y el tiempo estimado restante (ej. *"Sección 2 de 8: Datos de la Vivienda — ~3 min"*).
   - Permite siempre navegar hacia atrás y hacia adelante sin perder las respuestas ya ingresadas, configurando `enterkeyhint="next"` y `enterkeyhint="previous"`.
2. **Diseño de Una Sola Columna y Proximidad Visual (Gestalt):**
   - Usa estrictamente disposición de **una sola columna (`single-column layout`)** en formularios para evitar saltos visuales en zigzag.
   - Coloca siempre el `<label>` **encima** del control y aplica la **Regla de Proximidad de Gestalt**: el margen vertical entre la etiqueta y su campo (`0.25rem–0.375rem`) debe ser visiblemente menor que el margen entre preguntas distintas (`1.5rem`).
   - Coloca las instrucciones o pistas de formato (`<span id="...-hint" class="hint">`) **encima del `<input>`** (entre el `<label>` y el `<input>`) vinculadas mediante `aria-describedby`, para que el teclado virtual en móviles o los menús de autocompletado nunca las tapen.

### 2. Matriz de Selección de Controles y Teclados Móviles
Elige siempre el control que minimice el número de toques y errores de digitación:

| Cantidad de Opciones | Tipo de Elección | Control Obligatorio | Justificación UX y Accesibilidad |
| :--- | :--- | :--- | :--- |
| **2 a 5 opciones** | Única (Exclusiva) | `<input type="radio">` (Tarjetas táctiles) | **Escaneo sin clics (Zero-click scanning):** Todas las opciones son visibles de inmediato con 1 solo toque. Prohibido usar `<select>` para menos de 6 opciones. |
| **6 a 15 opciones** (ej. 11 Parroquias) | Única (Exclusiva) | `<select>` o Selector con filtro | Conserva espacio vertical permitiendo selección rápida. |
| **> 15 opciones** (ej. Zonas O-D / Sectores) | Única (Exclusiva) | `<input list="id">` (`<datalist>`) o Combobox buscable | **Búsqueda difusa (Fuzzy search):** Evita la fatiga de desplazamiento en catálogos largos. |
| **Cualquiera** | Múltiple ("admite respuestas múltiples") | `<input type="checkbox">` (`selectboxes`) | Semántica nativa no exclusiva con casillas de verificación amplias. |

- **Configuración de Teclados en Móvil (`inputmode` y `autocomplete`):**
  - Para **Cédula, Teléfono o Códigos Numéricos:** Usa `<input type="text" inputmode="numeric" pattern="[0-9]{6,9}" autocorrect="off" autocapitalize="off" spellcheck="false">`. **Nunca uses `type="number"`** para documentos de identidad o códigos (evita que el scroll cambie el número por accidente, elimina los botones de flecha innecesarios y conserva ceros a la izquierda).
  - Usa `type="number"` únicamente para cantidades aritméticas reales (`total_cuartos_vivienda`, `edad`, `tiempo_viaje_min`, `costo_viaje_bs`) acompañado de botones `+` / `-` (`PrimeVue InputNumber` con `showButtons`) para facilitar la captura con una sola mano.

### 3. UX Simplificada para Tablas Repetibles (Secciones IV y V del PDUL)
Las tablas anchas (`datagrid` horizontal de 12 columnas) son ilegibles en teléfonos móviles. Aplica el patrón **Tarjetas Apiladas con Pre-llenado Inteligente** documentado en [ux-components-and-offline-patterns.md](./references/ux-components-and-offline-patterns.md):
1. **Captura en Tarjetas o Modal por Ítem (`Stacked Cards`):**
   - Cada residente (Sección IV) o viaje (Sección V) se edita en una tarjeta vertical limpia y, al confirmarse, se resume en una tarjeta compacta:
     - *"👤 Residente 1: María Pérez (42 años, Jefa de hogar)"* con botones `[Editar]` y `[Eliminar]`.
     - Desambigua siempre el nombre accesible de los botones repetidos: `aria-label="Editar residente 1: María Pérez"` y `aria-label="Eliminar residente 1: María Pérez"`.
2. **Pre-llenado Inteligente (Smart Defaults) para Viajes O-D:**
   - Al agregar el **primer viaje** de un residente, pre-llena automáticamente el campo `zona_od_origen` con la `zona_residencia_od` ingresada en la Sección I.
   - Ofrece un botón de acción rápida **"🔄 Agregar viaje de regreso a casa"** que crea un nuevo viaje invirtiendo automáticamente `zona_od_destino` ↔ `zona_od_origen` y copiando el `modo_principal`, reduciendo a la mitad el tiempo de llenado de la Sección V.

### 4. Validación Amigable Tardía (*Validate After Interaction*)
1. **Cero Errores Prematuros:**
   - Ningún campo debe mostrarse en rojo al cargar la encuesta ni mientras el ciudadano está escribiendo por primera vez.
2. **Matriz de Eventos de Validación:**
   - **Al salir del campo (`blur` / `:user-invalid`):** Evalúa la regla y muestra el mensaje de error si el campo quedó inválido.
   - **Al escribir (`input`):** Limpia de inmediato cualquier estado de error tan pronto el usuario corrige el valor, sincronizando `aria-invalid="false"`.
   - **Al enviar (`submit`):** **Nunca deshabilites el botón de envío para bloquear la validación.** Mantén el botón habilitado; si faltan campos requeridos al pulsarlo, enfoca automáticamente el primer campo inválido y anuncia el resumen de errores con `aria-live="assertive"`. Deshabilita el botón **únicamente mientras la petición HTTP `POST` válida está en vuelo** para prevenir envíos duplicados.
3. **Indicadores Multimodales:**
   - Todo mensaje de error debe combinar borde, ícono (`❌` con `aria-hidden="true"`) y texto explicativo claro en lenguaje ciudadano (ej. *"Escriba solo los números de su cédula, sin puntos ni guiones"*), nunca solo cambio de color.

### 5. Autoguardado Local, Modo Offline y Ergonomía Táctil
1. **Persistencia Automática de Borrador (`localStorage` / `IndexedDB`):**
   - Guarda automáticamente las respuestas parciales cada vez que el usuario avanza de sección o modifica un campo, mostrando un indicador tranquilo (`aria-live="polite"`: *"Progreso guardado automáticamente"*).
   - Al reabrir la encuesta tras un cierre accidental o caída de batería, ofrece un banner claro: *"Tienes una encuesta en curso (Sección 4 de 8). ¿Deseas continuar donde la dejaste?"*.
2. **Cola de Sincronización Offline (`Offline Queue`):**
   - Si el dispositivo pierde conexión al enviar, almacena el paquete en una cola local junto con un `client_submission_id` (UUID v4) y muestra confirmación de resguardo local, reintentando automáticamente al detectar el evento `online`.
3. **Ergonomía Táctil, Visual y Tokens de Diseño (WCAG 2.2 AA + [DESIGN.md](./references/DESIGN.md)):**
   - Consulta [DESIGN.md](./references/DESIGN.md) antes de escribir estilos CSS o configurar temas de PrimeVue v3:
     - **Superficies:** Lienzo principal `--color-snow-canvas` (`#fcfcfc`), fondo de secciones destacadas `--color-lavender-wash` (`#f0f4fe`), tarjetas de preguntas `--surface-card` (`#ffffff`) y fondos de inputs deshabilitados/agrupados `--color-fog-surface` (`#f1f5f9`).
     - **Texto y Contraste (≥ 17.8:1 en titulares/cuerpo):** Títulos en `--color-midnight-ink` (`#020520`), cuerpo y etiquetas en `--color-graphite-body` (`#14141e`), textos secundarios en `--color-slate-caption` (`#374151`) y ayudas en `--color-ash-helper` (`#6b7280`).
     - **Acento y Estados:** Acento institucional primario `--color-royal-signal` (`#145aff`), anillo de foco `--color-azure-focus` (`#0099ff`), y puntos de estado (`4–6px`) en `--color-cobalt-glow` (`#3b82f6`), `--color-mint-win` (`#16ca2e`), `--color-amber-pending` (`#ffa64d`) y `--color-coral-lost` (`#f26052`).
     - **Geometría de 2 Niveles y Botones Píldora:** Inputs con `border-radius: 12px` (`--radius-inputs`), tarjetas internas de residentes/viajes con `8px` (`--radius-cards`), contenedores de sección con `16px–40px` (`--radius-containers`) y todos los botones/tags con radio píldora `9999px` (`--radius-buttons`).
     - **Adaptación Open Source Obligatoria:** Ignora las referencias a `Font Awesome 6 Pro` (propietario) o `Pretendard` (coreano) presentes en la extracción cruda de `DESIGN.md`; utiliza exclusivamente `Inter` (`400/500/600`), `Roboto Mono` para códigos/métricas y paquetes de íconos 100% Open Source (`primeicons` o `lucide-vue-next`).
   - Tamaño mínimo de objetivos táctiles (`min-block-size`): `48px` (`52px` en `@media (pointer: coarse)`).
   - Tamaño de fuente en `<input>`, `<select>` y `<textarea>`: mínimo `1rem` (`16px`, `--text-body`) para impedir el zoom automático forzado en iOS/Android.
   - Indicador de foco de alto contraste en `:focus-visible` (`outline: 3px solid var(--color-azure-focus, #0099ff); outline-offset: 2px;`).
4. **Arquitectura de Estilos con CSS Nativo (`:root`) y `<style scoped>` (Sin Tailwind CSS):**
   - Utiliza exclusivamente **CSS Custom Properties (`:root`)** definidas en [DESIGN.md](./references/DESIGN.md) junto con bloques `<style scoped>` en los componentes Vue 3 y una hoja global de alcance `.formio-local-wrapper` para estilizar los controles inyectados por `@formio/js`.
   - **No utilices Tailwind CSS ni PrimeFlex:** esto mantiene las plantillas HTML/ARIA limpias y evita que un *CSS Preflight* rompa los componentes de PrimeVue v3, los bordes de Form.io o las teselas de Leaflet.

## Validación y Verificación
- **Prueba de Teclado y Foco:** Recorre toda la encuesta usando únicamente `Tab`, `Shift+Tab`, flechas, `Space` y `Enter`, verificando que el orden sea secuencial, ningún elemento interactivo tenga `tabindex > 0` y el anillo `:focus-visible` sea siempre visible.
- **Prueba de Viewport Móvil (`360x800`):** Verifica que no exista scroll horizontal en ninguna de las 8 secciones (incluyendo las grillas de Residentes y Viajes) y que todos los botones tengan al menos `48px` de altura.
- **Prueba de Resiliencia:** Recarga la página a mitad de la Sección IV y comprueba que el borrador local restaure los datos ingresados sin pérdida.

## Errores Comunes a Evitar
- **Usar `placeholder` como reemplazo de `<label>`:** El placeholder desaparece al escribir y tiene bajo contraste; usa siempre `<label for="...">` persistente arriba del control.
- **Envolver grupos de `radio` o `checkbox` en listas `<ul>`/`<li>`:** Los lectores de pantalla ya anuncian el conteo de radios/casillas dentro de un `<fieldset>`; envolverlos en listas duplica los anuncios y confunde al usuario.
- **Ocultar controles nativos con `display: none` al estilizar tarjetas de radio/checkbox:** `display: none` los elimina del árbol de accesibilidad y del foco por teclado; usa la utilidad `.visually-hidden` (`clip-path: inset(50%)`).

