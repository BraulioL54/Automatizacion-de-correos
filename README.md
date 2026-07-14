# Automatizacion de Correos

Proyecto en Python para enviar correos personalizados desde una cuenta de Gmail usando datos cargados desde un archivo Excel. Actualmente el sistema ya cuenta con una arquitectura modular, validacion previa, seleccion de archivos desde interfaz grafica y generacion de logs y reportes por ejecucion.

## Estado Actual

Hasta este momento el proyecto ya permite:

- Cargar configuracion desde `.env`.
- Leer destinatarios desde un archivo Excel.
- Renderizar el cuerpo del correo desde una plantilla HTML.
- Resolver adjuntos personalizados o un adjunto por defecto.
- Iniciar sesion en Gmail por SMTP.
- Validar archivos, credenciales, correos y carpeta de salida antes de enviar.
- Seleccionar desde la GUI:
  - archivo Excel
  - plantilla HTML
  - carpeta de salida
- Enviar correos desde una interfaz grafica con `Tkinter`.
- Mostrar el progreso del proceso en una bitacora visual.
- Generar un reporte final en Excel.
- Guardar logs del proceso.
- Crear nombres unicos para log y reporte con fecha y hora.

## Interfaz Grafica Actual

La interfaz actual ya incluye:

- Ventana principal.
- Boton `Validar datos`.
- Boton `Enviar correos`.
- Boton `Examinar Excel`.
- Boton `Examinar HTML`.
- Boton `Examinar carpeta`.
- Estado del proceso en pantalla.
- Area de bitacora.
- Resumen final con ventana emergente.

## Estructura Del Proyecto

```text
Automatizacion de correos/
  .env
  requirements.txt
  README.md

  src/
    main.py
    config.py

    app/
      bootstrap.py

    domain/
      models.py
      validators.py

    services/
      attachment_resolver.py
      campaign_service.py
      email_builder.py
      excel_reader.py
      gmail_client.py
      logger_service.py
      preflight_validator.py
      report_generator.py
      template_renderer.py

    ui/
      cli.py
      gui.py
      notifier.py

    assets/
      plantilla.html
      estilos.css

    data/
      clientes.xlsx

    outputs/
      ...

    pdfs/
      ...
```

## Responsabilidad De Cada Carpeta

- `src/app`
  Punto de arranque de la aplicacion y conexion entre configuracion, servicios e interfaz.

- `src/domain`
  Modelos del negocio y validaciones principales.

- `src/services`
  Logica principal del sistema: lectura del Excel, armado del correo, validacion previa, envio, logging y reporte.

- `src/ui`
  Capa de interfaz. Actualmente incluye una implementacion de consola y una interfaz grafica con `Tkinter`.

- `src/assets`
  Archivos de presentacion como la plantilla HTML y estilos.

- `src/data`
  Archivos de entrada del proceso.

- `src/outputs`
  Carpeta de salida por defecto para logs y reportes.

- `src/pdfs`
  Adjuntos disponibles para enviar.

## Flujo General Del Sistema

1. `src/main.py` inicia la aplicacion.
2. `src/app/bootstrap.py` carga la configuracion base y abre la interfaz.
3. El usuario puede seleccionar:
   - Excel
   - plantilla HTML
   - carpeta de salida
4. El usuario presiona `Validar datos`.
5. `PreflightValidator` revisa:
   - archivos obligatorios
   - credenciales
   - Excel
   - correos
   - adjuntos
   - carpeta de salida
6. Si la validacion es correcta, se habilita `Enviar correos`.
7. Al enviar, se genera un identificador de ejecucion con fecha y hora.
8. Se crean rutas unicas para:
   - log
   - reporte
9. `CampaignService` inicia el envio en segundo plano.
10. La interfaz muestra mensajes de avance y errores en la bitacora.
11. Al terminar, se muestra un resumen final y queda disponible el reporte generado.

## Archivos Clave

### `src/main.py`

Punto de entrada del programa.

### `src/config.py`

Carga variables de entorno y construye la configuracion base y la configuracion efectiva de cada ejecucion.

Tambien define:

- carpeta de salida
- nombre dinamico de log
- nombre dinamico de reporte
- identificador de ejecucion por fecha y hora

### `src/services/preflight_validator.py`

