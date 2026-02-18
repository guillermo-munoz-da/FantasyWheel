Prototipo Ruleta - Dark Fantasy

Pequeo prototipo de juego de creacin narrativa mediante ruedas de opciones (spinner).

Cmo ejecutar (Windows):

1. Instalar Python 3.10+.
2. Crear un entorno virtual (opcional) e instalar dependencias:

```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
```

3. Ejecutar (GUI - tkinter):

```bash
python main_tk.py
```

Si prefieres PySimpleGUI (anterior prototipo), ejecuta `main.py`, pero si tu instalación de
PySimpleGUI causa fallos nativos la versión `main_tk.py` usa `tkinter` y es más fiable.

Este prototipo usa PySimpleGUI y un archivo `data.json` con ejemplos de razas, clases y dependencias.

Siguientes pasos recomendados: extender datos, aadir ms dependencias y portar a Unity/Android.
