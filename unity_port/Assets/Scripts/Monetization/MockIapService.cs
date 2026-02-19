using UnityEngine;

namespace DarkWheel.Monetization
{
    public class MockIapService : IIapService
    {
        public bool IsEnabled => false;

        public bool Purchase(string productId)
        {
            Debug.Log($"[MockIAP] Compra simulada: {productId}");
            return false;
        }
    }
}
