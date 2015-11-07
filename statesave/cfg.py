# -*- coding: utf-8 -*-

import argparse
import configparser
import os
import re
import textwrap

from stateitem import StateItem


date_string = '%Y-%m-%d_%H%M%S'
tab = '    '


def init():
    global ini_file, saves_path, arc_ext, arc_keep, rel_path, sort_files, states, col1

    # init arg parser
    parser = argparse.ArgumentParser(description='''%(prog)s''')
    parser.add_argument("inifile", help="specify ini file to use")
    parser.add_argument("-c", "--create", action="store_true",
        help="create a default config file")
    parser.add_argument("-d", "--destination",
        help="specify destination directory, defaults to the dir of the config file")
    args = parser.parse_args()

    if not os.path.isfile(args.inifile):
        if args.create:
            _createIni(args.inifile)
            print("configuration file created, edit it to add archives")
            exit(0)
        else:
            print(args.inifile, "does not exist, use -c to create a default file")
            exit(1)
    else:
        if args.create:
            print(args.inifile, "already exists")
            exit(1)
        else:
            ini_file = args.inifile

    if args.destination:
        if not os.path.isdir(args.destination):
            print(args.destination, "does not exist or is not a directory")
            exit(1)
        else:
            saves_path = args.destination
    else:
        saves_path = os.path.realpath(os.path.dirname(args.inifile))

    # init config parser
    ini = configparser.ConfigParser()
    ini.optionxform = str
    ini.read(args.inifile)
    ini.sections()

    #self.arc_cmd = ini['STATE']['ArchiveCommand']
    #self.arc_ext = ini['STATE']['ArchiveExtension']
    #if not self.arc_ext.startswith('.'):
        #self.arc_ext = '.' + self.arc_ext
    arc_ext = '.tar.xz'
    arc_keep = max(1, int(ini['STATE']['KeepArchives']))
    rel_path = ini['STATE'].getboolean('HomeRelativePath')
    sort_files = ini['STATE']['SortFiles']
    if sort_files not in ('no', 'age', 'smart'):
        print("SortFiles option must be one of no/age/smart")
        exit(1)

    statesave_dict = dict(ini.items('SAVE'))
    exclude_dict = {}

    for i in statesave_dict:
        path_search = re.findall('^.+?(?=$| +@exclude)|(?<=exclude\:\').+(?=\')', statesave_dict[i])
        if len(path_search) == 2:
            statesave_dict[i] = path_search[0]
            exclude_dict[i] = path_search[1]
        elif len(path_search) > 2:
            print("Error parsing path:", statesave_dict[i])
            exit(1)
    #print(exclude_dict)

    # find existing saves
    save_regex = '^.+?(?=_[0-9_\-]{10,})'
    save_files = [f for f in os.listdir(saves_path) if f.endswith(arc_ext)
        and re.search(save_regex, f) is not None
        and re.search(save_regex, f).group() in statesave_dict]
    save_dict = {}
    for i in save_files:
        name = re.search(save_regex, i).group()
        if name not in save_dict:
            save_dict[name] = [i]
        else:
            save_dict[name].append(i)

    # create list with state objects
    states = []
    for i in statesave_dict:
        states.append(StateItem(i, os.path.expanduser(statesave_dict[i]).rstrip('/'),
        exclude_dict.get(i, None), save_dict.get(i, [])))
    states.sort(key=lambda x: x.name.casefold())

    if states:
        col1 = len(max(states, key=lambda x: len(x.name)).name) + 4


def cyan(string):
    return '\033[96m' + str(string) + '\033[0m'

def green(string):
    return '\033[92m' + str(string) + '\033[0m'

def red(string):
    return '\033[91m' + str(string) + '\033[0m'

def yellow(string):
    return '\033[93m' + str(string) + '\033[0m'


def _createIni(ini_path):
    ini = configparser.ConfigParser()
    ini.optionxform = str
    ini['STATE'] = {}
    #ini['STATE']['ArchiveCommand'] = 'tar'
    #ini['STATE']['ArchiveExtension'] = 'tar.xz'
    ini['STATE']['KeepArchives'] = '5'
    ini['STATE']['HomeRelativePath'] = 'no'
    ini['STATE']['SortFiles'] = 'smart'
    ini['SAVE'] = {}
    ini['SAVE']['#name 1'] = '/foo/dir'
    ini['SAVE']['#name 2'] = '~/foo/singlefile'
    ini['SAVE']['#name 3'] = '~/foo/dir @exclude:\'regex\''
    with open(ini_path, 'w') as inifile:
        ini.write(inifile)
        inifile.write(textwrap.dedent('''
            # KeepArchives = n
            #     n: keep this many archives per save state, oldest archives
            #        will be deleted
            # HomeRelativePath = yes/no
            #     yes: truncate /home/user/foo to /foo inside archives
            # SortFiles = no/age/smart
            #     age: oldest first, can reduce differences between archives
            #     smart: group similar files, potentially better compression
        '''))
