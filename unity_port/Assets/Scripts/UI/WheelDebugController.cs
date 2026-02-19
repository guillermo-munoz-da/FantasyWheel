using System.Collections.Generic;
using System.Text;
using DarkWheel.Bootstrap;
using DarkWheel.Core;
using UnityEngine;
using UnityEngine.UI;

namespace DarkWheel.UI
{
    public class WheelDebugController : MonoBehaviour
    {
        [Header("UI")]
        [SerializeField] private Text currentWheelText;
        [SerializeField] private Text currentResultText;
        [SerializeField] private Text summaryText;

        private int _wheelIndex;
        private IReadOnlyList<string> _order;

        private void Start()
        {
            _order = GameBootstrap.Instance.CharacterFlow.WheelOrder;
            _wheelIndex = 0;
            RefreshTexts("Listo para girar");
        }

        public void SpinCurrentWheel()
        {
            if (_wheelIndex >= _order.Count)
            {
                currentResultText.text = "Creación completa";
                return;
            }

            var wheelId = _order[_wheelIndex];
            var state = GameBootstrap.Instance.State;
            var wheel = GameBootstrap.Instance.CharacterFlow.BuildWheel(wheelId, state);
            var spin = GameBootstrap.Instance.WheelEngine.Spin(wheel, state);

            if (spin.Option == null)
            {
                currentResultText.text = $"Sin opciones para {wheelId}";
                return;
            }

            state.SetSelection(wheelId, spin.Option.Label);
            state.AddLog($"{wheelId}: {spin.Option.Label}");

            currentResultText.text = $"{wheelId} -> {spin.Option.Label}";
            _wheelIndex++;
            RefreshTexts(currentResultText.text);
        }

        public void ResetFlow()
        {
            var oldState = GameBootstrap.Instance.State;
            oldState.Selections.Clear();
            oldState.HistoryLog.Clear();
            _wheelIndex = 0;
            RefreshTexts("Reseteado");
        }

        public void SaveState()
        {
            GameBootstrap.Instance.SaveService.Save(GameBootstrap.Instance.State);
            RefreshTexts("Partida guardada");
        }

        public void LoadState()
        {
            var loaded = GameBootstrap.Instance.SaveService.TryLoad(GameBootstrap.Instance.State);
            if (loaded)
            {
                _wheelIndex = GameBootstrap.Instance.State.Selections.Count;
                if (_wheelIndex > _order.Count)
                {
                    _wheelIndex = _order.Count;
                }
            }
            RefreshTexts(loaded ? "Partida cargada" : "No hay guardado");
        }

        public void SimulateRewardedAd()
        {
            GameBootstrap.Instance.AdService.ShowRewarded("debug.reroll", out var rewardGranted);
            RefreshTexts(rewardGranted ? "Reward concedido" : "Reward denegado");
        }

        public void SpinAdventureSlice()
        {
            var state = GameBootstrap.Instance.State;
            var activityWheel = GameBootstrap.Instance.AdventureFlow.BuildActivityWheel();
            var eventWheel = GameBootstrap.Instance.AdventureFlow.BuildEventWheel();
            var actionWheel = GameBootstrap.Instance.AdventureFlow.BuildActionWheel();

            var activity = GameBootstrap.Instance.WheelEngine.Spin(activityWheel, state);
            var ev = GameBootstrap.Instance.WheelEngine.Spin(eventWheel, state);
            var action = GameBootstrap.Instance.WheelEngine.Spin(actionWheel, state);

            if (activity.Option == null || ev.Option == null || action.Option == null)
            {
                RefreshTexts("No hay datos suficientes para aventura");
                return;
            }

            state.SetSelection("AdventureActivity", activity.Option.Label);
            state.SetSelection("AdventureEvent", ev.Option.Label);
            state.SetSelection("AdventureAction", action.Option.Label);

            state.AddLog($"Adventure Activity: {activity.Option.Label}");
            state.AddLog($"Adventure Event: {ev.Option.Label}");
            state.AddLog($"Adventure Action: {action.Option.Label}");

            RefreshTexts($"Aventura -> {activity.Option.Label} / {ev.Option.Label} / {action.Option.Label}");
        }

        private void RefreshTexts(string status)
        {
            if (_wheelIndex >= _order.Count)
            {
                currentWheelText.text = "Current Wheel: FIN";
            }
            else
            {
                currentWheelText.text = $"Current Wheel: {_order[_wheelIndex]}";
            }

            if (!string.IsNullOrWhiteSpace(status))
            {
                currentResultText.text = status;
            }

            var state = GameBootstrap.Instance.State;
            var builder = new StringBuilder();
            builder.AppendLine("Character Summary");

            foreach (var entry in state.Selections)
            {
                builder.AppendLine($"- {entry.Key}: {entry.Value}");
            }

            summaryText.text = builder.ToString();
        }
    }
}
