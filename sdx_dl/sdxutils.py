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
import random
from zipfile import ZipFile
from rarfile import RarFile
from sdx_dl.sdxclasses import HTML2BBCode, NoResultsError, GenerateUserAgent, IMDB, validate_proxy, VideoMetadataExtractor
from sdx_dl.sdxparser import logger, args as parser_args
from json import JSONDecodeError
from urllib3.exceptions import HTTPError
from bs4 import BeautifulSoup
from collections import namedtuple
from datetime import datetime, timedelta
from readchar import readkey, key
from sdx_dl.sdxconsole import console
from rich import box
from rich.layout import Layout
from rich.console import Group
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.align import Align
from rich.live import Live
from rich.prompt import IntPrompt

args = parser_args

#obtained from https://flexget.com/Plugins/quality#qualities

_qualities = ('1080i', '1080p', '2160p', '8bits', '10bit', '1280x720',
              '1920x1080', '360p', '368p', '480', '480p', '576p',
               '720i', '720p', 'bdrip', 'brrip', 'bdscr', 'bluray',
               'blurayrip', 'cam', 'dl', 'dsrdsrip', 'dvb', 'dvdrip',
               'dvdripdvd', 'dvdscr', 'hdtv', 'hr', 'ppvrip',
               'preair', 'sdtvpdtv', 'tvrip', 'web', 'web-dl',
               'web-dlwebdl', 'webrip', 'workprint', 'avc')
_keywords = (
'2hd', 'adrenaline', 'amzn', 'asap', 'axxo', 'compulsion', 'crimson', 'ctrlhd', 
'ctrlhd', 'ctu', 'dimension', 'ebp', 'gttv','ettv', 'eztv', 'fanta', 'fov', 'fqm', 'ftv', 
'galaxyrg', 'galaxytv', 'hazmatt', 'immerse', 'internal', 'ion10', 'killers', 'loki', 
'lol', 'mement', 'minx', 'notv', 'phoenix', 'rarbg', 'sfm', 'sva', 'sparks', 'turbo', 
'torrentgalaxy', 'psa', 'nf', 'rrb', 'pcok', 'edith', 'successfulcrab', 'megusta', 'ethel',
'ntb', 'flux', 'yts', 'rbb', 'xebec', 'rubik')

_codecs = ('xvid', 'x264', 'h264', 'x265', 'hevc')

_audio = ('dts-hd', 'dts', 'ma', '5.1', 'ddp5.1', 'hdr', 'atmos' )

_sub_extensions = ['.srt', '.ssa', '.ass', '.sub']

_compressed_extensions = ['.zip', '.rar']

SUBDIVX_SEARCH_URL = 'https://www.subdivx.com/inc/ajax.php'

SUBDIVX_DOWNLOAD_PAGE = 'https://www.subdivx.com/'

Metadata = namedtuple('Metadata', 'keywords quality codec audio')

signal.signal(signal.SIGINT, lambda _, __: sys.exit(0))

# Configure connections
lst_ua = GenerateUserAgent.generate_all()
ua = random.choice(lst_ua)
headers={"user-agent" : ua}

if (args.proxy and validate_proxy(args.proxy)):
    proxie = f"{args.proxy}"
    if not (any(p in proxie for p in ["http", "https"])):
        proxie = "http://" + proxie
    s = urllib3.ProxyManager(proxie, num_pools=8, headers=headers, cert_reqs="CERT_REQUIRED", ca_certs=certifi.where(), retries=False, timeout=30)
else:
    s = urllib3.PoolManager(num_pools=8, headers=headers, cert_reqs="CERT_REQUIRED", ca_certs=certifi.where(), retries=False, timeout=30)

