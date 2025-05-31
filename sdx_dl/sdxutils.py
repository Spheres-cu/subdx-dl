# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import re
import sys
import time
import json
import shutil
import signal
import certifi
import urllib3
import tempfile
import html2text
import urllib3.util
import typing
from zipfile import ZipFile, is_zipfile, ZipInfo
from rarfile import RarFile, is_rarfile, RarInfo # type: ignore
from sdx_dl.sdxparser import logger, args as parser_args
from sdx_dl.sdxclasses import HTML2BBCode, NoResultsError, GenerateUserAgent, VideoMetadataExtractor 
from json import JSONDecodeError
from urllib3.exceptions import HTTPError
from bs4 import BeautifulSoup
from typing import Dict, Any, NamedTuple, NewType
from itertools import chain
from datetime import datetime, timedelta
from readchar import readkey, key
from .sdxconsole import console
from rich import box
from rich.layout import Layout
from rich.console import Group
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.align import Align
from rich.live import Live
from rich.prompt import IntPrompt

__all__ = [
"get_imdb_search", "get_aadata", "convert_date", "get_filtered_results", "sort_results", "get_selected_subtitle_id",
"HTTPErrorsMessageException", "clean_screen", "paginate", "extract_subtitles", "sub_extensions", "Metadata", "metadata",
"SUBDIVX_DOWNLOAD_PAGE", "HTTPError", "headers", "conn"
]

args = parser_args

#obtained from https://flexget.com/Plugins/quality#qualities
_audio = ('dts-hd', 'dts', 'dd5.1', 'ddp5.1','atmos', 'truehd', 'aac', 'opus', 'flac', 'dolby')

sub_extensions = ['.srt', '.ssa', '.ass', '.sub']

_compressed_extensions = ['.zip', '.rar']

SUBDIVX_SEARCH_URL = 'https://www.subdivx.com/inc/ajax.php'

SUBDIVX_DOWNLOAD_PAGE = 'https://www.subdivx.com/'

Metadata = NamedTuple(
    'Metadata',
    [('keywords', list[str]),
    ('quality', list[str]),
    ('codec', list[str]),
    ('audio', list[str]),
    ('hasdata', bool)]
)

DataConn = NamedTuple('DataConn', [('cookie', str),('token', str), ('search', str)])

listDict = NewType('listDict', list[Dict[str,Any]])

signal.signal(signal.SIGINT, lambda _, __: sys.exit(0))

# Configure connections
ua = GenerateUserAgent.random_browser()
headers={"user-agent" : ua}

if args.proxy:
    proxie = f"{args.proxy}"
    if not (any(p in proxie for p in ["http", "https"])):
        proxie = "http://" + proxie
    conn = urllib3.ProxyManager(proxie, headers=headers, cert_reqs="CERT_REQUIRED", ca_certs=certifi.where(),  retries=2, timeout=15)
else:
    conn = urllib3.PoolManager(headers=headers, cert_reqs="CERT_REQUIRED", ca_certs=certifi.where(), retries=2, timeout=15)

# Network connections Errors
def HTTPErrorsMessageException(e: HTTPError) -> None:
    """ Manage HTTP Network connection Errors Exceptions message:
        * Log HTTP Network connection Error message
        * Print HTTP Network connection error message.
    """
    msg_err = e.__str__().split(":", maxsplit=1)[1].split("(")[0]
    error_class = e.__class__.__name__
    msg = f'{error_class}:{msg_err}'

    if not args.quiet:clean_screen()
    console.print(":no_entry: [bold red]Some Network Connection Error occurred[/]: " + msg, new_line_start=True, emoji=True)
    logger.debug(f'Some Network Connection Error occurred: {msg}')

