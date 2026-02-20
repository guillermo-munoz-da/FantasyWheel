// WheelEngine.cs – Builds wheel segments for ALL wheel types.
// Full 1:1 port of Python build_wheel_data(), build_adventure_tag_weights(),
// compute_death_weight(), compute_victory_weight(), build_chain_wheel_segments(), etc.
using System;
using System.Collections.Generic;
using System.Linq;
using DarkWheel.Core;
using UnityEngine;
using Random = UnityEngine.Random;

namespace DarkWheel.Flow
{
    /// <summary>Segment returned by the wheel engine for rendering & selection.</summary>
    public struct WheelSegment
    {
        public string Name;
        public float Weight;
        public string Desc;
        public ChainOption ChainOptionData; // non-null only for chain steps
    }

    public static class WheelEngine
    {
        // ═══════════════════════════════════════════════════════════
        //  BUILD WHEEL DATA  (mirrors Python build_wheel_data)
        // ═══════════════════════════════════════════════════════════

        public static List<WheelSegment> Build(string wheelName, DataRoot data, GameState state)
        {
            if (wheelName == "Travel") return BuildTravel(data, state);

            var segs = new List<WheelSegment>();

            // ── Simple categorical wheels ──
            if (wheelName == "Race") return Simple(data.races, "Raza");
            if (wheelName == "Gender") return Simple(data.genders, "Género");
            if (wheelName == "Age") return Simple(data.ages, "Edad");
            if (wheelName == "Alignment") return SimpleFlat(data.alignments, "Alineación");

            if (wheelName == "Archetype")
                return SimpleFlat(data.archetypes?.Select(a => new NameWeight { name = a.name }).ToArray(), "Arquetipo");

            if (wheelName == "Class")
            {
                string arch = state.Selections.GetValueOrDefault("Archetype", "");
                var archObj = data.archetypes?.FirstOrDefault(a => a.name == arch);
                if (archObj?.classes != null)
                    foreach (var c in archObj.classes)
                        segs.Add(new WheelSegment { Name = c, Weight = 1f, Desc = $"Clase: {c}" });
                return segs;
            }

            // ── Stats ──
            if (wheelName is "Strength" or "Agility" or "Durability" or "Intelligence" or "Charisma")
                return Simple(data.stat_values, wheelName);

            // ── Weapon / Weapon Mastery ──
            if (wheelName == "Weapon") return Simple(data.weapons, "Arma");
            if (wheelName == "Weapon Mastery") return SimpleMastery(data.weapon_masteries, "Dominio de Arma");

            // ── Count wheels ──
            if (wheelName == "Power Count") return Simple(data.power_count, "Poderes");

            if (wheelName == "Magic Count")
            {
                string archetype = state.Selections.GetValueOrDefault("Archetype", "");
                bool isMagical = CharacterCreationFlow.MagicalArchetypes.Contains(archetype);
                if (data.magic_count == null) return segs;
                foreach (var item in data.magic_count)
                {
                    float w = item.weight;
                    if (isMagical)
                        w = item.name == "0 (None)" ? 1f : w * 1.5f;
                    segs.Add(new WheelSegment { Name = item.name, Weight = w, Desc = $"Tipos de Magia: {item.name}" });
                }
                return segs;
            }

            if (wheelName == "Skill Count") return Simple(data.skills_count, "Habilidades");
            if (wheelName == "Items Count") return Simple(data.items_count, "Objetos");

            // ── Skill Efficiency ──
            if (wheelName == "Skill Efficiency")
            {
                if (data.skill_efficiency == null) return segs;
                foreach (var e in data.skill_efficiency)
                    segs.Add(new WheelSegment { Name = e.name, Weight = e.weight, Desc = $"Eficiencia: {e.name}" });
                return segs;
            }

            // ── Dynamic Power wheels (Power 1, Power 2…) ──
            if (wheelName.StartsWith("Power Mastery "))
                return SimpleMastery(data.power_skills, "Dominio");

            if (wheelName.StartsWith("Power ") && !wheelName.StartsWith("Power Count"))
                return Simple(data.powers, "Poder");

            // ── Dynamic Magic Skill wheels ──
            if (wheelName.StartsWith("Magic Skill "))
                return SimpleMastery(data.magic_skills, "Maestría Mágica");

            // ── Dynamic Skill Mastery wheels ──
            if (wheelName.StartsWith("Skill Mastery "))
                return SimpleMastery(data.power_skills, "Dominio Habilidad"); // matches Python: uses power_skills

            // ── Dynamic Magic Type wheels ──
            if (wheelName.StartsWith("Magic Type"))
            {
                if (data.magic_types == null) return segs;
                string archetype = state.Selections.GetValueOrDefault("Archetype", "");
                string charClass = state.Selections.GetValueOrDefault("Class", "");
                string race = state.Selections.GetValueOrDefault("Race", "");
                var selected = new HashSet<string>();
                foreach (var kv in state.Selections)
                    if (kv.Key.StartsWith("Magic Type")) selected.Add(kv.Value);
                var affinities = CharacterCreationFlow.BuildMagicAffinities(archetype, charClass, race);

                foreach (var item in data.magic_types)
                {
                    if (item.name == "None" || selected.Contains(item.name)) continue;
                    float w = item.weight;
                    if (affinities.TryGetValue(item.name, out float mult)) w *= mult;
                    segs.Add(new WheelSegment { Name = item.name, Weight = w, Desc = $"Magia: {item.name}" });
                }
                // Add None if less than 5 selected
                if (selected.Count < 5)
                {
                    float noneW = data.magic_types.Length > 0 ? data.magic_types[0].weight : 1f;
                    segs.Add(new WheelSegment { Name = "None", Weight = noneW, Desc = "Magia: None" });
                }
                return segs;
            }

            // ── Dynamic Spell wheels (Spells 1, Spells 2…) ──
            if (wheelName.StartsWith("Spells "))
            {
                string num = wheelName.Split(' ').Last();
                string magicKey = $"Magic Type {num}";
                string magicType = state.Selections.GetValueOrDefault(magicKey, "None");
                if (data.spells == null) return segs;

                foreach (var spell in data.spells)
                {
                    if (CharacterCreationFlow.SpellMagicMap.TryGetValue(spell.name, out var allowed))
                    {
                        if (!allowed.Contains(magicType) && !allowed.Contains("Any"))
                            continue;
                    }
                    segs.Add(new WheelSegment { Name = spell.name, Weight = spell.weight, Desc = $"Hechizo: {spell.name}" });
                }
                if (segs.Count == 0) // fallback: all spells
                    foreach (var spell in data.spells)
                        segs.Add(new WheelSegment { Name = spell.name, Weight = spell.weight, Desc = $"Hechizo: {spell.name}" });
                return segs;
            }

            // ── Dynamic Skill wheels (Skill 1, Skill 2…) ──
            if (wheelName.StartsWith("Skill ") && !wheelName.StartsWith("Skill Count") &&
                !wheelName.StartsWith("Skill Mastery") && !wheelName.StartsWith("Skill Efficiency"))
            {
                if (data.skills == null) return segs;
                var selected = new HashSet<string>();
                foreach (var kv in state.Selections)
                    if (kv.Key.StartsWith("Skill ") && !kv.Key.StartsWith("Skill Count") &&
                        !kv.Key.StartsWith("Skill Mastery") && !kv.Key.StartsWith("Skill Efficiency"))
                        selected.Add(kv.Value);
                foreach (var item in data.skills)
                {
                    if (selected.Contains(item.name)) continue;
                    segs.Add(new WheelSegment { Name = item.name, Weight = item.weight, Desc = $"Habilidad: {item.name}" });
                }
                return segs;
            }

            // ── Dynamic Item wheels (Item 1, Item 2…) ──
            if (wheelName.StartsWith("Item "))
            {
                if (data.objects == null) return segs;
                var selected = new HashSet<string>();
                foreach (var kv in state.Selections)
                    if (kv.Key.StartsWith("Item ")) selected.Add(kv.Value);
                foreach (var item in data.objects)
                {
                    if (selected.Contains(item.name)) continue;
                    segs.Add(new WheelSegment { Name = item.name, Weight = item.weight, Desc = $"Objeto: {item.name}" });
                }
                return segs;
            }

            // ── Territory ──
            if (wheelName == "Territory")
            {
                return BuildTravel(data, state); // uses same affinity logic
            }

            // ══════════════════════════════════════════════════════
            //  ADVENTURE WHEELS
            // ══════════════════════════════════════════════════════

            if (wheelName.StartsWith("Adventure Activity "))
                return BuildAdventureCategory(data.adventure_activities, data, state, "Actividad", boostChains: true, checkChainLimits: true);

            if (wheelName.StartsWith("Adventure Event "))
                return BuildAdventureCategory(data.adventure_events, data, state, "Evento", boostChains: true, checkChainLimits: true);

            if (wheelName.StartsWith("Adventure Action "))
                return BuildAdventureCategory(data.adventure_actions, data, state, "Accion", boostChains: false, checkChainLimits: false);

            if (wheelName.StartsWith("Adventure Outcome "))
                return BuildAdventureOutcome(data, state);

            return segs;
        }

