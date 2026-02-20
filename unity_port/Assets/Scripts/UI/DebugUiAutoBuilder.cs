// DebugUiAutoBuilder.cs – Runtime canvas builder for quick testing without manual UI setup.
// Creates a full debug UI with TMP labels, buttons, and scroll views,
// then attaches WheelDebugController with all references wired.
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace DarkWheel.UI
{
    /// <summary>
    /// Attach to the same GameObject as GameBootstrap. On Awake it creates
    /// a complete Canvas + TMP debug UI and wires it to WheelDebugController.
    /// </summary>
    [DefaultExecutionOrder(-50)]
    public class DebugUiAutoBuilder : MonoBehaviour
    {
        [Header("Optional overrides")]
        [SerializeField] Font _fallbackFont;

        Canvas _canvas;

        void Start()
        {
            BuildCanvas();
        }

        void BuildCanvas()
        {
            // ── Canvas ──
            var canvasGo = new GameObject("DebugCanvas");
            canvasGo.transform.SetParent(transform);
            _canvas = canvasGo.AddComponent<Canvas>();
            _canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            _canvas.sortingOrder = 100;
            canvasGo.AddComponent<CanvasScaler>().uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            canvasGo.GetComponent<CanvasScaler>().referenceResolution = new Vector2(1920, 1080);
            canvasGo.AddComponent<GraphicRaycaster>();

            // ── Background ──
            var bg = AddPanel(canvasGo.transform, "BG", Color.black * 0.92f);
            bg.anchorMin = Vector2.zero; bg.anchorMax = Vector2.one;
            bg.offsetMin = Vector2.zero; bg.offsetMax = Vector2.zero;

            // ── Left column (wheel info) ──
            var leftCol = AddPanel(canvasGo.transform, "Left", new Color(0.07f, 0.07f, 0.18f));
            leftCol.anchorMin = new Vector2(0, 0); leftCol.anchorMax = new Vector2(0.45f, 1f);
            leftCol.offsetMin = new Vector2(10, 10); leftCol.offsetMax = new Vector2(-5, -10);
            var leftLayout = leftCol.gameObject.AddComponent<VerticalLayoutGroup>();
            leftLayout.padding = new RectOffset(10, 10, 10, 10);
            leftLayout.spacing = 8;
            leftLayout.childForceExpandHeight = false;

            var titleLabel = AddLabel(leftCol.transform, "Title", "Dark Wheel", 24, Color.yellow);
            var contextLabel = AddLabel(leftCol.transform, "Context", "...", 14, new Color(0.93f, 0.74f, 0.11f));
            var resultLabel = AddLabel(leftCol.transform, "Result", "", 18, Color.green);

            // Segment list (scrollable)
            var segScroll = AddScrollView(leftCol.transform, "SegmentScroll", 400);
            var segContent = segScroll.content;

            // Segment prefab (hidden template)
            var segPrefab = new GameObject("SegPrefab");
            segPrefab.SetActive(false);
            segPrefab.transform.SetParent(canvasGo.transform);
            var segPrefabRect = segPrefab.AddComponent<RectTransform>();
            segPrefabRect.sizeDelta = new Vector2(0, 28);
            var segLayout = segPrefab.AddComponent<LayoutElement>();
            segLayout.preferredHeight = 28;
            segLayout.flexibleWidth = 1;
            var segTmp = segPrefab.AddComponent<TextMeshProUGUI>();
            segTmp.fontSize = 13;
            segTmp.color = new Color(0.93f, 0.74f, 0.11f);
            segTmp.alignment = TextAlignmentOptions.MidlineLeft;

            // Buttons row
            var btnRow = new GameObject("BtnRow");
            btnRow.transform.SetParent(leftCol.transform);
            var btnRowRect = btnRow.AddComponent<RectTransform>();
            btnRowRect.sizeDelta = new Vector2(0, 50);
            var btnLayout = btnRow.AddComponent<HorizontalLayoutGroup>();
            btnLayout.spacing = 10;
            btnLayout.childForceExpandWidth = true;
            var btnLE = btnRow.AddComponent<LayoutElement>();
            btnLE.preferredHeight = 50;

            var spinBtn = AddButton(btnRow.transform, "SPIN", new Color(0.93f, 0.74f, 0.11f), Color.black);
            var endRunBtn = AddButton(btnRow.transform, "END RUN", new Color(0.8f, 0.2f, 0.2f), Color.white);
            var newGameBtn = AddButton(btnRow.transform, "NEW GAME", new Color(0.2f, 0.6f, 0.2f), Color.white);

            // ── Right column (char sheet + log) ──
            var rightCol = AddPanel(canvasGo.transform, "Right", new Color(0.05f, 0.05f, 0.14f));
            rightCol.anchorMin = new Vector2(0.45f, 0); rightCol.anchorMax = new Vector2(1f, 1f);
            rightCol.offsetMin = new Vector2(5, 10); rightCol.offsetMax = new Vector2(-10, -10);
            var rightLayout = rightCol.gameObject.AddComponent<VerticalLayoutGroup>();
            rightLayout.padding = new RectOffset(10, 10, 10, 10);
            rightLayout.spacing = 8;
            rightLayout.childForceExpandHeight = false;

            AddLabel(rightCol.transform, "CharHeader", "Character Sheet", 16, Color.yellow);
            var charScroll = AddScrollView(rightCol.transform, "CharScroll", 350);
            var charSheetText = AddLabel(charScroll.content, "CharSheet", "", 11, new Color(0.93f, 0.74f, 0.11f));

            AddLabel(rightCol.transform, "LogHeader", "Adventure Log", 16, Color.yellow);
            var logScroll = AddScrollView(rightCol.transform, "LogScroll", 300);
            var logText = AddLabel(logScroll.content, "Log", "", 10, new Color(0.7f, 0.7f, 0.7f));

            // ── Wire WheelDebugController ──
            var ctrl = canvasGo.AddComponent<WheelDebugController>();
            // Use reflection to set serialized fields (debug-only convenience)
            SetField(ctrl, "_titleLabel", titleLabel);
            SetField(ctrl, "_contextLabel", contextLabel);
            SetField(ctrl, "_resultLabel", resultLabel);
            SetField(ctrl, "_charSheetText", charSheetText);
            SetField(ctrl, "_logText", logText);
            SetField(ctrl, "_spinButton", spinBtn);
            SetField(ctrl, "_endRunButton", endRunBtn);
            SetField(ctrl, "_newGameButton", newGameBtn);
            SetField(ctrl, "_segmentListParent", segContent);
            SetField(ctrl, "_segmentPrefab", segPrefab);
        }

        // ── UI Factory Helpers ──────────────────────────────────────

        static RectTransform AddPanel(Transform parent, string name, Color color)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var rect = go.AddComponent<RectTransform>();
            var img = go.AddComponent<Image>();
            img.color = color;
            return rect;
        }

        static TMP_Text AddLabel(Transform parent, string name, string text, int size, Color color)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var rect = go.AddComponent<RectTransform>();
            rect.sizeDelta = new Vector2(0, size + 10);
            var le = go.AddComponent<LayoutElement>();
            le.preferredHeight = size + 10;
            le.flexibleWidth = 1;
            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.text = text;
            tmp.fontSize = size;
            tmp.color = color;
            tmp.alignment = TextAlignmentOptions.TopLeft;
            tmp.enableWordWrapping = true;
            return tmp;
        }

        static Button AddButton(Transform parent, string label, Color bgColor, Color textColor)
        {
            var go = new GameObject(label);
            go.transform.SetParent(parent, false);
            var rect = go.AddComponent<RectTransform>();
            rect.sizeDelta = new Vector2(0, 44);
            var img = go.AddComponent<Image>();
            img.color = bgColor;
            var btn = go.AddComponent<Button>();

            var txtGo = new GameObject("Label");
            txtGo.transform.SetParent(go.transform, false);
            var txtRect = txtGo.AddComponent<RectTransform>();
            txtRect.anchorMin = Vector2.zero; txtRect.anchorMax = Vector2.one;
            txtRect.offsetMin = Vector2.zero; txtRect.offsetMax = Vector2.zero;
            var tmp = txtGo.AddComponent<TextMeshProUGUI>();
            tmp.text = label;
            tmp.fontSize = 16;
            tmp.color = textColor;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.fontStyle = FontStyles.Bold;

            return btn;
        }

        static ScrollRect AddScrollView(Transform parent, string name, float height)
        {
            // Scroll container
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var rect = go.AddComponent<RectTransform>();
            rect.sizeDelta = new Vector2(0, height);
            var le = go.AddComponent<LayoutElement>();
            le.preferredHeight = height;
            le.flexibleWidth = 1;
            le.flexibleHeight = 1;
            var mask = go.AddComponent<RectMask2D>();

            var scrollRect = go.AddComponent<ScrollRect>();
            scrollRect.horizontal = false;

            // Content
            var contentGo = new GameObject("Content");
            contentGo.transform.SetParent(go.transform, false);
            var contentRect = contentGo.AddComponent<RectTransform>();
            contentRect.anchorMin = new Vector2(0, 1);
            contentRect.anchorMax = new Vector2(1, 1);
            contentRect.pivot = new Vector2(0.5f, 1);
            contentRect.offsetMin = Vector2.zero;
            contentRect.offsetMax = Vector2.zero;
            var csf = contentGo.AddComponent<ContentSizeFitter>();
            csf.verticalFit = ContentSizeFitter.FitMode.PreferredSize;
            var vlg = contentGo.AddComponent<VerticalLayoutGroup>();
            vlg.childForceExpandHeight = false;
            vlg.childForceExpandWidth = true;
            vlg.spacing = 2;

            scrollRect.content = contentRect;
            return scrollRect;
        }

        static void SetField(object target, string fieldName, object value)
        {
            var field = target.GetType().GetField(fieldName,
                System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            field?.SetValue(target, value);
        }
    }
}
