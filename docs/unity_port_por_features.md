# Port a Unity (Android primero) - Plan por Features

## Objetivo

Portar el prototipo actual de Python a Unity con arquitectura data-driven, UI minimalista oscura y capacidad de pruebas manuales continuas en cada incremento.

## Enfoque de trabajo

- Desarrollo por features verticales (cada feature termina en algo jugable).
- Cada feature incluye alcance, criterios de aceptación, checklist de pruebas manuales y salida esperada.
- Validación en dispositivo Android real en cada feature crítica.

## Feature backlog (orden recomendado)

### F0 - Base técnica Unity

- Alcance: proyecto Unity LTS (2022/2023), escena base, estructura de carpetas y bootstrap de estado.
- Aceptación: app abre en Android sin errores y puede mostrar al menos una rueda cargada desde JSON.
- Pruebas manuales: build APK debug, abrir/cerrar app 5 veces y validar logs de carga.

### F1 - Core Wheel Engine

- Alcance: selección ponderada por peso, API genérica de rueda y semilla opcional para reproducibilidad.
- Aceptación: spin válido y consistente con pesos; misma seed produce misma secuencia.
- Pruebas manuales: 100 spins de rueda de test y repetición con seed fija.

### F2 - Character Creation Flow

- Alcance: flujo Race → Archetype → Class → Height → Age → Gender/Alignment → Place.
- Aceptación: flujo completo sin bloqueos y dependencias correctas entre subruedas.
- Pruebas manuales: 20 generaciones completas y casos dirigidos de dependencias.

### F3 - Dynamic Modifiers System

- Alcance: reglas dinámicas para pesos, bloqueos/desbloqueos y condiciones de estado.
- Aceptación: cambios de probabilidad visibles y aparición/desaparición de opciones según contexto.
- Pruebas manuales: forzar condiciones y comparar spins con/sin condición activa.

### F4 - Adventure Phase (Tree Chains)

- Alcance: Activity → Event → Action → Outcome y cadenas especiales por actividad.
- Aceptación: run completa de aventura y efectos persistentes que afectan ruedas posteriores.
- Pruebas manuales: 15 runs completas con al menos 3 finales distintos.

### F5 - UI/UX Mobile minimalista

- Alcance: tema oscuro limpio, rueda central, botón girar, panel de estado y fondos por Place.
- Aceptación: UI legible en 3 resoluciones Android y animaciones fluidas.
- Pruebas manuales: test visual en distintos tamaños y 30 spins continuos.

### F6 - Save/Load + telemetría base

- Alcance: guardado/carga local y eventos analíticos básicos (inicio run, spin, final run).
- Aceptación: cerrar/reabrir conserva estado y eventos quedan registrados.
- Pruebas manuales: 5 ciclos save/load verificando integridad.

### F7 - Preparación monetización (sin activar)

- Alcance: interfaces `AdService` (rewarded/interstitial) con mocks e interfaz futura `IAPService`.
- Aceptación: juego operativo con y sin proveedor de anuncios.
- Pruebas manuales: simular success/fail/cancel sin romper UX.

### F8 - Legacy Heroes (futuro)

- Alcance: personajes finalizados reaparecen como contenido de ruedas/eventos futuros.
- Aceptación: un personaje de run A puede aparecer en run B.
- Pruebas manuales: completar run A y verificar aparición controlada en run B.

## Ritual de prueba manual por sprint

1. Seleccionar 1-2 features máximo por sprint.
2. Preparar checklist de casos felices y edge cases.
3. Ejecutar en Editor y Android real.
4. Registrar bugs con pasos, esperado, actual y evidencia.
5. Cerrar sprint sólo cuando se cumplan los criterios de aceptación.

## Plantilla rápida de caso manual

- Feature:
- Build:
- Escenario:
- Pasos:
- Resultado esperado:
- Resultado actual:
- Estado: OK / KO

## Definición de done por feature

- Criterios de aceptación cumplidos.
- Checklist manual ejecutado y documentado.
- Sin bloqueos críticos (crash, soft-lock, pérdida de progreso).
- Build Android de validación disponible.

## Próximo incremento recomendado

- Implementar F0 + F1 + primer slice de F2 (Race/Archetype/Class) como MVP técnico-jugable.
