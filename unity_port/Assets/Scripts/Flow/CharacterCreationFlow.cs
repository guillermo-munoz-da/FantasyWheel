using System;
using System.Collections.Generic;
using System.Linq;
using DarkWheel.Core;

namespace DarkWheel.Flow
{
    public class CharacterCreationFlow
    {
        private readonly DataRoot _data;

        public CharacterCreationFlow(DataRoot data)
        {
            _data = data;
        }

        public IReadOnlyList<string> WheelOrder => new[]
        {
            "Race", "Archetype", "Class", "Gender", "Age", "Height", "Alignment", "Place", "MagicType", "Skill", "Personality"
        };

        public WheelDefinition BuildWheel(string wheelId, GameState state)
        {
            return wheelId switch
            {
                "Race" => BuildFromSimple("Race", _data.races),
                "Archetype" => BuildFromSimple("Archetype", _data.archetypes),
                "Class" => BuildClassWheel(state),
                "Gender" => BuildFromSimple("Gender", _data.genders),
                "Age" => BuildAgeWheel(state),
                "Height" => BuildHeightWheel(state),
                "Alignment" => BuildFromSimple("Alignment", _data.alignments),
                "Place" => BuildFromSimple("Place", _data.places),
                "MagicType" => BuildFromSimple("MagicType", _data.magic_types),
                "Skill" => BuildFromSimple("Skill", _data.skills),
                "Personality" => BuildFromSimple("Personality", _data.personality_traits),
                _ => new WheelDefinition { Id = wheelId }
            };
        }

        private static WheelDefinition BuildFromSimple(string wheelId, List<NamedWeightedOption> list)
        {
            var wheel = new WheelDefinition { Id = wheelId };
            if (list == null)
            {
                return wheel;
            }

            foreach (var item in list)
            {
                wheel.Options.Add(new WheelOption
                {
                    Id = item.name,
                    Label = item.name,
                    Weight = Math.Max(1, item.weight),
                    Description = item.desc,
                    IsAvailable = _ => true
                });
            }

            return wheel;
        }

        private WheelDefinition BuildClassWheel(GameState state)
        {
            var wheel = new WheelDefinition { Id = "Class" };
            var selectedArchetype = state.GetSelection("Archetype");
            var fallback = _data.classes ?? new List<NamedWeightedOption>();

            if (string.IsNullOrEmpty(selectedArchetype))
            {
                foreach (var item in fallback)
                {
                    wheel.Options.Add(ToOption(item));
                }

                return wheel;
            }

            var archetype = _data.archetypes?.FirstOrDefault(a => string.Equals(a.name, selectedArchetype, StringComparison.OrdinalIgnoreCase));
            var allowedClasses = archetype?.classes ?? Array.Empty<string>();

            if (allowedClasses.Length == 0)
            {
                foreach (var item in fallback)
                {
                    wheel.Options.Add(ToOption(item));
                }

                return wheel;
            }

            foreach (var className in allowedClasses)
            {
                wheel.Options.Add(new WheelOption
                {
                    Id = className,
                    Label = className,
                    Weight = 1,
                    Description = $"Clase derivada de {selectedArchetype}",
                    IsAvailable = _ => true
                });
            }

            return wheel;
        }

        private WheelDefinition BuildAgeWheel(GameState state)
        {
            var selectedRace = state.GetSelection("Race");
            if (!string.IsNullOrWhiteSpace(selectedRace))
            {
                var race = _data.races?.FirstOrDefault(r => string.Equals(r.name, selectedRace, StringComparison.OrdinalIgnoreCase));
                var ageRange = race?.age_range;
                if (ageRange != null && ageRange.max > ageRange.min)
                {
                    var raceWheel = new WheelDefinition { Id = "Age" };
                    var span = Math.Max(1, ageRange.max - ageRange.min);
                    var step = Math.Max(1, span / 4);

                    var segmentStart = ageRange.min;
                    while (segmentStart <= ageRange.max)
                    {
                        var segmentEnd = Math.Min(ageRange.max, segmentStart + step - 1);
                        raceWheel.Options.Add(new WheelOption
                        {
                            Id = $"{segmentStart}-{segmentEnd}",
                            Label = $"{segmentStart}-{segmentEnd}",
                            Weight = 1,
                            IsAvailable = _ => true
                        });
                        segmentStart += step;
                    }

                    if (ageRange.immortal_chance > 0f)
                    {
                        raceWheel.Options.Add(new WheelOption
                        {
                            Id = "Immortal",
                            Label = "Immortal",
                            Weight = Math.Max(1, (int)Math.Round(ageRange.immortal_chance * 100f)),
                            IsAvailable = _ => true
                        });
                    }

                    return raceWheel;
                }
            }

            var configured = _data.age_brackets ?? _data.ages;
            if (configured != null && configured.Count > 0)
            {
                return BuildFromSimple("Age", configured);
            }

            var wheel = new WheelDefinition { Id = "Age" };
            wheel.Options.Add(new WheelOption { Id = "Young Adult", Label = "Young Adult", Weight = 40, IsAvailable = _ => true });
            wheel.Options.Add(new WheelOption { Id = "Adult", Label = "Adult", Weight = 35, IsAvailable = _ => true });
            wheel.Options.Add(new WheelOption { Id = "Elder", Label = "Elder", Weight = 20, IsAvailable = _ => true });
            wheel.Options.Add(new WheelOption { Id = "Immortal", Label = "Immortal", Weight = 5, IsAvailable = _ => true });
            return wheel;
        }

        private WheelDefinition BuildHeightWheel(GameState state)
        {
            var wheel = new WheelDefinition { Id = "Height" };
            var selectedRace = state.GetSelection("Race");
            var race = _data.races?.FirstOrDefault(r => string.Equals(r.name, selectedRace, StringComparison.OrdinalIgnoreCase));

            if (race?.height_options != null && race.height_options.Count > 0)
            {
                foreach (var option in race.height_options)
                {
                    wheel.Options.Add(new WheelOption
                    {
                        Id = option.name,
                        Label = option.name,
                        Weight = Math.Max(1, option.weight),
                        IsAvailable = _ => true
                    });
                }

                return wheel;
            }

            wheel.Options.Add(new WheelOption { Id = "1.60 m", Label = "1.60 m", Weight = 30, IsAvailable = _ => true });
            wheel.Options.Add(new WheelOption { Id = "1.75 m", Label = "1.75 m", Weight = 50, IsAvailable = _ => true });
            wheel.Options.Add(new WheelOption { Id = "1.90 m", Label = "1.90 m", Weight = 20, IsAvailable = _ => true });
            return wheel;
        }

        private static WheelOption ToOption(NamedWeightedOption item)
        {
            return new WheelOption
            {
                Id = item.name,
                Label = item.name,
                Weight = Math.Max(1, item.weight),
                Description = item.desc,
                IsAvailable = _ => true
            };
        }
    }
}
