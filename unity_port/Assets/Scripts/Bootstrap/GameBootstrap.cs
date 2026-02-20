// GameBootstrap.cs – DontDestroyOnLoad singleton. Loads JSON data, creates GameState,
// wires up CharacterCreationFlow, WheelEngine, and AdventureFlow.
using System.Collections;
using DarkWheel.Core;
using DarkWheel.Data;
using DarkWheel.Flow;
using UnityEngine;

namespace DarkWheel.Bootstrap
{
    /// <summary>
    /// Entry-point MonoBehaviour. Attach to a single GameObject in the boot scene.
    /// Survives scene loads and exposes all game systems for UI controllers.
    /// </summary>
    public class GameBootstrap : MonoBehaviour
    {
        // ── Singleton ──
        public static GameBootstrap Instance { get; private set; }

        // ── Public systems (read by UI) ──
        public DataRoot Data { get; private set; }
        public GameState State { get; private set; }
        public AdventureFlow Adventure { get; private set; }

        // ── Internal state ──
        bool _dataLoaded;
        int _wheelIndex;            // current index in the ordered wheel list
        string[] _wheelOrder;       // built dynamically by CharacterCreationFlow
        bool _creationComplete;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            StartCoroutine(LoadAndInit());
        }

        IEnumerator LoadAndInit()
        {
            // Load JSON data from StreamingAssets (synchronous – works on all platforms)
            Data = JsonDataLoader.Load();
            _dataLoaded = Data != null;
            yield return null; // yield once so coroutine completes normally

            if (Data == null)
            {
                Debug.LogError("[GameBootstrap] Failed to load data.json");
                yield break;
            }

            // Create fresh game state
            State = new GameState();

            // Build initial wheel order from character creation
            _wheelOrder = CharacterCreationFlow.BaseWheels;
            _wheelIndex = 0;
            _creationComplete = false;

            Debug.Log($"[GameBootstrap] Loaded {Data.races?.Length ?? 0} races, " +
                      $"{Data.archetypes?.Length ?? 0} archetypes, ready to play.");
        }

        // ═══════════════════════════════════════════════════════════
        //  CHARACTER CREATION API  (called by WheelDebugController)
        // ═══════════════════════════════════════════════════════════

        public string GetCurrentWheelName()
        {
            if (_creationComplete) return Adventure != null ? Adventure.GetCurrentWheelName() : null;
            var config = CharacterCreationFlow.GetCurrentWheelConfig(State);
            return _wheelIndex < config.Count ? config[_wheelIndex] : null;
        }

        /// <summary>Returns segments for the current wheel (creation or adventure).</summary>
        public System.Collections.Generic.List<WheelSegment> GetCurrentSegments()
        {
            string name = GetCurrentWheelName();
            if (name == null) return new();
            return WheelEngine.Build(name, Data, State);
        }

        /// <summary>Process spin result, advance to next wheel or adventure phase.</summary>
        public void ProcessSpinResult(string selectedName)
        {
            if (_creationComplete)
            {
                Adventure?.HandleSpinResult(selectedName);
                return;
            }

            // Store selection
            string wheelName = GetCurrentWheelName();
            if (wheelName != null) State.Selections[wheelName] = selectedName;

            // Rebuild wheel order (sub-wheels may have been inserted)
            var config = CharacterCreationFlow.GetCurrentWheelConfig(State);
            _wheelIndex++;

            if (_wheelIndex >= config.Count)
            {
                // Character creation complete → adventure phase
                _creationComplete = true;
                Adventure = new AdventureFlow(Data, State);
                Adventure.StartAdventurePhase();
            }
        }

        /// <summary>Is character creation still in progress?</summary>
        public bool IsCreating => !_creationComplete;

        /// <summary>Is adventure phase active?</summary>
        public bool IsAdventure => _creationComplete && State?.AdventureActive == true;

        /// <summary>Is data loaded and ready?</summary>
        public bool IsReady => _dataLoaded && Data != null && State != null;

        /// <summary>Reset everything for a new game.</summary>
        public void NewGame()
        {
            State = new GameState();
            Adventure = null;
            _wheelIndex = 0;
            _creationComplete = false;
        }
    }
}
