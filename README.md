# Subdx-dl

![PyPI - Downloads](https://img.shields.io/pypi/dm/subdx-dl?link=https%3A%2F%2Fpypistats.org%2Fpackages%2Fsubdx-dl)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/subdx-dl)
![GitHub Release](https://img.shields.io/github/v/release/Spheres-cu/subdx-dl)
![PyPI - Version](https://img.shields.io/pypi/v/subdx-dl)
![GitHub License](https://img.shields.io/github/license/Spheres-cu/subdx-dl)
![GitHub Repo stars](https://img.shields.io/github/stars/Spheres-cu/subdx-dl)

A cli tool for download subtitle from [www.subdivx.com](https://www.subdivx.com) with the better possible matching results.

## Install

```bash
pip install -U subdx-dl
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
  --nlines [], -nl []   Show nl(5,10,15,20) availables records per screen. Default 10 records.
  --version, -V         Show program version
  --check-version, -cv  Check for new version

Download:
  --path PATH, -p PATH  Path to download subtitles
  --proxy px, -P px     Set a http(s) proxy(px) connection

Search by:
  --Season, -S          Search by Season
  --kword kw, -k kw     Add keywords to search among subtitles descriptions
  --title t, -t t       Set the title to search
  --search-imdb, -si    Search first for the IMDB id or title
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

_Search for a Movie by Title, Year or simple title, even by __IMDB ID__ :_

```shell
sdx-dl "Deadpool and Wolverine 2024"

sdx-dl "Deadpool 3"

sdx-dl tt6263850
```

_Search by a file reference:_

```shell
sdx-dl Harold.and.the.Purple.Crayon.2024.720p.AMZN.WEBRip.800MB.x264-GalaxyRG.mkv
```

_Search first for the __IMDB ID__ or  correct tv show __Title__ if don't know they name or it's in another language:_

```shell
sdx-dl --search-imdb "Los Caza fantasmas"

sdx-dl -si "Duna S1E3"
```

- _IMDB search:_

![![IMDB search film]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search01.png?raw=true)

![![IMDB search film reults]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search02.png?raw=true)

![![IMDB search TV show]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search03.png?raw=true)

![![IMDB search TV show results]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search04.png?raw=true)

## Tips

- Always try to search with __Title, Year or season number__ for better results.

- Search by filename reference.
  > Search in this way have advantage because the results are filtered and ordered by the metadata of the filename.

- Try to pass the _IMDB ID_ of the movie or TV Show.

- Pass keywords (```--keyword -k "<str1 str2 str3 ...>"```) of the subtitle   you are searching for better ordered results.

- If the search not found any records by a single chapter number (exe. S01E02) try search by the complete Seasson with ``` --Seasson -S ``` parameter.

- If you don't wanna filter the search results for a better match and, instead,  improved response time use ``` --no-filter -nf ``` argument.

- __Very important!__: You need to be installed some rar decompression tool for example: [unrar](https://www.rarlab.com/) (preferred), [unar](https://theunarchiver.com/command-line), [7zip](https://www.7-zip.org/) or [bsdtar](https://github.com/libarchive/libarchive). Otherwise, subtitle file will do not decompress.

## Some Captures

- _Performing search:_
  
![Performing search](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot01.png?raw=true)

- _Navigable searches results:_

![Navigable searches results](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot02.jpg?raw=true)

- _Subtitle description:_

![Subtitle description](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot03.jpg?raw=true)

- _User comments:_

![![Subtitle description]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot04.jpg?raw=true)