### Setting data connection ###
class DataConnection:
    """
    Class for manage the connection data

    Attributes:
        _sdx_dc_path (str): Path to data connection file.
        __cookie (str): The cookie value for connections.
        __token (str):  The token for search requests.
        __search (str): Search field suffix.
        __data (DataConn): The entire data connection attributes.
        :type DataConn: NamedTuple
    """
    def __init__(self) -> None:
        self._sdx_dc_path = os.path.join(tempfile.gettempdir(), 'sdx_data_connection')
        self.__cookie, self.__token, self.__search = self._get_connection_data()
        self.__data = DataConn(self.__cookie, self.__token, self.__search)
    
    @property
    def cookie(self) -> str: return self.__data.cookie

    @property
    def token(self) -> str: return self.__data.token

    @property
    def search(self) -> str: return self.__data.search

    def _get_connection_data(self):
        """Return data connection"""
        sdx_data_connection = self._load_data_connection()

        if sdx_data_connection.count(";") != 2 or sdx_data_connection.count("=") != 1:
            logger.debug(f'Getting data connection')
            cookie, token, f_search = self._retrieve_data_connection()
        else:
            cookie, token, f_search = sdx_data_connection.split(";", maxsplit=2)
            logger.debug(f'Loaded data connection')
        
        return cookie, token, f_search

    def _exp_data_connection(self) -> bool:
        """Compare modified time and return `True` if is expired."""
        if not os.path.exists(self._sdx_dc_path): return True
        
        # Get data connection modified time and convert it to datetime
        csdx_ti_m = datetime.fromtimestamp(os.path.getmtime(self._sdx_dc_path))
        delta_csdx = datetime.now() - csdx_ti_m
        exp_c_time = timedelta(hours=2)

        return delta_csdx > exp_c_time

    def _retrieve_data_connection(self):
        """ Retrieve, save and return data connection."""
        cookie_sdx, _f_token, _f_search = f'', f'', f''

        try:
            sdx_request = conn.request('GET', SUBDIVX_DOWNLOAD_PAGE, timeout=10)
            cookie_sdx = f"{sdx_request.headers.get('Set-Cookie')}".split(';')[0]
            _vdata = BeautifulSoup(sdx_request.data.decode(), 'lxml')
            _f_search = str(_vdata('div', id="vs")[0].text.replace("v", "").replace(".", ""))
            _f_tk = SUBDIVX_SEARCH_URL[:-8] + 'gt.php?gt=1'
            _r_ftoken = conn.request('GET', _f_tk, headers={"Cookie":cookie_sdx},preload_content=False).data
            _f_token = f"{json.loads(_r_ftoken)['token']}"
        except HTTPError as e:
            HTTPErrorsMessageException(e)
            sys.exit(1)
        except JSONDecodeError as e:
            console.print(":no_entry: [bold red]Couldn't load data connection. Try again![/]: " +\
                        e.__str__(), emoji=True, new_line_start=True)
            sys.exit(1)
    
        with open(self._sdx_dc_path, 'w') as file:
            file.write(f'{cookie_sdx};{_f_token};{_f_search}')
            file.close()

        return cookie_sdx, _f_token, _f_search
        
    def _load_data_connection(self) -> str:
        """ Load stored sdx data connection return empty string if not exists or expired"""
        if not self._exp_data_connection():
            with open(self._sdx_dc_path, 'r') as filecookie:
                sdx_data_connection = filecookie.read()
        else:
            return f""

        return sdx_data_connection
    
    def reset_data_connection(self) -> None:
        """ Reset connection data """
        with open(self._sdx_dc_path, 'w') as file:
            file.write(f'')
            file.close()
    
conn_data = DataConnection()
headers['Cookie'] = conn_data.cookie

#### sdxlib utils ####
def extract_meta_data(search:str, kword:str, is_file:bool=False) -> Metadata:
    """
    Extract metadata from search based in matchs of keywords.

    The lists of keywords includen quality and codec for videos.
    """
    extractor = VideoMetadataExtractor()
    extracted_kwords = extractor.extract_specific(f"{search}", 'screen_size', 'video_codec',
                                                'release_group', 'source','streaming_service','other', options="-as")
    
    if ( all(x is None for x in extracted_kwords.values()) ):
        keywords = [x for x in f'{kword}'.split()[:4]] if kword else []
        return Metadata(keywords, [], [], [], bool(keywords))

    words = f""

    def clean_words(word:str):
        """clean words"""
        word = f'{word}'
        clean = [".", "-dl","-"]
        for i in clean:
            word = word.lower().replace(i, '')
        return word
    
    for k in ["release_group", "source", "streaming_service", "other"]:
        value = extracted_kwords[k]['raw'] if extracted_kwords[k] else None
        if (value):
            words += f"{value} " if k not in 'source' else f"{clean_words(value)} "
    
    words = words.strip()
    search = f'{search}'

    f = search.lower()[:-4] if is_file else search.lower()
    
    quality = [f"{extracted_kwords['screen_size']['value']}"] if extracted_kwords['screen_size'] else []
    codec = [clean_words(extracted_kwords['video_codec']['value'])] if extracted_kwords['video_codec'] else []
    audio = [o for o in _audio if o in f] or []
    keywords = [x for x in words.split()] if words else []

    #Split input keywords and add to the list   
    if (kword):
        keywords += f'{kword}'.split()[:4]
    
    # logger.debug(f'Keywords: {keywords} quality: {quality} codec: {codec} audio: {audio}')
    return Metadata(keywords, quality, codec, audio, True)

if not args.no_filter:
    metadata = extract_meta_data(args.search, args.kword, os.path.isfile(args.search))
else:
    metadata = Metadata([], [], [], [], False)

def sort_results(results_list:list[Dict[str,Any]], metadata:Metadata=metadata) -> list[Dict[str,Any]]:
    """
    Finding the `Metadata` (keywords, quality, codec, audio) in the description

    and order by `score`.
    
    ### Score:

    The scale of `scores`: `0.125` by `Metadata` and `0.5` for max `download`.

    `Score`-->`Metadata`: 0.125 --> 1 , 0.25 --> 2 , ... 0.50 --> 4
    """
    max_dl = max( [ int(x['descargas']) for x in results_list ] )
    results = listDict([])

    # compile patterns
    compile_keywords = re.compile(r'\b(?:' + '|'.join(map(re.escape, sorted(metadata.keywords, key=len, reverse=True))) + r')\b', flags=re.I)
    compile_quality = re.compile(r'\b(?:' + '|'.join(map(re.escape, sorted(metadata.quality, key=len, reverse=True))) + r')\b', flags=re.I)
    compile_codec = re.compile(r'\b(?:' + '|'.join(map(re.escape, sorted(metadata.codec, key=len, reverse=True))) + r')\b', flags=re.I)
    compile_audio = re.compile(r'\b(?:' + '|'.join(map(re.escape, sorted(metadata.audio, key=len, reverse=True))) + r')\b', flags=re.I)

    for subs_dict in results_list:
        description = f"{subs_dict['descripcion']}"
        score = 0
        meta = False
        
        if metadata.keywords and compile_keywords.search(description):
            score += .125
            meta = True

        if metadata.quality and compile_quality.search(description):
            score += .125
            meta = True

        if metadata.codec and compile_codec.search(description):
            score += .125
            meta = True

        if metadata.audio and compile_audio.search(description):
            score += .125
            meta = True

        if  max_dl == int(subs_dict['descargas']):
            score += .5

        subs_dict['score'] = score
        subs_dict['meta']  = True if meta else False
        results.append(subs_dict)

    results = sorted(results, key=lambda item: (item['score']), reverse=True)
      
    return results     

