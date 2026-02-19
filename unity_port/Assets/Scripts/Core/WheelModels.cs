using System;
using System.Collections.Generic;

namespace DarkWheel.Core
{
    [Serializable]
    public class DataRoot
    {
        public List<NamedWeightedOption> races;
        public List<NamedWeightedOption> archetypes;
        public List<NamedWeightedOption> classes;
        public List<NamedWeightedOption> alignments;
        public List<NamedWeightedOption> places;
        public List<NamedWeightedOption> magic_types;
        public List<NamedWeightedOption> genders;
        public List<NamedWeightedOption> ages;
        public List<NamedWeightedOption> age_brackets;
        public List<NamedWeightedOption> skills;
        public List<NamedWeightedOption> personality_traits;
        public List<NamedWeightedOption> adventure_activities;
        public List<NamedWeightedOption> adventure_events;
        public List<NamedWeightedOption> adventure_actions;
    }

    [Serializable]
    public class NamedWeightedOption
    {
        public string name;
        public int weight = 1;
        public string desc;
        public string[] tags;
        public string[] classes;
        public List<HeightOption> height_options;
        public AgeRange age_range;
    }

    [Serializable]
    public class HeightOption
    {
        public string name;
        public int weight = 1;
    }

    [Serializable]
    public class AgeRange
    {
        public int min;
        public int max;
        public float immortal_chance;
    }

    public class WheelDefinition
    {
        public string Id;
        public List<WheelOption> Options = new List<WheelOption>();
    }

    public class WheelOption
    {
        public string Id;
        public string Label;
        public int Weight;
        public string Description;
        public Func<GameState, bool> IsAvailable;
    }

    public class SpinResult
    {
        public string WheelId;
        public WheelOption Option;
        public int Seed;
    }
}
