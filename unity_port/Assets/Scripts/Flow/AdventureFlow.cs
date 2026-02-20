// AdventureFlow.cs – Adventure phase management, chain execution, decisions, travel, end-run.
// Full 1:1 port of Python adventure system including chains, decisions, travel, and end_run.
using System;
using System.Collections.Generic;
using System.Linq;
using DarkWheel.Core;
using UnityEngine;
using Random = UnityEngine.Random;

namespace DarkWheel.Flow
{
    /// <summary>Phases within each adventure chapter.</summary>
    public enum AdventureStep { Activity = 0, Event = 1, Action = 2, Outcome = 3 }

    /// <summary>End-of-run reasons.</summary>
    public enum RunEndReason { Death, Victory, Manual }

    /// <summary>Result of a single chain effect application, for UI feedback.</summary>
    public readonly struct EffectLogEntry
    {
        public readonly string Text;
        public EffectLogEntry(string text) => Text = text;
    }

    /// <summary>
    /// Manages the adventure phase (post-character-creation). Handles:
    ///   – Adventure wheel sequencing (Activity → Event → Action → Outcome)
    ///   – Event chain lifecycle (start, spin, result, effects, end)
    ///   – Decision popups (tag mods + rep)
    ///   – Travel (territory + sublocation)
    ///   – End run (death / victory / manual)
    ///   – Reputation updates from outcomes
    /// </summary>
    public class AdventureFlow
    {
        static readonly string[] StepLabels = { "Actividad", "Evento", "Accion", "Resultado" };
        static readonly string[] AdventureStepPrefixes = { "Adventure Activity", "Adventure Event", "Adventure Action", "Adventure Outcome" };

        readonly DataRoot _data;
        readonly GameState _state;

        // ── Callbacks for the UI layer ──
        public Action<string, string, List<WheelSegment>> OnShowWheel; // title, context, segments
        public Action<string, DecisionDef> OnShowDecision;             // eventName, definition
        public Action<RunEndReason, string, string> OnEndRun;          // reason, title, message
        public Action OnStateChanged;                                   // repaint character display

        public AdventureFlow(DataRoot data, GameState state)
        {
            _data = data;
            _state = state;
        }

        // ═══════════════════════════════════════════════════════════
        //  START ADVENTURE
        // ═══════════════════════════════════════════════════════════

        public void StartAdventurePhase()
        {
            _state.AdventureActive = true;
            _state.Chapter = 1;
            _state.Step = 0;
            _state.TravelDoneForChapter = false;
            _state.TravelActive = false;

            // Initialize faction reputation
            var factionNames = _data.factions?.Select(f => f.name) ?? Enumerable.Empty<string>();
            _state.InitReputation(factionNames);

            ShowAdventureWheel();
        }

        // ═══════════════════════════════════════════════════════════
        //  WHEEL NAME / LABEL
        // ═══════════════════════════════════════════════════════════

        public string GetCurrentWheelName()
            => $"{AdventureStepPrefixes[_state.Step]} {_state.Chapter}";

        // ═══════════════════════════════════════════════════════════
        //  SHOW WHEELS
        // ═══════════════════════════════════════════════════════════

        public void ShowAdventureWheel()
        {
            // If a chain is active, show the chain wheel instead
            if (_state.ChainActive)
            {
                ShowChainWheel();
                return;
            }

            // Travel check: before Activity (step 0), check if travel is needed
            if (_state.Step == 0 && !_state.TravelDoneForChapter)
            {
                ShowTravelWheel();
                return;
            }

            string wheelName = GetCurrentWheelName();
            string title = $"Cap. {_state.Chapter} - {StepLabels[_state.Step]}";
            string context = WheelEngine.GetWheelContext(wheelName, _state);

            var segments = WheelEngine.Build(wheelName, _data, _state);
            OnShowWheel?.Invoke(title, context, segments);
        }

        public void ShowTravelWheel()
        {
            _state.TravelActive = true;
            string title = $"Cap. {_state.Chapter} - Viajar";
            string context = WheelEngine.GetWheelContext("Travel", _state);
            var segments = WheelEngine.Build("Travel", _data, _state);

            if (segments == null || segments.Count == 0)
            {
                // Skip travel if no options
                _state.TravelActive = false;
                _state.TravelDoneForChapter = true;
                ShowAdventureWheel();
                return;
            }

            OnShowWheel?.Invoke(title, context, segments);
        }

