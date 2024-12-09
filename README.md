![PyPI - Downloads](https://img.shields.io/pypi/dm/subdx-dl?link=https%3A%2F%2Fpypistats.org%2Fpackages%2Fsubdx-dl)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/subdx-dl)
![GitHub Release](https://img.shields.io/github/v/release/Spheres-cu/subdx-dl)
![PyPI - Version](https://img.shields.io/pypi/v/subdx-dl)
![GitHub License](https://img.shields.io/github/license/Spheres-cu/subdx-dl)
![GitHub User's stars](https://img.shields.io/github/stars/Spheres-cu)

A cli tool for download subtitle from www.subdivx.com with the better possible matching results.


# Install
-------
```bash
pip install -U subdx-dl
```

### For testing use a virtual env and install it there:

_For linux:_

```bash
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

# Usage
-----

```
usage: sdx-dl [-h or --help] [optional arguments] search
```
_positional arguments_:

```
search                  file, directory or movie/series title or IMDB Id to retrieve subtitles
```
_optional arguments_:

```shell
-h, --help            Show this help message and exit.
--quiet, -q           No verbose mode and very quiet. Applies even in verbose mode (-v).
--path, -p            Path to download subtitles.
--verbose -v          Be in verbose mode.
--no-choose, -nc      Download the default match subtitle available. Show all the available subtitles to download is de default behavior.
--Season, -S          Search for Season.
--search-imdb, -si    Search first for the IMDB id or title.
--force, -f           Override existing subtitle file.
--version -V          Show program version.
--title -t "<string>" _ Set the title to search instead of getting it from the file name. This option is invalid if --imdb is setting. 
--keyword -k "<strings>" _ Add an <strings> to the list of keywords separated by spaces. Keywords are used when you search by filename.
--imdb -i IMDB_ID _ Search by IMDB id regardless filename, search strings or serie season.
```

## Examples
-----

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

```shell
sdx-dl --imdb tt13062500 -q The.Walking.Dead.Daryl.Dixon.S02E06.480p.x264-RUBiK.mkv
```
  > Search by IMDB id regardless filename, search strings keeping the serie season/number and in quiet mode.

_Search first for the __IMDB ID__ or  correct tv show __Title__ if don't know they name or it's in another language:_

```bash
sdx-dl --search-imdb "Los Caza fantasmas"

sdx-dl -si "Duna S1E3"
```
- _IMDB search:_

![![IMDB search film]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search01.png?raw=true)

![![IMDB search film reults]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search02.png?raw=true)

![![IMDB search TV show]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search03.png?raw=true)

![![IMDB search TV show results]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/imdb_search04.png?raw=true)


## Tips

- Always try to search with *__Title, Year or season number__* for better results.

- Search by filename reference.
  > Search in this way have advantage because the results are filtered and ordered by the metadata of the filename.

- Try to pass the *_IMDB ID_* of the movie or TV Show.

- Pass keywords (```--keyword -k "<str1 str2 str3 ...>"```) of the subtitle   you are searching for better ordered results.

- If the search not found any records by a single chapter number (exe. S01E02) try search by the complete Seasson with ``` --Seasson -S ``` parameter.

- **Very important!**: You need to be installed some rar decompression tool for example: [unrar](https://www.rarlab.com/) (preferred), [unar](https://theunarchiver.com/command-line), [7zip](https://www.7-zip.org/) or [bsdtar](https://github.com/libarchive/libarchive). Otherwise, subtitle file will do not decompress.

## Some Captures

- _Performing search:_
  
![Performing search](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot01.png?raw=true)

- _Navigable searches results:_

![Navigable searches results](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot02.jpg?raw=true)

- _Subtitle description:_

![Subtitle description](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot03.jpg?raw=true)

- _User comments:_

![![Subtitle description]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot04.jpg?raw=true)