        // ═══════════════════════════════════════════════════════════
        //  ADVENTURE CATEGORY  (Activity / Event / Action)
        // ═══════════════════════════════════════════════════════════

        static List<WheelSegment> BuildAdventureCategory(
            AdventureItemData[] items, DataRoot data, GameState state,
            string prefix, bool boostChains, bool checkChainLimits)
        {
            var segs = new List<WheelSegment>();
            if (items == null) return segs;

            var tagWeights = BuildAdventureTagWeights(state);

            // Reputation bonuses
            foreach (var kv in state.Reputation)
            {
                if (kv.Value <= 0) continue;
                var factionData = data.factions?.FirstOrDefault(f => f.name == kv.Key);
                if (factionData?.tags != null)
                    foreach (var tag in factionData.tags)
                        tagWeights[tag] = Mathf.Max(tagWeights.GetValueOrDefault(tag, 1f), 1f + kv.Value * 0.1f);
            }

            foreach (var item in items)
            {
                // Chain blocking
                if (checkChainLimits && EventChainData.Chains.TryGetValue(item.name, out var chainDef))
                {
                    if (chainDef.BlockedBy != null && state.Conditions.Contains(chainDef.BlockedBy))
                        continue;
                }

                // Chain repeat limits
                if (checkChainLimits && state.CompletedChains.TryGetValue(item.name, out int count))
                {
                    if (EventChainData.ChainLimits.TryGetValue(item.name, out var limit))
                    {
                        if (limit.Unique && count > 0) continue;
                        if (limit.MaxRepeats >= 0 && count >= limit.MaxRepeats) continue;
                    }
                }

                float weight = ApplyTagWeights(item, tagWeights);

                // Decision mods
                if (item.tags != null)
                    foreach (var tag in item.tags)
                        if (state.DecisionMods.TryGetValue(tag, out float dm))
                            weight *= dm;

                // Boost chains
                if (boostChains && EventChainData.Chains.ContainsKey(item.name))
                    weight *= 1.3f;

                // Diminishing returns
                if (state.CompletedChains.TryGetValue(item.name, out int cc) && cc > 0)
                    weight *= Mathf.Max(0.15f, 1f / (1f + cc * 0.6f));

                segs.Add(new WheelSegment { Name = item.name, Weight = weight, Desc = $"{prefix}: {item.desc ?? item.name}" });
            }
            return segs;
        }