        void ShowChainWheel()
        {
            if (string.IsNullOrEmpty(_state.ChainName) || string.IsNullOrEmpty(_state.ChainStepId))
            {
                EndChain();
                return;
            }

            if (!EventChainData.Chains.TryGetValue(_state.ChainName, out var chainDef))
            {
                EndChain();
                return;
            }

            var step = chainDef.Steps.FirstOrDefault(s => s.Id == _state.ChainStepId);
            if (step == null) { EndChain(); return; }

            string title = $"Cap. {_state.Chapter} - {step.Label}";
            string context = $"{_state.ChainName}: {step.Label}";
            var segments = WheelEngine.BuildChainSegments(_state);

            if (segments.Count == 0) { EndChain(); return; }
            OnShowWheel?.Invoke(title, context, segments);
        }

        // ═══════════════════════════════════════════════════════════
        //  HANDLE SPIN RESULT  (dispatch based on context)
        // ═══════════════════════════════════════════════════════════

        /// <summary>Call this when the wheel spin completes. Dispatches to the right handler.</summary>
        public void HandleSpinResult(string selectedName, ChainOption chainOptionData = null)
        {
            if (_state.TravelActive)
            {
                HandleTravelResult(selectedName);
                return;
            }

            if (_state.ChainActive)
            {
                HandleChainResult(selectedName, chainOptionData);
                return;
            }

            HandleAdventureResult(selectedName);
        }

        // ═══════════════════════════════════════════════════════════
        //  ADVENTURE RESULT
        // ═══════════════════════════════════════════════════════════

        void HandleAdventureResult(string selectedName)
        {
            int step = _state.Step;
            int chapter = _state.Chapter;
            string wheelKey = GetCurrentWheelName();

            _state.Selections[wheelKey] = selectedName;

            // Step 0: Activity → check if this triggers a chain
            if (step == 0)
            {
                if (EventChainData.Chains.ContainsKey(selectedName))
                {
                    OnStateChanged?.Invoke();
                    StartChain(selectedName);
                    return;
                }
            }

            // Step 1: Event → decisions / chains / travel
            if (step == 1)
            {
                // Decision popup?
                if (EventChainData.AdventureDecisions.TryGetValue(selectedName, out var decision))
                {
                    OnStateChanged?.Invoke();
                    OnShowDecision?.Invoke(selectedName, decision);
                    return; // Decision popup will call OnDecisionMade → AdvanceAdventure
                }
                // Chain?
                if (EventChainData.Chains.ContainsKey(selectedName))
                {
                    OnStateChanged?.Invoke();
                    StartChain(selectedName);
                    return;
                }
                // Travel trigger?
                if (WheelEngine.ShouldTriggerTravel(selectedName, _data))
                {
                    _state.TravelActive = true;
                    _state.TravelDoneForChapter = false;
                    OnStateChanged?.Invoke();
                    ShowTravelWheel();
                    return;
                }
            }

            // Step 3: Outcome → terminal checks, reputation, log
            if (step == 3)
            {
                var outcomeData = _data.adventure_outcomes?.FirstOrDefault(o => o.name == selectedName);

                if (outcomeData?.terminal == "death")
                {
                    OnStateChanged?.Invoke();
                    FireEndRun(RunEndReason.Death, selectedName);
                    return;
                }
                if (outcomeData?.terminal == "victory")
                {
                    OnStateChanged?.Invoke();
                    FireEndRun(RunEndReason.Victory, selectedName);
                    return;
                }

                // Update reputation
                UpdateReputationFromOutcome(selectedName, chapter);

                // Log chapter summary
                string activity = _state.Selections.GetValueOrDefault($"Adventure Activity {chapter}", "?");
                string evt = _state.Selections.GetValueOrDefault($"Adventure Event {chapter}", "?");
                string action = _state.Selections.GetValueOrDefault($"Adventure Action {chapter}", "?");
                _state.LogAppend($"Cap.{chapter}: {activity} > {evt} > {action} > {selectedName}");

                // Clear temporary decision mods
                _state.DecisionMods.Clear();
            }

            OnStateChanged?.Invoke();
            AdvanceAdventure();
        }

