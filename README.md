# Subdx-dl

[![en readme](https://img.shields.io/badge/readme-en-red?logo=readme&logoColor=red&label=readme)](https://github.com/Spheres-cu/subdx-dl#subdx-dl)
[![es readme](https://img.shields.io/badge/readme-es-brightgreen?logo=readme&logoColor=brightgreen&label=readme)](https://github.com/Spheres-cu/subdx-dl/blob/main/README.es.md#subdx-dl)

[![GitHub Downloads](https://img.shields.io/badge/downloads-green?logo=github&logoColor=1f1f23&labelColor=fbfbfb&color=brightblue)](https://github.com/Spheres-cu/subdx-dl/releases/latest)
[![latest release windows portable](https://img.shields.io/github/downloads/Spheres-cu/subdx-dl/subdx-dl.exe?logo=artifacthub&logoColor=brightblue&label=%20&labelColor=fbfbfb)](https://github.com/Spheres-cu/subdx-dl/releases/latest/download/subdx-dl.exe)
[![latest release linux binario](https://img.shields.io/github/downloads/Spheres-cu/subdx-dl/subdx-dl?logo=linux&logoColor=1f1f23&label=%20&labelColor=fbfbfb)](https://github.com/Spheres-cu/subdx-dl/releases/latest/download/subdx-dl)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/subdx-dl?logo=pypi&logoColor=1f1f23&labelColor=fbfbfb&label=%20)](https://pypistats.org/packages/subdx-dl)

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/subdx-dl?logo=python&logoSize=auto&label=%20&labelColor=1f1f23)
![GitHub Release](https://img.shields.io/github/v/release/Spheres-cu/subdx-dl?logo=github&logoSize=auto&label=%20&labelColor=1f1f23)
[![PyPI - Version](https://img.shields.io/pypi/v/subdx-dl?logo=pypi&logoSize=auto&label=%20&labelColor=1f1f23)](https://pypi.org/project/subdx-dl/)
![GitHub License](https://img.shields.io/github/license/Spheres-cu/subdx-dl)
![GitHub Repo stars](https://img.shields.io/github/stars/Spheres-cu/subdx-dl)

A cli tool for download subtitle from [www.subdivx.com](https://www.subdivx.com) with the better possible matching results.

## Install

```bash
pip install -U subdx-dl
```

### Portable Version

You can download the portable version for Windows x64 (subdx-dl.exe) and x86 (subdx-dl_x86.exe), as well as the binary for Linux (subdx-dl) from: [release](https://github.com/Spheres-cu/subdx-dl/releases/latest)

#### Tips for portable usage

Try to put the executable version in the environment variables **PATH** ,  here some examples:

_In Linux:_

```bash
mkdir -p ~/.local/bin && \
curl --progress-bar -L "https://github.com/Spheres-cu/subdx-dl/releases/latest/download/subdx-dl" -o ~/.local/bin/subdx-dl && \
chmod +x ~/.local/bin/subdx-dl && \
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

or

```bash
mkdir -p ~/.local/bin && \
wget --show-progress --progress=bar:force -qO ~/.local/bin/subdx-dl "https://github.com/Spheres-cu/subdx-dl/releases/latest/download/subdx-dl" && \
chmod +x ~/.local/bin/subdx-dl && \
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

_In Windows:_

```powershell
$dir = "$env:APPDATA\subdx-dl"; mkdir -Force $dir; `
Invoke-WebRequest -Uri "https://github.com/Spheres-cu/subdx-dl/releases/latest/download/subdx-dl.exe" -OutFile "$dir\subdx-dl.exe"; `
$path = [Environment]::GetEnvironmentVariable("PATH", "User"); `
if ($path -notlike "*$dir*") { [Environment]::SetEnvironmentVariable("PATH", "$path;$dir", "User") }; `
Write-Host "Added to PATH. Restart terminal for changes to take effect."
```

### Special case installing on Termux (Android) for first time

```bash
pkg install python-lxml && pip install -U subdx-dl
```

### For testing use a virtual env and install it there

_For linux:_

```shell
mkdir subdx
python3 -m venv subdx
source subdx/bin/activate
git clone https://github.com/Spheres-cu/subdx-dl.git
cd subdx-dl
pip install -e .
```

_For Windows:_

```batch
mkdir subdx
python -m venv subdx
.\subdx\Scripts\activate
git clone https://github.com/Spheres-cu/subdx-dl.git
cd subdx-dl
pip install -e .
```

## Usage

```text
usage: sdx-dl [-h or --help] [optional arguments] search
```

_positional arguments_:

```text
search                  file, directory or movie/series title or IMDB Id to retrieve subtitles
```

_optional arguments_:

```text
  -h, --help            show this help message and exit
  --quiet, -q           No verbose mode
  --verbose, -v         Be in verbose mode
  --force, -f           override existing file
  --no-choose, -nc      No Choose sub manually
  --no-filter, -nf      Do not filter search results
  --nlines [], -nl []   Show nl(5,10,15,20) availables records per screen. Default 10 records
  --lang [], -l []      Show messages in language es or en
  --version, -V         Show program version
  --check-version, -cv  Check for new version

Download:
  --path PATH, -p PATH  Path to download subtitles
  --proxy x, -x x       Set a http(s) proxy(x) connection

Search by:
  --Season, -S          Search by Season
  --kword kw, -k kw     Add keywords to search among subtitles descriptions
  --title t, -t t       Set the title to search
  --imdb, -i            Search first for the IMDB id or title

Config:
  --view-config, -vc    View config file
  --save-config, -sc    Save options to config file
  --load-config, -lc    Load config file options
  --config [o], -c [o]  Save an option[o] to config file
  --reset [o], -r [o]   Reset an option[o] in the config file
```

## Examples

_Search a single TV-Show by: Title, Season number or simple show name:_

```shell
sdx-dl "Abbott Elementary S04E01"

sdx-dl "Abbott Elementary 04x01"

sdx-dl "Abbott Elementary"
```

_or search for complete  Season:_

```shell
sdx-dl -S "Abbott Elementary S04E01"
```

_Search for a Movie by Title, Year or simple title, even by **IMDB ID**_:

```shell
sdx-dl "Deadpool and Wolverine 2024"

sdx-dl "Deadpool 3"

sdx-dl tt6263850
```

_Search by a file reference:_

```shell
sdx-dl Harold.and.the.Purple.Crayon.2024.720p.AMZN.WEBRip.800MB.x264-GalaxyRG.mkv
```

_Search first for the _IMDB ID_ or  correct tv show _Title_ if don't know they name or it's in another language:

```shell
sdx-dl --imdb "Los Caza fantasmas"

sdx-dl -i "Duna S1E3"
```

- _IMDB search:_

![![IMDB search film]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search01.png?raw=true)

![![IMDB search film reults]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search02.png?raw=true)

## Config options

With config file arguments you can save some options for use any time, thats options are: quiet, verbose, force, no_choose, no_filter, nlines, path, proxy, Season, imdb, lang.

The arguments for settings this options are:

--view-config, -vc to view what config you have saved.

--save-config, -sc this argument can save all allowed options you pass in search session, keeping the options already saved, merging, with preferer the new passed options.

--config, -c with this argument you can save an option to the config file. The options to save always be the allowed one.

--reset, -r opposite to --config, -c this argument simply reset an option.

--load-config, -lc this is for load all saved options and run the search with they. If you pass some others options those will merged, maintaining preference over the loaded options.

## Tips

- Always try to search with _Title, Year or season number_ for better results.

- Search by filename reference.
  > Search in this way have advantage because the results are filtered and ordered by the metadata of the filename (e.g.: 1080p, Web, Blu-ray, DDP5.1., Atmos, PSA, etc.).

- Try to pass the _IMDB ID_ of the movie or TV Show.

- Pass keywords (```--kword, -k "<str1 str2 str3 ...>"```) of the subtitle   you are searching for better ordered results.

- If the search not found any records by a single chapter number (exe. S01E02) try search by the complete Seasson with ``` --Seasson, -S ``` parameter.

- If you don't wanna filter the search results for a better match and, instead,  improved response time use ``` --no-filter, -nf ``` argument.

- Sometimes our display is a little tiny and the amount of results don't fix well, a way to fix that is using the  --nlines, -nl argument with an amount of records who fix in the screen size.

- _Very important!_: You need to be installed some rar decompression tool for example: [unrar](https://www.rarlab.com/) (preferred), [unar](https://theunarchiver.com/command-line), [7zip](https://www.7-zip.org/) or [bsdtar](https://github.com/libarchive/libarchive). Otherwise, subtitle file will do not decompress.

## Some Captures

### _Performing search:_

- _Navigable searches results:_
- _Subtitle description:_
- _User comments:_
  
![Performing search](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/search_view.gif?raw=true)