        // ═══════════════════════════════════════════════════════════
        //  ADVENTURE OUTCOME
        // ═══════════════════════════════════════════════════════════

        static List<WheelSegment> BuildAdventureOutcome(DataRoot data, GameState state)
        {
            var segs = new List<WheelSegment>();
            if (data.adventure_outcomes == null) return segs;

            var tagWeights = BuildAdventureTagWeights(state);
            int chapter = state.Chapter;

            // Get action tags for stat checks
            var actionTags = GetActionTags(data, state, chapter);
            float statBonus = ComputeStatBonusForTags(actionTags, state);

            foreach (var item in data.adventure_outcomes)
            {
                float weight = ApplyTagWeights(item, tagWeights);

                // Decision mods
                if (item.tags != null)
                    foreach (var tag in item.tags)
                        if (state.DecisionMods.TryGetValue(tag, out float dm))
                            weight *= dm;

                // Stat checks: positive outcomes boosted by good stats
                var tags = item.tags ?? Array.Empty<string>();
                if (tags.Any(t => t is "positive" or "good" or "merchant"))
                    weight *= Mathf.Max(0.3f, 1f + statBonus);
                else if (tags.Any(t => t is "negative" or "evil" or "dark"))
                    weight *= Mathf.Max(0.3f, 1f - statBonus);

                // Dynamic death/victory
                if (item.terminal == "death")
                    weight = ComputeDeathWeight(state);
                else if (item.terminal == "victory")
                    weight = ComputeVictoryWeight(state, item.name);

                if (weight > 0f)
                    segs.Add(new WheelSegment { Name = item.name, Weight = weight, Desc = $"Resultado: {item.desc ?? item.name}" });
            }
            return segs;
        }

        // ═══════════════════════════════════════════════════════════
        //  CHAIN WHEEL SEGMENTS
        // ═══════════════════════════════════════════════════════════

