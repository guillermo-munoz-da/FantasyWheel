# GUÍA COMPLETA: Implementar Dark Wheel en Unity (paso a paso)

Esta guía cubre **desde cero** hasta ejecutar el juego completo en Unity Editor.  
El port consta de **16 scripts C#** organizados en 6 carpetas, un JSON de datos y un sistema de debug UI que se auto-construye en runtime.

---

## Requisitos previos

| Herramienta | Versión mínima |
|---|---|
| Unity Hub | 3.x |
| Unity Editor | **2022.3 LTS** o **2023.2+** |
| Git | 2.x (ya instalado si llegaste aquí) |
| TextMeshPro | Incluido por defecto en Unity 2022+ |

---

## Paso 1 — Crear el proyecto Unity

1. Abrir **Unity Hub → New Project**.
2. Seleccionar plantilla **2D Core** (o 2D URP si prefieres; ambas funcionan).
3. Nombre: `DarkWheelUnity` (o el que prefieras).
4. Ubicación: cualquier carpeta local.
5. Click **Create project** y esperar a que abra.

### Importar TextMeshPro

La primera vez que Unity necesite TMP, mostrará un diálogo *"Import TMP Essentials"*.  
Si no aparece automáticamente:

1. **Window → TextMeshPro → Import TMP Essential Resources**.
2. Click **Import** en la ventana que aparece.

> TMP es necesario para `DebugUiAutoBuilder.cs` y `WheelDebugController.cs`.

---

## Paso 2 — Copiar los archivos del port

### Opción A: Desde el repositorio (recomendada)

```powershell
# Clonar si aún no lo has hecho
git clone https://github.com/guillermo-munoz-da/FantasyWheel.git
cd FantasyWheel
git checkout feature/full-complexity-port
```

### Opción B: Copia manual

Copiar el contenido de `unity_port/Assets/` al directorio `Assets/` de tu proyecto Unity.

### Estructura resultante en tu proyecto

```
<TuProyecto>/Assets/
├── Scripts/
│   ├── Bootstrap/
│   │   └── GameBootstrap.cs
│   ├── Core/
│   │   ├── GameState.cs
│   │   ├── SaveService.cs
│   │   ├── WeightedSelector.cs
│   │   └── WheelModels.cs
│   ├── Data/
│   │   └── JsonDataLoader.cs
│   ├── Flow/
│   │   ├── AdventureFlow.cs
│   │   ├── CharacterCreationFlow.cs
│   │   ├── EventChainData.cs
│   │   └── WheelEngine.cs
│   ├── Monetization/
│   │   ├── IAdService.cs
│   │   ├── IIapService.cs
│   │   ├── MockAdService.cs
│   │   └── MockIapService.cs
│   └── UI/
│       ├── DebugUiAutoBuilder.cs
│       └── WheelDebugController.cs
└── StreamingAssets/
    ├── data.json
    └── data.unity.json
```

> **Importante:** Verifica que `Assets/StreamingAssets/data.json` (o `data.unity.json`) existe. Sin este archivo el juego no cargará ningún dato.

---

## Paso 3 — Esperar la compilación

1. Vuelve a Unity Editor. Se ejecutará una compilación automática.
2. Revisa la **Console** (Window → General → Console).
3. **No debería haber errores de compilación.** Si los hay, verifica:
   - Que TextMeshPro está importado (Paso 1).
   - Que todos los archivos `.cs` están en las carpetas correctas.
   - Que `data.json` está en `Assets/StreamingAssets/`.

---

## Paso 4 — Crear la escena principal

1. **File → New Scene → Basic (Built-in)** → Save como `Main.unity` en `Assets/Scenes/`.
2. Eliminar el `Main Camera` por defecto (la usaremos diferente) o déjala según prefieras.

### 4.1 — Crear el GameObject Bootstrap

1. En la **Hierarchy**, click derecho → **Create Empty**.
2. Renombrar a `Bootstrap`.
3. En el **Inspector**, click **Add Component** → buscar `GameBootstrap` → añadir.
4. En el mismo GameObject, click **Add Component** → buscar `DebugUiAutoBuilder` → añadir.

