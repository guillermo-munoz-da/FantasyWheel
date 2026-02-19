using System;
using System.IO;
using UnityEngine;

namespace DarkWheel.Core
{
    [Serializable]
    public class SaveData
    {
        public string Race;
        public string Archetype;
        public string Class;
        public string Gender;
        public string Age;
        public string Alignment;
        public string Place;
        public string MagicType;
    }

    public class SaveService
    {
        private const string SaveFileName = "save.json";

        public void Save(GameState state)
        {
            var data = new SaveData
            {
                Race = state.GetSelection("Race"),
                Archetype = state.GetSelection("Archetype"),
                Class = state.GetSelection("Class"),
                Gender = state.GetSelection("Gender"),
                Age = state.GetSelection("Age"),
                Alignment = state.GetSelection("Alignment"),
                Place = state.GetSelection("Place"),
                MagicType = state.GetSelection("MagicType")
            };

            var json = JsonUtility.ToJson(data, true);
            var path = GetSavePath();
            File.WriteAllText(path, json);
            Debug.Log($"Save escrito en {path}");
        }

        public bool TryLoad(GameState state)
        {
            var path = GetSavePath();
            if (!File.Exists(path))
            {
                return false;
            }

            var json = File.ReadAllText(path);
            var data = JsonUtility.FromJson<SaveData>(json);
            if (data == null)
            {
                return false;
            }

            SetIfPresent(state, "Race", data.Race);
            SetIfPresent(state, "Archetype", data.Archetype);
            SetIfPresent(state, "Class", data.Class);
            SetIfPresent(state, "Gender", data.Gender);
            SetIfPresent(state, "Age", data.Age);
            SetIfPresent(state, "Alignment", data.Alignment);
            SetIfPresent(state, "Place", data.Place);
            SetIfPresent(state, "MagicType", data.MagicType);
            return true;
        }

        private static string GetSavePath()
        {
            return Path.Combine(Application.persistentDataPath, SaveFileName);
        }

        private static void SetIfPresent(GameState state, string key, string value)
        {
            if (!string.IsNullOrWhiteSpace(value))
            {
                state.SetSelection(key, value);
            }
        }
    }
}