        public static List<WheelSegment> BuildChainSegments(GameState state)
        {
            var segs = new List<WheelSegment>();
            if (!state.ChainActive || string.IsNullOrEmpty(state.ChainName) || string.IsNullOrEmpty(state.ChainStepId))
                return segs;

            if (!EventChainData.Chains.TryGetValue(state.ChainName, out var chainDef))
                return segs;

            var step = chainDef.Steps.FirstOrDefault(s => s.Id == state.ChainStepId);
            if (step == null) return segs;

            string statCheck = step.StatCheck;
            int difficulty = 5;
            if (step.DifficultyKey != null && state.ChainTempVars.TryGetValue(step.DifficultyKey, out object dv))
            {
                if (dv is int di) difficulty = di;
                else if (dv is float df) difficulty = (int)df;
                else if (dv is double dd) difficulty = (int)dd;
                else if (int.TryParse(dv.ToString(), out int dp)) difficulty = dp;
            }

            foreach (var opt in step.Options)
            {
                float weight = opt.Weight;

                // requires_magic
                if (opt.RequiresMagic && state.GetMagicCount() == 0) continue;

                // requires_condition
                if (opt.RequiresCondition != null && !state.Conditions.Contains(opt.RequiresCondition)) continue;

                // blocked_by_condition
                if (opt.BlockedByCondition != null && state.Conditions.Contains(opt.BlockedByCondition)) continue;

                // stat_weight
                if (opt.StatWeight != null)
                    foreach (var kv in opt.StatWeight)
                        weight *= (state.GetStatValue(kv.Key) / 5f) * kv.Value;

                // skill_bonus
                if (opt.SkillBonus != null)
                    foreach (var kv in opt.SkillBonus)
                        if (state.HasSkill(kv.Key))
                            weight *= kv.Value;

                // Power bonuses (shadow powers boost stealth options)
                foreach (var sel in state.Selections)
                {
                    if (sel.Key.StartsWith("Power ") && !sel.Key.StartsWith("Power Count") && !sel.Key.StartsWith("Power Mastery"))
                    {
                        string pname = sel.Value.ToLowerInvariant();
                        string oname = opt.Name.ToLowerInvariant();
                        if (pname.Contains("shadow") && (oname.Contains("infiltra") || oname.Contains("sigilo") || oname.Contains("nocturna")))
                            weight *= 1.4f;
                    }
                }

                // Stat-checked results (success tiers)
                if (statCheck != null && opt.SuccessTier != null)
                {
                    int checkVal = state.GetStatValue(statCheck);
                    float ratio = checkVal / Mathf.Max(1f, difficulty);

                    weight *= opt.SuccessTier switch
                    {
                        "high" => Mathf.Max(0.3f, ratio * 1.5f),
                        "mid"  => Mathf.Max(0.5f, 0.8f + ratio * 0.3f),
                        "low"  => Mathf.Max(0.3f, 1.5f - ratio * 0.5f),
                        "fail" => Mathf.Max(0.2f, 1.8f - ratio * 0.8f),
                        _ => 1f
                    };
                }

                // Inline stat check
                if (opt.StatCheckInline != null)
                {
                    int checkVal = state.GetStatValue(opt.StatCheckInline);
                    if (checkVal >= 7) weight *= 0.5f;
                    else if (checkVal <= 3) weight *= 1.5f;
                }

                weight = Mathf.Max(0.1f, weight);
                segs.Add(new WheelSegment { Name = opt.Name, Weight = weight, Desc = opt.Desc ?? opt.Name, ChainOptionData = opt });
            }
            return segs;
        }

        // ═══════════════════════════════════════════════════════════
        //  TRAVEL
        // ═══════════════════════════════════════════════════════════

        static List<WheelSegment> BuildTravel(DataRoot data, GameState state)
        {
            var segs = new List<WheelSegment>();
            var places = data.places;
            if (places == null) return segs;

            var affinities = CharacterCreationFlow.BuildTerritoryAffinities(
                state.Selections.GetValueOrDefault("Race", ""),
                state.Selections.GetValueOrDefault("Class", ""),
                state.Selections.GetValueOrDefault("Alignment", ""));

            foreach (var p in places)
            {
                float w = p.weight * affinities.GetValueOrDefault(p.name, 1f);
                segs.Add(new WheelSegment { Name = p.name, Weight = w, Desc = $"Viajar a {p.name}" });
            }
            return segs;
        }

        // ═══════════════════════════════════════════════════════════
        //  ADVENTURE TAG WEIGHTS  (mirrors Python build_adventure_tag_weights)
        // ═══════════════════════════════════════════════════════════