> **¿Por qué ambos en el mismo objeto?**  
> `GameBootstrap` carga los datos y gestiona el flujo del juego.  
> `DebugUiAutoBuilder` crea automáticamente toda la UI de debug (Canvas, botones, labels) en runtime — **no necesitas crear UI manualmente**.

### Resultado en el Inspector:

```
Bootstrap (GameObject)
  ├── Transform
  ├── GameBootstrap (script)
  └── DebugUiAutoBuilder (script)
```

---

## Paso 5 — Play! (primera ejecución)

1. Pulsa **▶ Play** en Unity Editor.
2. Deberías ver:

| Zona | Contenido |
|---|---|
| **Panel izquierdo** | Título "Dark Wheel", contexto, lista de segmentos con porcentajes, botones SPIN / END RUN / NEW GAME |
| **Panel derecho** | Character Sheet (vacía al inicio), Adventure Log |

3. Pulsa **SPIN** para girar la primera rueda (Race).
4. El resultado aparece en `>> [nombre seleccionado]`.
5. Sigue pulsando SPIN — el sistema recorre automáticamente:
   - **17 ruedas base** de creación de personaje (Race → Gender → Age → Archetype → Class → Alignment → 5 stats → Weapon → Power Count → Magic Count → Skill Count → Territory → Items Count).
   - **Sub-ruedas dinámicas** que se insertan según los contadores (ej: si Magic Count = 2, aparecerán Magic Type 1, Spells 1, Magic Skill 1, Magic Type 2, Spells 2, Magic Skill 2).
6. Al completar la creación, el juego pasa automáticamente a **Fase de Aventura**:
   - Travel (elegir territorio) → Activity → Event → Action → Outcome → siguiente capítulo.
   - Las cadenas de eventos (chains) se activan si la actividad/evento coincide con una cadena definida.
   - Decisiones popup se resuelven automáticamente (first option) en modo debug.
7. Pulsa **END RUN** para terminar manualmente, o espera a que ocurra death/victory.
8. Pulsa **NEW GAME** para empezar de nuevo.

---

## Paso 6 — Verificar que todo funciona

### Checklist rápido

| # | Qué verificar | Cómo |
|---|---|---|
| 1 | JSON cargado | Console muestra `[GameBootstrap] Loaded X races, Y archetypes, ready to play.` |
| 2 | Ruedas de creación | SPIN avanza por Race, Gender, Age, Archetype, Class... |
| 3 | Sub-ruedas dinámicas | Si Magic Count > 0, aparecen ruedas Magic Type N, Spells N |
| 4 | Fase de aventura activa | Tras la última rueda de creación, título cambia a "Cap. 1 - Viajar" |
| 5 | Cadenas de eventos | Si una actividad/evento coincide con un chain (ej: "Forge Legendary Gear"), se muestra la rueda del chain |
| 6 | Gold system | El character sheet muestra "Gold: 50" al inicio, cambia con gain_wealth/lose_wealth |
| 7 | Death/Victory | En outcomes, si sale un terminal "death" → aparece "MUERTE"; "victory" → "VICTORIA" |
| 8 | Save/Load funcional | Llama `SaveService.Save(state)` / `SaveService.Load()` desde un script de prueba |

---

## Paso 7 — Entender la arquitectura

### Diagrama de flujo

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│ GameBootstrap │────▶│ JsonDataLoader   │────▶│  DataRoot     │
│  (singleton)  │     │  Load()          │     │  (data.json)  │
└──────┬───────┘     └──────────────────┘     └──────────────┘
       │
       │  Character Creation Phase
       ▼
┌──────────────────────┐     ┌─────────────────────┐
│ CharacterCreationFlow│────▶│  WheelEngine.Build() │
│  GetCurrentWheelConfig│     │  → List<WheelSegment> │
└──────────────────────┘     └─────────────────────┘
       │
       │  When all wheels done
       ▼
┌──────────────┐     ┌─────────────────────┐
│ AdventureFlow │────▶│  WheelEngine.Build() │
│  (chapter loop│     │  BuildChainSegments()│
│   chains,     │     │  BuildAdventureTag   │
│   decisions)  │     │  Weights()           │
└──────┬───────┘     └─────────────────────┘
       │
       │  UI callbacks
       ▼
