// CharacterCreationFlow.cs – Dynamic wheel configuration matching Python get_current_wheel_config()
// Implements: base wheels, dynamic sub-wheel insertion, magic affinities, territory affinities, spell map
using System.Collections.Generic;
using System.Linq;
using DarkWheel.Core;

namespace DarkWheel.Flow
{
    public static class CharacterCreationFlow
    {
        // Base wheel order (before dynamic insertion)
        public static readonly string[] BaseWheels =
        {
            "Race", "Gender", "Age", "Archetype", "Class", "Alignment",
            "Strength", "Agility", "Durability", "Intelligence", "Charisma",
            "Weapon", "Power Count", "Magic Count", "Skill Count", "Territory", "Items Count"
        };

        /// <summary>Build the full wheel config list, inserting dynamic sub-wheels
        /// based on current selections (Power Count, Magic Count, Skill Count, Items Count, Weapon).</summary>
        public static List<string> GetCurrentWheelConfig(GameState state)
        {
            var config = new List<string>();

            foreach (var wheel in BaseWheels)
            {
                config.Add(wheel);

                switch (wheel)
                {
                    case "Weapon":
                    {
                        string weapon = state.Selections.GetValueOrDefault("Weapon", "None");
                        if (weapon != "None") config.Add("Weapon Mastery");
                        break;
                    }
                    case "Power Count":
                    {
                        int count = ParseCount(state.Selections.GetValueOrDefault("Power Count", "0 (None)"));
                        for (int i = 1; i <= count; i++)
                        {
                            config.Add($"Power {i}");
                            config.Add($"Power Mastery {i}");
                        }
                        break;
                    }
                    case "Magic Count":
                    {
                        int count = ParseCount(state.Selections.GetValueOrDefault("Magic Count", "0 (None)"));
                        for (int i = 1; i <= count; i++)
                        {
                            config.Add($"Magic Type {i}");
                            config.Add($"Spells {i}");
                            config.Add($"Magic Skill {i}");
                        }
                        break;
                    }
                    case "Skill Count":
                    {
                        int count = ParseCount(state.Selections.GetValueOrDefault("Skill Count", "0 (None)"));
                        for (int i = 1; i <= count; i++)
                        {
                            config.Add($"Skill {i}");
                            config.Add($"Skill Mastery {i}");
                        }
                        if (count > 0) config.Add("Skill Efficiency");
                        break;
                    }
                    case "Items Count":
                    {
                        int count = ParseCount(state.Selections.GetValueOrDefault("Items Count", "0 (None)"));
                        for (int i = 1; i <= count; i++)
                            config.Add($"Item {i}");
                        break;
                    }
                }
            }
            return config;
        }

        static int ParseCount(string val)
        {
            if (string.IsNullOrEmpty(val)) return 0;
            var parts = val.Split(' ');
            return int.TryParse(parts[0], out int n) ? n : 0;
        }

        // ── Magic affinities (archetype/class/race → magic type weight multipliers) ──

        public static Dictionary<string, float> BuildMagicAffinities(string archetype, string charClass, string race)
        {
            var a = new Dictionary<string, float>();

            // Archetype
            switch (archetype)
            {
                case "Mage":   a["Arcane"] = 3f; a["Divine"] = 0.5f; a["Shadow"] = 1.5f; break;
                case "Priest": a["Divine"] = 3f; a["Nature"] = 2f; a["Arcane"] = 0.5f; break;
                case "Druid":  a["Nature"] = 3f; a["Earth"] = 2f; a["Water"] = 1.5f; break;
                case "Rogue":  a["Shadow"] = 2.5f; a["Blood"] = 1.5f; break;
                case "Warrior":a["Fire"] = 1.5f; a["Lightning"] = 1.5f; a["Arcane"] = 0.3f; break;
                case "Hunter": a["Nature"] = 2f; a["Fire"] = 1.5f; break;
                case "Bard":   a["Arcane"] = 2f; a["Divine"] = 1.5f; break;
            }

            // Race
            switch (race)
            {
                case "Vampire":  a["Blood"] = 3f; a["Shadow"] = 2.5f; break;
                case "Werewolf": a["Blood"] = 2f; a["Nature"] = 1.5f; break;
                case "Demon":    a["Infernal"] = 3f; a["Blood"] = 2f; a["Shadow"] = 1.5f; break;
                case "Dark Elf": a["Shadow"] = 2.5f; a["Arcane"] = 2f; break;
                case "Elf":      a["Arcane"] = 2f; a["Nature"] = 2f; break;
            }

            // Default 1.0 for all magic types
            foreach (var m in new[] { "Arcane", "Divine", "Nature", "Blood", "Shadow", "Infernal",
                                       "Fire", "Water", "Earth", "Air", "Lightning", "Ice" })
                if (!a.ContainsKey(m)) a[m] = 1f;

            return a;
        }

