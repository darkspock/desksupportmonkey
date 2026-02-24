# DSM Control — Landing Page Structure

**Date:** 2026-02-24
**Target:** IT managers, CISOs, and operations leads at regulated EU SMBs (10-300 employees)
**Goal:** Demo requests and free trial signups

---

## Navigation Bar

```
[DSM Control logo]    Producto    Compliance    Sectores    Pricing    Contacto        [Acceder]  [Solicitar Demo ↗]
```

- Fixed on scroll
- White background with subtle bottom border
- "Solicitar Demo" is the primary CTA — teal background, white text
- "Acceder" is secondary — text link
- No "Open Source", no "GitHub", no "Transparency"
- Mobile: hamburger menu with "Solicitar Demo" always visible

---

## Section 1: Hero

### Layout
- Left-aligned text (60%) + product screenshot (40%)
- White/light background
- No centered text walls

### Content

**Badge:** `NIS2 compliant` (teal background, white text, small pill)

**Headline:**
> Control total de tus activos TIC

**Subtitle:**
> Gestiona el ciclo de vida completo de cada dispositivo — desde la compra hasta la baja — con trazabilidad completa para auditorias NIS2, DORA y CRA.

**CTAs:**
- `[Solicitar Demo]` — teal/blue, primary
- `[Ver Pricing]` — outlined, secondary

**Visual:** Real screenshot of the DSM Control dashboard showing asset inventory with status badges and metrics cards. Clean browser chrome, no distracting UI elements.

---

## Section 2: Trust Bar

### Pre-customer version (launch)
```
[NIS2 Ready]    [RGPD Compliant]    [Datos alojados en la UE]    [Open Source Core]    [SOC 2 in progress]
```
- Gray icons/badges on white background
- Subtle, not loud — establishes baseline trust

### Post-customer version (when we have logos)
```
"Empresas de sanidad, manufactura y finanzas confian en DSM Control"
[Hospital X logo]  [Factory Y logo]  [Finance Z logo]  [Logistics W logo]
```

---

## Section 3: Problem Statement

### Headline
> Si te suena alguno de estos problemas, necesitas DSM Control

### 3 columns (icon + title + description)

**Column 1 — The Spreadsheet**
- Icon: table/grid
- Title: "El inventario vive en Excel"
- Text: "Cada vez que alguien pregunta cuantos portatiles tenemos, la respuesta es 'depende de quien tenga la ultima version del Excel'. No hay fuente unica de verdad."

**Column 2 — The Audit**
- Icon: clipboard/shield
- Title: "El auditor ha preguntado y no tienes respuesta"
- Text: "NIS2 exige documentar que activos tienes, quien los tiene y que incidencias han tenido. Si no puedes mostrarlo, tienes un problema de compliance."

**Column 3 — The Disconnect**
- Icon: unlinked chain
- Title: "Las incidencias no estan vinculadas a los dispositivos"
- Text: "Cuando un portatil falla 5 veces en un ano, deberia ser visible de un vistazo. Hoy esa informacion esta repartida entre emails, tickets y la memoria del tecnico."

---

## Section 4: Asset Lifecycle (Core Value Prop)

### Headline
> El ciclo de vida completo, en una sola plataforma

### Horizontal timeline/flow

```
Compra          Almacen         Asignacion       Incidencias      Mantenimiento     Baja
───●───────────────●───────────────●───────────────●───────────────●───────────────●───
Ordenes de      Stock y         Quien tiene      Cada ticket      Preventivo y     Historial
compra y        ubicacion       que dispositivo  vinculado al     correctivo       completo y
proveedores                                      activo           programado       auditoria
```

Each step is clickable/hoverable and shows a small product screenshot below the timeline.

### Subtitle
> Cada dispositivo tiene un historial completo: quien lo pidio, cuando llego, a quien se asigno, cada incidencia que ha tenido, y cuando se dio de baja. Ese historial es tu auditoria NIS2.

---

## Section 5: Features Grid

### Headline
> Todo lo que necesitas para gestionar tus activos TIC

### 3x3 grid (icon + title + one line)

| Feature | Description |
|---|---|
| **Inventario de activos** | Todos tus dispositivos en un solo lugar — portatiles, monitores, telefonos, servidores |
| **Incidencias vinculadas** | Cada ticket esta vinculado al dispositivo que lo causa. Historial completo por activo. |
| **Ordenes de compra** | Gestion de compras, proveedores y presupuestos por departamento |
| **Mantenimiento** | Planes de mantenimiento preventivo y correctivo con calendario |
| **Envios de equipos** | Seguimiento de envios a empleados — nuevos equipos, devoluciones, reemplazos |
| **Dashboard en tiempo real** | Metricas clave: activos por estado, incidencias abiertas, SLA, costes |
| **Audit trail NIS2** | Trazabilidad completa de cada accion sobre cada activo — exportable para auditores |
| **Roles y permisos** | Empleados, tecnicos y administradores con permisos granulares por departamento |
| **API e integraciones** | API REST completa. Integra con tus herramientas existentes. |