Ejecuta la validacion previa antes del envio. Devuelve un resultado estructurado que la interfaz usa para habilitar o bloquear el boton de envio.

### `src/services/campaign_service.py`

Es el orquestador principal del envio. Coordina todos los servicios, inicializa el logger de la ejecucion actual y devuelve el resumen final.

### `src/services/gmail_client.py`

Se encarga de abrir la conexion SMTP con Gmail, iniciar sesion y enviar los correos.

### `src/ui/gui.py`

Contiene la interfaz grafica actual del proyecto. Gestiona:

- seleccion de archivos
- seleccion de carpeta de salida
- validacion previa
- bitacora visual
- estado del proceso
- arranque del envio en segundo plano
- mensajes emergentes al finalizar

## Variables De Entorno

El archivo `.env` debe contener las credenciales necesarias para autenticarse con Gmail.

Variables usadas actualmente:

```env
CORREO_PROPIO_DE_PRUEVA=tu_correo@gmail.com
CONTRASENA_GOOGLE_PROPIA=tu_contrasena_o_app_password
```

Compatibilidad heredada:

- El sistema tambien intenta leer una variante antigua del nombre de la contraseña que venia con problema de codificacion.

## Requisitos

Dependencias actuales registradas en `requirements.txt`:

- `pandas`
- `openpyxl`
- `python-dotenv`
- `numpy`
- `python-dateutil`
- `six`
- `tzdata`
- `et_xmlfile`

La interfaz grafica usa `tkinter`, que normalmente ya viene incluida con Python en Windows.

## Instalacion

Crear y activar entorno virtual:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

## Ejecucion

Desde la raiz del proyecto:

```powershell
.\env\Scripts\python.exe src\main.py
```

Esto abre la interfaz grafica actual.

## Formato Esperado Del Excel

El archivo Excel debe contener como minimo estas columnas:

- `correo`
- `nombre`
- `mensaje`

Columnas opcionales:

- `asunto`
- `archivo`

## Validacion Previa

Antes de enviar, la aplicacion ejecuta una validacion previa desde la GUI.

Esta validacion revisa:

- existencia del Excel
- existencia de la plantilla HTML
- credenciales en `.env`
- columnas obligatorias
- cantidad de destinatarios
- formato de correos
- adjuntos por fila
- disponibilidad del adjunto por defecto
- carpeta de salida

Si la validacion no pasa:

- `Enviar correos` permanece deshabilitado
- la bitacora muestra los errores y advertencias detectados

## Seleccion De Archivos Desde La GUI

La interfaz permite seleccionar visualmente:

- archivo Excel
- plantilla HTML
- carpeta de salida

Cuando alguno de estos cambia:

- se invalida la validacion previa anterior
- `Enviar correos` vuelve a deshabilitarse
- la app obliga a validar otra vez antes de enviar

## Archivos De Salida

Cada ejecucion genera archivos unicos con fecha y hora en el nombre.

Ejemplo:

- `envio_correos_2026-05-06_19-35-10.log`
- `reporte_envios_2026-05-06_19-35-10.xlsx`

Estos archivos se guardan en:

- la carpeta seleccionada por el usuario desde la GUI
- o `src/outputs` si no se cambia la ruta

## Logging

El contenido del log incluye marca de tiempo por linea y ahora cada ejecucion usa su propio archivo.

Ventajas:

- no se sobrescriben logs anteriores
- cada corrida queda identificada
- es mas facil rastrear errores por fecha y hora

## Estado De La Interfaz Grafica

Actualmente la GUI ya resuelve:

- arranque visual del programa
- seleccion de archivos y carpeta de salida
- validacion previa antes del envio
- ejecucion del envio desde un boton
- visualizacion de mensajes en tiempo real
- recuperacion del control al terminar
- resumen final de la ejecucion

## Limitaciones Actuales

- El envio sigue dependiendo de una cuenta Gmail valida.
- La interfaz aun no permite editar credenciales desde pantalla.
- No hay barra de progreso visual por porcentaje.
- El proyecto aun no esta empaquetado como ejecutable final.
- No hay pruebas automatizadas todavia.

## Siguiente Objetivo

La siguiente fase recomendada es fortalecer la interfaz grafica con:

- barra de progreso
- contador de correos enviados y fallidos en vivo
- boton para restaurar rutas por defecto
- empaquetado a `.exe` con `PyInstaller`
