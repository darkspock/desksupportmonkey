# Legal Structure

**Date:** 2026-02-22

---

## Legal Entity

| Field | Value |
|---|---|
| Legal name | Plan Zeta Tech S.L. |
| Brand / Product name | DeskSupportMonkey |
| Entity type | Sociedad Limitada (S.L.) |
| Country | España |
| Status | Activa — sin actividad real reciente |
| Shareholders | 1 (fundador único) |
| Administrator | Fundador único |

---

## Pending Actions (before launch — 2026-03-01)

### 1. Verificar estado de Plan Zeta Tech S.L.
- [ ] Verificar que la sociedad sigue en el Registro Mercantil y no está disuelta
- [ ] Verificar que la actividad económica está dada de alta en Hacienda (modelo 036) y el epígrafe IAE es correcto
- [ ] Añadir el CNAE correcto si no está: **6201** (Actividades de programación informática) o **6311** (Proceso de datos, hosting)
- [ ] Verificar que no hay deudas pendientes con Hacienda o Seguridad Social de la actividad anterior
- [ ] Abrir cuenta bancaria de empresa si no está activa (Wise Business, Revolut Business o banco tradicional)

### 2. Stripe y facturación
- [ ] Registrar Plan Zeta Tech S.L. en Stripe con el CIF de la sociedad
- [ ] Configurar Stripe Tax para IVA europeo (OSS — One Stop Shop) — obligatorio para facturar a clientes EU
- [ ] Preparar plantilla de factura con datos fiscales completos: Plan Zeta Tech S.L., CIF, domicilio social, número de factura
- [ ] Decidir software de facturación: Holded, Quaderno, o Stripe Invoicing directamente

### 3. Protección de la marca
- [ ] Verificar disponibilidad de "DeskSupportMonkey" en la OEPM (Oficina Española de Patentes y Marcas)
- [ ] Valorar registro de marca en la EUIPO (Oficina de Propiedad Intelectual de la UE) — cubre todos los países EU con un solo trámite (~€850 para 1 clase)
- [ ] Clase 42: servicios de software, SaaS, servicios tecnológicos

### 4. GDPR / Protección de datos
- [ ] Registrar actividades de tratamiento de datos (obligatorio bajo RGPD)
- [ ] Redactar Política de Privacidad y Política de Cookies para la web
- [ ] Redactar Términos y Condiciones de Servicio (incluir: limitación de responsabilidad, SLA, cancelación, datos)
- [ ] Designar responsable de tratamiento: Plan Zeta Tech S.L.
- [ ] Dado que el producto gestiona datos de dispositivos y usuarios de empresas clientes: considerar si se necesita DPA (Data Processing Agreement) con clientes enterprise

### 5. Open Source License
- [ ] Decidir licencia para el repositorio público:
  - **AGPL-3.0** (recomendado): obliga a que cualquier modificación del código también sea open source, incluidas versiones SaaS. Protege contra que un competidor tome el código y lo monetice sin contribuir.
  - **MIT**: más permisiva, más contribuciones de comunidad, pero permite uso comercial sin restricciones
- [ ] Añadir `LICENSE` file al repositorio
- [ ] Añadir CLA (Contributor License Agreement) si se espera contribuciones externas

---

## Corporate Structure

```
Plan Zeta Tech S.L.
└── Fundador único (100% participaciones)
    ├── Administrador único
    └── CEO / CTO
```

No hay inversores, no hay co-fundadores, no hay cap table que gestionar. Estructura máxima simplicidad.

---

## Tax Considerations (España)

| Concepto | Detalle |
|---|---|
| Impuesto de Sociedades | 15% primeros 2 años de beneficio (tipo reducido nueva actividad), luego 25% |
| IVA clientes España | 21% — repercutir en facturas |
| IVA clientes EU (B2B) | Inversión del sujeto pasivo — el cliente declara el IVA en su país |
| IVA clientes EU (B2C) | OSS (One Stop Shop) — declarar y pagar IVA en cada país del cliente desde España |
| IVA clientes fuera EU | No se aplica IVA |
| Stripe fees | ~1.5% + €0.25 por transacción (tarjetas EU) |

**Recomendación:** Registrarse en el régimen OSS desde el primer cliente EU para simplificar la gestión del IVA intracomunitario. Stripe Tax puede automatizar esto.

---

## Risks & Notes

- **Deudas de actividad anterior:** verificar que Plan Zeta Tech S.L. no arrastra deudas fiscales o de Seguridad Social de la actividad previa. La sociedad está activa pero sin actividad real reciente; una deuda antigua puede bloquear la cuenta o generar embargos.
- **Marca no registrada:** hasta registrar "DeskSupportMonkey" en EUIPO, el nombre no está protegido en la UE. Dado el lanzamiento en 8 días, priorizar al menos la verificación de disponibilidad ahora y el registro formal en las semanas siguientes.
- **AGPL vs. competidores:** si se elige MIT, Lansweeper u otro competidor con recursos podría tomar el código, añadir NIS2 features, y competir directamente. AGPL lo impide.
