# Ecosistema Menopausia Dichosa®

Este repositorio es la fuente principal del dominio `menopausiadichosa.com`.

## Rutas oficiales

| Ruta | Función | Estado |
|---|---|---|
| `/` | Portada y centro de accesos | Activa |
| `/test/` | Test de los 12 Villanos | Activa |
| `/ficha/` | Acceso estable a la ficha | Puente temporal |
| `/metodo/` | Acceso estable al Método D.I.C.H.O.S.A.® | Puente temporal |
| `/embajadoras/` | Acceso estable a Embajadoras | Puente temporal |
| `/guia/` | Guía para vencer a tus Villanos | Activa |
| `/recursos/` | Nutrientes y enlaces de compra | Activa |
| `/histamina/` | Test y diario de seguimiento de 7 días | Activa |
| `/agenda/` | Agenda y orientación | Pendiente |

## Regla de publicación

1. La rama `main` es la versión que debe publicar Cloudflare.
2. `index.html` es la única portada oficial.
3. Los archivos `index(2).html`, `index_corregido.html`, `index_movil_corregido.html` y `landing-v2.html` se conservan temporalmente como archivo histórico; no deben configurarse como entrada de Cloudflare.
4. Las nuevas páginas deben vivir en carpetas con un `index.html`.
5. Toda página compartible debe usar URLs de `menopausiadichosa.com` en sus etiquetas Open Graph.
