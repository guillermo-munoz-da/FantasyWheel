# Documentación: Backgrounds y Plantillas

## BACKGROUNDS (Fondos de pantalla o ilustraciones)

1. Coloca tus imágenes en la carpeta `backgrounds/` en el directorio raíz del proyecto.
2. Usa archivos JPG o PNG. El nombre del archivo debe ser descriptivo (ejemplo: bosque_oscuro.jpg).
3. Puedes asociar backgrounds a razas, lugares, eventos o arquetipos usando el mismo nombre (sin extensión) en el campo correspondiente del personaje o evento.
4. Si no hay coincidencia exacta, se usará un fondo por defecto.
5. Ejemplo: `backgrounds/bosque_oscuro.jpg` se asocia con `"place": "Bosque Oscuro"`.

---

## PLANTILLAS DE PERSONAJE (`character_template`)

1. La sección `character_template` en `data.json` define todos los campos y ruedas que puede tener un personaje.
2. Para añadir un nuevo campo, agrega un objeto en el array `fields` con las propiedades:
   - `name`: nombre del campo
   - `type`: tipo de dato (`string`, `int`, `enum`, `wheel`, `list`, `object`)
   - `desc`: descripción breve
   - `wheel`: (opcional) nombre de la rueda asociada
   - `depends_on`: (opcional) lista de campos de los que depende
   - `options`: (para `enum`) lista de valores posibles
   - `fields`: (para `object`/`list`) definición de subcampos
3. Para nuevas ruedas, añade el array correspondiente (ejemplo: `races`, `classes`, `skills`) siguiendo el formato de los existentes.
4. Mantén la coherencia de nombres y dependencias para que el generador funcione correctamente.
5. Ejemplo de campo personalizado:

```json
{"name": "facción", "type": "wheel", "desc": "Facción a la que pertenece", "wheel": "factions"}
```

---

¿Dudas? Puedes expandir esta documentación según evolucione el proyecto.