        // ═══════════════════════════════════════════════════════════
        //  ADVANCE ADVENTURE
        // ═══════════════════════════════════════════════════════════

        public void AdvanceAdventure()
        {
            _state.Step += 1;
            if (_state.Step > 3)
            {
                _state.Step = 0;
                _state.Chapter += 1;
                _state.TravelDoneForChapter = false;
                _state.TravelActive = false;
            }
            ShowAdventureWheel();
        }

        // ═══════════════════════════════════════════════════════════
        //  DECISION HANDLING
        // ═══════════════════════════════════════════════════════════

        /// <summary>Call when user picks a decision option from the popup.</summary>
        public void OnDecisionMade(DecisionOption option)
        {
            // Apply tag mods
            if (option.TagMods != null)
                foreach (var kv in option.TagMods)
                    _state.DecisionMods[kv.Key] = Mathf.Max(_state.DecisionMods.GetValueOrDefault(kv.Key, 1f), kv.Value);

            // Apply reputation
            if (option.Rep != null)
                foreach (var kv in option.Rep)
                {
                    if (!_state.Reputation.ContainsKey(kv.Key))
                        _state.Reputation[kv.Key] = 0;
                    _state.Reputation[kv.Key] += kv.Value;
                }

            OnStateChanged?.Invoke();
            AdvanceAdventure();
        }

        // ═══════════════════════════════════════════════════════════
        //  TRAVEL
        // ═══════════════════════════════════════════════════════════

        void HandleTravelResult(string selectedName)
        {
            _state.TravelActive = false;
            _state.TravelDoneForChapter = true;
            _state.CurrentTerritory = selectedName;
            _state.CurrentSublocation = WheelEngine.PickSublocation(selectedName);

            _state.Selections["Territory"] = selectedName;
            if (_state.CurrentSublocation != null)
                _state.Selections["_Sublocation"] = _state.CurrentSublocation;
            else
                _state.Selections.Remove("_Sublocation");

            string subPart = _state.CurrentSublocation != null ? $" ({_state.CurrentSublocation})" : "";
            _state.LogAppend($"Viajas a {selectedName}{subPart}");

            OnStateChanged?.Invoke();

            // After travel, proceed with adventure flow
            if (_state.AdventureActive && _state.Step == 1)
                AdvanceAdventure();
            else
                ShowAdventureWheel();
        }

        // ═══════════════════════════════════════════════════════════
        //  CHAIN SYSTEM
        // ═══════════════════════════════════════════════════════════

        public bool StartChain(string chainName)
        {
            if (!EventChainData.Chains.TryGetValue(chainName, out var chainDef))
                return false;

            // Check blocked_by condition
            if (chainDef.BlockedBy != null && _state.Conditions.Contains(chainDef.BlockedBy))
            {
                string msg = chainDef.BlockedMessage ?? $"Esta accion esta bloqueada ({chainDef.BlockedBy}).";
                _state.LogAppend($"[BLOQUEADO] {msg}");
                AdvanceAdventure();
                return true;
            }

            _state.ChainActive = true;
            _state.ChainName = chainName;
            _state.ChainStepId = chainDef.Steps[0].Id;
            _state.ChainChoices.Clear();
            _state.ChainTempVars.Clear();

            ShowChainWheel();
            return true;
        }

        void HandleChainResult(string selectedName, ChainOption selectedOpt)
        {
            string chainName = _state.ChainName;
            string stepId = _state.ChainStepId;

            if (!EventChainData.Chains.TryGetValue(chainName, out var chainDef))
            { EndChain(); return; }

            var step = chainDef.Steps.FirstOrDefault(s => s.Id == stepId);
            if (step == null) { EndChain(); return; }

            // Find selected option if not passed
            if (selectedOpt == null)
                selectedOpt = step.Options.FirstOrDefault(o => o.Name == selectedName);
            if (selectedOpt == null) { EndChain(); return; }

            // Store choice
            _state.ChainChoices[stepId] = selectedName;

            // Apply immediate effects
            string contextStat = step.StatCheck;
            var logs = ApplyChainEffects(selectedOpt.Effects, contextStat);
            foreach (var log in logs) _state.LogAppend(log.Text);

            // Store temp vars
            if (selectedOpt.Effects != null)
                foreach (var kv in selectedOpt.Effects)
                    if (kv.Key.StartsWith("_"))
                        _state.ChainTempVars[kv.Key] = kv.Value;

            // Store in selections for display
            string selKey = $"{step.Label} (Cap.{_state.Chapter})";
            _state.Selections[selKey] = selectedName;
            OnStateChanged?.Invoke();

            // Terminal death check
            if (selectedOpt.Effects != null && selectedOpt.Effects.TryGetValue("terminal", out object termVal))
            {
                if (termVal?.ToString() == "death")
                {
                    FireEndRun(RunEndReason.Death, selectedOpt.Desc ?? selectedName);
                    return;
                }
            }

            // Move to next step
            if (selectedOpt.Next != null)
            {
                _state.ChainStepId = selectedOpt.Next;
                ShowChainWheel();
            }
            else
            {
                EndChain();
            }
        }

