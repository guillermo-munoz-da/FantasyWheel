using System;
using System.Collections.Generic;
using System.Linq;
using DarkWheel.Core;

namespace DarkWheel.Flow
{
    public class AdventureFlow
    {
        private readonly DataRoot _data;

        public AdventureFlow(DataRoot data)
        {
            _data = data;
        }

        public WheelDefinition BuildActivityWheel()
        {
            var wheel = new WheelDefinition { Id = "AdventureActivity" };
            if (_data.adventure_activities == null)
            {
                return wheel;
            }

            foreach (var option in _data.adventure_activities)
            {
                wheel.Options.Add(new WheelOption
                {
                    Id = option.name,
                    Label = option.name,
                    Weight = Math.Max(1, option.weight),
                    Description = option.desc,
                    IsAvailable = _ => true
                });
            }

            return wheel;
        }

        public WheelDefinition BuildEventWheel(string selectedActivity)
        {
            var wheel = new WheelDefinition { Id = "AdventureEvent" };
            if (_data.adventure_events == null)
            {
                return wheel;
            }

            var activityTags = GetTags(_data.adventure_activities, selectedActivity);

            foreach (var option in _data.adventure_events)
            {
                var weight = Math.Max(1, option.weight);
                if (activityTags.Count > 0 && option.tags != null && option.tags.Any(tag => activityTags.Contains(tag)))
                {
                    weight = Math.Max(1, weight * 2);
                }

                wheel.Options.Add(new WheelOption
                {
                    Id = option.name,
                    Label = option.name,
                    Weight = weight,
                    Description = option.desc,
                    IsAvailable = _ => true
                });
            }

            return wheel;
        }

        public WheelDefinition BuildActionWheel(string selectedActivity, string selectedEvent)
        {
            var wheel = new WheelDefinition { Id = "AdventureAction" };
            if (_data.adventure_actions == null)
            {
                return wheel;
            }

            var activityTags = GetTags(_data.adventure_activities, selectedActivity);
            var eventTags = GetTags(_data.adventure_events, selectedEvent);
            var mergedTags = new HashSet<string>(activityTags, StringComparer.OrdinalIgnoreCase);
            foreach (var tag in eventTags)
            {
                mergedTags.Add(tag);
            }

            foreach (var option in _data.adventure_actions)
            {
                var weight = Math.Max(1, option.weight);
                if (mergedTags.Count > 0 && option.tags != null && option.tags.Any(tag => mergedTags.Contains(tag)))
                {
                    weight = Math.Max(1, weight * 2);
                }

                wheel.Options.Add(new WheelOption
                {
                    Id = option.name,
                    Label = option.name,
                    Weight = weight,
                    Description = option.desc,
                    IsAvailable = _ => true
                });
            }

            return wheel;
        }

        private static HashSet<string> GetTags(List<NamedWeightedOption> source, string selectedName)
        {
            if (source == null || string.IsNullOrWhiteSpace(selectedName))
            {
                return new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            }

            var selected = source.FirstOrDefault(item => string.Equals(item.name, selectedName, StringComparison.OrdinalIgnoreCase));
            if (selected?.tags == null)
            {
                return new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            }

            return new HashSet<string>(selected.tags, StringComparer.OrdinalIgnoreCase);
        }
    }
}
