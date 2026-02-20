// SaveService.cs – JSON save/load for GameState
using System.IO;
using UnityEngine;

namespace DarkWheel.Core
{
    public static class SaveService
    {
        static string SavePath => Path.Combine(Application.persistentDataPath, "save.json");

        public static void Save(GameState state)
        {
            string json = JsonUtility.ToJson(new SerWrap(state), true);
            File.WriteAllText(SavePath, json);
        }

        public static GameState Load()
        {
            if (!File.Exists(SavePath)) return null;
            string json = File.ReadAllText(SavePath);
            var wrap = JsonUtility.FromJson<SerWrap>(json);
            return wrap?.Unwrap();
        }

        public static void Delete()
        {
            if (File.Exists(SavePath)) File.Delete(SavePath);
        }

        // JsonUtility cannot serialize Dictionary, so we flatten to parallel arrays
        [System.Serializable]
        class SerWrap
        {
            public string[] selKeys, selVals;
            public int gold, chapter, step;
            public bool advActive, chainActive, travelActive, travelDone;
            public string chainName, chainStepId;
            public string territory, sublocation;
            public string[] conditions;
            public string[] repKeys; public int[] repVals;
            public string[] ccKeys; public int[] ccVals;
            public string[] titles;
            public string[] log;

            public SerWrap() { }
            public SerWrap(GameState s)
            {
                selKeys = new string[s.Selections.Count];
                selVals = new string[s.Selections.Count];
                int i = 0;
                foreach (var kv in s.Selections) { selKeys[i] = kv.Key; selVals[i] = kv.Value; i++; }

                gold = s.Gold; chapter = s.Chapter; step = s.Step;
                advActive = s.AdventureActive; chainActive = s.ChainActive; travelActive = s.TravelActive; travelDone = s.TravelDoneForChapter;
                chainName = s.ChainName; chainStepId = s.ChainStepId;
                territory = s.CurrentTerritory; sublocation = s.CurrentSublocation;
                conditions = new string[s.Conditions.Count];
                s.Conditions.CopyTo(conditions);
                repKeys = new string[s.Reputation.Count]; repVals = new int[s.Reputation.Count];
                i = 0; foreach (var kv in s.Reputation) { repKeys[i] = kv.Key; repVals[i] = kv.Value; i++; }
                ccKeys = new string[s.CompletedChains.Count]; ccVals = new int[s.CompletedChains.Count];
                i = 0; foreach (var kv in s.CompletedChains) { ccKeys[i] = kv.Key; ccVals[i] = kv.Value; i++; }
                titles = s.Titles.ToArray();
                log = s.AdventureLog.ToArray();
            }

            public GameState Unwrap()
            {
                var s = new GameState();
                if (selKeys != null)
                    for (int i = 0; i < selKeys.Length; i++) s.Selections[selKeys[i]] = selVals[i];
                s.Gold = gold; s.Chapter = chapter; s.Step = step;
                s.AdventureActive = advActive; s.ChainActive = chainActive; s.TravelActive = travelActive; s.TravelDoneForChapter = travelDone;
                s.ChainName = chainName; s.ChainStepId = chainStepId;
                s.CurrentTerritory = territory; s.CurrentSublocation = sublocation;
                if (conditions != null) foreach (var c in conditions) s.Conditions.Add(c);
                if (repKeys != null) for (int i = 0; i < repKeys.Length; i++) s.Reputation[repKeys[i]] = repVals[i];
                if (ccKeys != null) for (int i = 0; i < ccKeys.Length; i++) s.CompletedChains[ccKeys[i]] = ccVals[i];
                if (titles != null) s.Titles.AddRange(titles);
                if (log != null) s.AdventureLog.AddRange(log);
                return s;
            }
        }
    }
}
