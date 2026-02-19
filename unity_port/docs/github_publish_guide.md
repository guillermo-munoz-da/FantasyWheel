# Publicar `unity_port` en GitHub

No puedo ejecutar autenticación remota por ti, pero dejo el flujo exacto para publicarlo en tu cuenta.

## Opción A - Repositorio dedicado para Unity

Desde `c:/workspace/unity_port`:

```powershell
git init
git add .
git commit -m "Initial Unity port base (feature roadmap + starter code)"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/darkwheel-unity-port.git
git push -u origin main
```

## Opción B - Mantener dentro del repo actual

Desde `c:/workspace`:

```powershell
git add unity_port docs/unity_port_por_features.md docs/unity_port_roadmap.md README.md
git commit -m "Add Unity port starter, docs and manual testing plan"
git push
```

## Recomendaciones antes de publicar

- Revisar que no haya secretos en archivos de configuración local.
- Mantener este scope en el primer push:
  - `unity_port/Assets/Scripts`
  - `unity_port/Assets/StreamingAssets/data.json`
  - `unity_port/docs`
  - docs de roadmap por features.

## Tag sugerido

Cuando cierres el primer milestone jugable:

```powershell
git tag v0.1.0-mvp-port
git push origin v0.1.0-mvp-port
```