        void EndChain()
        {
            string chainName = _state.ChainName ?? "?";

            // Track completion
            _state.CompletedChains.TryGetValue(chainName, out int cnt);
            _state.CompletedChains[chainName] = cnt + 1;

            // Check title awards
            foreach (var kv in _state.ChainChoices)
            {
                var titleKey = (chainName, kv.Value);
                if (EventChainData.ChainTitles.TryGetValue(titleKey, out string newTitle))
                {
                    if (!_state.Titles.Contains(newTitle))
                    {
                        _state.Titles.Add(newTitle);
                        _state.LogAppend($"  [TITULO] Obtienes: {newTitle}");
                    }
                }
            }

            // Log chain summary
            string choicesStr = string.Join(" > ", _state.ChainChoices.Values);
            _state.LogAppend($"Cap.{_state.Chapter}: {chainName} > {choicesStr}");

            // Reset chain state
            _state.ChainActive = false;
            _state.ChainName = null;
            _state.ChainStepId = null;
            _state.ChainChoices.Clear();
            _state.ChainTempVars.Clear();
            _state.DecisionMods.Clear();
            OnStateChanged?.Invoke();

            // Random event chance (30%)
            if (Random.value < 0.3f)
            {
                string eventChain = WheelEngine.PickRandomEventChain(_data, _state);
                if (eventChain != null)
                {
                    _state.LastRandomEventChapter = _state.Chapter;
                    _state.LastRandomEventName = eventChain;
                    _state.Chapter += 1;
                    _state.Step = 0;
                    _state.TravelDoneForChapter = false;
                    _state.TravelActive = false;
                    StartChain(eventChain);
                    return;
                }
            }

            // Advance chapter
            _state.Chapter += 1;
            _state.Step = 0;
            _state.TravelDoneForChapter = false;
            _state.TravelActive = false;
            ShowAdventureWheel();
        }

        // ═══════════════════════════════════════════════════════════
        //  APPLY CHAIN EFFECTS
        // ═══════════════════════════════════════════════════════════