### Filters searchs functions ###
def match_text(title:str, number:str, inf_sub:Dict[str, Any], text:str):
  """Filter Search results with the best match possible"""

  # Setting Patterns
  special_char = ["`", "'", "´", ":", ".", "?"]
  for i in special_char:
      title = title.replace(i, '')
      text = text.replace(i, '')
  text = str(html2text.html2text(text)).strip()
  aka = "aka"
  search = f"{title} {number}"
  match_type = None
  rnumber = False
  raka = False
  
  # Setting searchs Patterns
  re_full_match = re.compile(rf"^{re.escape(search)}$", re.I)
  re_full_pattern = re.compile(rf"^{re.escape(title)}.*{number}.*$", re.I) if inf_sub['type'] == "movie"\
    else re.compile(rf"^{re.escape(title.split()[0])}.*{number}.*$", re.I)
  re_title_pattern = re.compile(rf"^{re.escape(title)}\b", re.I)

  # Perform searches
  r = True if re_full_match.search(text.strip()) else False
  match_type = 'full' if r else None

  if not r:
    r = True if re_full_pattern.search(text.strip()) else False
    match_type = 'pattern' if r else None 

  if not r :
    rtitle = True if re_title_pattern.search(text.strip()) else False
    for num in number.split(" "):
        if not inf_sub['season']:
           rnumber = True if re.search(rf"\b{num}\b", text, re.I) else False
        else:
           rnumber = True if re.search(rf"\b{num}.*\b", text, re.I) else False

    raka = True if re.search(rf"\b{aka}\b", text, re.I) else False

    if raka :
        r = True if rtitle and rnumber and raka else False
        match_type = 'partial' if r else None
    else:
        r = True if rtitle and rnumber else False
        match_type = 'partial' if r else None

  if not r:
    if all(re.search(rf"\b{word}\b", text, re.I) for word in search.split()) :
        r = True if rnumber and raka else False
        match_type = 'partial' if r else None

  if not r:
    if all(re.search(rf"\b{word}\b", text, re.I) for word in title.split()) :
        r = True if rnumber else False
        match_type = 'partial' if r else None

  if not r:
    match_type = 'any'

  return match_type 

