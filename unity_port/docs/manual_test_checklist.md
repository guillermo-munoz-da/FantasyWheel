# Manual Test Checklist - Unity Port

## Build info

- Feature:
- Build/Commit:
- Dispositivo Android:
- Tester:
- Fecha:

## Smoke (siempre)

- [ ] App abre en editor sin errores de consola.
- [ ] App abre en Android sin crash.
- [ ] Pantalla responde a input táctil.

## F0/F1 - Core

- [ ] `data.json` carga correctamente (sin null en ruedas base).
- [ ] 20 spins consecutivos sin errores.
- [ ] No aparecen opciones con peso 0 o bloqueadas indebidamente.

## F2 - Character flow

- [ ] Flujo completo hasta MagicType.
- [ ] Archetype filtra Class de forma coherente.
- [ ] Reset no conserva estado previo.

## Save/Load

- [ ] Guardar a mitad de flujo.
- [ ] Cerrar app y reabrir.
- [ ] Cargar y validar estado restaurado.

## Ads mock

- [ ] Rewarded success aplica resultado esperado.
- [ ] Rewarded fail/cancel no bloquea flujo.
- [ ] Interstitial no interrumpe input.

## Registro de incidencias

- Caso:
- Pasos:
- Esperado:
- Actual:
- Severidad: Bloqueante / Alta / Media / Baja
- Evidencia: captura o video
