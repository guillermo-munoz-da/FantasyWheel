// GameState.cs – Full character + adventure state matching Python prototype
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using Random = UnityEngine.Random;

namespace DarkWheel.Core
{
    [Serializable]
    public class GameState
    {
        // ── Character creation selections ─────────────────────────────
        public Dictionary<string, string> Selections = new();
        // Stats: Strength, Agility, Durability, Intelligence, Charisma → numeric
        public Dictionary<string, int> Stats = new()
        {
            ["Strength"] = 5, ["Agility"] = 5, ["Durability"] = 5,
            ["Intelligence"] = 5, ["Charisma"] = 5
        };

        // ── Adventure runtime ─────────────────────────────────────────
        public int Gold = 50;
        public HashSet<string> Conditions = new();
        public Dictionary<string, int> Reputation = new();
        public Dictionary<string, int> CompletedChains = new();
        public Dictionary<string, float> DecisionMods = new();
        public List<string> Titles = new();
        public List<string> AdventureLog = new();

        // ── Adventure phase tracking ──────────────────────────────────
        public bool AdventureActive;
        public int Chapter = 1;
        public int Step;              // 0=Activity, 1=Event, 2=Action, 3=Outcome

        // ── Chain state ───────────────────────────────────────────────
        public bool ChainActive;
        public string ChainName;
        public string ChainStepId;
        public Dictionary<string, string> ChainChoices = new();
        public Dictionary<string, object> ChainTempVars = new();

        // ── Travel ────────────────────────────────────────────────────
        public bool TravelActive;
        public bool TravelDoneForChapter;
        public string CurrentTerritory = "Human City (Good Factions)";
        public string CurrentSublocation;

        // ── Random event tracking ─────────────────────────────────────
        public int LastRandomEventChapter;
        public string LastRandomEventName;

        // ───────────────────── Helpers ─────────────────────────────────

        public static readonly Dictionary<int, string> StatLabels = new()
        {
            [1] = "Abysmal", [2] = "Poor", [3] = "Below Average", [4] = "Average",
            [5] = "Good", [6] = "Excellent", [7] = "Great", [8] = "Outstanding",
            [9] = "Superhuman", [10] = "Legendary"
        };

        /// <summary>Extract numeric stat value from selection string like "5 (Good)".</summary>
        public int GetStatValue(string statName)
        {
            if (Selections.TryGetValue(statName, out var val))
            {
                var parts = val.Split(' ');
                if (int.TryParse(parts[0], out int n)) return n;
            }
            if (Stats.TryGetValue(statName, out int s)) return s;
            return 5;
        }

        public void SetStat(string statName, int value)
        {
            value = Mathf.Clamp(value, 1, 10);
            string label = StatLabels.ContainsKey(value) ? StatLabels[value] : "Good";
            Selections[statName] = $"{value} ({label})";
        }

        public int GetMagicCount()
        {
            if (Selections.TryGetValue("Magic Count", out var v))
            {
                var parts = v.Split(' ');
                if (int.TryParse(parts[0], out int n)) return n;
            }
            return 0;
        }

        public bool HasSkill(string skillName)
        {
            foreach (var kv in Selections)
            {
                if (kv.Key.StartsWith("Skill ") && !kv.Key.StartsWith("Skill Count") &&
                    !kv.Key.StartsWith("Skill Mastery") && !kv.Key.StartsWith("Skill Efficiency"))
                {
                    if (kv.Value == skillName) return true;
                }
            }
            return false;
        }

        public List<string> GetMagicTypes()
        {
            var result = new List<string>();
            foreach (var kv in Selections)
            {
                if (kv.Key.StartsWith("Magic Type") && kv.Value != "None" && !string.IsNullOrEmpty(kv.Value))
                    result.Add(kv.Value);
            }
            return result;
        }

        public void ChangeGold(int amount, string source = "")
        {
            Gold = Mathf.Max(0, Gold + amount);
            string sign = amount >= 0 ? "+" : "";
            string entry = $"  [ORO] {sign}{amount}";
            if (!string.IsNullOrEmpty(source)) entry += $" {source}";
            LogAppend(entry);
        }

        public void LogAppend(string text)
        {
            AdventureLog.Add(text);
            if (AdventureLog.Count > 200) AdventureLog.RemoveRange(0, AdventureLog.Count - 200);
        }

        public void InitReputation(List<string> factionNames)
        {
            foreach (var f in factionNames)
                if (!Reputation.ContainsKey(f)) Reputation[f] = 0;
        }
    }
}