┌──────────────────────┐     ┌────────────────────┐
│ WheelDebugController │◀───│ DebugUiAutoBuilder  │
│  (button handlers,   │     │  (runtime Canvas)   │
│   segment list)      │     └────────────────────┘
└──────────────────────┘
```

### Namespaces

| Namespace | Responsabilidad |
|---|---|
| `DarkWheel.Bootstrap` | Entry point, singleton, lifecycle |
| `DarkWheel.Core` | Data models, game state, save/load, weighted selection |
| `DarkWheel.Data` | JSON loading from StreamingAssets |
| `DarkWheel.Flow` | Character creation, adventure loop, wheel engine, event chains |
| `DarkWheel.Monetization` | Ad/IAP interfaces + mocks (ready for real SDKs) |
| `DarkWheel.UI` | Debug UI controller + auto-builder |

### Archivos por líneas de código

| Archivo | Líneas | Rol |
|---|---|---|
| EventChainData.cs | 2072 | 27+ cadenas de eventos, límites, títulos, decisiones |
| WheelEngine.cs | 852 | Motor de ruedas (30+ tipos), tag weights, death/victory |
| AdventureFlow.cs | 731 | Loop de aventura, cadenas, efectos, viaje, fin de run |
| CharacterCreationFlow.cs | 198 | Config dinámica de ruedas, afinidades mágicas/territorio |
| WheelDebugController.cs | 190 | Controlador UI debug |
| DebugUiAutoBuilder.cs | 177 | Constructor de Canvas en runtime |
| GameBootstrap.cs | 129 | Singleton de arranque |
| GameState.cs | 118 | Estado completo del personaje y aventura |
| WheelModels.cs | 97 | 29 clases de datos + DataRoot |
| JsonDataLoader.cs | 99 | Carga de JSON con fallback UTF-8/BOM |
| SaveService.cs | 84 | Save/Load a JSON local |
| WeightedSelector.cs | 58 | Selector aleatorio ponderado |

---

## Paso 8 — Personalización y próximos pasos

### 8.1 — Reemplazar la UI de debug por UI final

El `DebugUiAutoBuilder` crea UI funcional pero fea. Para la UI final:

1. **Elimina** el componente `DebugUiAutoBuilder` del Bootstrap.
2. **Crea manualmente** un Canvas con:
   - Un prefab de **rueda circular** (shader o sprite-based).
   - Labels TMP para título, contexto, resultado.
   - Scroll view para el character sheet.
   - Botones estilizados.
3. **Crea un nuevo MonoBehaviour** (ej: `GameUIController`) que:
   - Referencie los elementos UI por `[SerializeField]`.
   - Use `GameBootstrap.Instance` para obtener datos.
   - Implemente animación de giro.
   - Muestre popups de decisión reales (en vez de auto-pick).

### 8.2 — Implementar la rueda circular visual

El script `ruleta_circular.py` del prototipo tiene la lógica de rendering.  
En Unity, opciones comunes:

| Técnica | Pros | Contras |
|---|---|---|
| **UI Image + Shader** | Smooth, GPU-based | Requiere shader custom |
| **LineRenderer / Mesh** | Flexible | Más código |
| **Sprite segments** | Simple | Muchos sprites |
| **Canvas wedges** | Pure UGUI | Limitado en estilo |

La rueda necesita:
- Dibujarse con N segmentos proporcionales a `WheelSegment.Weight`.
- Animación de giro (easing: fast start → slow stop).
- Indicador fijo (flecha) que señala el segmento ganador.

### 8.3 — Conectar monetización real

Los interfaces ya están preparados:

```csharp
// Reemplazar MockAdService por tu SDK real:
public class AdMobService : IAdService
{
    public bool IsEnabled => true;
    public void ShowInterstitial(string p) { /* AdMob API */ }
    public bool ShowRewarded(string p, out bool r) { /* AdMob API */ r = true; return true; }
}
```

### 8.4 — Build Android

1. **File → Build Settings → Android** → Switch Platform.
2. **Player Settings:**
   - Company Name / Product Name.
   - Package Name: `com.tucompany.darkwheel`.
   - Minimum API Level: 24+.
   - Target API Level: 34.
3. **StreamingAssets** se incluye automáticamente en el APK.
4. **Build & Run** con dispositivo USB o emulador.

> **Nota Android:** `JsonDataLoader.Load()` usa `File.ReadAllBytes()` que funciona con StreamingAssets en Android porque Unity lo extrae automáticamente. Si encuentras problemas, cambia a `UnityWebRequest` para leer desde `Application.streamingAssetsPath`.

### 8.5 — Save/Load

El `SaveService` ya está implementado:

```csharp
// Guardar
SaveService.Save(GameBootstrap.Instance.State);

