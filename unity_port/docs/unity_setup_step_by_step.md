# Unity Setup Step by Step (Port Base)

Esta guía deja el port base funcionando en Unity para pruebas manuales rápidas.

## 1) Crear proyecto

1. Abrir Unity Hub.
2. Crear proyecto **2D Core** (Unity 2022 LTS o 2023 LTS).
3. Nombre recomendado: `DarkWheelUnity`.

## 2) Copiar carpeta base

1. Cerrar Unity (si estaba abierto).
2. Copiar `unity_port/Assets` al proyecto Unity (`<Proyecto>/Assets`).
3. Verificar que exista `<Proyecto>/Assets/StreamingAssets/data.unity.json`.
4. Si no existe, copia `data.json` y crea una versión saneada UTF-8 sin BOM llamada `data.unity.json`.
5. Comando recomendado para regenerarlo:

```powershell
powershell -ExecutionPolicy Bypass -File c:/workspace/unity_port/tools/sanitize_json.ps1
```

## 3) Crear escena principal

1. Abrir Unity y crear escena `Main.unity`.
2. Añadir un `GameObject` vacío llamado `Bootstrap`.
3. Agregar componente `GameBootstrap`.

## 4) Crear UI debug mínima

1. Crear `Canvas`.
2. Dentro del Canvas, crear 3 `Text` (Legacy):
   - `CurrentWheelText`
   - `CurrentResultText`
   - `SummaryText`
3. Crear 6 botones:
   - `Spin Character`
   - `Spin Adventure`
   - `Reset`
   - `Save`
   - `Load`
   - `Rewarded Mock`
4. Crear objeto `UIController` y agregar `WheelDebugController`.
5. Enlazar en el inspector los 3 `Text` al script.

## 5) Enlazar botones a métodos

- `Spin Character` -> `WheelDebugController.SpinCurrentWheel`
- `Spin Adventure` -> `WheelDebugController.SpinAdventureSlice`
- `Reset` -> `WheelDebugController.ResetFlow`
- `Save` -> `WheelDebugController.SaveState`
- `Load` -> `WheelDebugController.LoadState`
- `Rewarded Mock` -> `WheelDebugController.SimulateRewardedAd`

## 6) Ejecutar pruebas manuales

1. Presionar Play.
2. Pulsar `Spin Character` hasta completar las ruedas.
3. Pulsar `Spin Adventure` para generar Activity/Event/Action.
4. Probar `Save` -> detener Play -> Play -> `Load`.
5. Probar `Rewarded Mock` para validar hook de monetización.

## 7) Build Android debug

1. `File > Build Settings > Android > Switch Platform`.
2. Añadir escena `Main.unity`.
3. `Player Settings`:
   - Package Name (ejemplo): `com.darkwheel.prototype`
   - Minimum API: según dispositivo de prueba.
4. `Build` y generar APK.
5. Instalar en Android y ejecutar checklist en `docs/manual_test_checklist.md`.

## Notas

- Esta base es de **port funcional inicial**, no UI final de producción.
- El cargador prioriza `data.unity.json` y usa `data.json` como fallback.
- La próxima iteración recomendada es reemplazar UI textual por ruleta visual animada móvil.
