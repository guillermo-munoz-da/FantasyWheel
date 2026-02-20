// WheelDebugController.cs – TMP-based debug controller for the circular wheel.
// Reads from GameBootstrap, renders segments as a list, handles spin simulation.
using System.Collections.Generic;
using DarkWheel.Bootstrap;
using DarkWheel.Core;
using DarkWheel.Flow;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace DarkWheel.UI
{
    /// <summary>
    /// Minimal debug UI that drives the game loop via GameBootstrap.
    /// Attach to a Canvas with children built by DebugUiAutoBuilder or manually.
    /// </summary>
    public class WheelDebugController : MonoBehaviour
    {
        [Header("UI References")]
        [SerializeField] TMP_Text _titleLabel;
        [SerializeField] TMP_Text _contextLabel;
        [SerializeField] TMP_Text _resultLabel;
        [SerializeField] TMP_Text _charSheetText;
        [SerializeField] TMP_Text _logText;
        [SerializeField] Button _spinButton;
        [SerializeField] Button _endRunButton;
        [SerializeField] Button _newGameButton;
        [SerializeField] Transform _segmentListParent;
        [SerializeField] GameObject _segmentPrefab;

        GameBootstrap _boot;
        List<WheelSegment> _currentSegments;

        void Start()
        {
            _boot = GameBootstrap.Instance;
            if (_boot == null)
            {
                Debug.LogError("[WheelDebugController] GameBootstrap.Instance is null. Place GameBootstrap in your scene.");
                return;
            }

            _spinButton?.onClick.AddListener(OnSpinClicked);
            _endRunButton?.onClick.AddListener(OnEndRunClicked);
            _newGameButton?.onClick.AddListener(OnNewGameClicked);

            // Wire adventure callbacks
            WireAdventureCallbacks();
        }

        void Update()
        {
            if (_boot == null || !_boot.IsReady) return;

            // Refresh wheel if changed (lazy refresh)
            if (_currentSegments == null)
                RefreshWheel();
        }

        // ═══════════════════════════════════════════════════════════
        //  REFRESH
        // ═══════════════════════════════════════════════════════════

        void RefreshWheel()
        {
            string wheelName = _boot.GetCurrentWheelName();
            if (wheelName == null)
            {
                if (_titleLabel) _titleLabel.text = "Done";
                return;
            }

            _currentSegments = _boot.GetCurrentSegments();
            if (_titleLabel) _titleLabel.text = _boot.IsCreating ? $"Creacion: {wheelName}" : wheelName;
            if (_contextLabel) _contextLabel.text = WheelEngine.GetWheelContext(wheelName, _boot.State);

            RenderSegmentList();
            RefreshCharSheet();
        }

        void RenderSegmentList()
        {
            if (_segmentListParent == null || _segmentPrefab == null) return;

            // Clear old entries
            foreach (Transform child in _segmentListParent)
                Destroy(child.gameObject);

            if (_currentSegments == null) return;

            float totalWeight = 0f;
            foreach (var s in _currentSegments) totalWeight += s.Weight;

            foreach (var seg in _currentSegments)
            {
                var go = Instantiate(_segmentPrefab, _segmentListParent);
                var tmp = go.GetComponentInChildren<TMP_Text>();
                if (tmp)
                {
                    float pct = totalWeight > 0 ? seg.Weight / totalWeight * 100f : 0f;
                    tmp.text = $"{seg.Name}  ({pct:F1}%)";
                }
            }
        }

        void RefreshCharSheet()
        {
            if (_charSheetText == null || _boot.State == null) return;

            var sb = new System.Text.StringBuilder();
            foreach (var kv in _boot.State.Selections)
            {
                if (kv.Key.StartsWith("_")) continue; // hide internal keys
                sb.AppendLine($"{kv.Key}: {kv.Value}");
            }
            sb.AppendLine($"Gold: {_boot.State.Gold}");

            if (_boot.State.Conditions.Count > 0)
            {
                sb.AppendLine("\nConditions:");
                foreach (var c in _boot.State.Conditions) sb.AppendLine($"  - {c}");
            }

            if (_boot.State.Titles.Count > 0)
            {
                sb.AppendLine("\nTitles:");
                foreach (var t in _boot.State.Titles) sb.AppendLine($"  * {t}");
            }

            _charSheetText.text = sb.ToString();
        }

        void RefreshLog()
        {
            if (_logText == null || _boot.State == null) return;
            _logText.text = string.Join("\n", _boot.State.AdventureLog);
        }

        // ═══════════════════════════════════════════════════════════
        //  SPIN
        // ═══════════════════════════════════════════════════════════

        void OnSpinClicked()
        {
            if (_currentSegments == null || _currentSegments.Count == 0) return;

            // Weighted random pick
            float[] weights = new float[_currentSegments.Count];
            for (int i = 0; i < _currentSegments.Count; i++) weights[i] = _currentSegments[i].Weight;
            int idx = WeightedSelector.Pick(weights);

            var selected = _currentSegments[idx];
            if (_resultLabel) _resultLabel.text = $">> {selected.Name}";

            // Process
            if (_boot.IsCreating)
            {
                _boot.ProcessSpinResult(selected.Name);
                WireAdventureCallbacks(); // in case adventure just started
            }
            else
            {
                _boot.Adventure?.HandleSpinResult(selected.Name, selected.ChainOptionData);
            }

            _currentSegments = null; // force refresh on next Update
            RefreshLog();
        }

        void OnEndRunClicked()
        {
            _boot.Adventure?.EndRunManual();
        }

        void OnNewGameClicked()
        {
            _boot.NewGame();
            _currentSegments = null;
            if (_resultLabel) _resultLabel.text = "";
            if (_logText) _logText.text = "";
        }

        // ═══════════════════════════════════════════════════════════
        //  ADVENTURE CALLBACKS
        // ═══════════════════════════════════════════════════════════

        void WireAdventureCallbacks()
        {
            if (_boot.Adventure == null) return;

            _boot.Adventure.OnShowWheel = (title, context, segments) =>
            {
                if (_titleLabel) _titleLabel.text = title;
                if (_contextLabel) _contextLabel.text = context;
                _currentSegments = segments;
                RenderSegmentList();
                RefreshCharSheet();
            };

            _boot.Adventure.OnEndRun = (reason, title, msg) =>
            {
                if (_titleLabel) _titleLabel.text = title;
                if (_resultLabel) _resultLabel.text = msg;
                string summary = _boot.Adventure.BuildEndRunSummary();
                if (_logText) _logText.text = summary;
                RefreshCharSheet();
            };

            _boot.Adventure.OnShowDecision = (eventName, decision) =>
            {
                // In debug mode, auto-pick first option
                Debug.Log($"[Decision] {eventName}: {decision.Prompt}");
                if (decision.Options != null && decision.Options.Count > 0)
                {
                    _boot.Adventure.OnDecisionMade(decision.Options[0]);
                }
            };

            _boot.Adventure.OnStateChanged = () =>
            {
                RefreshCharSheet();
                RefreshLog();
            };
        }
    }
}
