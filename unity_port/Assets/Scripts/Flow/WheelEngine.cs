using System;
using System.Collections.Generic;
using System.Linq;
using DarkWheel.Core;

namespace DarkWheel.Flow
{
    public class WheelEngine
    {
        private readonly Random _random;

        public WheelEngine(int? seed = null)
        {
            _random = seed.HasValue ? new Random(seed.Value) : new Random();
        }

        public List<WheelOption> GetAvailableOptions(WheelDefinition wheel, GameState state)
        {
            return wheel.Options
                .Where(option => option.Weight > 0)
                .Where(option => option.IsAvailable == null || option.IsAvailable(state))
                .ToList();
        }

        public SpinResult Spin(WheelDefinition wheel, GameState state, int seed = 0)
        {
            var options = GetAvailableOptions(wheel, state);
            var selected = WeightedSelector.Pick(options, option => option.Weight, _random);
            return new SpinResult
            {
                WheelId = wheel.Id,
                Option = selected,
                Seed = seed
            };
        }
    }
}
