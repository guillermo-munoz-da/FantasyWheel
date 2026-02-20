// WheelModels.cs – Complete data models matching Python prototype 1:1
using System;
using System.Collections.Generic;
using UnityEngine;

namespace DarkWheel.Core
{
    [Serializable] public class HeightOption { public string name; public float weight = 1f; }
    [Serializable] public class AgeRange { public int min = 16; public int max = 60; public float immortal_chance; }

    [Serializable]
    public class RaceData
    {
        public string name;
        public float weight = 1f;
        public HeightOption[] height_options;
        public AgeRange age_range;
        // stat_mods parsed manually (JsonUtility can't do Dict)
    }

    [Serializable] public class ArchetypeData { public string name; public string[] classes; }
    [Serializable] public class MagicTypeData { public string name; public float weight = 1f; }
    [Serializable] public class SpellData { public string name; public float weight = 1f; public string desc; }
    [Serializable] public class PowerData { public string name; public float weight = 1f; public string desc; }
    [Serializable] public class SkillData { public string name; public float weight = 1f; public string desc; }
    [Serializable] public class ObjectData { public string name; public float weight = 1f; public string desc; }
    [Serializable] public class PersonalityTrait { public string name; public string desc; public float weight = 1f; }
    [Serializable] public class AlignmentData { public string name; public float weight = 1f; }
    [Serializable] public class PlaceData { public string name; public float weight = 1f; }
    [Serializable] public class GenderData { public string name; public float weight = 1f; }
    [Serializable] public class AgeBracketData { public string name; public float weight = 1f; }
    [Serializable] public class StatValueData { public string name; public float weight = 1f; public int value; }
    [Serializable] public class WeaponData { public string name; public float weight = 1f; }
    [Serializable] public class MasteryData { public string name; public float weight = 1f; public int bonus; }
    [Serializable] public class EfficiencyData { public string name; public float weight = 1f; public float multiplier = 1f; }
    [Serializable] public class CountData { public string name; public float weight = 1f; }
    [Serializable] public class FactionData { public string name; public string[] tags; }

    [Serializable] public class EventOutcome
    {
        public string name; public float weight = 1f; public string narrative;
        // effects: key=stat abbreviation (str,int,agi,cha,durability,random_stat), value=delta
    }
    [Serializable] public class EventData
    {
        public string name; public float weight = 1f; public string desc;
        public EventOutcome[] outcomes;
    }
    [Serializable] public class ActionData { public string name; public string desc; public float weight = 1f; }

    [Serializable]
    public class AdventureItemData
    {
        public string name;
        public float weight = 1f;
        public string desc;
        public string[] tags;
        public string terminal; // "death" | "victory" | null
    }

    // ── Root JSON container ───────────────────────────────────────────
    [Serializable]
    public class DataRoot
    {
        public RaceData[] races;
        public ArchetypeData[] archetypes;
        public AlignmentData[] alignments;
        public MagicTypeData[] magic_types;
        public GenderData[] genders;
        public AgeBracketData[] ages;
        public StatValueData[] stat_values;
        public WeaponData[] weapons;
        public PowerData[] powers;
        public SkillData[] skills;
        public SpellData[] spells;
        public ObjectData[] objects;
        public PersonalityTrait[] personality_traits;
        public PlaceData[] places;
        public CountData[] power_count;
        public CountData[] magic_count;
        public CountData[] skills_count;
        public CountData[] items_count;
        public MasteryData[] weapon_masteries;
        public MasteryData[] power_skills;
        public MasteryData[] magic_skills;
        public EfficiencyData[] skill_efficiency;
        public EventData[] events;
        public ActionData[] actions;
        public AdventureItemData[] adventure_activities;
        public AdventureItemData[] adventure_events;
        public AdventureItemData[] adventure_actions;
        public AdventureItemData[] adventure_outcomes;
        public FactionData[] factions;
    }

    // ── Lightweight option used by wheel engine ───────────────────────
    public struct WheelOption
    {
        public string Name;
        public float Weight;
        public string Desc;
        public string[] Tags;
        public string Terminal;
    }
}
