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
            "Race", "Archetype", "Class", "Gender", "Age", "Alignment", "Place", "MagicType"
        };

        public WheelDefinition BuildWheel(string wheelId, GameState state)
        {
            return wheelId switch
            {
                "Race" => BuildFromSimple("Race", _data.races),
                "Archetype" => BuildFromSimple("Archetype", _data.archetypes),
                "Class" => BuildClassWheel(state),
                "Gender" => BuildFromSimple("Gender", _data.genders),
                "Age" => BuildDefaultAgeWheel(),
                "Alignment" => BuildFromSimple("Alignment", _data.alignments),
                "Place" => BuildFromSimple("Place", _data.places),
                "MagicType" => BuildFromSimple("MagicType", _data.magic_types),
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

        private static WheelDefinition BuildDefaultAgeWheel()
        {
            var wheel = new WheelDefinition { Id = "Age" };
            wheel.Options.Add(new WheelOption { Id = "Young Adult", Label = "Young Adult", Weight = 40, IsAvailable = _ => true });
            wheel.Options.Add(new WheelOption { Id = "Adult", Label = "Adult", Weight = 35, IsAvailable = _ => true });
            wheel.Options.Add(new WheelOption { Id = "Elder", Label = "Elder", Weight = 20, IsAvailable = _ => true });
            wheel.Options.Add(new WheelOption { Id = "Immortal", Label = "Immortal", Weight = 5, IsAvailable = _ => true });
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
