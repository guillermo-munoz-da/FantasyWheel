using System.Collections.Generic;
using System.Text;
using DarkWheel.Bootstrap;
using DarkWheel.Core;
using TMPro;
using UnityEngine;

namespace DarkWheel.UI
{
    public class WheelDebugController : MonoBehaviour
    {
        [Header("UI")]
        [SerializeField] private TMP_Text currentWheelText;
        [SerializeField] private TMP_Text currentResultText;
        [SerializeField] private TMP_Text summaryText;

        private int _wheelIndex;
        private IReadOnlyList<string> _order;
        private int _adventureStage;

        public void BindTexts(TMP_Text wheelText, TMP_Text resultText, TMP_Text summary)
        {
            currentWheelText = wheelText;
            currentResultText = resultText;
            summaryText = summary;
        }

        private void Start()
        {
            if (GameBootstrap.Instance == null)
            {
                Debug.LogError("GameBootstrap no encontrado en escena.");
                enabled = false;
                return;
            }

            if (currentWheelText == null || currentResultText == null || summaryText == null)
            {
                Debug.LogError("WheelDebugController: faltan referencias TMP_Text en el inspector o en auto-setup.");
                enabled = false;
                return;
            }

            _order = GameBootstrap.Instance.CharacterFlow.WheelOrder;
            _wheelIndex = 0;
            _adventureStage = 0;
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
            _adventureStage = 0;
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
            if (_adventureStage <= 0)
            {
                var activityWheel = GameBootstrap.Instance.AdventureFlow.BuildActivityWheel();
                var activity = GameBootstrap.Instance.WheelEngine.Spin(activityWheel, state);
                if (activity.Option == null)
                {
                    RefreshTexts("No hay actividades de aventura disponibles");
                    return;
                }

                state.SetSelection("AdventureActivity", activity.Option.Label);
                state.AddLog($"Adventure Activity: {activity.Option.Label}");
                _adventureStage = 1;
                RefreshTexts($"Aventura[1/3] Activity -> {activity.Option.Label}");
                return;
            }

            if (_adventureStage == 1)
            {
                var selectedActivity = state.GetSelection("AdventureActivity");
                var eventWheel = GameBootstrap.Instance.AdventureFlow.BuildEventWheel(selectedActivity);
                var ev = GameBootstrap.Instance.WheelEngine.Spin(eventWheel, state);
                if (ev.Option == null)
                {
                    RefreshTexts("No hay eventos de aventura disponibles");
                    return;
                }

                state.SetSelection("AdventureEvent", ev.Option.Label);
                state.AddLog($"Adventure Event: {ev.Option.Label}");
                _adventureStage = 2;
                RefreshTexts($"Aventura[2/3] Event -> {ev.Option.Label}");
                return;
            }

            var activitySelection = state.GetSelection("AdventureActivity");
            var eventSelection = state.GetSelection("AdventureEvent");
            var actionWheel = GameBootstrap.Instance.AdventureFlow.BuildActionWheel(activitySelection, eventSelection);
            var action = GameBootstrap.Instance.WheelEngine.Spin(actionWheel, state);
            if (action.Option == null)
            {
                RefreshTexts("No hay acciones de aventura disponibles");
                return;
            }

            state.SetSelection("AdventureAction", action.Option.Label);
            state.AddLog($"Adventure Action: {action.Option.Label}");
            _adventureStage = 0;
            RefreshTexts($"Aventura[3/3] Action -> {action.Option.Label}. Siguiente click inicia nueva aventura.");
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
