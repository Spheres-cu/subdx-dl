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
  --verbose -v          Be in verbose mode.
  --no-choose, -nc      Download the default match subtitle avaible. Now show all the available subtitle to download is de default behavior.
  --Season, -S          Search for Season.
  --force, -f           Override existing subtitle file.
  --version -V          Show program version.
  --title -t "<string>" _ Set the title to search instead of getting it from the file name. This option is invalid if --imdb is setting. 
  --keyword -k "<string>" _ Add the <string> to the list of keywords. Keywords are used when you have.

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
## Tips

- Always try to search with *__Title, Year or season number__* for better results.

- Search by filename reference.
  > Search in this way have advantage because the results are filtered and ordered by the metadata of the filename.

- Try to pass the *_IMDB ID_* of the movies(not for TV Show www.subdivx.com site have not implement it yet).

- Pass keywords (```--keyword -k "<string>"```) of the subtitle   you are searching for better ordered results.

## Some Captures

- _Performing search:_
  
![Performing search](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot01.png?raw=true)

- _Navigable searches results:_

![Navigable searches results](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot02.jpg?raw=true)

- _Subtitle description:_

![Subtitle description](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot03.jpg?raw=true)

- _User comments:_

  ![![Subtitle description]](https://github.com/Spheres-cu/subdx-dl/blob/main/screenshots/screenshot04.jpg?raw=true)


 
