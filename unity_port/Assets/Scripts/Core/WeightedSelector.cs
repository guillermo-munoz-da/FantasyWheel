// WeightedSelector.cs – Generic weighted random picker matching Python weighted_choice
using System.Collections.Generic;
using UnityEngine;

namespace DarkWheel.Core
{
    public static class WeightedSelector
    {
        /// <summary>Pick a random index from a list of weights.</summary>
        public static int Pick(IReadOnlyList<float> weights)
        {
            float total = 0f;
            for (int i = 0; i < weights.Count; i++) total += Mathf.Max(0f, weights[i]);
            if (total <= 0f) return 0;
            float r = Random.Range(0f, total);
            float upto = 0f;
            for (int i = 0; i < weights.Count; i++)
            {
                upto += Mathf.Max(0f, weights[i]);
                if (upto >= r) return i;
            }
            return weights.Count - 1;
        }

        /// <summary>Pick from WheelOption list.</summary>
        public static int Pick(IReadOnlyList<WheelOption> options)
        {
            float total = 0f;
            for (int i = 0; i < options.Count; i++) total += Mathf.Max(0f, options[i].Weight);
            if (total <= 0f) return 0;
            float r = Random.Range(0f, total);
            float upto = 0f;
            for (int i = 0; i < options.Count; i++)
            {
                upto += Mathf.Max(0f, options[i].Weight);
                if (upto >= r) return i;
            }
            return options.Count - 1;
        }

        /// <summary>Pick from a list of (name, weight) tuples.</summary>
        public static int Pick(IReadOnlyList<(string name, float weight)> items)
        {
            float total = 0f;
            for (int i = 0; i < items.Count; i++) total += Mathf.Max(0f, items[i].weight);
            if (total <= 0f) return 0;
            float r = Random.Range(0f, total);
            float upto = 0f;
            for (int i = 0; i < items.Count; i++)
            {
                upto += Mathf.Max(0f, items[i].weight);
                if (upto >= r) return i;
            }
            return items.Count - 1;
        }
    }
}