# Network connections Errors
def Network_Connection_Error(e: HTTPError) -> str:
    """ Return a Network Connection Error message."""

    msg = e.__str__()
    error_class = e.__class__.__name__
    Network_error_msg= {
        'ConnectTimeoutError' : "Connection to host timed out",
        'ReadTimeoutError'    : "Read timed out",
        'NameResolutionError' : 'Failed to resolve host name',
        'ProxyError'          : "Unable to connect to proxy",
        'NewConnectionError'  : "Failed to establish a new connection",
        'ProtocolError'       : "Connection aborted. Remote end closed connection without response",
        'MaxRetryError'       : "Maxretries exceeded",
        'SSLError'            : "Certificate verify failed: unable to get local issuer certificate",
        'HTTPError' : msg
    }
    error_msg = f'{error_class} : {Network_error_msg[error_class] if error_class in Network_error_msg else msg }'
    return error_msg

def HTTPErrorsMessageException(e: HTTPError):
    """ Manage HTTP Network connection Errors Exceptions message:
        * Log HTTP Network connection Error message
        * Print HTTP Network connection error message.
    """

    msg = Network_Connection_Error(e)
    if args.quiet: 
        logger.debug(f'Some Network Connection Error occurred: {msg}')
    else:
        console.print(":no_entry: [bold red]Some Network Connection Error occurred[/]: " + msg, new_line_start=True, emoji=True)
    
    if logger.level == 10:
        logger.debug(f'Network Connection Error occurred: {e.__str__()}')


### Setting data connection ###
sdx_data_connection_name = 'sdx_data_connection'

def check_data_connection():
    """Check the time and existence of the `cookie` session and return data connection."""

    sdx_data_connection = load_data_connection()

    if sdx_data_connection is None or exp_time_Cookie() is True:
        logger.debug(f'Getting data connection')
        cookie, token, f_search = get_data_connection()
        stor_data_connection(cookie, token, f_search)
    else:
        cookie, token, f_search = sdx_data_connection.split(";")
        logger.debug(f'Loaded data connection')
    return cookie, token, f_search

def exp_time_Cookie():
    """Compare modified time and return `True` if is expired."""
    # Get data connection modified time and convert it to datetime
    temp_dir = tempfile.gettempdir()
    sdx_dc_path = os.path.join(temp_dir, sdx_data_connection_name)
    csdx_ti_m = datetime.fromtimestamp(os.path.getmtime(sdx_dc_path))
    delta_csdx = datetime.now() - csdx_ti_m
    exp_c_time = timedelta(hours=2)
    return delta_csdx > exp_c_time

def get_data_connection():
    """ Retrieve sdx data connection."""
    try:
        sdx_request = s.request('GET', SUBDIVX_DOWNLOAD_PAGE, timeout=10)
        cookie_sdx = sdx_request.headers.get('Set-Cookie').split(';')[0]
        _vdata = BeautifulSoup(sdx_request.data, 'html5lib')
        _f_search = _vdata('div', id="vs")[0].text.replace("v", "").replace(".", "")
        _f_tk = SUBDIVX_SEARCH_URL[:-8] + 'gt.php?gt=1'
        _r_ftoken = s.request('GET', _f_tk, headers={"Cookie":cookie_sdx},preload_content=False).data
        _f_token = json.loads(_r_ftoken)['token']
    except HTTPError as e:
        HTTPErrorsMessageException(e)
        exit(1)
    except JSONDecodeError as e:
        console.print(":no_entry: [bold red]Couldn't load results page![/]: " + e.__str__(), emoji=True, new_line_start=True)

    return cookie_sdx, _f_token, _f_search

def stor_data_connection(sdx_cookie, token, f_search):
    """ Store sdx cookies."""
    temp_dir = tempfile.gettempdir()
    cookiesdx_path = os.path.join(temp_dir, sdx_data_connection_name)
    sdx_data_connection =f'{sdx_cookie};{token};{f_search}'
    with open(cookiesdx_path, 'w') as file:
        file.write(sdx_data_connection)
        file.close()
    
