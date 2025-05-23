# Copyright (C) 2024 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import sys
import tempfile
import argparse
import logging
from sdx_dl.sdxconsole import console
from sdx_dl.sdxclasses import ChkVersionAction, ConfigManager, ViewConfigAction, SaveConfigAction, SetConfigAction, ResetConfigAction, validate_proxy
from importlib.metadata import version
from rich.logging import RichHandler
from rich.traceback import install
install(show_locals=True)

__all__ = ["args", "logger"]

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
    config_opts.add_argument('--view-config', '-vc', action=ViewConfigAction, help="View config file")
    config_opts.add_argument('--save-config', '-sc', action=SaveConfigAction, help="Save options to config file")
    config_opts.add_argument('--load-config', '-lc',action='store_true', default=False, help="Load config file options")
    
    config_opts.add_argument('--config', '-c',
                            action=SetConfigAction,
                            choices=["quiet", "verbose", "force", "no_choose", "no_filter", "nlines", "path", "proxy", "Season", "imdb"],
                            nargs='?',metavar="o",help="Save an option[o] to config file")
    config_opts.add_argument('--reset', '-r',
                            action=ResetConfigAction,
                            choices=["quiet", "verbose", "force", "no_choose", "no_filter", "nlines", "path", "proxy", "Season", "imdb"],
                            metavar="o",help="Reset an option[o] in the config file")
 
    return parser

def create_logger(level:str = "DEBUG", verbose:bool=False):

    # Setting logger
    levels = ["CRITICAL", "ERROR", "WARNING","INFO", "DEBUG"]
    LOGGER_LEVEL = levels[4]
    LOGGER_FORMATTER_LONG = logging.Formatter('%(asctime)-12s %(levelname)-6s %(message)s', '%Y-%m-%d %H:%M:%S')
    LOGGER_FORMATTER_SHORT = logging.Formatter(fmt='%(message)s', datefmt="[%X]")

    level = level if level in levels else LOGGER_LEVEL
    temp_log_dir = tempfile.gettempdir()
    file_log = os.path.join(temp_log_dir, 'subdx-dl.log') 

    global logger
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    
    if not verbose:
        logfile = logging.FileHandler(file_log, mode='w', encoding='utf-8')
        logfile.setFormatter(LOGGER_FORMATTER_LONG)
        logfile.setLevel(level)
        logger.addHandler(logfile)
    else:
        console = RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)
        console.setFormatter(LOGGER_FORMATTER_SHORT)
        console.setLevel(level)
        logger.addHandler(console)

parser = create_parser()
args = parser.parse_args()

if args.load_config:
    config = ConfigManager()
    if config.exists and config.hasconfig:
        copied_args = args.__dict__.copy()
        new_args = config.merge_config(copied_args)

        for k, v in new_args.items():
            args.__setattr__(k, v)

if args.verbose: args.__setattr__("quiet", True)
create_logger(verbose=args.verbose)

if args.load_config:
     logger.debug("Config loaded!")

if args.path:
    if not (os.path.isdir(args.path) and os.access(args.path, os.W_OK)):
        if args.quiet:
            logger.debug(f'Directory {args.path} do not exists')
        else:
            console.print(":no_entry:[bold red] Directory:[yellow] " + args.path + "[bold red] do not exists or don't have access[/]",
                        new_line_start=True, emoji=True) 
        sys.exit(1)

if (args.proxy and not validate_proxy(args.proxy)):
    if args.quiet:
        logger.debug(f'Incorrect proxy setting. Only http, https or IP/domain:PORT is accepted')
    else:
        console.print(":no_entry:[bold red] Incorrect proxy setting:[yellow] " + args.proxy + "[/]",
                    new_line_start=True, emoji=True)
    sys.exit(1)
