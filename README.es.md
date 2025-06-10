# Subdx-dl

[![en leeme](https://img.shields.io/badge/readme-en-red?logo=readme&logoColor=red&label=leeme)](https://github.com/Spheres-cu/subdx-dl#subdx-dl)
[![es leeme](https://img.shields.io/badge/readme-es-brightgreen?logo=readme&logoColor=brightgreen&label=leeme)](https://github.com/Spheres-cu/subdx-dl/blob/main/README.es.md#subdx-dl)

[![GitHub Downloads](https://img.shields.io/badge/descargas-green?logo=github&logoColor=1f1f23&labelColor=fbfbfb&color=brightblue)](https://github.com/Spheres-cu/subdx-dl/releases/latest)
[![latest release windows portable](https://img.shields.io/github/downloads/Spheres-cu/subdx-dl/subdx-dl.exe?logo=artifacthub&logoColor=brightblue&label=%20&labelColor=fbfbfb)](https://github.com/Spheres-cu/subdx-dl/releases/latest/download/subdx-dl.exe)
[![latest release linux binario](https://img.shields.io/github/downloads/Spheres-cu/subdx-dl/subdx-dl?logo=linux&logoColor=1f1f23&label=%20&labelColor=fbfbfb)](https://github.com/Spheres-cu/subdx-dl/releases/latest/download/subdx-dl)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/subdx-dl?logo=pypi&logoColor=1f1f23&labelColor=fbfbfb&label=%20)](https://pypistats.org/packages/subdx-dl)

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/subdx-dl?logo=python&logoSize=auto&label=%20&labelColor=1f1f23)
![GitHub Release](https://img.shields.io/github/v/release/Spheres-cu/subdx-dl?logo=github&logoSize=auto&label=%20&labelColor=1f1f23)
[![PyPI - Version](https://img.shields.io/pypi/v/subdx-dl?logo=pypi&logoSize=auto&label=%20&labelColor=1f1f23)](https://pypi.org/project/subdx-dl/)
![GitHub License](https://img.shields.io/github/license/Spheres-cu/subdx-dl)
![GitHub Repo stars](https://img.shields.io/github/stars/Spheres-cu/subdx-dl)

Aplicación de línea de comandos para descargar subtítulos de [www.subdivx.com](https://www.subdivx.com) con la mejor coincidencia  de resultados posible.

## Instalación

```bash
pip install -U subdx-dl
```

### Versión portable

Puede descargar la version portable para Windows x64 (subdx-dl.exe) y x86 (subdx-dl_x86.exe) tambien el binario para Linux (subdx-dl) desde: [release](https://github.com/Spheres-cu/subdx-dl/releases/latest)

#### Consejos para el uso portátil

Intente poner la versión ejecutable en las variables de entorno **PATH**, aquí algunos ejemplos:

_En Linux:_

```bash
mkdir -p ~/.local/bin && curl --progress-bar -L "https://github.com/Spheres-cu/subdx-dl/releases/latest/download/subdx-dl" -o ~/.local/bin/subdx-dl && \
chmod +x ~/.local/bin/subdx-dl && echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

ó

```bash
mkdir -p ~/.local/bin && \
wget --show-progress --progress=bar:force -qO ~/.local/bin/subdx-dl "https://github.com/Spheres-cu/subdx-dl/releases/latest/download/subdx-dl" && \
chmod +x ~/.local/bin/subdx-dl && \
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

_En Windows:_

```powershell
$dir = "$env:APPDATA\subdx-dl"; mkdir -Force $dir; `
Invoke-WebRequest -Uri "https://github.com/Spheres-cu/subdx-dl/releases/latest/download/subdx-dl.exe" -OutFile "$dir\subdx-dl.exe"; `
$path = [Environment]::GetEnvironmentVariable("PATH", "User"); `
if ($path -notlike "*$dir*") { [Environment]::SetEnvironmentVariable("PATH", "$path;$dir", "User") }; `
Write-Host "Se agregó a PATH. Reinicie la terminal para que los cambios surtan efecto."
```

### Caso especial de instalación en Termux (Android) por primera vez

```bash
pkg install python-lxml && pip install -U subdx-dl
```

### Para realizar pruebas use un entorno virtual (env) de Python e instale ahí

_En linux:_

```shell
mkdir subdx
python3 -m venv subdx
source subdx/bin/activate
git clone https://github.com/Spheres-cu/subdx-dl.git
cd subdx-dl
pip install -e .
```

_En Windows:_

```batch
mkdir subdx
python -m venv subdx
.\subdx\Scripts\activate
git clone https://github.com/Spheres-cu/subdx-dl.git
cd subdx-dl
pip install -e .
```

## Uso

```text
usage: sdx-dl [-h or --help] [argumentos opcionales] search
```

_argumentos posicionales_:

```text
search                  archivo, directorio o  título de la película/serie ó el Id de IMDB Id que desee buscar subtítulos.
```

_argumentos opcionales_:

```text
  -h, --help            Muestra la ayuda
  --quiet, -q           Modo silencioso
  --verbose, -v         Modo informativo de toda la ejecución del programa
  --force, -f           Sobreescribe el archivo de subtítulo si ya existe
  --no-choose, -nc      Sin selección manual del subtítulo a descargar
  --no-filter, -nf      No filtrar los resultados de la búsqueda 
  --nlines [], -nl []   Muestra nl (5,10,15,20) resultados en pantalla según espacio disponible. Por defecto muestra 10 resultados
  --lang [], -l []      Muestra los mensajes del programa en idioma (-l o --lang) español (es) o inglés (en) 
  --version, -V         Muestra la versión actual
  --check-version, -cv  Revisa si existe nueva versión

Download:
  --path PATH, -p PATH  Directorio donde descagar los subtítulos
  --proxy x, -x x       Establece la conexión a través de un servidor proxy(x) de tipo http(s) que especifique

Search by:
  --Season, -S          Buscar por temporadas
  --kword kw, -k kw     Buscar por las palabras claves que especifique (kw) para ordenar los resultados
  --title t, -t t       Usar el título t en la búsquedad
  --imdb, -i            Buscar primero el título o el Id de IMDB antes de realizar la búsqueda

Config:
  --view-config, -vc    Ver el archivo de configuración
  --save-config, -sc    Salvar los argumentos pasados al archivo de configuración
  --load-config, -lc    Cargar la configuración antes de realizar la búsqueda
  --config [o], -c [o]  Guardar una opción [o] en el archivo de configuración
  --reset [o], -r [o]   Eliminar una opción guardada [o] en el archivo de configuración
```

## Ejemplos

_Buscar una serie de TV por: Título, temporada y episodio ó solo por el nombre:_

```shell
sdx-dl "Abbott Elementary S04E01"

sdx-dl "Abbott Elementary 04x01"

sdx-dl "Abbott Elementary"
```

_o por la temporada completa:_

```shell
sdx-dl -S "Abbott Elementary S04E01"
```

_Buscar por una película por el Título y Año ó solo por el Título, incluso solo por el **ID de IMDB**:_

```shell
sdx-dl "Deadpool and Wolverine 2024"

sdx-dl "Deadpool 3"

sdx-dl tt6263850
```

_Buscar por el nombre del archivo:_

```shell
sdx-dl Harold.and.the.Purple.Crayon.2024.720p.AMZN.WEBRip.800MB.x264-GalaxyRG.mkv
```

_Buscar primero por el _ID de IMDB_ o por el _Título_ correcto de la serie si no lo conoce exactamente o está en otro idioma:_

```shell
sdx-dl --imdb "Los Caza fantasmas"

sdx-dl -i "Duna S1E3"
```

- _Búsqueda en IMDB:_

![![IMDB search film]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search01.png?raw=true)

![![IMDB search film reults]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search02.png?raw=true)

## Opciones de configuración

Las opciones guardadas en el archivo de configuración las puede usar en cualquier momento que realice una búsqueda, estas son las opciones disponibles: quiet, verbose, force, no_choose, no_filter, nlines, path, proxy, Season, imdb, lang.

Los argumentos para configurar las opciones son :

--view-config, -vc muestra la configuración guardada.

--save-config, -sc guarda todos los argumentos que pase durante una búsqueda, manteniendo las opciones antes guardadas, mezclándolas con las nuevas, dando preferencia a las nuevas.

--config, -c guarda una opción en específico. La opción a guardar simpre debe ser una de las disponibles.

--reset, -r contrario a --config, -c este argumento simplemente elimina una opción del archivo de configuración.

--load-config, -lc carga las opciones guardadas y realiza la búsqueda con ellas. Si pasa otras opciones también se cargarán teniendo preferencia sobre las del archivo de configuración.

## Consejos

- Siempre trate de buscar con el _Título_ y año o temporada y episodio_ para el caso de las series, obtendrá mejores resultados.

- Busque usando el nombre del archivo directamente.
  > Buscar de esta forma tiene la ventaja que los resultados se organizarán y filtrarán por los metadatos del archivo (ejem.: 1080p, Web, Bluray, DDP5.1., Atmos, PSA, etc.).

- Intente pasar el _ID de IMDB_ de la película o serie.

- Pase las palabras claves (conocidas también como _metadatos_) (```--kword, -k "<kw1 kw2 kw3 ...>"```) del subtítulo específico que está buscando. Separe las palabras claves por espacio.

- Si no obtiene resultados de la búsqueda de un episodio (ejem.:... S01E02) intente buscar por la temporada completa  con el argumento ``` --Seasson, -S ``` .

- Si no desea filtrar y organizar los resultados de la búsqueda con la mejor coincidencia (no recomendable) y solo quiere que se muestren rápidamente use ``` --no-filter, -nf ``` .

- A veces la cantidad de resultados que se muestran sobrepasan la capacidad de la pantalla, con  --nlines, -nl puede arreglar esto indicando una cantidad que se ajuste a su pantalla.

- _¡Muy importante!_: Debe tener instalado en su sistema algún programa descompresor de archivos rar, ejemplo: [unrar](https://www.rarlab.com/) (preferentemente), [unar](https://theunarchiver.com/command-line), [7zip](https://www.7-zip.org/) ó [bsdtar](https://github.com/libarchive/libarchive). De lo contrario, el archivo de subtítulo no se descomprimirá.

## Algunas capturas de pantalla

### _Realizando una búsqueda:_

- _Resultados de búsqueda navegables:_
- _Descripción de los subtítulos:_
- _Comentarios de los usuarios:_
  
![Performing search](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/search_view.gif?raw=true)
