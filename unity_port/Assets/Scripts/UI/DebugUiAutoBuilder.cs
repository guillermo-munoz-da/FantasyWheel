using DarkWheel.Bootstrap;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace DarkWheel.UI
{
    public class DebugUiAutoBuilder : MonoBehaviour
    {
        [SerializeField] private bool buildOnStart = true;

        private void Start()
        {
            if (!buildOnStart)
            {
                return;
            }

            Build();
        }

        [ContextMenu("Build Debug UI")]
        public void Build()
        {
            EnsureBootstrap();
            EnsureEventSystem();

            var canvas = EnsureCanvas();
            var panel = EnsurePanel(canvas.transform as RectTransform);

            var currentWheelText = EnsureText(panel, "CurrentWheelText", 30f, 32f, 26f);
            var currentResultText = EnsureText(panel, "CurrentResultText", 30f, 32f, 24f);
            var summaryText = EnsureText(panel, "SummaryText", 30f, 220f, 22f);

            var spinCharacter = EnsureButton(panel, "Spin Character", "Spin Character");
            var adventure = EnsureButton(panel, "Adventure", "Adventure");
            var reset = EnsureButton(panel, "Reset", "Reset");
            var save = EnsureButton(panel, "Save", "Save");
            var load = EnsureButton(panel, "Load", "Load");
            var rewarded = EnsureButton(panel, "Rewarded Mock", "Rewarded Mock");

            var controllerObject = GameObject.Find("UIController") ?? new GameObject("UIController");
            var controller = controllerObject.GetComponent<WheelDebugController>() ?? controllerObject.AddComponent<WheelDebugController>();
            controller.BindTexts(currentWheelText, currentResultText, summaryText);

            BindButton(spinCharacter, controller.SpinCurrentWheel);
            BindButton(adventure, controller.SpinAdventureSlice);
            BindButton(reset, controller.ResetFlow);
            BindButton(save, controller.SaveState);
            BindButton(load, controller.LoadState);
            BindButton(rewarded, controller.SimulateRewardedAd);

            Debug.Log("Debug UI auto-build completado.");
        }

        private static void EnsureBootstrap()
        {
            if (GameBootstrap.Instance != null)
            {
                return;
            }

            var bootstrapObject = GameObject.Find("Bootstrap") ?? new GameObject("Bootstrap");
            if (bootstrapObject.GetComponent<GameBootstrap>() == null)
            {
                bootstrapObject.AddComponent<GameBootstrap>();
            }
        }

        private static void EnsureEventSystem()
        {
            if (EventSystem.current != null)
            {
                return;
            }

            var eventSystemObject = new GameObject("EventSystem");
            eventSystemObject.AddComponent<EventSystem>();
            eventSystemObject.AddComponent<StandaloneInputModule>();
        }

        private static Canvas EnsureCanvas()
        {
            var canvasObject = GameObject.Find("Canvas");
            Canvas canvas;
            if (canvasObject == null)
            {
                canvasObject = new GameObject("Canvas");
                canvas = canvasObject.AddComponent<Canvas>();
                canvasObject.AddComponent<CanvasScaler>();
                canvasObject.AddComponent<GraphicRaycaster>();
            }
            else
            {
                canvas = canvasObject.GetComponent<Canvas>() ?? canvasObject.AddComponent<Canvas>();
                if (canvasObject.GetComponent<CanvasScaler>() == null)
                {
                    canvasObject.AddComponent<CanvasScaler>();
                }

                if (canvasObject.GetComponent<GraphicRaycaster>() == null)
                {
                    canvasObject.AddComponent<GraphicRaycaster>();
                }
            }

            canvas.renderMode = RenderMode.ScreenSpaceOverlay;

            var scaler = canvasObject.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1080, 1920);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;

            return canvas;
        }

        private static RectTransform EnsurePanel(RectTransform canvasTransform)
        {
            var panelObject = GameObject.Find("DebugPanel");
            if (panelObject == null)
            {
                panelObject = new GameObject("DebugPanel", typeof(RectTransform), typeof(Image), typeof(VerticalLayoutGroup), typeof(ContentSizeFitter));
                panelObject.transform.SetParent(canvasTransform, false);
            }

            var panelRect = panelObject.GetComponent<RectTransform>();
            panelRect.anchorMin = new Vector2(0f, 1f);
            panelRect.anchorMax = new Vector2(0f, 1f);
            panelRect.pivot = new Vector2(0f, 1f);
            panelRect.anchoredPosition = new Vector2(24f, -24f);
            panelRect.sizeDelta = new Vector2(640f, 0f);

            var image = panelObject.GetComponent<Image>();
            image.color = new Color(0f, 0f, 0f, 0.55f);

            var layout = panelObject.GetComponent<VerticalLayoutGroup>();
            layout.childControlWidth = true;
            layout.childControlHeight = false;
            layout.childForceExpandWidth = true;
            layout.childForceExpandHeight = false;
            layout.spacing = 10f;
            layout.padding = new RectOffset(16, 16, 16, 16);

            var fitter = panelObject.GetComponent<ContentSizeFitter>();
            fitter.horizontalFit = ContentSizeFitter.FitMode.Unconstrained;
            fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            return panelRect;
        }

        private static TMP_Text EnsureText(Transform parent, string name, float width, float height, float fontSize)
        {
            var textObject = GameObject.Find(name);
            if (textObject == null)
            {
                textObject = new GameObject(name, typeof(RectTransform), typeof(TextMeshProUGUI));
                textObject.transform.SetParent(parent, false);
            }

            var textRect = textObject.GetComponent<RectTransform>();
            textRect.sizeDelta = new Vector2(width, height);

            var text = textObject.GetComponent<TextMeshProUGUI>();
            text.text = name;
            text.fontSize = fontSize;
            text.color = Color.white;
            text.alignment = TextAlignmentOptions.Left;
            text.enableWordWrapping = true;

            return text;
        }

        private static Button EnsureButton(Transform parent, string name, string label)
        {
            var buttonObject = GameObject.Find(name);
            if (buttonObject == null)
            {
                buttonObject = new GameObject(name, typeof(RectTransform), typeof(Image), typeof(Button));
                buttonObject.transform.SetParent(parent, false);

                var labelObject = new GameObject("Label", typeof(RectTransform), typeof(TextMeshProUGUI));
                labelObject.transform.SetParent(buttonObject.transform, false);
                var labelRect = labelObject.GetComponent<RectTransform>();
                labelRect.anchorMin = Vector2.zero;
                labelRect.anchorMax = Vector2.one;
                labelRect.offsetMin = Vector2.zero;
                labelRect.offsetMax = Vector2.zero;
            }

            var rect = buttonObject.GetComponent<RectTransform>();
            rect.sizeDelta = new Vector2(280f, 64f);

            var image = buttonObject.GetComponent<Image>();
            image.color = new Color32(38, 50, 56, 255);

            var button = buttonObject.GetComponent<Button>();
            var colors = button.colors;
            colors.normalColor = new Color32(38, 50, 56, 255);
            colors.highlightedColor = new Color32(55, 71, 79, 255);
            colors.pressedColor = new Color32(69, 90, 100, 255);
            colors.selectedColor = colors.highlightedColor;
            button.colors = colors;

            var labelText = buttonObject.GetComponentInChildren<TextMeshProUGUI>();
            labelText.text = label;
            labelText.fontSize = 24f;
            labelText.color = Color.white;
            labelText.alignment = TextAlignmentOptions.Center;

            return button;
        }

        private static void BindButton(Button button, UnityEngine.Events.UnityAction action)
        {
            button.onClick.RemoveAllListeners();
            button.onClick.AddListener(action);
        }
    }
}