        List<EffectLogEntry> ApplyChainEffects(Dictionary<string, object> effects, string contextStat)
        {
            var logs = new List<EffectLogEntry>();
            if (effects == null) return logs;

            // stat_boost
            if (effects.TryGetValue("stat_boost", out object sbObj) && TryInt(sbObj, out int statBoost) && statBoost > 0)
            {
                string stat = contextStat;
                var validStats = new[] { "Strength", "Agility", "Durability", "Intelligence", "Charisma" };
                if (stat == null || !validStats.Contains(stat))
                    stat = validStats[Random.Range(0, validStats.Length)];
                int old = _state.GetStatValue(stat);
                int nv = Mathf.Min(10, old + statBoost);
                _state.SetStat(stat, nv);
                logs.Add(new EffectLogEntry($"  [+{statBoost}] {stat}: {old} -> {nv}"));
            }

            // stat_boost_specific
            if (effects.TryGetValue("stat_boost_specific", out object specObj) && specObj is string specStat)
            {
                int old = _state.GetStatValue(specStat);
                int nv = Mathf.Min(10, old + 1);
                _state.SetStat(specStat, nv);
                logs.Add(new EffectLogEntry($"  [+1] {specStat}: {old} -> {nv}"));
            }

            // stat_damage
            if (effects.TryGetValue("stat_damage", out object sdObj) && TryInt(sdObj, out int statDmg) && statDmg > 0)
            {
                string stat = contextStat;
                var validStats = new[] { "Strength", "Agility", "Durability", "Intelligence", "Charisma" };
                if (stat == null || !validStats.Contains(stat))
                {
                    // Damage weakest stat
                    stat = validStats.OrderBy(s => _state.GetStatValue(s)).First();
                }
                int old = _state.GetStatValue(stat);
                int nv = Mathf.Max(1, old - statDmg);
                _state.SetStat(stat, nv);
                logs.Add(new EffectLogEntry($"  [-{statDmg}] {stat}: {old} -> {nv}"));
            }

            // add_condition
            if (effects.TryGetValue("add_condition", out object acObj) && acObj is string cond)
            {
                _state.Conditions.Add(cond);
                string desc = EventChainData.ConditionDescriptions.GetValueOrDefault(cond, cond);
                logs.Add(new EffectLogEntry($"  [ESTADO] {desc}"));
            }

            // remove_condition
            if (effects.TryGetValue("remove_condition", out object rcObj) && rcObj is string rmCond)
            {
                _state.Conditions.Remove(rmCond);
                string desc = EventChainData.ConditionDescriptions.GetValueOrDefault(rmCond, rmCond);
                logs.Add(new EffectLogEntry($"  [CURADO] {desc}"));
            }

            // add_random_item
            if (effects.TryGetValue("add_random_item", out object ariObj) && ariObj is bool ari && ari)
            {
                if (_data.objects != null && _data.objects.Length > 0)
                {
                    var item = _data.objects[Random.Range(0, _data.objects.Length)];
                    int idx = 1;
                    while (_state.Selections.ContainsKey($"Item {idx}")) idx++;
                    _state.Selections[$"Item {idx}"] = item.name;
                    logs.Add(new EffectLogEntry($"  [ITEM] Obtienes: {item.name}"));
                }
            }

            // add_item (from temp_vars _forge_item)
            if (effects.TryGetValue("add_item", out object aiObj) && aiObj is bool ai && ai)
            {
                string forgeItem = _state.ChainTempVars.GetValueOrDefault("_forge_item", "Artefacto")?.ToString() ?? "Artefacto";
                int idx = 1;
                while (_state.Selections.ContainsKey($"Item {idx}")) idx++;
                _state.Selections[$"Item {idx}"] = forgeItem;
                logs.Add(new EffectLogEntry($"  [ITEM] Forjado: {forgeItem}"));
            }

            // add_item_from (from temp_vars)
            if (effects.TryGetValue("add_item_from", out object aifObj) && aifObj is string sourceKey)
            {
                string sourceName = _state.ChainTempVars.GetValueOrDefault(sourceKey, "Trofeo")?.ToString() ?? "Trofeo";
                string trophyName = $"Trofeo: {sourceName}";
                int idx = 1;
                while (_state.Selections.ContainsKey($"Item {idx}")) idx++;
                _state.Selections[$"Item {idx}"] = trophyName;
                logs.Add(new EffectLogEntry($"  [ITEM] Trofeo: {sourceName}"));
            }

            // gain_wealth / lose_wealth
            if (effects.TryGetValue("gain_wealth", out object gwObj) && (gwObj is bool && (bool)gwObj))
            {
                _state.ChangeGold(25, "ganas riqueza");
                logs.Add(new EffectLogEntry("  [ORO] +25 ganas riqueza"));
            }
            if (effects.TryGetValue("lose_wealth", out object lwObj) && (lwObj is bool && (bool)lwObj))
            {
                _state.ChangeGold(-20, "pierdes riqueza");
                logs.Add(new EffectLogEntry("  [ORO] -20 pierdes riqueza"));
            }

            // rep
            if (effects.TryGetValue("rep", out object repObj) && repObj is Dictionary<string, int> repDict)
            {
                foreach (var kv in repDict)
                {
                    if (!_state.Reputation.ContainsKey(kv.Key))
                        _state.Reputation[kv.Key] = 0;
                    _state.Reputation[kv.Key] += kv.Value;
                    string symbol = kv.Value >= 0 ? "+" : "";
                    logs.Add(new EffectLogEntry($"  [REP] {kv.Key}: {symbol}{kv.Value}"));
                }
            }

            return logs;
        }

        // ═══════════════════════════════════════════════════════════
        //  REPUTATION FROM OUTCOME
        // ═══════════════════════════════════════════════════════════