def load_data_connection():
    """ Load stored sdx cookies return ``None`` if not exists."""
    temp_dir = tempfile.gettempdir()
    sdx_dc_path = os.path.join(temp_dir, sdx_data_connection_name)
    if os.path.exists(sdx_dc_path):
        with open(sdx_dc_path, 'r') as filecookie:
            sdx_data_connection = filecookie.read()
    else:
        return None

    return sdx_data_connection

headers['Cookie'], _f_token, _f_search = check_data_connection()

#### sdxlib utils ####
def extract_meta_data(filename, kword):
    """Extract metadata from a filename based in matchs of keywords
    the lists of keywords includen quality and codec for videos."""

    extractor = VideoMetadataExtractor()
    extracted_kwords = extractor.extract_specific(f"{filename}", 'screen_size', 'video_codec','audio_channels',\
                        'release_group', 'source')
    words = f""

    def clean_words(word):
        """clean words"""
        clean = [".", "-"]
        for i in clean:
            word = word.replace(i, '')
        return f"{word}"
    
    for k in extracted_kwords.keys():
        value = extracted_kwords[k]
        if (value):
            words += f"{value} " if k not in ['video_codec', 'source'] else f"{clean_words(value)} "
    
    words = words.strip()
    # logger.debug(f'Extracted kwords:{words}')
    
    f = filename.lower()[:-4] if os.path.isfile(filename) else filename.lower()

    def _match(options):
        try:
            matches = [option for option in options if option in f]
        except IndexError:
            matches = []
        return matches
    
    keywords = _match(_keywords)
    quality = _match(_qualities)
    codec = _match(_codecs)
    audio = _match(_audio)
    
    #Split keywords and add to the list
    if (words):
        keywords = keywords + [x for x in words.split(' ') if x not in keywords]
    
    if (kword):
        keywords += kword.split(' ')
    
    return Metadata(keywords, quality, codec, audio)

### Filters searchs functions ###
def match_text(title, number, inf_sub, text):
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

#   logger.debug(f'Match type for: {text} :{match_type}')
  return match_type 

def get_filtered_results (title, number, inf_sub, list_Subs_Dicts):
    """Filter subtitles search for the best match results"""
    
    filtered_results = []
    lst_full = []
    lst_pattern = []
    lst_partial = []
    lst_any = []

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

