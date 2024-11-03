A cli tool for download subtitle from www.subdivx.com with the better possible matching results.


# Install
-------
```
git clone https://github.com/Spheres-cu/subdx-dl.git
cd subdx-dl
python3 -m pip install .

OR

pip install -U subdx-dl

```

### My recomendation is to use a virtual env and install it there:

```
mkdir subdx
python3 -m venv subdx
source subdx/bin/activate
then clone with git and install with all the dependencies among them:
pip install -r requirements.txt

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

```
  -h, --help            Show this help message and exit.
  --quiet, -q           No verbose mode and very quiet. Applies even in verbose mode (-v).
  --path, -p            Path to download subtitles.
  --verbose -v          Be in verbose mode.
  --no-choose, -nc      Download the default match subtitle available. Show all the available subtitles to download is de default behavior.
  --Season, -S          Search for Season.
  --force, -f           Override existing subtitle file.
  --version -V          Show program version.
  --title -t "<string>" _ Set the title to search instead of getting it from the file name. This option is invalid if --imdb is setting. 
  --keyword -k "<strings>" _ Add an <strings> to the list of keywords separated by spaces. Keywords are used when you search by filename.
  --imdb -i IMDB_ID _ Search by IMDB id regardless filename, search strings or serie season.

```

## Examples
-----

_Search a single TV-Show by: Title, Season number or simple show name:_

```
$ sdx-dl "Abbot Elementary S04E01"

$ sdx-dl "Abbot Elementary 04x01"

$ sdx-dl "Abbot Elementary"
 ```
 
 _or search for complete  Season:_
 
 ```
 sdx-dl -S "Abbot Elementary S04E01"
 ```
 _Search for a Movie by Title, Year or simple title, even by __IMDB ID__ :_
 
 ```
$ sdx-dl "Deadpool and Wolverine 2024"

$ sdx-dl "Deadpool 3"

$ sdx-dl tt6263850
```
_Search by a file reference:_

```
$ sdx-dl Harold.and.the.Purple.Crayon.2024.720p.AMZN.WEBRip.800MB.x264-GalaxyRG.mkv

```
```

$ sdx-dl --imdb tt13062500 -q The.Walking.Dead.Daryl.Dixon.S02E06.480p.x264-RUBiK.mkv

```
  > Search by IMDB id regardless filename, search strings keeping the serie season/number and in quiet mode.

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


 