        // ── Territory affinities ──

        public static Dictionary<string, float> BuildTerritoryAffinities(string race, string charClass, string alignment)
        {
            var a = new Dictionary<string, float>();

            // Race
            switch (race)
            {
                case "Elf":     a["Elven Forest"] = 3f; a["Human City (Good Factions)"] = 2f; break;
                case "Dark Elf":a["Elven Forest"] = 3f; a["Outlands"] = 2.5f; break;
                case "Dwarf":   a["Dwarven Hold"] = 3f; break;
                case "Orc":     a["Human Slums"] = 2.5f; a["Outlands"] = 2f; break;
                case "Vampire": case "Werewolf": case "Demon":
                    a["Outlands"] = 3f; a["Human Slums"] = 2f; break;
                case "Gnome":   a["Human City (Good Factions)"] = 2.5f; break;
            }

            // Class
            switch (charClass)
            {
                case "Thief":   a["Human City (Good Factions)"] = 2.5f; a["Elven Forest"] = 1.5f; break;
                case "Knight":  a["Dwarven Hold"] = 2.5f; a["Human City (Good Factions)"] = 1.5f; break;
                case "Cleric": case "Priest":
                    a["Human City (Good Factions)"] = 3f; a["Dwarven Hold"] = 2f; break;
                case "Mage": case "Sorcerer": case "Enchanter":
                    a["Outlands"] = 3f; a["Human City (Good Factions)"] = 1.5f; break;
                case "Beast Hunter":
                    a["Elven Forest"] = 2.5f; a["Human Slums"] = 2f; break;
            }

            // Alignment
            if (alignment != null && alignment.Contains("Good"))
            {
                a.TryAdd("Human City (Good Factions)", 2f);
                a.TryAdd("Dwarven Hold", 1.5f);
            }
            else if (alignment != null && alignment.Contains("Evil"))
            {
                a.TryAdd("Outlands", 2.5f);
                a.TryAdd("Human Slums", 2f);
            }

            // Default 1.0
            foreach (var t in new[] { "Elven Forest", "Human City (Good Factions)", "Dwarven Hold", "Human Slums", "Outlands" })
                if (!a.ContainsKey(t)) a[t] = 1f;

            return a;
        }

        // ── Spell → magic type map ──

        public static readonly Dictionary<string, string[]> SpellMagicMap = new()
        {
            ["Chain Lightning"]   = new[] { "Lightning", "Arcane" },
            ["Frost Nova"]        = new[] { "Ice", "Arcane" },
            ["Arcane Missile"]    = new[] { "Arcane" },
            ["Shadow Veil"]       = new[] { "Shadow" },
            ["Curse of Weakness"] = new[] { "Shadow", "Blood" },
            ["Sanctuary"]         = new[] { "Divine" },
            ["Wind Walk"]         = new[] { "Air", "Divine" },
            ["Earthquake"]        = new[] { "Earth", "Nature" },
            ["Fireball"]          = new[] { "Fire", "Arcane" },
            ["Dark Flame"]        = new[] { "Infernal", "Shadow" },
            ["Nature Blessing"]   = new[] { "Nature", "Divine" },
            ["Beast Call"]        = new[] { "Nature" },
            ["Blood Curse"]       = new[] { "Blood" },
            ["Blood Drain"]       = new[] { "Blood", "Infernal" },
        };

        // ── Magical archetypes (for Magic Count weight boosting) ──
        public static readonly HashSet<string> MagicalArchetypes = new() { "Mage", "Priest", "Druid" };
    }
}