// Cargar
GameState loaded = SaveService.Load();
if (loaded != null) GameBootstrap.Instance.State = loaded;

// Borrar
SaveService.Delete();
```

Los datos se guardan en `Application.persistentDataPath/save.json`.

---

## Paso 9 — Troubleshooting

| Problema | Solución |
|---|---|
| `TMP_Text not found` | Window → TextMeshPro → Import TMP Essential Resources |
| `data.json not found` | Verificar que existe `Assets/StreamingAssets/data.json` o `data.unity.json` |
| `NullReferenceException` en GameBootstrap | Verificar que el componente está en la escena y que el JSON se cargó (ver Console) |
| No aparece UI al dar Play | Verificar que `DebugUiAutoBuilder` está como componente en el mismo GO que `GameBootstrap` |
| Los segmentos están vacíos | El JSON puede no tener los arrays esperados. Verificar estructura de `data.json` con las claves de `DataRoot` |
| Error en Android: file not found | Cambiar `File.ReadAllBytes` por `UnityWebRequest.Get(Application.streamingAssetsPath + "/data.json")` en `JsonDataLoader.cs` |
| Rueda no avanza después de SPIN | Verificar Console por excepciones. El flujo debería ser automático |

---

## Paso 10 — Resumen de sistemas del prototipo portados

| Sistema Python | Archivo C# | Estado |
|---|---|---|
| `build_wheel_data()` (todas las ruedas) | `WheelEngine.cs` | ✅ Completo |
| `build_adventure_tag_weights()` | `WheelEngine.cs` | ✅ Completo |
| `compute_death_weight()` / `compute_victory_weight()` | `WheelEngine.cs` | ✅ Completo |
| `build_chain_wheel_segments()` | `WheelEngine.cs` | ✅ Completo |
| `get_current_wheel_config()` (sub-ruedas dinámicas) | `CharacterCreationFlow.cs` | ✅ Completo |
| `build_magic_affinities()` | `CharacterCreationFlow.cs` | ✅ Completo |
| `build_territory_affinities()` | `CharacterCreationFlow.cs` | ✅ Completo |
| `spell_magic_map` | `CharacterCreationFlow.cs` | ✅ Completo |
| EVENT_CHAINS (27+ cadenas) | `EventChainData.cs` | ✅ Completo |
| CHAIN_LIMITS / CHAIN_TITLES | `EventChainData.cs` | ✅ Completo |
| ADVENTURE_DECISIONS (10 decisiones) | `EventChainData.cs` | ✅ Completo |
| CONDITION_DESCRIPTIONS | `EventChainData.cs` | ✅ Completo |
| `start_chain` / `handle_chain_result` / `end_chain` | `AdventureFlow.cs` | ✅ Completo |
| `apply_chain_effects` (13 tipos de efecto) | `AdventureFlow.cs` | ✅ Completo |
| `handle_adventure_result` / `advance_adventure` | `AdventureFlow.cs` | ✅ Completo |
| `show_decision_popup` | `AdventureFlow.cs` | ✅ Completo |
| `end_run` (death/victory/manual) | `AdventureFlow.cs` | ✅ Completo |
| `update_reputation_from_outcome` | `AdventureFlow.cs` | ✅ Completo |
| Travel system + sublocations | `WheelEngine.cs` + `AdventureFlow.cs` | ✅ Completo |
| `weighted_choice()` | `WeightedSelector.cs` | ✅ Completo |
| State management | `GameState.cs` | ✅ Completo |
| JSON data loading | `JsonDataLoader.cs` | ✅ Completo |
| Save/Load | `SaveService.cs` | ✅ Completo |
| Monetización (interfaces) | `Monetization/*.cs` | ✅ Mock ready |
