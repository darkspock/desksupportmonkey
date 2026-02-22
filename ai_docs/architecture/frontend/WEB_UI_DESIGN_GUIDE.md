# Web UI Design Guide (Refactoring UI Based)

Guia practica para diseno web de producto, basada en principios de Refactoring UI y orientada a implementacion real en app.

---

## 1) Empieza por la funcionalidad, no por el layout

Disena primero la tarea del usuario y despues el contenedor visual.

- Define el objetivo de la pantalla en una frase.
- Define la accion principal (solo una por pantalla).
- Lista los datos minimos necesarios para completar la tarea.
- Si no puedes responder "que debe lograr el usuario aqui", no disenes navbar/sidebar aun.

Regla de calidad:
- En menos de 5 segundos debe ser obvio que se puede hacer en la pantalla.

---

## 2) Estructura primero, detalle despues

Antes de tipografia fina, sombras y color, valida estructura y flujo.

- Prototipa en grises.
- Primero orden y jerarquia; luego estetica.
- No discutas detalles de branding hasta que el flujo funcione.

Regla de calidad:
- Si la pantalla no se entiende en escala de grises, todavia no esta lista.

---

## 3) Jerarquia visual explicita

No todos los elementos deben competir por atencion.

- Titulo y CTA principal con mayor peso visual.
- Acciones secundarias con menor contraste.
- Metadatos y ayuda visualmente de-emphasized.
- Usa tamano, peso tipografico, contraste y espacio (no solo color).

Regla de calidad:
- Debe existir un camino visual claro: titulo -> contenido clave -> CTA principal.

---

## 4) Limita tus decisiones (sistema, no improvisacion)

Reducir opciones mejora coherencia y velocidad de diseno/desarrollo.

- Paleta acotada de colores.
- Escala tipografica fija.
- Escala de espaciado fija.
- Set limitado de radios/sombras.

Regla de calidad:
- Evitar valores arbitrarios (ej: 17px, 23px, colores fuera de tokens).

---

## 5) Espaciado sin ambiguedad

El espacio debe explicar agrupacion y relacion entre elementos.

- Menos espacio dentro de un grupo; mas espacio entre grupos.
- Label + input deben percibirse como unidad.
- Secciones distintas deben estar claramente separadas.

Escala sugerida:
- `4, 8, 12, 16, 24, 32, 48, 64`

Regla de calidad:
- Si dos bloques parecen igual de conectados, hay ambiguedad de espaciado.

---

## 6) Tipografia para legibilidad, no decoracion

La tipografia define ritmo, claridad y prioridad.

- Usa maximo 2 familias.
- Usa 2-3 pesos maximo.
- Mantiene line-height generoso en texto largo.
- Evita depender de escalado relativo ciego; ajusta por contexto y breakpoint.

Escala sugerida:
- `H1 36/44`, `H2 28/36`, `H3 22/30`, `Body 16/24`, `Small 14/20`, `Caption 12/16`

---

## 7) Color con intencion y contraste correcto

El color debe comunicar estado, accion o prioridad.

- No usar texto gris sobre fondo de color.
- En superficies coloreadas, aumenta contraste del texto.
- Reserva color vivo para acciones/estados importantes.
- Usa neutros para estructura.

Regla de calidad:
- Todo texto debe pasar contraste funcional y ser legible en condiciones reales.

---

## 8) Formularios y listados orientados a uso real

Interfaces operativas deben priorizar rapidez y claridad.

Formularios:
- Label claro; placeholder complementario, no sustituto.
- Errores humanos y accionables (no payload tecnico crudo).
- Estados consistentes: default, focus, error, disabled.

Listados:
- Primero legibilidad y escaneo.
- Acciones alineadas a reglas del producto.
- Estados visibles y consistentes.

Regla de calidad:
- El usuario debe poder completar una tarea sin interpretar jerga tecnica.

---

## 9) Profundidad y superficies con moderacion

La profundidad ayuda a entender capas y jerarquia.

- Prioriza contraste de superficie antes que sombras fuertes.
- Usa sombras suaves y consistentes.
- Bordes y fondos deben separar sin ruido visual.

Regla de calidad:
- Cada capa debe tener una razon (estructura), no solo decoracion.

---

## 10) Responsive por recomposicion, no por escala proporcional

En movil no se "encoge" todo: se reordena para mantener claridad.

- Reorganiza layout por breakpoint.
- Mantiene CTA principal visible.
- Simplifica densidad y prioridades en pantallas pequenas.
- Evita que acciones clave queden ocultas por exceso de controles.

Regla de calidad:
- La tarea principal debe completarse en movil con la misma logica que en desktop.

---

## Checklist rapido de revision (UI/PR)

- [ ] Hay una sola accion principal clara por pantalla.
- [ ] La pantalla funciona visualmente en grises.
- [ ] Jerarquia visual clara (titulo, contenido, accion).
- [ ] Espaciado consistente sin ambiguedad entre grupos.
- [ ] Tokens de diseno respetados (sin valores arbitrarios).
- [ ] Contraste legible en todos los estados.
- [ ] Formularios con mensajes de error entendibles.
- [ ] Listados optimizados para escaneo.
- [ ] Capas y sombras usadas con moderacion y coherencia.
- [ ] Responsive recompone contenido, no solo lo reduce.
