using DarkWheel.Core;
using DarkWheel.Data;
using DarkWheel.Flow;
using DarkWheel.Monetization;
using UnityEngine;

namespace DarkWheel.Bootstrap
{
    public class GameBootstrap : MonoBehaviour
    {
        public static GameBootstrap Instance { get; private set; }

        public GameState State { get; private set; }
        public DataRoot Data { get; private set; }
        public WheelEngine WheelEngine { get; private set; }
        public CharacterCreationFlow CharacterFlow { get; private set; }
        public AdventureFlow AdventureFlow { get; private set; }
        public SaveService SaveService { get; private set; }
        public IAdService AdService { get; private set; }
        public IIapService IapService { get; private set; }

        [SerializeField] private int seed = 0;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }

            Instance = this;
            DontDestroyOnLoad(gameObject);

            State = new GameState();
            Data = new JsonDataLoader().Load();
            WheelEngine = seed == 0 ? new WheelEngine() : new WheelEngine(seed);
            CharacterFlow = new CharacterCreationFlow(Data);
            AdventureFlow = new AdventureFlow(Data);
            SaveService = new SaveService();
            AdService = new MockAdService();
            IapService = new MockIapService();

            Debug.Log("GameBootstrap inicializado.");
        }
    }
}
