using UnityEngine;

namespace DarkWheel.Monetization
{
    public class MockAdService : IAdService
    {
        public bool IsEnabled => true;

        public bool ShowInterstitial(string placement)
        {
            Debug.Log($"[MockAd] Interstitial mostrado en {placement}");
            return true;
        }

        public bool ShowRewarded(string placement, out bool rewardGranted)
        {
            Debug.Log($"[MockAd] Rewarded solicitado en {placement}");
            rewardGranted = true;
            return true;
        }
    }
}
