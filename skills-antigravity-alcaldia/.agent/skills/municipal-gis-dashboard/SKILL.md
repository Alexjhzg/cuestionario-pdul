---
name: municipal-gis-dashboard
description: >-
  Desarrolla componentes e interfaces frontend con Vue 3 (Composition API) y
  PrimeVue v3 (o React), integrando renderizado de formularios Form.io (@formio/js),
  mapas coropléticos y flujos Origen-Destino con Leaflet + OpenStreetMap, y gráficos
  estadísticos interactivos con Apache ECharts. Úsala cuando trabajes en vistas del
  dashboard municipal, mapas GIS de parroquias/zonas O-D, o integración visual de
  encuestas. No la uses para diseñar el esquema JSON de preguntas (usa
  formio-survey-architect) ni para consultas SQL/FastAPI.
---

# Frontend de Encuestas, Mapas GIS (Leaflet) y Dashboard (ECharts + PrimeVue v3)

## Descripción General
Esta skill guía la construcción del frontend municipal 100% open-source combinando **Vue 3 (`<script setup>`) + PrimeVue v3** con **Form.io (`@formio/js`)**, **Leaflet (`leaflet` + OpenStreetMap)** y **Apache ECharts (`echarts`)**, respetando la Soberanía de Datos (cero dependencias de Google Maps o Form.io Cloud).

## Dependencias y Coordinación con Otras Skills
- **Sistema de Diseño ([DESIGN.md](../citizen-survey-ux/references/DESIGN.md))**: Aplica la paleta (`#fcfcfc` canvas, `#f0f4fe` wash, `#145aff` Royal Signal, puntos de estado `#3b82f6`/`#16ca2e`/`#ffa64d`/`#f26052`), tipografía (`Inter` + `Roboto Mono`) y sombras multicapa definidas en `citizen-survey-ux/references/DESIGN.md`.
- **`formio-survey-architect`**: Renderiza el esquema JSON almacenado en la base de datos mediante `Formio.createForm(containerRef, schema)` sin conexión a servidores externos.
- **`citizen-survey-ux`**: Delega las vistas públicas de llenado de encuestas, asistentes paso a paso (wizards), tarjetas móviles O-D y autoguardado offline a las directrices de `citizen-survey-ux`.
- **`fastapi-survey-backend`**: Consume los endpoints `/api/v1/encuestas/{id}/resultados-parroquia`, `/metricas` y `/matriz-od`.

## Mejores Prácticas de Ingeniería Frontend (Vue 3 + TypeScript)
1. **Arquitectura Basada en Composables y Servicios Tipados:**
   - Extrae las llamadas HTTP a una capa `services/encuestasApi.ts` con tipos TypeScript estrictos (`strict: true`, prohibido usar `any` en modelos de datos).
   - Encapsula el estado reactivo de filtros, carga (`isLoading`), errores (`error`) y actualización de gráficos en composables reutilizables (`useEncuestaAnalytics.ts`).
2. **Accesibilidad en Visualizaciones Complejas (WCAG AA):**
   - Todo gráfico de ECharts o mapa coroplético de Leaflet debe estar contenido en un `<figure>` con `<figcaption>` descriptivo y ofrecer una alternativa tabular accesible (activando `dataView` en ECharts o mostrando una tabla `<table>` con `<caption>` y `<th scope="col">`).
3. **Estilizado Limpio con Variables CSS Nativas (`:root` de `DESIGN.md`) y `<style scoped>`:**
   - Maqueta los paneles del dashboard con CSS Grid y Flexbox nativos dentro de `<style scoped>` consumiendo los tokens `--color-*`, `--spacing-*`, `--radius-*` y `--shadow-*` de [DESIGN.md](../citizen-survey-ux/references/DESIGN.md). No uses Tailwind CSS ni PrimeFlex.

## Flujo de Trabajo Paso a Paso