---

## Section 6: Compliance (The Selling Section)

### Background: light navy or very subtle teal tint — stands out from white sections

### Headline
> Responde a las 3 preguntas que hara tu auditor NIS2

### 3 cards

**Card 1**
- Auditor question: *"Que dispositivos tiene tu empresa en su red?"*
- DSM Control answer: "Inventario completo de activos con estado, ubicacion y responsable"
- Icon: server/devices

**Card 2**
- Auditor question: *"Quien tiene acceso a que dispositivos?"*
- DSM Control answer: "Asignacion por usuario con historial de cambios y trazabilidad temporal"
- Icon: user + device link

**Card 3**
- Auditor question: *"Que incidencias han tenido esos dispositivos?"*
- DSM Control answer: "Cada incidencia vinculada al activo especifico, con timeline exportable"
- Icon: ticket + asset link

### Subtitle
> Tambien preparado para DORA (sector financiero) y CRA (fabricantes de hardware). Una plataforma, tres marcos regulatorios.

### CTA
`[Descarga la guia NIS2 gratuita]` — lead generation via email capture

---

## Section 7: Sectors

### Headline
> Disenado para sectores regulados

### 4 cards (icon + sector + one paragraph)

**Sanidad**
> Hospitales y clinicas gestionan cientos de dispositivos: estaciones de enfermeria, equipos de diagnostico, portatiles de administracion. DSM Control te da visibilidad y trazabilidad para cumplir NIS2 sin dedicar un equipo a ello.

**Manufactura**
> Equipos de produccion, PLCs, estaciones de control y dispositivos de oficina. NIS2 afecta directamente a la industria manufacturera. Documenta cada activo y cada incidencia.

**Servicios financieros**
> DORA exige a fintechs, aseguradoras y gestoras documentar sus activos TIC y reportar incidencias. DSM Control cubre ambos requisitos desde el primer dia.

**Logistica y transporte**
> Dispositivos distribuidos en multiples sedes, almacenes y vehiculos. Controla que tienes, donde esta, y quien lo usa — sin importar la ubicacion.

---

## Section 8: Pricing

### Headline
> Pricing simple. Sin coste por usuario.

### Subtitle
> Paga segun el tamano de tu empresa, no por el numero de tecnicos o activos. Todos los planes incluyen todas las funcionalidades.

### 3 plan cards (Starter highlighted as "Popular")

**Starter — €49/mes**
- Hasta 25 empleados
- Todas las funcionalidades
- Soporte por email
- `[Empieza gratis 15 dias]`

**Growth — €99/mes** *(Most popular)*
- Hasta 100 empleados
- Todas las funcionalidades
- Soporte prioritario
- `[Empieza gratis 15 dias]`

**Scale — €199/mes**
- 100+ empleados
- Todas las funcionalidades
- Soporte dedicado + onboarding
- `[Contacta con ventas]`

### Below pricing
> "Quieres self-hosting? DeskSupportMonkey es open source y gratuito." (small text, link to desksupportmonkey.com)

---

## Section 9: Final CTA

### Background: Navy

### Content
> Empieza a cumplir NIS2 esta semana

> Sin instalacion. Sin coste por usuario. 15 dias gratis.

**CTAs:**
- `[Solicitar Demo]` — teal, primary
- `[Empieza Gratis]` — white outlined

---

## Section 10: Footer

### Layout: 4 columns + bottom bar

```
DSM Control              Producto              Compliance            Recursos
Plan Zeta Tech S.L.      Funcionalidades       NIS2                  Blog
Hecho en Espana          Pricing               DORA                  Guia NIS2 (PDF)
                         API Docs              CRA                   Centro de ayuda
                         Changelog             Seguridad             Contacto
                         Open Source            RGPD

─────────────────────────────────────────────────────────────────────────────────
(c) 2026 Plan Zeta Tech S.L.    Privacidad    Terminos    Cookies    DPA
```

---

## Responsive Behavior

- **Desktop (1200px+):** Full layout as described above
- **Tablet (768-1199px):** 2-column grids, hero stacks vertically
- **Mobile (<768px):** Single column, sticky "Solicitar Demo" button at bottom, hamburger nav

---

## Pages Needed (Beyond Landing)

| Page | Purpose |
|---|---|
| `/producto` | Detailed features with screenshots |
| `/compliance/nis2` | NIS2-specific page with regulation mapping |
| `/compliance/dora` | DORA-specific page |
| `/sectores/sanidad` | Healthcare-specific use case and language |
| `/sectores/manufactura` | Manufacturing-specific use case |
| `/pricing` | Full pricing page with FAQ |
| `/contacto` | Contact form + demo scheduling |
| `/seguridad` | Security practices, data hosting, encryption, RGPD |
| `/blog` | SEO content — NIS2 guides, compliance articles |