        public static Dictionary<string, float> BuildAdventureTagWeights(GameState state)
        {
            var tw = new Dictionary<string, float>();
            void Add(string tag, float mult) => tw[tag] = Mathf.Max(tw.GetValueOrDefault(tag, 1f), mult);

            string archetype = state.Selections.GetValueOrDefault("Archetype", "");
            string charClass = state.Selections.GetValueOrDefault("Class", "");
            string race = state.Selections.GetValueOrDefault("Race", "");
            string alignment = state.Selections.GetValueOrDefault("Alignment", "");

            // Archetype
            switch (archetype)
            {
                case "Merchant": Add("merchant", 2f); Add("trade", 2f); Add("commerce", 1.8f); Add("social", 1.4f); break;
                case "Warrior": Add("combat", 1.8f); Add("honor", 1.4f); break;
                case "Mage": Add("magic", 1.8f); Add("arcane", 1.5f); Add("research", 1.3f); break;
                case "Rogue": Add("crime", 1.8f); Add("stealth", 1.8f); break;
                case "Priest": Add("divine", 1.8f); Add("faith", 1.6f); Add("healing", 1.4f); break;
                case "Hunter": Add("hunt", 1.8f); Add("tracking", 1.6f); break;
                case "Druid": Add("nature", 1.8f); Add("ritual", 1.4f); break;
                case "Noble": Add("politics", 1.8f); Add("leadership", 1.6f); Add("social", 1.4f); break;
                case "Beast": Add("beast", 1.8f); Add("hunt", 1.4f); break;
            }

            // Class-based tags
            var mercClasses = new HashSet<string> { "Trader", "Smuggler", "Black Market Dealer", "Banker", "Artisan", "Caravan Master", "Fence", "Relic Seller" };
            var stealthClasses = new HashSet<string> { "Assassin", "Spy", "Saboteur", "Shadow Dancer", "Poisoner" };
            var combatClasses = new HashSet<string> { "Knight", "Bodyguard", "Duelist", "Warlord", "Gladiator" };
            var divineClasses = new HashSet<string> { "Cleric", "Inquisitor", "Exorcist", "Healer", "Oracle", "Prophet" };
            var magicClasses = new HashSet<string> { "Elementalist", "Illusionist", "Necromancer", "Enchanter", "Sorcerer", "Alchemist", "Blood Mage", "Chronomancer" };

            if (mercClasses.Contains(charClass)) { Add("merchant", 2f); Add("trade", 1.8f); }
            if (stealthClasses.Contains(charClass)) { Add("crime", 2f); Add("stealth", 1.6f); }
            if (combatClasses.Contains(charClass)) { Add("combat", 1.8f); Add("honor", 1.3f); }
            if (divineClasses.Contains(charClass)) { Add("divine", 1.7f); Add("healing", 1.5f); }
            if (magicClasses.Contains(charClass)) { Add("magic", 1.8f); Add("arcane", 1.4f); }

            // Alignment
            if (alignment.Contains("Good")) Add("good", 1.4f);
            else if (alignment.Contains("Evil")) Add("evil", 1.6f);
            else Add("neutral", 1.2f);

            // Race
            if (race is "Vampire" or "Demon" or "Werewolf") Add("dark", 1.7f);
            if (race == "Elf") Add("elven", 1.3f);
            if (race == "Dwarf") Add("dwarf", 1.3f);
            if (race == "Orc") Add("orc", 1.3f);

            // Magic types
            foreach (var mt in state.GetMagicTypes())
            {
                Add("magic", 1.4f);
                Add($"magic_{mt.ToLowerInvariant()}", 1.5f);
            }

            // Skills
            foreach (var kv in state.Selections)
            {
                if (!kv.Key.StartsWith("Skill ") || kv.Key.StartsWith("Skill Count") ||
                    kv.Key.StartsWith("Skill Mastery") || kv.Key.StartsWith("Skill Efficiency"))
                    continue;
                switch (kv.Value)
                {
                    case "Persuasion": Add("social", 1.6f); Add("trade", 1.4f); break;
                    case "Stealth": Add("stealth", 1.8f); break;
                    case "Tracking": Add("tracking", 1.6f); Add("hunt", 1.4f); break;
                    case "Smithing": Add("craft", 1.7f); break;
                    case "Alchemy": Add("alchemy", 1.6f); Add("magic", 1.2f); break;
                    case "Leadership": Add("leadership", 1.6f); break;
                    case "Investigation": Add("investigation", 1.6f); break;
                    case "Lockpicking": Add("crime", 1.5f); break;
                    case "Medicine": Add("healing", 1.5f); break;
                }
            }

            // Powers
            foreach (var kv in state.Selections)
            {
                if (!kv.Key.StartsWith("Power ") || kv.Key.StartsWith("Power Count") || kv.Key.StartsWith("Power Mastery"))
                    continue;
                string val = kv.Value;
                if (val.Contains("Blood")) { Add("blood", 1.6f); Add("dark", 1.3f); }
                if (val.Contains("Shadow")) { Add("shadow", 1.6f); Add("dark", 1.3f); }
                if (val.Contains("Wings")) Add("flight", 1.4f);
                if (val.Contains("Mind Control")) Add("domination", 1.6f);
                if (val.Contains("Regeneration")) Add("survival", 1.3f);
                if (val.Contains("Animal")) Add("beast", 1.4f);
            }

            return tw;
        }

