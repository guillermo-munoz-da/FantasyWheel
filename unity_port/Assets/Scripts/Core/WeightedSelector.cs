using System;
using System.Collections.Generic;
using System.Linq;

namespace DarkWheel.Core
{
    public static class WeightedSelector
    {
        public static T Pick<T>(IReadOnlyList<T> options, Func<T, int> weightSelector, Random random)
        {
            if (options == null || options.Count == 0)
            {
                return default;
            }

            var weighted = options.Where(x => weightSelector(x) > 0).ToList();
            if (weighted.Count == 0)
            {
                return default;
            }

            var total = weighted.Sum(weightSelector);
            var roll = random.Next(0, total);
            var cumulative = 0;

            foreach (var option in weighted)
            {
                cumulative += weightSelector(option);
                if (roll < cumulative)
                {
                    return option;
                }
            }

            return weighted[weighted.Count - 1];
        }
    }
}