        void UpdateReputationFromOutcome(string outcomeName, int chapter)
        {
            if (_data.factions == null) return;
            string actionKey = $"Adventure Action {chapter}";
            string actionName = _state.Selections.GetValueOrDefault(actionKey, "");
            var actionData = _data.adventure_actions?.FirstOrDefault(a => a.name == actionName);
            var actionTags = actionData?.tags ?? Array.Empty<string>();

            foreach (var faction in _data.factions)
            {
                if (faction.tags == null) continue;
                if (!_state.Reputation.ContainsKey(faction.name))
                    _state.Reputation[faction.name] = 0;

                bool hasMatch = faction.tags.Any(t => actionTags.Contains(t));
                if (!hasMatch) continue;

                if (outcomeName is "Great Success" or "Gain Ally" or "Gain Wealth" or "Gain Relic")
                    _state.Reputation[faction.name] += 1;
                else if (outcomeName is "Catastrophe" or "Failure" or "Lose Wealth")
                    _state.Reputation[faction.name] -= 1;
            }
        }

        // ═══════════════════════════════════════════════════════════
        //  END RUN
        // ═══════════════════════════════════════════════════════════

        public void EndRunManual()
        {
            FireEndRun(RunEndReason.Manual, "");
        }

        void FireEndRun(RunEndReason reason, string detail)
        {
            _state.AdventureActive = false;
            int chapter = _state.Chapter;

            string title, msg;
            switch (reason)
            {
                case RunEndReason.Death:
                    title = "MUERTE";
                    msg = $"Tu aventura termina en el capitulo {chapter}.\n\n{detail}\n\nHas caido sin posibilidad de resurreccion.";
                    break;
                case RunEndReason.Victory:
                    title = "VICTORIA";
                    msg = $"Has logrado tu objetivo vital en el capitulo {chapter}!\n\n{detail}\n\nTu leyenda perdurara por siempre.";
                    break;
                default:
                    title = "FIN DE RUN";
                    msg = $"Has decidido terminar tu aventura en el capitulo {chapter}.\n\nTu historia queda inconclusa, pero vives para contarla.";
                    break;
            }

            OnEndRun?.Invoke(reason, title, msg);
        }

        // ═══════════════════════════════════════════════════════════
        //  BUILD END-RUN SUMMARY
        // ═══════════════════════════════════════════════════════════

        public string BuildEndRunSummary()
        {
            var sb = new System.Text.StringBuilder();

            // Adventure log
            if (_state.AdventureLog.Count > 0)
            {
                sb.AppendLine("Registro de Aventura:");
                foreach (var entry in _state.AdventureLog) sb.AppendLine(entry);
                sb.AppendLine();
            }

            // Reputation
            bool hasRep = _state.Reputation.Any(kv => kv.Value != 0);
            if (hasRep)
            {
                sb.AppendLine("Reputacion Final:");
                foreach (var kv in _state.Reputation)
                {
                    if (kv.Value == 0) continue;
                    string symbol = kv.Value > 0 ? "+" : "";
                    sb.AppendLine($"  {kv.Key}: {symbol}{kv.Value}");
                }
                sb.AppendLine();
            }

            // Titles
            if (_state.Titles.Count > 0)
            {
                sb.AppendLine("Titulos Obtenidos:");
                foreach (var t in _state.Titles) sb.AppendLine($"  * {t}");
                sb.AppendLine();
            }

            // Conditions
            if (_state.Conditions.Count > 0)
            {
                sb.AppendLine("Estado del Mundo:");
                foreach (var c in _state.Conditions.OrderBy(x => x))
                {
                    string desc = EventChainData.ConditionDescriptions.GetValueOrDefault(c, c.Replace('_', ' '));
                    sb.AppendLine($"  * {desc}");
                }
            }

            return sb.ToString();
        }

        // ═══════════════════════════════════════════════════════════
        //  HELPERS
        // ═══════════════════════════════════════════════════════════

        static bool TryInt(object o, out int v)
        {
            v = 0;
            if (o is int i) { v = i; return true; }
            if (o is long l) { v = (int)l; return true; }
            if (o is float f) { v = (int)f; return true; }
            if (o is double d) { v = (int)d; return true; }
            if (o is string s) return int.TryParse(s, out v);
            return false;
        }
    }
}