        // ═══════════════════════════════════════════════════════════
        //  COMPUTE DEATH / VICTORY WEIGHT
        // ═══════════════════════════════════════════════════════════

        public static float ComputeDeathWeight(GameState state)
        {
            float b = 0.5f;
            int ch = state.Chapter;
            if (ch > 3) b += (ch - 3) * 0.4f;

            // Recent catastrophes
            for (int i = Mathf.Max(1, ch - 2); i < ch; i++)
            {
                string outcome = state.Selections.GetValueOrDefault($"Adventure Outcome {i}", "");
                if (outcome is "Catastrophe" or "Curse") b *= 1.8f;
                if (outcome == "Make Enemy") b *= 1.3f;
            }

            int dur = state.GetStatValue("Durability");
            if (dur <= 2) b *= 2f;
            else if (dur <= 4) b *= 1.3f;
            else if (dur >= 8) b *= 0.5f;

            // Powers influence
            foreach (var kv in state.Selections)
            {
                if (!kv.Key.StartsWith("Power ") || kv.Key.StartsWith("Power Count") || kv.Key.StartsWith("Power Mastery"))
                    continue;
                if (kv.Value == "Regeneration") b *= 0.6f;
                if (kv.Value == "Unbreakable") b *= 0.7f;
            }

            return Mathf.Max(0.3f, b);
        }

        public static float ComputeVictoryWeight(GameState state, string victoryType)
        {
            int ch = state.Chapter;
            if (ch < 3) return 0f;

            float b = 0.5f;

            switch (victoryType)
            {
                case "Retire Wealthy":
                {
                    if (ch < 4) return 0f;
                    int wealthCount = state.Selections.Count(kv =>
                        kv.Key.StartsWith("Adventure Outcome") && kv.Value == "Gain Wealth");
                    if (state.Selections.GetValueOrDefault("Archetype", "") == "Merchant") b *= 2f;
                    b += wealthCount * 0.8f;
                    if (ch >= 6) b *= 1.5f;
                    break;
                }
                case "Ascend to Godhood":
                {
                    if (ch < 5) return 0f;
                    int mc = state.GetMagicCount();
                    if (mc == 0) return 0f;
                    int intel = state.GetStatValue("Intelligence");
                    b += (intel - 5) * 0.3f;
                    b += mc * 0.5f;
                    int asc = state.Selections.Count(kv =>
                        kv.Key.StartsWith("Adventure Outcome") && kv.Value == "Ascension Attempt");
                    b += asc * 1.5f;
                    if (ch >= 8) b *= 1.5f;
                    break;
                }
                case "Found a Dynasty":
                {
                    if (ch < 4) return 0f;
                    string arch = state.Selections.GetValueOrDefault("Archetype", "");
                    if (arch is "Noble" or "Merchant") b *= 2f;
                    int cha = state.GetStatValue("Charisma");
                    b += (cha - 5) * 0.3f;
                    int allyCount = state.Selections.Count(kv =>
                        kv.Key.StartsWith("Adventure Outcome") && kv.Value == "Gain Ally");
                    b += allyCount * 0.6f;
                    break;
                }
                case "Legendary Hero":
                {
                    if (ch < 5) return 0f;
                    int successes = state.Selections.Count(kv =>
                        kv.Key.StartsWith("Adventure Outcome") && kv.Value is "Great Success" or "Costly Victory");
                    int str = state.GetStatValue("Strength");
                    b += successes * 0.5f;
                    b += (str - 5) * 0.2f;
                    string align = state.Selections.GetValueOrDefault("Alignment", "");
                    if (align.Contains("Good")) b *= 1.5f;
                    break;
                }
            }

            return Mathf.Max(0f, b);
        }

        // ═══════════════════════════════════════════════════════════
        //  PICK RANDOM EVENT CHAIN
        // ═══════════════════════════════════════════════════════════

