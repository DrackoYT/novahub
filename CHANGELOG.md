# Cambios

Versiones con [versionado semántico](https://semver.org/lang/es/): **MAYOR.MENOR.PARCHE**. Los parches solo arreglan
errores; las versiones menores añaden funciones sin romper nada; las mayores pueden necesitar pasos a mano.

## Sin publicar

## 1.0.1 — 2026-10-06

- **Centro de actualizaciones** (Ajustes → Actualizaciones): NovaHub (versiones de GitHub o canal de desarrollo, con
  copia previa y vuelta atrás automática si la versión nueva no arranca), el sistema con apt (solo seguridad o todo,
  y de seguridad automáticas cada noche si quieres), reinicio pendiente con reinicio ordenado del servidor, imágenes de
  contenedores, servicios con git y dependencias de cada proyecto (npm, pip) con copia de seguridad previa. Se comprueba
  cada 6 horas, avisa por correo y guarda un historial.
- Lo que necesita root pasa por un único script con órdenes fijas, `tools/novahub-sistema`.
- La versión de NovaHub se ve en Ajustes → Actualizaciones.
- Mejoras: «Cerrar versión…» agrupa las hechas en un desplegable por versión.
- La página oculta de mejoras solo existe en paneles que ya tienen una lista.
- En el móvil, el menú del selector de servidor ya no se sale de la pantalla.

## 1.0.0 — 2026-10-06

Primera versión pública: servicios (programas, contenedores con Podman y docker-compose), consola en directo con
búsqueda, salud y límite de memoria, gráficas, avisos por correo, editor de archivos, Git, editor de `.env`, copias de
seguridad, tareas programadas, publicación con Cloudflare Tunnel, despliegue desde GitHub y plantillas, modo
producción, usuarios y roles, varios servidores por Tailscale, procesos, red y enchufe Tapo, apagado ordenado y app para
el móvil (PWA y APK de Android).
