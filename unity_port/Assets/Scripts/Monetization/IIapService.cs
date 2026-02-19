namespace DarkWheel.Monetization
{
    public interface IIapService
    {
        bool IsEnabled { get; }
        bool Purchase(string productId);
    }
}