        public static string PickRandomEventChain(DataRoot data, GameState state)
        {
            if (data.adventure_events == null) return null;
            var tagWeights = BuildAdventureTagWeights(state);
            var candidates = new List<(string name, float weight)>();

            foreach (var item in data.adventure_events)
            {
                if (!EventChainData.Chains.ContainsKey(item.name)) continue;
                if (state.LastRandomEventName == item.name && state.Chapter - state.LastRandomEventChapter < 2) continue;

                var chainDef = EventChainData.Chains[item.name];
                if (chainDef.BlockedBy != null && state.Conditions.Contains(chainDef.BlockedBy)) continue;

                if (state.CompletedChains.TryGetValue(item.name, out int count))
                {
                    if (EventChainData.ChainLimits.TryGetValue(item.name, out var limit))
                    {
                        if (limit.Unique && count > 0) continue;
                        if (limit.MaxRepeats >= 0 && count >= limit.MaxRepeats) continue;
                    }
                }

                float w = ApplyTagWeights(item, tagWeights);
                if (state.CompletedChains.TryGetValue(item.name, out int cc) && cc > 0)
                    w *= Mathf.Max(0.15f, 1f / (1f + cc * 0.6f));

                // Reputation bonuses
                foreach (var rep in state.Reputation)
                {
                    if (rep.Value <= 0) continue;
                    var fd = data.factions?.FirstOrDefault(f => f.name == rep.Key);
                    if (fd?.tags == null || item.tags == null) continue;
                    foreach (var tag in fd.tags)
                        if (item.tags.Contains(tag))
                        { w *= 1f + rep.Value * 0.1f; break; }
                }

                if (w > 0f) candidates.Add((item.name, w));
            }

            if (candidates.Count == 0) return null;
            int idx = WeightedSelector.Pick(candidates);
            return candidates[idx].name;
        }

        // ═══════════════════════════════════════════════════════════
        //  WHEEL CONTEXT TEXT
        // ═══════════════════════════════════════════════════════════

        public static string GetWheelContext(string wheelName, GameState state)
        {
            if (wheelName == "Travel")
                return $"Cap. {state.Chapter}: Elige tu destino antes de la accion.";
            if (wheelName.StartsWith("Adventure Activity"))
            {
                string loc = state.CurrentTerritory;
                string sub = state.CurrentSublocation;
                return !string.IsNullOrEmpty(sub) ? $"En {loc} ({sub}), rumores de oportunidades circulan." : $"En {loc}, buscas tu proxima aventura.";
            }
            if (wheelName.StartsWith("Adventure Event")) return "Un giro del destino se acerca.";
            if (wheelName.StartsWith("Adventure Action")) return "Decide tu enfoque frente al desafio.";
            if (wheelName.StartsWith("Adventure Outcome")) return "Las consecuencias de tus actos se revelan.";
            if (wheelName.StartsWith("Adventure")) return "Progreso de aventura.";
            if (wheelName.StartsWith("Magic") || wheelName.StartsWith("Spells")) return "Elige el camino arcano que te define.";
            if (wheelName.StartsWith("Power")) return "Poderes despiertan en tu sangre.";
            if (wheelName.StartsWith("Skill")) return "Talentos mortales afinan tu oficio.";
            if (wheelName.StartsWith("Territory")) return "Donde empezara tu historia.";
            return "Forja tu leyenda.";
        }

        // ═══════════════════════════════════════════════════════════
        //  SHOULD TRIGGER TRAVEL
        // ═══════════════════════════════════════════════════════════

        public static bool ShouldTriggerTravel(string eventName, DataRoot data)
        {
            string lower = eventName.ToLowerInvariant();
            var ev = data.adventure_events?.FirstOrDefault(e => e.name == eventName);
            var tags = ev?.tags;
            var travelTags = new HashSet<string> { "explore", "travel", "caravan", "escort", "escort_caravan", "guard_caravan" };
            if (tags != null && tags.Any(t => travelTags.Contains(t))) return true;
            string[] keywords = { "explor", "caravan", "caravana", "escolta", "escoltar" };
            return keywords.Any(k => lower.Contains(k));
        }

        // ═══════════════════════════════════════════════════════════
        //  SUBLOCATIONS
        // ═══════════════════════════════════════════════════════════

        public static readonly Dictionary<string, string[]> Sublocations = new()
        {
            ["Human City (Good Factions)"] = new[] { "Distrito Mercante", "Catedral", "Casa de Gremios" },
            ["Human Slums"] = new[] { "Callejones", "Puertos", "Foso de Lucha" },
            ["Elven Forest"] = new[] { "Arboleda Antigua", "Canopia", "Claro Lunar" },
            ["Dwarven Hold"] = new[] { "Gran Forja", "Minas Profundas", "Bazar de Piedra" },
            ["Outlands"] = new[] { "Fortin en Ruinas", "Pantano Sangriento", "Campamento Bandido" }
        };

        public static string PickSublocation(string territory)
        {
            if (Sublocations.TryGetValue(territory, out var opts) && opts.Length > 0)
                return opts[Random.Range(0, opts.Length)];
            return null;
        }

