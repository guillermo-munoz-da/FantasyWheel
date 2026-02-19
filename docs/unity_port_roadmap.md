# Roadmap de Port a Unity (por Features)

Este roadmap divide el port del prototipo Python a Unity en features incrementales con criterios de aceptación y pruebas manuales.

## Target inicial

- Plataforma: Android first.
- UI: minimalista oscura.
- Arquitectura: data-driven para ruletas y dependencias.
- Monetización: ads preparados (sin activación comercial en MVP).

## Reglas de entrega

- Cada feature termina en algo jugable y validable manualmente.
- Cada feature cierra con build Android debug instalable.
- Si una feature rompe otra, no se considera terminada.

## Features del roadmap

### F0 - Base técnica Unity

- MVP: proyecto Unity LTS, estructura base, bootstrap y pipeline Android debug.
- No incluye: gameplay completo ni monetización real.
- Aceptación: abre sin errores de compilación, corre escena inicial y genera APK.
- Pruebas manuales: play en editor sin errores, instalar APK, validar 2 minutos sin crash.

### F1 - Motor de ruletas data-driven

- MVP: modelo de rueda/opción/peso/requisito/efecto, carga JSON, selección ponderada y seed opcional.
- No incluye: UI final ni árbol completo de aventura.
- Aceptación: resultados válidos según reglas y reproducibles con misma seed.
- Pruebas manuales: 20 spins por rueda, validación de bloqueos y repetición con seed fija.

### F2 - Creación de personaje

- MVP: Race → Archetype → Class → Gender/Sex → Age → Height → Alignment → Magic Type.
- No incluye: cosmética avanzada ni inventario profundo.
- Aceptación: flujo completo sin bloqueos, dependencias correctas y ficha serializable.
- Pruebas manuales: 10 personajes, caso crítico de subclase dependiente y reset limpio.

### F3 - Aventura por cadenas de eventos

- MVP: Activity → Event → Action → Outcome y soporte de cadenas específicas.
- No incluye: todas las cadenas futuras ni cinemáticas.
- Aceptación: efectos persistentes modifican estado y se alcanzan múltiples finales.
- Pruebas manuales: 15 aventuras, validación de dinámica contextual y finales terminales.

### F4 - Persistencia y legado

- MVP: save/load local, registro de personajes finalizados e inyección en runs futuras.
- No incluye: nube o sincronización entre dispositivos.
- Aceptación: persistencia íntegra y aparición controlada de personajes históricos.
- Pruebas manuales: cerrar/reabrir, run encadenada con histórico y reset de datos.

### F5 - UI/UX móvil

- MVP: layout portrait, ruleta animada, panel de estado y fondos dinámicos por lugar.
- No incluye: skins múltiples ni VFX avanzados.
- Aceptación: UI usable y fluida en dispositivos Android de gama media.
- Pruebas manuales: 2 resoluciones mínimas, legibilidad 20 min y cambio de fondos estable.

### F6 - Preparación de monetización

- MVP: interfaz `IAdService` y mock con placements definidos (interstitial/rewarded).
- No incluye: campañas reales ni IAP funcional.
- Aceptación: placements activables/desactivables sin tocar gameplay core.
- Pruebas manuales: simular success/fail/cancel y validar continuidad del flujo.

### F7 - Telemetría y balance

- MVP: eventos analíticos base y export local de métricas.
- No incluye: DWH completo ni A/B testing.
- Aceptación: funnel básico de progreso trazable.
- Pruebas manuales: 5 partidas con eventos completos y ajuste de pesos verificable.

### F8 - Hardening pre-lanzamiento

- MVP: optimización base, QA de regresión y preparación operativa mínima.
- No incluye: liveops complejos día 1.
- Aceptación: build estable en sesión larga y sin bloqueos críticos.
- Pruebas manuales: 45-60 min de sesión, estrés de spins y regresión F1-F7.

## Plan de prueba manual por ciclo

1. Smoke test en Editor (5-10 min).
2. Build Android debug e instalación limpia.
3. Happy path completo de la feature.
4. 2-3 edge cases relevantes.
5. Regresión rápida de la feature anterior.
6. Registro de incidencias con feature, pasos, esperado, actual y severidad.

## Orden recomendado

F0 → F1 → F2 → F3 → F5 → F4 → F6 → F7 → F8

## Backlog post-MVP

- IAP real (remove ads, packs, rerolls premium).
- Backend cloud para perfiles y legado compartido.
- Meta-progresión por temporadas.
- Eventos narrativos en vivo.
