# Unity Port Starter (Android first)

Este paquete contiene una base funcional para iniciar el port del prototipo Python a Unity por features.

## Estructura

- `Assets/Scripts/Bootstrap`: inicialización global (`GameBootstrap`).
- `Assets/Scripts/Core`: estado, modelos, weighted selector y guardado.
- `Assets/Scripts/Data`: carga de JSON desde `StreamingAssets`.
- `Assets/Scripts/Flow`: motor de ruletas y flujos de creación/aventura.
- `Assets/Scripts/Monetization`: interfaces y mocks de Ads/IAP.
- `Assets/Scripts/UI`: controlador de debug para pruebas manuales rápidas.

## Requisitos

- Unity 2022 LTS o 2023 LTS.
- Target Android instalado en Unity Hub.

## Setup rápido en Unity

1. Crea un proyecto Unity 2D vacío.
2. Copia la carpeta `unity_port/Assets` dentro del proyecto Unity.
3. Verifica que existe `Assets/StreamingAssets/data.unity.json` (prioritario) y `Assets/StreamingAssets/data.json` (fallback).
4. Crea una escena `Main.unity`.
5. Añade un `GameObject` llamado `Bootstrap` y agrega `GameBootstrap`.
6. Crea un Canvas simple con 3 `Text` y 6 botones:
   - Text: `currentWheelText`, `currentResultText`, `summaryText`
   - Botones: `Spin Character`, `Spin Adventure`, `Reset`, `Save`, `Load`, `Rewarded Mock`
7. Añade `WheelDebugController` a un objeto `UIController` y enlaza referencias.
8. Conecta eventos `OnClick` de botones a:
   - `SpinCurrentWheel`
   - `SpinAdventureSlice`
   - `ResetFlow`
   - `SaveState`
   - `LoadState`
   - `SimulateRewardedAd`

Guía detallada: `docs/unity_setup_step_by_step.md`.

## Qué puedes probar ya

- F0: arranque de app, bootstrap y carga de JSON.
- F1: spin ponderado por rueda.
- F2 (slice): flujo de creación de personaje con dependencias básicas Archetype -> Class.
- F6 (preparación): hooks de anuncios mock y persistencia local.

## Limitaciones actuales (esperadas)

- Sin UI final de ruleta animada todavía (debug UI textual).
- Sin árbol profundo de eventos especiales del prototipo.
- Sin integración de SDK de anuncios real.

## Siguiente implementación recomendada

1. Reemplazar UI debug por rueda visual móvil.
2. Migrar reglas dinámicas avanzadas de dependencias/condiciones.
3. Implementar Adventure chains completas y finales.
4. Integrar proveedor de ads real detrás de `IAdService`.

## Publicación en GitHub

- Ver `docs/github_publish_guide.md` para comandos listos (repo dedicado o monorepo actual).
