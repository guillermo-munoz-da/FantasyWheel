using System;
using System.IO;
using System.Text;
using DarkWheel.Core;
using UnityEngine;

namespace DarkWheel.Data
{
    public class JsonDataLoader
    {
        private const string SanitizedDataFileName = "data.unity.json";
        private const string DefaultDataFileName = "data.json";

        public DataRoot Load()
        {
            var primaryPath = Path.Combine(Application.streamingAssetsPath, SanitizedDataFileName);
            var fallbackPath = Path.Combine(Application.streamingAssetsPath, DefaultDataFileName);
            var path = File.Exists(primaryPath) ? primaryPath : fallbackPath;

            if (!File.Exists(path))
            {
                Debug.LogError($"No se encontró {SanitizedDataFileName} ni {DefaultDataFileName} en {Application.streamingAssetsPath}");
                return new DataRoot();
            }

            try
            {
                var json = ReadUtf8NoBom(path);
                var root = JsonUtility.FromJson<DataRoot>(json);

                if (root != null)
                {
                    Debug.Log($"JSON cargado desde {Path.GetFileName(path)}");
                    return root;
                }

                var escapedUnicodeJson = EscapeNonAscii(json);
                var retryRoot = JsonUtility.FromJson<DataRoot>(escapedUnicodeJson);
                if (retryRoot != null)
                {
                    Debug.LogWarning($"JSON cargado con fallback unicode desde {Path.GetFileName(path)}");
                    return retryRoot;
                }

                return new DataRoot();
            }
            catch (Exception ex)
            {
                Debug.LogError($"Error leyendo JSON: {ex.Message}");
                return new DataRoot();
            }
        }

        private static string ReadUtf8NoBom(string path)
        {
            var bytes = File.ReadAllBytes(path);
            var utf8Strict = new UTF8Encoding(false, true);
            var json = utf8Strict.GetString(bytes);
            if (json.Length > 0 && json[0] == '\uFEFF')
            {
                json = json.Substring(1);
            }

            return json;
        }

        private static string EscapeNonAscii(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return value;
            }

            var builder = new StringBuilder(value.Length + 128);
            foreach (var ch in value)
            {
                if (ch <= 127)
                {
                    builder.Append(ch);
                    continue;
                }

                builder.Append("\\u");
                builder.Append(((int)ch).ToString("x4"));
            }

            return builder.ToString();
        }
    }
}