        // ═══════════════════════════════════════════════════════════
        //  PRIVATE HELPERS
        // ═══════════════════════════════════════════════════════════

        static List<WheelSegment> Simple<T>(T[] items, string prefix) where T : class
        {
            var segs = new List<WheelSegment>();
            if (items == null) return segs;
            foreach (var item in items)
            {
                string name; float weight;
                switch (item)
                {
                    case CountData cd: name = cd.name; weight = cd.weight; break;
                    case StatValueData sv: name = sv.name; weight = sv.weight; break;
                    case WeaponData wd: name = wd.name; weight = wd.weight; break;
                    case PowerData pd: name = pd.name; weight = pd.weight; break;
                    case SkillData sd: name = sd.name; weight = sd.weight; break;
                    case SpellData sp: name = sp.name; weight = sp.weight; break;
                    case ObjectData od: name = od.name; weight = od.weight; break;
                    case RaceData rd: name = rd.name; weight = rd.weight; break;
                    case GenderData gd: name = gd.name; weight = gd.weight; break;
                    case AgeBracketData ab: name = ab.name; weight = ab.weight; break;
                    case AlignmentData al: name = al.name; weight = al.weight; break;
                    case PlaceData pl: name = pl.name; weight = pl.weight; break;
                    case MagicTypeData mt: name = mt.name; weight = mt.weight; break;
                    case NameWeight nw: name = nw.name; weight = 1f; break;
                    default: continue;
                }
                segs.Add(new WheelSegment { Name = name, Weight = weight, Desc = $"{prefix}: {name}" });
            }
            return segs;
        }

        static List<WheelSegment> SimpleFlat<T>(T[] items, string prefix) where T : class
        {
            var segs = new List<WheelSegment>();
            if (items == null) return segs;
            foreach (var item in items)
            {
                string name;
                switch (item)
                {
                    case AlignmentData al: name = al.name; break;
                    case NameWeight nw: name = nw.name; break;
                    default: continue;
                }
                segs.Add(new WheelSegment { Name = name, Weight = 1f, Desc = $"{prefix}: {name}" });
            }
            return segs;
        }

        static List<WheelSegment> SimpleMastery(MasteryData[] items, string prefix)
        {
            var segs = new List<WheelSegment>();
            if (items == null) return segs;
            foreach (var m in items)
                segs.Add(new WheelSegment { Name = m.name, Weight = m.weight, Desc = $"{prefix}: {m.name} (+{m.bonus})" });
            return segs;
        }

        static float ApplyTagWeights(AdventureItemData item, Dictionary<string, float> tagWeights)
        {
            float weight = item.weight;
            if (item.tags != null)
                foreach (var tag in item.tags)
                    if (tagWeights.TryGetValue(tag, out float mult))
                        weight *= mult;
            return weight;
        }

        static float ComputeStatBonusForTags(List<string> tags, GameState state)
        {
            float bonus = 0f;
            if (tags.Any(t => t is "combat" or "honor"))
            {
                bonus += (state.GetStatValue("Strength") - 5) * 0.12f;
                bonus += (state.GetStatValue("Agility") - 5) * 0.08f;
                bonus += (state.GetStatValue("Durability") - 5) * 0.05f;
            }
            if (tags.Any(t => t is "magic" or "arcane" or "ritual" or "divine" or "research"))
                bonus += (state.GetStatValue("Intelligence") - 5) * 0.15f;
            if (tags.Any(t => t is "social" or "trade" or "politics" or "merchant" or "leadership"))
                bonus += (state.GetStatValue("Charisma") - 5) * 0.15f;
            if (tags.Any(t => t is "stealth" or "crime"))
                bonus += (state.GetStatValue("Agility") - 5) * 0.15f;
            if (tags.Any(t => t is "tracking" or "hunt" or "exploration"))
            {
                bonus += (state.GetStatValue("Agility") - 5) * 0.08f;
                bonus += (state.GetStatValue("Intelligence") - 5) * 0.07f;
            }
            if (tags.Any(t => t == "healing"))
            {
                bonus += (state.GetStatValue("Intelligence") - 5) * 0.1f;
                bonus += (state.GetStatValue("Charisma") - 5) * 0.05f;
            }
            return bonus;
        }

        static List<string> GetActionTags(DataRoot data, GameState state, int chapter)
        {
            string actionKey = $"Adventure Action {chapter}";
            string actionName = state.Selections.GetValueOrDefault(actionKey, "");
            var actionData = data.adventure_actions?.FirstOrDefault(a => a.name == actionName);
            return actionData?.tags != null ? new List<string>(actionData.tags) : new List<string>();
        }

        // Internal helper class
        class NameWeight { public string name; }
    }
}
