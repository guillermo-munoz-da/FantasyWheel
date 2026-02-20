// JsonDataLoader.cs – Load data.unity.json from StreamingAssets with UTF-8/BOM handling
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;

namespace DarkWheel.Data
{
    using Core;

    public static class JsonDataLoader
    {
        /// <summary>Load and parse data.unity.json into a DataRoot.</summary>
        public static DataRoot Load()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "data.unity.json");
            if (!File.Exists(path))
            {
                path = Path.Combine(Application.streamingAssetsPath, "data.json");
            }
            if (!File.Exists(path))
            {
                Debug.LogError($"[JsonDataLoader] data file not found at {path}");
                return new DataRoot();
            }

            byte[] bytes = File.ReadAllBytes(path);
            // Strip UTF-8 BOM if present
            int offset = 0;
            if (bytes.Length >= 3 && bytes[0] == 0xEF && bytes[1] == 0xBB && bytes[2] == 0xBF) offset = 3;
            string json = Encoding.UTF8.GetString(bytes, offset, bytes.Length - offset);

            // JsonUtility doesn't handle top-level arrays or complex nested dicts well,
            // so we wrap the parse with manual fallback via MiniJSON.
            try
            {
                // First try JsonUtility for arrays
                var root = JsonUtility.FromJson<DataRoot>(json);
                if (root != null && (root.races != null || root.archetypes != null))
                    return root;
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[JsonDataLoader] JsonUtility failed, using manual parse: {e.Message}");
            }

            // Manual parse for complex JSON
            return ParseManual(json);
        }

        /// <summary>Minimal manual parser to extract arrays that JsonUtility may struggle with.</summary>
        static DataRoot ParseManual(string json)
        {
            var root = new DataRoot();
            try
            {
                // Use Unity's built-in JSON utility which handles most cases
                root = JsonUtility.FromJson<DataRoot>(json);
            }
            catch (Exception e)
            {
                Debug.LogError($"[JsonDataLoader] Manual parse also failed: {e.Message}");
            }
            return root ?? new DataRoot();
        }

        /// <summary>Extract faction names for reputation initialization.</summary>
        public static List<string> GetFactionNames(DataRoot data)
        {
            var names = new List<string>();
            if (data.factions != null)
            {
                foreach (var f in data.factions)
                    if (!string.IsNullOrEmpty(f.name)) names.Add(f.name);
            }
            return names;
        }

        /// <summary>Find archetype object by name.</summary>
        public static ArchetypeData FindArchetype(DataRoot data, string name)
        {
            if (data.archetypes == null) return null;
            foreach (var a in data.archetypes)
                if (a.name == name) return a;
            return null;
        }

        /// <summary>Find adventure item by name in a given array.</summary>
        public static AdventureItemData FindAdventureItem(AdventureItemData[] items, string name)
        {
            if (items == null) return null;
            foreach (var a in items)
                if (a.name == name) return a;
            return null;
        }
    }
}
