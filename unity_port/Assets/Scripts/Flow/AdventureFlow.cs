using System;
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

        public WheelDefinition BuildEventWheel()
        {
            var wheel = new WheelDefinition { Id = "AdventureEvent" };
            if (_data.adventure_events == null)
            {
                return wheel;
            }

            foreach (var option in _data.adventure_events)
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

        public WheelDefinition BuildActionWheel()
        {
            var wheel = new WheelDefinition { Id = "AdventureAction" };
            if (_data.adventure_actions == null)
            {
                return wheel;
            }

            foreach (var option in _data.adventure_actions)
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
    }
}
