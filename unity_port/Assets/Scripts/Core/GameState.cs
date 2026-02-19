using System;
using System.Collections.Generic;

namespace DarkWheel.Core
{
    [Serializable]
    public class GameState
    {
        public Dictionary<string, string> Selections = new Dictionary<string, string>();
        public Dictionary<string, int> Stats = new Dictionary<string, int>
        {
            { "strength", 5 },
            { "agility", 5 },
            { "durability", 5 },
            { "intelligence", 5 },
            { "charisma", 5 }
        };
        public HashSet<string> Conditions = new HashSet<string>();
        public List<string> Skills = new List<string>();
        public List<string> Powers = new List<string>();
        public List<string> Objects = new List<string>();
        public List<string> HistoryLog = new List<string>();

        public void SetSelection(string key, string value)
        {
            Selections[key] = value;
        }

        public string GetSelection(string key)
        {
            return Selections.TryGetValue(key, out var value) ? value : string.Empty;
        }

        public int GetStat(string key)
        {
            return Stats.TryGetValue(key, out var value) ? value : 0;
        }

        public void AddLog(string line)
        {
            HistoryLog.Add(line);
            if (HistoryLog.Count > 400)
            {
                HistoryLog.RemoveRange(0, HistoryLog.Count - 400);
            }
        }
    }
}