def get_filtered_results (title:str, number:str, inf_sub:Dict[str, Any], list_Subs_Dicts:list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Filter subtitles search for the best match results"""
    
    filtered_results = listDict([])
    lst_full = listDict([])
    lst_pattern = listDict([])
    lst_partial = listDict([])
    lst_any = listDict([])

    if inf_sub['type'] == "movie" and inf_sub['number'] == "":
        return list_Subs_Dicts

    for subs_dict in list_Subs_Dicts:
        mtype = match_text(title, number, inf_sub, subs_dict['titulo'])
        if mtype == 'full':
            lst_full.append(subs_dict)
        elif mtype == 'pattern':
            lst_pattern.append(subs_dict)
        elif mtype == 'partial':
            lst_partial.append(subs_dict)
        else:
            if mtype == 'any':
                lst_any.append(subs_dict)
    
    if inf_sub['season']:
        filtered_results = lst_full + lst_partial if len(lst_partial) !=0 else lst_full + lst_pattern
    
    if inf_sub['type'] == "episode":
        if (inf_sub['season']):
            if len(lst_full) != 0:
                filtered_results = lst_full + lst_pattern         
        else:
            if len(lst_full) != 0:
                filtered_results = lst_full
            elif len(lst_partial) != 0:
                filtered_results = lst_partial
            elif len(lst_pattern) != 0:
                filtered_results = lst_pattern
            else:
                filtered_results = lst_any
    
    
    if inf_sub['type'] == "movie":

        if len(lst_full) != 0 or len(lst_pattern) != 0:
            filtered_results = lst_full + lst_pattern
        elif len(lst_partial) != 0:
            filtered_results = lst_partial
        else:
            filtered_results = lst_any
    
    filtered_results = sorted(filtered_results, key=lambda item: item['id'], reverse=True)

    return filtered_results

### Filters searchs functions ###

def clean_screen() -> None:
    """Clean the screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

@typing.no_type_check
def highlight_text(text:str, metadata:Metadata=metadata) -> str:
    """Highlight all `text`  matches  `metadata`"""
    
    # make a list of keywords and escaped it. Sort list for efficiency
    keywords = list(chain(*metadata[:4]))

    # compile a pattern
    matches_compile = re.compile(r'\b(?:' + '|'.join(map(re.escape, sorted(keywords, key=len, reverse=True))) + r')\b', flags=re.I)

    @typing.no_type_check
    def _highlight(matches):
        return "[white on green4]" + f'{matches.group(0)}' + "[default on default]" 

    highlighted = matches_compile.sub(_highlight, text) 
    
    return highlighted

def backoff_delay(backoff_factor:float = 2, attempts:int = 2) -> None:
    """ backoff algorithm: backoff_factor * (2 ** attempts)."""
    delay:float = backoff_factor * (2 ** attempts)
    time.sleep(delay)

def convert_datetime(string_datetime:str):
    """
       Convert ``string_datetime`` in a datetime obj then format it to "%d/%m/%Y %H:%M"

       Return ``--- --`` if not invalid datetime string.
    """

    try:
        date_obj = datetime.strptime(string_datetime, '%Y-%m-%d %H:%M:%S').date()
        time_obj = datetime.strptime(string_datetime, '%Y-%m-%d %H:%M:%S').time()
        date_time_str = datetime.combine(date_obj, time_obj).strftime('%d/%m/%Y %H:%M')

    except ValueError:
        return "--- --"
    
    return date_time_str

def convert_date(list_dict_subs:list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """   
    Convert to datetime Items ``fecha_subida``.
    """
    for dictionary in list_dict_subs:
        dictionary['fecha_subida'] = convert_datetime(str(dictionary['fecha_subida']))

    return list_dict_subs

def get_aadata(search:str) -> Any:
    """Get a json data with the ``search`` results."""
    json_aaData:Any = ''
    try:
        retries = urllib3.util.Retry(total=2, backoff_factor=1)
        fields:Dict[str, Any] = {'buscar' + conn_data.search: search,
        'filtros': '', 'tabla': 'resultados', 'token': conn_data.token
        }
        
        page = conn.request(
            'POST',
            SUBDIVX_SEARCH_URL,
            headers=headers,
            fields=fields,
            retries=retries
        ).data

        if not page :
            if not args.quiet: console.clear()
            console.print(":no_entry: [bold red]Couldn't load results page. Try later![/]", emoji=True, new_line_start=True)
            conn_data.reset_data_connection()
            logger.debug('Could not load results page')
            sys.exit(1)
        else :
            json_aaData = json.loads(page)
            if json_aaData['sEcho'] == "0":
                site_msg = str(json.loads(page)['mensaje'])
                logger.debug(f'Site message: {site_msg}')
                backoff_delay(backoff_factor=1.5)
                page = conn.request('POST', SUBDIVX_SEARCH_URL, headers=headers, fields=fields, retries=retries).data
                
                if page:
                    json_aaData = json.loads(page)
                    if json_aaData['sEcho'] == "0":
                        raise NoResultsError(f'Site message: {site_msg}')
                else:
                    sys.exit(1)
    
    except HTTPError as e:
        HTTPErrorsMessageException(e)
        sys.exit(1)

    except JSONDecodeError as msg:
        logger.debug(f'Error JSONDecodeError: "{msg.__str__()}"')
        console.print(":no_entry: [bold red]Couldn't load results page![/]", emoji=True, new_line_start=True)
    
    return json_aaData

def make_layout() -> Layout:
    """Define the layout."""
    layout = Layout(name="results")

    layout.split_column(
        Layout(name="table")
    )
    return layout

def make_screen_layout() -> Layout:
    """Define a screen layout."""
    layout = Layout(name="screen")

    layout.split_column(
        Layout(name="subtitle"),
        Layout(name="description", size=8, ratio=1),
        Layout(name="caption")
    )
    layout["caption"].update(Align.center("Download:[[bold green]D[/]] Back:[[bold green]A[/]]",
                                          vertical="middle", style="italic bright_yellow"))

    return layout

def make_description_panel(description:str) -> Panel:
    """Define a description Panel."""
    descriptions = Table.grid(padding=1)
    descriptions.add_column()
    descriptions.add_row(description)
    descriptions_panel = Panel(
        Align.center(
            Group(Align.center(descriptions)), vertical = "middle"
        ),
        box = box.ROUNDED,
        title = "[bold yellow]Descripción:[/]",
        title_align = "left",
        subtitle = "[white on green4]Coincidencias[/] [italic bright_yellow]con los metadatos del archivo[/]",
        subtitle_align = "center",
        padding = 1 
    )

    return descriptions_panel

## Get Comments functions ##
def get_comments_data(subid:str):
    """Get comments Json data"""

    fields={'getComentarios': subid}
    try:
        page = conn.request('POST', SUBDIVX_SEARCH_URL, fields=fields, headers=headers).data
        json_comments = json.loads(page)

    except HTTPError as e:
        msg = e.__str__().split(":", maxsplit=1)[1].split("(")[0]
        logger.debug(f'Could not load comments ID:{subid}: Network Connection Error:"{msg}"')
        return None

    except JSONDecodeError as msg:
        logger.debug(f'Could not load comments ID:{subid}: Error JSONDecodeError:"{msg}"')
        return None

    return json_comments

def parse_list_comments(list_dict_comments:listDict) -> listDict:
    """ Parse comments :
       * Remove not used Items
       * Convert to datetime Items ``fecha_creacion``.
       * Convert ``nick`` to text
    """
    parser = html2text.HTML2Text()
    parser.ignore_images = True
    parser.ignore_links = True

    for dictionary in list_dict_comments:
        dictionary['fecha_creacion'] = convert_datetime(str(dictionary['fecha_creacion']))
        dictionary['nick'] = parser.handle(dictionary['nick']).strip()

    return list_dict_comments

def make_comments_table(title:str, results:Dict[str,Any], page:int, metadata:Metadata=metadata) -> Table:
    """Define a comments Table."""

    BG_STYLE = Style(color="white", bgcolor="gray0", bold=False)

    comment_table = Table(box=box.SIMPLE, title="\n" + title, caption="Prev.:[[bold green]\u2190[/]] Next:[[bold green]\u2192[/]] "\
                    "Back:[[bold green]A[/]] Download:[[bold green]D[/]] Metadata?:[green]Green[/]\n\n"\
                    "Pag.[bold white] " + str(page + 1) + "[/] of [bold white]" + str(results['pages_no']) + "[/] " \
                    "of [bold green]" + str(results['total']) + "[/] comment(s)",
                    show_header=True, header_style="bold yellow", title_style="bold green",
                    caption_style="italic bright_yellow", leading=0, show_lines=False, show_edge=False,show_footer=True)
    
    comment_table.add_column("#", justify="right", vertical="middle", style="bold green")
    comment_table.add_column("Comentarios", justify="left", vertical="middle", style="white")
    comment_table.add_column("Usuario", justify="center", vertical="middle")
    comment_table.add_column("Fecha", justify="center", vertical="middle")

    count = int(page * results['per_page'])
    rows: list[list[str]] = []
    items:list[str] = []
    
    for item in results['pages'][page]:
        try:
            comentario = html2text.html2text(item['comentario']).strip()
            if metadata.hasdata: comentario = highlight_text(comentario, metadata)
            usuario = str(item['nick'])
            fecha = str(item['fecha_creacion'])

            items = [str(count + 1), comentario, usuario, fecha]
            rows.append(items)
        except IndexError:
            pass
        count = count +1
    
    for row in rows:
        row[0] =  "[bold green]" + row[0] + "[/]"
        comment_table.add_row(*row, style = BG_STYLE )

    return comment_table

def not_comments(text:str) -> Panel:
    """Show Not Comments Panel"""

    not_comment_panel = Panel(
        Align.center(
            Group(Align.center(text,vertical='top')), vertical = "top"
        ),
        box = box.SIMPLE_HEAD,
        title = "[bold yellow]Comentarios[/]",
        subtitle ="Back:[[bold green]A[/]] Download:[[bold green]D[/]]",
        padding = 1,
        style="italic bright_yellow",
        height=5,
    )

    return not_comment_panel

### Show results and get subtitles ###

def generate_results(title:str, results:Dict[str, Any], page:int, selected:int, metadata:Metadata=metadata) -> Layout:
    """Generate Selectable results Table."""

    SELECTED = Style(color="white", bgcolor="gray35", bold=True)
    layout_results = make_layout() 

    table = Table(box=box.SIMPLE, title=">> " + f'{title}\n' +\
                "[italic]Pag.[bold white] " + f"{page + 1}" + "[/] of [bold white]" + f"{results['pages_no']}" +\
                "[/] of [bold green]" + f"{results['total']}" + "[/] result(s)[/]", 
                caption="\nDw:[bold green]\u2193[/] Up:[bold green]\u2191[/] Nx:[bold green]\u2192[/] Pv:[bold green]\u2190[/] "\
                "Dl:[bold green]ENTER[/] Descrip.:[bold green]D[/] Comments:[bold green]C[/] Exit:[bold green]S[/]\n" \
                "Date:[bold green]\u2193 PgDn[/] [bold green]\u2191 PgUp[/] Default:[bold green]F[/] Metadata?:[green]Green[/]",
                title_style="bold green", show_header=True, header_style="bold yellow", caption_style="bold bright_yellow",
                show_edge=False, pad_edge=False)
    
    table.add_column("#", justify="right", vertical="middle", style="bold green")
    table.add_column("Título", justify="left", vertical="middle", style="white", ratio=2)
    table.add_column("Descargas", justify="center", vertical="middle")
    table.add_column("Usuario", justify="center", vertical="middle")
    table.add_column("Fecha", justify="center", vertical="middle")

    count = int(page * results['per_page'])
    rows: list[list[str]] = []
    items:list[str] = []
 
    for item in results['pages'][page]:
        try:
            titulo = html2text.html2text(item['titulo']).strip()
            if metadata.hasdata: titulo = "[green]" + titulo + "[/]" if item['meta'] else titulo
            descargas = str(item['descargas'])
            usuario = str(item['nick'])
            fecha = str(item['fecha_subida'])

            items = [str(count + 1), titulo, descargas, usuario, fecha]
            rows.append(items)
        except IndexError:
            pass
        count = count +1
    
    for i, row in enumerate(rows):
        row[0] =  "[bold red]\u25cf[/]" + row[0] if i == selected else " " + row[0]
        table.add_row(*row, style=SELECTED if i == selected else "white")

    layout_results["table"].update(table)
    
    return layout_results

def paginate(items:list[Any], per_page:int) -> Dict[str, Any]:
    """ Paginate `items` in perpage lists 
    and return a `Dict` with:
     * Total items
     * Number of pages
     * Per page amount
     * List of pages.
    """
    pages = [items[i:i+per_page] for i in range(0, len(items), per_page)]
    results:Dict[str, Any] = {}
    results = {
        'total': len(items),
        'pages_no': len(pages),
        'per_page': per_page,
        'pages': pages
    }
    return results

def get_rows() -> int:
    """Get Terminal available rows"""
    lines = shutil.get_terminal_size().lines
    fixed_lines = lines - 10
    available_lines = fixed_lines if (fixed_lines > 0) else lines
    if args.nlines:
        num_lines = args.nlines
        available_lines = min(available_lines, num_lines)

    return available_lines

def get_comments_rows() -> int:
    """Get Terminal available rows for comments"""
    lines = shutil.get_terminal_size().lines
    fixed_lines = lines - 20
    available_lines = fixed_lines if (fixed_lines > 0) else lines
    if args.nlines:
        num_lines = args.nlines
        available_lines = min(available_lines, num_lines)

    return available_lines

def get_selected_subtitle_id(table_title:str, results:list[Dict[str,Any]], metadata:Metadata=metadata) -> str:
    """Show subtitles search results for obtain download id."""

    results_pages = paginate(results, get_rows())
    selected = 0
    page = 0
    res = f""

    try:
        with Live(
            generate_results (table_title, results_pages, page, selected, metadata),auto_refresh=False, screen=False, transient=True
        ) as live:
            while True:
                live.console.show_cursor(False)

                ch = readkey()
                if ch == key.UP:
                    selected = max(0, selected - 1)
                
                if ch == key.PAGE_UP:
                    results_pages = sorted(results, key=lambda item: (
                                    datetime.strptime(item['fecha_subida'],'%d/%m/%Y %H:%M')
                                    if item['fecha_subida'] != "--- --" else datetime.min
                                    ), reverse=False
                                )
                    results_pages = paginate(results_pages, get_rows())
                
                if ch == key.PAGE_DOWN:
                    results_pages = sorted(results, key=lambda item: (
                                    datetime.strptime(item['fecha_subida'],'%d/%m/%Y %H:%M')
                                    if item['fecha_subida'] != "--- --" else datetime.min
                                    ), reverse=True
                                )
                    results_pages = paginate(results_pages, get_rows())
                
                if ch in ["F", "f"]:
                      results_pages = paginate(results, get_rows())
                
                if ch == key.DOWN:
                    selected = min(len(results_pages['pages'][page]) - 1, selected + 1)

                if ch in ["D", "d"]:
                    description_selected = str(results_pages['pages'][page][selected]['descripcion'])
                    subtitle_selected =  results_pages['pages'][page][selected]['titulo']
                    parser = HTML2BBCode()
                    description = parser.html_to_bbcode(description_selected)
                    description = highlight_text(description, metadata) if metadata.hasdata else description

                    layout_description = make_screen_layout()
                    layout_description["description"].update(make_description_panel(description))
                    layout_description["subtitle"].update(Align.center(
                                html2text.html2text(subtitle_selected).strip(),
                                vertical="middle",
                                style="italic bold green"
                                ))

                    with console.screen(hide_cursor=True) as screen: 
                        while True:
                            screen.console.show_cursor(False)
                            screen.update(layout_description)

                            ch_exit = readkey()
                            if ch_exit in ["A", "a"]:
                                break

                            if ch_exit in ["D", "d"]:
                                res = f"{results_pages['pages'][page][selected]['id']}"
                                break
                                
                    if res != "": break
                
                if ch in ["C", "c"]:
                    cpage = 0
                    subtitle_selected =  results_pages['pages'][page][selected]['titulo']
                    subid = str(results_pages['pages'][page][selected]['id'])
                    layout_comments = make_layout()
                    title = html2text.html2text(subtitle_selected).strip()
                    show_comments = True if results_pages['pages'][page][selected]['comentarios'] != 0 else False
                    comment_msg = ":neutral_face: [bold red][i]¡No hay comentarios para este subtítulo![/]" if not show_comments else "" 
                    comments = {}

                    with console.screen(hide_cursor=True) as screen_comments:
                        if show_comments:
                            with console.status("[bold yellow][i]CARGANDO COMENTARIOS...[/]", spinner='aesthetic'):
                              aaData = get_comments_data(subid)
                            if aaData: 
                                comments = aaData['aaData']
                                comments = parse_list_comments(comments)
                                comments = paginate(comments, get_comments_rows())
                            
                            if not comments:
                                show_comments = False
                                comment_msg = ":neutral_face: [bold red][i]¡No se pudieron cargar los comentarios![/]"
                        
                        while True:
                            if show_comments :
                                layout_comments['table'].update(Align.center(
                                    Group(Align.center(make_comments_table(title, comments, cpage, metadata), vertical="top")), vertical='top'
                                    )
                                )
                            else :
                                layout_comments['table'].update(not_comments(comment_msg))
                            
                            screen_comments.console.show_cursor(False)
                            screen_comments.update(layout_comments)

                            ch_comment = readkey()
                            
                            if ch_comment in ["A", "a"]:
                                break
                            
                            if ch_comment == key.RIGHT :
                                cpage = min(comments["pages_no"] - 1, cpage + 1)

                            if ch_comment == key.LEFT :
                                cpage = max(0, cpage - 1)

                            if ch_comment in ["D", "d"]:
                                res = subid
                                break

                    if res != "": break

                if ch == key.RIGHT :
                    page = min(results_pages["pages_no"] - 1, page + 1)
                    selected = 0

                if ch == key.LEFT :
                    page = max(0, page - 1)
                    selected = 0

                if ch == key.ENTER:
                    res = f"{results_pages['pages'][page][selected]['id']}"
                    break

                if ch in ["S", "s"]:
                    res = -1
                    break
                live.update(generate_results(table_title, results_pages, page, selected, metadata), refresh=True)

    except KeyboardInterrupt:
        if not args.verbose:clean_screen()
        logger.debug('Interrupted by user')
        sys.exit(1)

    if (res == -1):
        if not args.verbose:clean_screen()
        logger.debug('Download Canceled')
        return f""
    
    # clean_screen()
    return res

### Extract Subtitles ###
@typing.no_type_check
def extract_subtitles(compressed_sub_file: ZipFile | RarFile, topath:str) -> None:
    """Extract ``compressed_sub_file`` from ``temp_file`` ``topath``."""
    # For portable Windows EXE
    if sys.platform == "win32":
        import rarfile #type: ignore

        @typing.no_type_check
        def resource_path(relative_path:str) -> str:
            """ Get absolute path to resource, works for dev and for PyInstaller """
            base_path:str = ""
            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                if hasattr(sys, '_MEIPASS'):
                    base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            
            return os.path.join(base_path, relative_path)
            
        rarfile.UNRAR_TOOL = resource_path("UnRAR.exe")

    def _is_supported(sub:RarInfo | ZipInfo) -> bool:
        filename = f'{os.path.basename(str(sub.filename))}'
        return any(filename.endswith(ext) for ext in sub_extensions) and '__MACOSX' not in filename

    def _is_compressed(filename: str) -> bool:
        """Check if a file is a supported archive based on its extension."""
        return any(filename.endswith(ext) for ext in _compressed_extensions)
    
    @typing.no_type_check
    def _uncompress(source:Any, topath:str) -> None:
        """Decompress compressed file"""
        compressed = RarFile(source) if is_rarfile(source) else ZipFile(source) if is_zipfile(source) else None
        if compressed:
            for sub in compressed.infolist(): 
                if _is_compressed(sub.filename):
                    source = compressed.open(sub)
                    _uncompress(source, topath)
                else:
                    compressed.extract(sub, topath)
            compressed.close()
        else:
            logger.debug(f'Unsupported archive format')

    # In case of existence of various subtitles choose which to download
    if len(compressed_sub_file.infolist()) > 1 : 
        res:int = 0
        count:int = 0
        choices:list[str] = []
        choices.append(str(count))
        list_sub:list[str] = []

        for i in compressed_sub_file.infolist():
            if i.is_dir() or os.path.basename(i.filename).startswith("._"): # type: ignore
                continue
            i.filename = os.path.basename(i.filename)
            list_sub.append(f'{i.filename}')
        
        if not args.no_choose:
            clean_screen()
            table = Table(box=box.ROUNDED, title=">> Subtítulos disponibles:", title_style="bold green",show_header=True, 
                        header_style="bold yellow", show_lines=True, title_justify='center')
            table.add_column("#", justify="center", vertical="middle", style="bold green")
            table.add_column("Subtítulos", justify="center" , no_wrap=True)

            for i in list_sub:
                table.add_row(str(count + 1), i)
                count += 1
                choices.append(str(count))
        
            choices.append(str(count + 1))
            console.print(table)
            console.print("[bold green]>> [0] Descargar todos\r", new_line_start=True)
            console.print("[bold red]>> [" + str(count + 1) + "] Cancelar descarga\r", new_line_start=True)

            try:
                res = IntPrompt.ask("[bold yellow]>> Elija un [" + "[bold green]#" + "][bold yellow]. Por defecto:", 
                            show_choices=False, show_default=True, choices=choices, default=0)
            except KeyboardInterrupt:
                logger.debug('Interrupted by user')
                if not args.quiet:
                    console.print(":x: [bold red]Interrupto por el usuario...", emoji=True, new_line_start=True)
                    time.sleep(0.2)
                    clean_screen()
                return
        
            if (res == count + 1):
                logger.debug('Canceled Download Subtitle') 
                if not args.quiet:
                    console.print(":x: [bold red] Cancelando descarga...", emoji=True, new_line_start=True)
                    time.sleep(0.2)
                    clean_screen()
                return

            clean_screen()

        logger.debug('Decompressing files')

        if res == 0:
            with compressed_sub_file as csf:
                for sub in csf.infolist():
                    if _is_supported(sub) and not sub.is_dir():
                        logger.debug(' '.join(['Decompressing subtitle:', sub.filename, 'to', topath]))
                        csf.extract(sub, topath)
                    elif _is_compressed(sub.filename):
                        with csf.open(sub) as source:
                            _uncompress(source, topath)
                        logger.debug(' '.join(['Decompressed file:', sub.filename, 'to', topath]))         
            compressed_sub_file.close()
        else:
            selected = f'{list_sub[res - 1]}'
            with compressed_sub_file as csf:
                for sub in csf.infolist():
                    if selected == os.path.basename(sub.filename):
                        if _is_supported(sub):
                            logger.debug(' '.join(['Decompressing subtitle:', selected, 'to', topath]))
                            csf.extract(sub, topath)
                        elif _is_compressed(sub.filename):
                            with csf.open(sub) as source:
                                _uncompress(source, topath=topath)
                            logger.debug(' '.join(['Decompressed file:', sub.filename, 'to', topath]))
                        break
            compressed_sub_file.close()

        logger.debug(f"Done extract subtitles!")

        if not args.quiet:
            clean_screen()
            console.print("\u2713 Done download subtitles!", emoji=True, new_line_start=True)
    else:
        for name in compressed_sub_file.infolist():
            # don't unzip stub __MACOSX folders
            if _is_supported(name):
                logger.debug(' '.join(['Decompressing subtitle:', name.filename, 'to', topath]))
                compressed_sub_file.extract(name, topath)
            elif _is_compressed(name.filename):
                with compressed_sub_file.open(name) as source:
                    _uncompress(source, topath=topath)
                logger.debug(' '.join(['Decompressed file:', name.filename, 'to', topath]))
        compressed_sub_file.close()

        logger.debug(f"Done extract subtitle!")
        if not args.quiet: console.print("\u2713 Done download subtitle!", emoji=True, new_line_start=True)

### Search IMDB ###

def get_imdb_search(title:str, number:str, inf_sub:Dict[str, Any]):
    """Get the IMDB ``id`` or ``title`` for search subtitles"""
    from sdx_dl.sdximdb import IMDB
    try:
        imdb = IMDB()
        if args.proxy:
            proxies = {'http': proxie, 'https': proxie}
            imdb.session.proxies.update(proxies)
            imdb.session.verify = False
        
        year = int(number[1:5]) if (inf_sub['type']  == "movie") and (number != "") else None

        if inf_sub['type'] == "movie":
            res = imdb.get_by_name(title, year, tv=False) if year is not None else imdb.search(title, tv=False) # type: ignore
        else:
            res = imdb.search(title, tv=True) # type: ignore
    except Exception:
        pass
        return None
    
    try:
        results = json.loads(res) if year is not None else json.loads(res)['results']
    except JSONDecodeError as e:
        msg = e.__str__()
        logger.debug(f'Could not decode json results: Error JSONDecodeError:"{msg}"')
        if not args.quiet: console.print(":no_entry: [bold red]Some error retrieving from IMDB:[/]: " + msg,\
                                        new_line_start=True, emoji=True)
        return None
    
    if not results:
        return None
    else:
        if "result_count" in results and not results['results']:
            return None

    if year is not None:
        search = f"{results['id']}" if inf_sub['type'] == "movie" else f"{results['name']} {number}"
        return search
    else:
        search = make_IMDB_table(title, results, inf_sub['type'])
        if inf_sub['type'] == "movie":
            return search
        else:
            return f'{search} {number}' if search else None

def make_IMDB_table(title:str, results:list[Any], type:str):
    """Define a IMDB Table."""
    count = 0
    choices:list[str] = []
    choices.append(str(count))

    BG_STYLE = Style(color="white", bgcolor="gray0", bold=False)

    imdb_table = Table(box=box.SIMPLE_HEAD, title="\n Resultados de IMDB para: " + title, caption="[italic bright_yellow]"\
                    "Seleccione un resultado o enter para cancelar[/]\n",
                    show_header=True, header_style="bold yellow", title_style="bold green",
                    caption_style="bold bright_yellow", leading=1, show_lines=True)
    
    imdb_table.add_column("#", justify="right", vertical="middle", style="bold green")
    imdb_table.add_column("Título + url", justify="left", vertical="middle", style="white")
    imdb_table.add_column("IMDB", justify="center", vertical="middle")
    imdb_table.add_column("Tipo", justify="center", vertical="middle")

    rows:list[list[str]] = []
 
    for item in results:
        try:
            titulo = str(html2text.html2text(item['name'])).strip() + " ("+ str(item['year'])+ ")\n" + str(item['url'])
            imdb = str(item['id'])
            tipo = str(item['type'])

            items = [str(count + 1), titulo, imdb, tipo]
            choices.append(str(count + 1))
            rows.append(items)
        except IndexError:
            pass
        count = count +1
    
    for row in rows:
        row[0] =  "[bold green]" + row[0] + "[/]"
        imdb_table.add_row(*row, style = BG_STYLE )
    
    console.print(imdb_table)
    console.print("[bold green]>> [0] Cancelar selección\n\r", new_line_start=True)
    
    res = IntPrompt.ask("[bold yellow]>> Elija un [" + "[bold green]#" + "][bold yellow]. Por defecto:", 
                    show_choices=False, show_default=True, choices=choices, default=0)
  
    search = f"{results[res-1]['id']}" if type == "movie" else f"{results[res-1]['name']}"

    return search if res else None
