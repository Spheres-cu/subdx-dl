# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import tempfile
import argparse
import logging
from sdx_dl.sdxclasses import ChkVersionAction, CheckConfigAction, CreateConfig
from importlib.metadata import version
from rich.logging import RichHandler
from rich.traceback import install
install(show_locals=True)

def create_parser():
    parser = argparse.ArgumentParser(prog='sdx-dl',
    formatter_class=argparse.RawTextHelpFormatter,
    usage="sdx-dl [options] search",
    description='A cli tool for download subtitle from https://www.subdivx.com with the better possible matching results.',
    epilog='Project issues:https://github.com/Spheres-cu/subdx-dl/issues\n\
            \nUsage examples:https://github.com/Spheres-cu/subdx-dl#examples\n\n'
    )

    parser.add_argument('search', type=str,help="file, directory or movie/series title or IMDB Id to retrieve subtitles")

    parser.add_argument('--quiet', '-q', action='store_true',default=False, help="No verbose mode")
    parser.add_argument('--verbose', '-v', action='store_true',default=False, help="Be in verbose mode")
    parser.add_argument('--force', '-f', action='store_true',default=False, help="override existing file")
    parser.add_argument('--no-choose', '-nc', action='store_true', default=False, help="No Choose sub manually")
    parser.add_argument('--no-filter', '-nf', action='store_true',default=False, help="Do not filter search results")
    parser.add_argument('--nlines', '-nl', type=int, choices=[5, 10, 15, 20], default=False, nargs='?', const=10,
                        help="Show nl(5,10,15,20) availables records per screen. Default 10 records.", metavar="")
    parser.add_argument('--version', '-V', action='version', version=f'subdx-dl {version("subdx-dl")}', help="Show program version")
    parser.add_argument('--check-version', '-cv', action=ChkVersionAction, help="Check for new version")
                        
    ## Download opts group
    download_opts = parser.add_argument_group('Download')
    download_opts.add_argument('--path', '-p', type=str, help="Path to download subtitles")
    download_opts.add_argument('--proxy', '-x', type=str, help="Set a http(s) proxy(x) connection", metavar="x")

    ## Search opts group
    search_opts = parser.add_argument_group('Search by')
    search_opts.add_argument('--Season', '-S', action='store_true',default=False, help="Search by Season")
    search_opts.add_argument('--kword','-k',type=str,help="Add keywords to search among subtitles descriptions", metavar="kw")
    search_opts.add_argument('--title','-t',type=str,help="Set the title to search", metavar="t")
    search_opts.add_argument('--imdb', '-i', action='store_true',default=False, help="Search first for the IMDB id or title")

    ## Config opts group
    config_opts = parser.add_argument_group('Config').add_mutually_exclusive_group()
    config_opts.add_argument('--show-config', '-sc', action=CheckConfigAction, help="Show config file")
    config_opts.add_argument('--make-config', '-mc', action=CreateConfig, help="Make a config file")

    return parser

parser = create_parser()
args = parser.parse_args()

# Setting logger
LOGGER_LEVEL = logging.DEBUG
LOGGER_FORMATTER_LONG = logging.Formatter('%(asctime)-12s %(levelname)-6s %(message)s', '%Y-%m-%d %H:%M:%S')
LOGGER_FORMATTER_SHORT = logging.Formatter(fmt='%(message)s', datefmt="[%X]")

temp_log_dir = tempfile.gettempdir()
file_log = os.path.join(temp_log_dir, 'subdx-dl.log')

global logger
logger = logging.getLogger(__name__)

def setup_logger(level):

    logger.setLevel(level)

setup_logger(LOGGER_LEVEL if not args.verbose else logging.DEBUG)

logfile = logging.FileHandler(file_log, mode='w', encoding='utf-8')
logfile.setFormatter(LOGGER_FORMATTER_LONG)
logfile.setLevel(logging.DEBUG)
logger.addHandler(logfile)

if not args.quiet:
    console = RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)
    console.setFormatter(LOGGER_FORMATTER_SHORT)
    console.setLevel(logging.INFO if not args.verbose else logging.DEBUG)
    logger.addHandler(console)