def clean_screen():
    """Clean the screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def highlight_text(text,  metadata):
    """Highlight all text  matches  metadata of the file"""
    highlighted = f"{text}"
    
    for keyword in metadata.keywords:
        if keyword.lower() in text.lower():
            Match_keyword = re.search(keyword, text, re.IGNORECASE).group(0)
            highlighted = highlighted.replace(f'{Match_keyword}', f'{"[white on green4]" + Match_keyword + "[default on default]"}', 1)

    for quality in metadata.quality:
        if quality.lower() in text.lower():
            Match_quality = re.search(quality, text, re.IGNORECASE).group(0)
            highlighted = highlighted.replace(f'{Match_quality}', f'{"[white on green4]" + Match_quality + "[default on default]"}', 1)

    for codec in metadata.codec:
        if codec.lower() in text.lower():
            Match_codec = re.search(codec, text, re.IGNORECASE).group(0)
            highlighted = highlighted.replace (f'{Match_codec}', f'{"[white on green4]" + Match_codec + "[default on default]"}', 1)
    
    return highlighted

def backoff_delay(backoff_factor = 2, attempts = 2):
    """ backoff algorithm: backoff_factor * (2 ** attempts)."""
    delay = backoff_factor * (2 ** attempts)
    time.sleep(delay)
    return delay

def convert_datetime(string_datetime:str):
    """
       Convert ``string_datetime`` in a datetime obj then format it to "%d/%m/%Y %H:%M"

       Return ``--- --`` if not invalid datetime string.
    """

    try:
        date_obj = datetime.strptime(string_datetime, '%Y-%m-%d %H:%M:%S').date()
        time_obj = datetime.strptime(string_datetime, '%Y-%m-%d %H:%M:%S').time()
        date_time_str = datetime.combine(date_obj, time_obj).strftime('%d/%m/%Y %H:%M')

    except ValueError as e:
        # logger.debug(f'Value Error parsing: {string_datetime} Error: {e}')
        return "--- --"
    
    return date_time_str

def get_list_Dict(Data):
    """ Checking if ``Data`` is a list of dictionarys."""

    if isinstance(Data, list) and all(isinstance(item, dict)  
        for item in Data):  
            list_of_dicts = Data
    else:
        return None
    
    return list_of_dicts

def clean_list_subs(list_dict_subs):
    """ Clean not used Items from list of subtitles dictionarys ``list_dict_subs``
        
        Convert to datetime Items ``fecha_subida``.
    """
    list_Item_Subs = ['id', 'titulo', 'descripcion', 'descargas', 'comentarios', 'fecha_subida', 'nick']
    
    for dictionary in list_dict_subs:
        for i in list(dictionary.keys()):
            if i not in list_Item_Subs:
                del dictionary[i]
    
        dictionary['fecha_subida'] = convert_datetime(str(dictionary['fecha_subida']))

    return list_dict_subs

def get_aadata(search):
    """Get a json data with the ``search`` results."""
   
    try:
        fields={'buscar'+ _f_search: search, 'filtros': '', 'tabla': 'resultados', 'token': _f_token}
        page = s.request(
            'POST',
            SUBDIVX_SEARCH_URL,
            headers=headers,
            fields=fields
        ).data

        if not page: 
            logger.debug('Could not load page!')
            attempts = 2
            for _ in range(attempts):
                logger.debug(f'Request Attempts #: {_}')
                backoff_delay(2, attempts)
                page = s.request('POST', SUBDIVX_SEARCH_URL, headers=headers, fields=fields).data
                if not page : 
                    continue
                else:
                    json_aaData = json.loads(page)
                    break

        if not page :
            console.clear()
            console.print(":no_entry: [bold red]Couldn't load results page. Try later![/]", emoji=True, new_line_start=True)
            logger.debug('Could not load results page')
            exit(1)
        else :
            if json.loads(page)['sEcho'] == "0":
                backoff_delay()
                page = s.request('POST', SUBDIVX_SEARCH_URL, headers=headers, fields=fields).data
                json_aaData = json.loads(page) if page else None
                if json.loads(page)['sEcho'] == "0":
                    site_msg = str(json.loads(page)['mensaje'])
                    raise NoResultsError(f'Site message: {site_msg}')
            else:
                json_aaData = json.loads(page)
                # For testing
                # store_aadata(page)
    
    except HTTPError as e:
        HTTPErrorsMessageException(e)
        exit(1)

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

def make_description_panel(description) -> Panel:
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
def get_comments_data(subid:int):
    """Get comments Json data"""

    fields={'getComentarios': subid}
    try:
        page = s.request('POST', SUBDIVX_SEARCH_URL, fields=fields, headers=headers).data
        json_comments = json.loads(page)

    except HTTPError as e:
        msg = Network_Connection_Error(e)
        logger.debug(f'Could not load comments ID:{subid}: Network Connection Error:"{msg}"')
        return None

    except JSONDecodeError as msg:
        logger.debug(f'Could not load comments ID:{subid}: Error JSONDecodeError:"{msg}"')
        return None

    return json_comments

def parse_list_comments(list_dict_comments):
    """ Parse comments :
       * Remove not used Items
       * Convert to datetime Items ``fecha_creacion``.
       * Convert ``nick`` to text
    """
    list_Item_Comments = ['comentario', 'nick',  'fecha_creacion']
    parser = html2text.HTML2Text()
    parser.ignore_images = True
    parser.ignore_links = True

    for dictionary in list_dict_comments:
        for i in list(dictionary.keys()):
            if i not in list_Item_Comments:
                del dictionary[i]
    
        dictionary['fecha_creacion'] = convert_datetime(str(dictionary['fecha_creacion']))
        dictionary['nick'] = parser.handle(dictionary['nick']).strip()

    return get_list_Dict(list_dict_comments)

def make_comments_table(title, results, page) -> Table:
    """Define a comments Table."""

    BG_STYLE = Style(color="white", bgcolor="gray0", bold=False)

    comment_table = Table(box=box.SIMPLE, title="\n" + title, caption="Prev.:[[bold green]\u2190[/]] Next:[[bold green]\u2192[/]] "\
                    "Back:[[bold green]A[/]] Download:[[bold green]D[/]]\n\n"\
                    "Pag.[bold white] " + str(page + 1) + "[/] of [bold white]" + str(results['pages_no']) + "[/] " \
                    "of [bold green]" + str(results['total']) + "[/] comment(s)",
                    show_header=True, header_style="bold yellow", title_style="bold green",
                    caption_style="italic bright_yellow", leading=0, show_lines=False, show_edge=False,show_footer=True)
    
    comment_table.add_column("#", justify="right", vertical="middle", style="bold green")
    comment_table.add_column("Comentarios", justify="left", vertical="middle", style="white")
    comment_table.add_column("Usuario", justify="center", vertical="middle")
    comment_table.add_column("Fecha", justify="center", vertical="middle")

    count = page * results['per_page']
    rows = []
 
    for item in results['pages'][page]:
        try:
            comentario = str(html2text.html2text(item['comentario'])).strip()
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

def not_comments(text) -> Panel:
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

def generate_results(title, results, page, selected) -> Layout:
    """Generate Selectable results Table."""

    SELECTED = Style(color="green", bgcolor="gray35", bold=True)
    layout_results = make_layout() 

    table = Table(box=box.SIMPLE, title=">> " + f'{title}\n' +\
                "[italic]Pag.[bold white] " + f"{page + 1}" + "[/] of [bold white]" + f"{results['pages_no']}" +\
                "[/] of [bold green]" + f"{results['total']}" + "[/] result(s)[/]", 
                caption="\nDw:[bold green]\u2193[/] Up:[bold green]\u2191[/] Nx:[bold green]\u2192[/] Pv:[bold green]\u2190[/] "\
                "Dl:[bold green]ENTER[/] Descrip.:[bold green]D[/] Coments.:[bold green]C[/] Exit:[bold green]S[/]\n" \
                "Order by Date:[bold green]\u2193 PgDn[/] [bold green]\u2191 PgUp[/] Default:[bold green]F[/]",
                title_style="bold green", show_header=True, header_style="bold yellow", caption_style="bold bright_yellow",
                show_edge=False, pad_edge=False)
    
    table.add_column("#", justify="right", vertical="middle", style="bold green")
    table.add_column("Título", justify="left", vertical="middle", style="white", ratio=2)
    table.add_column("Descargas", justify="center", vertical="middle")
    table.add_column("Usuario", justify="center", vertical="middle")
    table.add_column("Fecha", justify="center", vertical="middle")

    count = page * results['per_page']
    rows = []
 
    for item in results['pages'][page]:
        try:
            titulo = str(html2text.html2text(item['titulo'])).strip()
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
        table.add_row(*row, style=SELECTED if i == selected else "bold white")

    layout_results["table"].update(table)
    
    return layout_results

def paginate(items, per_page):
    """ Paginate `items` in perpage lists 
    and return a `Dict` with:
     * Total items
     * Number of pages
     * Per page amount
     * List of pages.
    """
    pages = [items[i:i+per_page] for i in range(0, len(items), per_page)]
    return {
        'total': len(items),
        'pages_no': len(pages),
        'per_page': per_page,
        'pages': pages
    }

def get_rows():
    """Get Terminal available rows"""
    lines = shutil.get_terminal_size().lines
    fixed_lines = lines - 10
    available_lines = fixed_lines if (fixed_lines > 0) else lines
    if args.nlines:
        num_lines = args.nlines
        available_lines = min(available_lines, num_lines)

    return available_lines

def get_comments_rows():
    """Get Terminal available rows for comments"""
    lines = shutil.get_terminal_size().lines
    fixed_lines = lines - 15
    available_lines = fixed_lines if (fixed_lines > 0) else lines
    if args.nlines:
        num_lines = args.nlines
        available_lines = min(available_lines, num_lines)

    return available_lines

def get_selected_subtitle_id(table_title, results, metadata):
    """Show subtitles search results for obtain download id."""
    
    try:
        results_pages = paginate(results, get_rows())
        selected = 0
        page = 0
        res = 0
        with Live(
            generate_results (table_title, results_pages, page, selected),auto_refresh=False, screen=True, transient=False
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
                      results_pages = sorted(results, key=lambda item: (item['score'], item['descargas']), reverse=True)
                      results_pages = paginate(results_pages, get_rows())
                
                if ch == key.DOWN:
                    selected = min(len(results_pages['pages'][page]) - 1, selected + 1)

                if ch in ["D", "d"]:
                    description_selected = results_pages['pages'][page][selected]['descripcion']
                    subtitle_selected =  results_pages['pages'][page][selected]['titulo']
                    parser = HTML2BBCode()
                    description = str(parser.feed(description_selected))
                    description = highlight_text(description, metadata)

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
                                res = results_pages['pages'][page][selected]['id']
                                break
                                
                    if res != 0: break
                
                if ch in ["C", "c"]:
                    cpage = 0
                    subtitle_selected =  results_pages['pages'][page][selected]['titulo']
                    subid = int(results_pages['pages'][page][selected]['id'])
                    layout_comments = make_layout()
                    title = html2text.html2text(subtitle_selected).strip()
                    show_comments = True if results_pages['pages'][page][selected]['comentarios'] != 0 else False
                    comment_msg = ":neutral_face: [bold red][i]¡No hay comentarios para este subtítulo![/]" if not show_comments else "" 

                    with console.screen(hide_cursor=True) as screen_comments:
                        if show_comments:
                            with console.status("[bold yellow][i]CARGANDO COMENTARIOS...[/]", spinner='aesthetic'):
                              aaData = get_comments_data(subid)
                            comments = get_list_Dict(aaData['aaData']) if aaData is not None else None
                            comments = parse_list_comments(comments) if comments is not None else None
                            comments = paginate(comments, get_comments_rows()) if comments is not None else None
                            
                            if comments is None:
                                show_comments = False
                                comment_msg = ":neutral_face: [bold red][i]¡No se pudieron cargar los comentarios![/]"
                        
                        while True:
                            if show_comments :
                                layout_comments['table'].update(Align.center(
                                    Group(Align.center(make_comments_table(title, comments, cpage), vertical="top")), vertical='top'
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

                    if res != 0: break

                if ch == key.RIGHT :
                    page = min(results_pages["pages_no"] - 1, page + 1)
                    selected = 0

                if ch == key.LEFT :
                    page = max(0, page - 1)
                    selected = 0

                if ch == key.ENTER:
                    res = results_pages['pages'][page][selected]['id']
                    break

                if ch in ["S", "s"]:
                    res = -1
                    break
                live.update(generate_results(table_title, results_pages, page, selected), refresh=True)

    except KeyboardInterrupt:
        clean_screen()
        logger.debug('Interrupted by user')
        exit(1)

    if (res == -1):
        clean_screen()
        logger.debug('Download Canceled')
        return None
    
    clean_screen()
    return res

### Extract Subtitles ###
def extract_subtitles(compressed_sub_file: ZipFile | RarFile, topath):
    """Extract ``compressed_sub_file`` from ``temp_file`` ``topath``."""

    # In case of existence of various subtitles choose which to download
    if len(compressed_sub_file.infolist()) > 1 :
        res = 0
        count = 0
        choices = []
        choices.append(str(count))
        list_sub = []

        for i in compressed_sub_file.infolist():
            if i.is_dir() or os.path.basename(i.filename).startswith("._"):
                continue
            i.filename = os.path.basename(i.filename)
            list_sub.append(i.filename)
        
        if not args.no_choose:
            clean_screen()
            table = Table(box=box.ROUNDED, title=">> Subtítulos disponibles:", title_style="bold green",show_header=True, 
                        header_style="bold yellow", show_lines=True, title_justify='center')
            table.add_column("#", justify="center", vertical="middle", style="bold green")
            table.add_column("Subtítulos", justify="center" , no_wrap=True)

            for i in list_sub:
                table.add_row(str(count + 1), str(i))
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
                    if not sub.is_dir():
                        sub.filename = os.path.basename(sub.filename)
                    if any(sub.filename.endswith(ext) for ext in _sub_extensions + _compressed_extensions) and '__MACOSX' not in sub.filename:
                        logger.debug(' '.join(['Decompressing subtitle:', sub.filename, 'to', topath]))
                        csf.extract(sub, topath)
            compressed_sub_file.close()
        else:
            if any(list_sub[res - 1].endswith(ext) for ext in _sub_extensions + _compressed_extensions) and '__MACOSX' not in list_sub[res - 1]:
                with compressed_sub_file as csf:
                    for sub in csf.infolist():
                        if not sub.is_dir():
                            sub.filename = os.path.basename(sub.filename)
                            if list_sub[res - 1] == sub.filename :
                                logger.debug(' '.join(['Decompressing subtitle:', list_sub[res - 1], 'to', topath]))
                                csf.extract(sub, topath)
                                break
            compressed_sub_file.close()

        logger.debug(f"Done extract subtitles!")

        if not args.quiet:
            clean_screen()
            console.print(":white_check_mark: Done extract subtitle!", emoji=True, new_line_start=True)
    else:
        for name in compressed_sub_file.infolist():
            # don't unzip stub __MACOSX folders
            if any(name.filename.endswith(ext) for ext in _sub_extensions) and '__MACOSX' not in name.filename:
                logger.debug(' '.join(['Decompressing subtitle:', name.filename, 'to', topath]))
                compressed_sub_file.extract(name, topath)
        compressed_sub_file.close()
        logger.debug(f"Done extract subtitle!")
        if not args.quiet: console.print(":white_check_mark: Done extract subtitle!", emoji=True, new_line_start=True)

### Search IMDB ###

def get_imdb_search(title, number, inf_sub):
    """Get the IMDB ``id`` or ``title`` for search subtitles"""
    try:
        imdb = IMDB()
        title = f'{title}'
        number = f'{number}'
        year = int(number[1:5]) if (inf_sub['type']  == "movie") and (number != "") else None
        # logger.debug(f'Year: {year} Number {number} Title {title}')

        if inf_sub['type'] == "movie":
            res = imdb.get_by_name(title, year, tv=False) if year is not None else imdb.search(title, tv=False)
        else:
            res = imdb.search(title, tv=True)
    except Exception:
        pass
        return None
    
    try:
        results = json.loads(res) if year is not None else json.loads(res)['results']
        # logger.debug(f'Search IMDB json: {str(json.dumps(results, default=str))}')
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
            return f'{search} {number}' if search is not None else None

def make_IMDB_table(title, results, type):
    """Define a IMDB Table."""
    count = 0
    choices = []
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

    rows = []
 
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


### Store aadata test ###
def store_aadata(aadata):
    """Store aadata."""
    temp_dir = tempfile.gettempdir()
    aadata_path = os.path.join(temp_dir, 'sdx-aadata')

    with open(aadata_path, 'wb') as file:
        file.write(aadata)
        file.close()
    logger.debug('Store aadata')

def load_aadata():
    """Load aadata."""
    temp_dir = tempfile.gettempdir()
    aadata_path = os.path.join(temp_dir, 'sdx-aadata')
    if os.path.exists(aadata_path):
        with open(aadata_path, 'r') as aadata_file:
            sdx_aadata = aadata_file.read()
    else:
        return None

    return sdx_aadata