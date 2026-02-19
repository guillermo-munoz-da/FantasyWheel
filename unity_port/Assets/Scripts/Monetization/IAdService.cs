namespace DarkWheel.Monetization
{
    public interface IAdService
    {
        bool IsEnabled { get; }
        bool ShowInterstitial(string placement);
        bool ShowRewarded(string placement, out bool rewardGranted);
    }
}