### 1. Ciclo de Vida Seguro de Instancias DOM (`@formio/js`, `leaflet`, `echarts`)
Revisa los patrones completos en [vue3-primevue-leaflet-echarts.md](./references/vue3-primevue-leaflet-echarts.md):
1. **Montaje (`onMounted` en Vue 3 / `useEffect` en React):**
   - Inicializa `Formio.createForm`, `L.map` y `echarts.init` usando referencias directas al DOM (`ref<HTMLElement | null>(null)`).
   - Almacena las instancias de `leaflet` y `echarts` en variables no reactivas o `shallowRef()` (nunca en `ref()` profundo de Vue 3, ya que los proxies de Vue rompen los métodos internos del canvas/SVG de Leaflet y ECharts).
2. **Desmontaje (`onBeforeUnmount` / cleanup de `useEffect`):**
   - Destruye siempre las instancias para evitar fugas de memoria:
     - Form.io: `formInstance?.destroy(true)`
     - Leaflet: `mapInstance?.remove()`
     - ECharts: `resizeObserver?.disconnect()` y `chartInstance?.dispose()`

### 2. Mapas Coropléticos y Líneas de Deseo O-D con Leaflet
1. **Capa Base OpenStreetMap:**
   - Usa `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` con atribución visible `© OpenStreetMap contributors`, centrando inicialmente en el Municipio Maturín (`[9.7457, -63.1832]`, zoom `11`).
2. **Polígonos `GeoJSON` de Parroquias y Zonas O-D:**
   - Empareja `feature.properties.codigo_parroquia` (en `snake_case`, ej. `san_simon`, `alto_de_los_godos`) con el resultado de `/resultados-parroquia`.
   - Aplica una escala secuencial accesible (ej. paleta YlOrRd o Viridis) en `style(feature)` y muestra un tooltip/popup con nombre de parroquia, total de respuestas y porcentaje.
   - Si el contenedor del mapa está dentro de un `TabView` o `Dialog` de PrimeVue v3, invoca `mapInstance.invalidateSize()` al mostrarse el contenedor.

### 3. Visualización Estadística con Apache ECharts y PrimeVue v3
1. **Configuración Obligatoria de Reportes de Gestión:**
   - Incluye siempre en las opciones de ECharts:
     ```javascript
     toolbox: {
       feature: {
         saveAsImage: { title: 'Descargar Gráfico', pixelRatio: 2 },
         dataView: { title: 'Ver Datos', readOnly: true }
       }
     }
     ```
2. **Tipos de Gráfico Recomendados para el PDUL:**
   - **Reparto Modal / Motivo de Viaje:** Gráfico de barras horizontales ordenadas o anillo (`pie` con `radius: ['40%', '70%']`).
   - **Matriz Origen-Destino (`/matriz-od`):** Mapa de calor (`heatmap`) o diagrama de flujos (`sankey`) entre `zona_origen` y `zona_destino`.
   - **Percepción y Seguridad Peatonal (Sección VII y VIII):** Barras apiladas al 100% para escalas Likert de 5 niveles.
3. **Diseño Responsivo:**
   - Vincula un `ResizeObserver` al contenedor del gráfico que invoque `chartInstance.resize()`.

## Validación y Verificación
- Comprueba que al cambiar de vista o desmontar el componente no queden observadores activos ni errores `Map container is already initialized` en la consola del navegador.
- Verifica en la pestaña *Network* del navegador que no existan peticiones hacia `*.form.io` ni `maps.googleapis.com`.

## Errores Comunes a Evitar
- **Envolver instancias de ECharts o Leaflet en `ref()` profundo de Vue 3:** Provoca fallos silenciosos en tooltips y redimensionamiento; usa `shallowRef()` o una variable local fuera del sistema reactivo.
- **No llamar a `map.invalidateSize()` dentro de pestañas (`TabView` de PrimeVue):** Cuando Leaflet se monta en un contenedor oculto (`display: none`), carga teselas grises incompletas hasta que se invoca `invalidateSize()`.

