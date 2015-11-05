#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import fileinput
import re
import subprocess


files_first = [
    'txt', 'readme', 'md', 'debian', 'tex', 'log',
    'cfg', 'conf', 'ini', 'rc', 'csv', 'sh', 'bat',
    'htm', 'html', 'css', 'js', 'json', 'xml', 'rtf',
    'lua', 'py', 'c', 'cc', 'cpp', 'h', '*text*', 'pdf',
    'bin', 'bin32', 'bin64', 'x86', 'x86_64', 'x64', 'i386', 'amd64', 'so',
    '*bin*', 'exe', 'dll']
files_last = ['gif', 'jpeg', 'jpg', 'png',
    'flac', 'm4a', 'mp3', 'ogg', 'opus',
    'flv', 'mkv', 'mp4', 'webm',
    '7z', 'bz2', 'gz', 'jar', 'rar', 'tgz', 'wad', 'xz', 'zip']


middleidx = len(files_first)
lastidx = middleidx + 1
file_id_dic = {}
file_id_fails = 0


def arcsort(file_list, id_unknown=False):
    files_dic = {}
    for i in range(len(file_list)):
        ext_search = re.search('(?P<basename>[^/\.]+)(?:\.)(?P<ext>[a-zA-Z0-9_~\.]+)$', file_list[i])

        if ext_search == None:
            base_search = re.search('([^/]+?)(?=$)', file_list[i])
            basename = str.lower(base_search.group())
            ext = '*noext*'
        else:
            basename = str.lower(ext_search.group('basename'))
            ext = str.lower(ext_search.group('ext'))

        # transform extensions for sorting
        if ext.startswith('so.'):
            ext = 'so'
        ext = ext.rstrip('~')
        if ext.endswith(('.bak', '.old')):
            ext = ext[0:-4]

        if ext in files_first:
            sortidx = "{:0>3}".format(files_first.index(ext))
        elif ext in files_last:
            sortidx = "{:0>3}".format(lastidx + files_last.index(ext))
        else:
            if id_unknown:
                sortidx = "{:0>3}".format(_file_id(file_list[i], ext))
            else:
                sortidx = "{:0>3}".format(middleidx)

        # stick the filename into the match dic to find matches
        # between foo.ext and foo.ext.old etc.
        filename = basename + '.' + ext
        if filename not in files_dic:
            sortname = str.lower(file_list[i])
            files_dic[filename] = sortname
        else:
            sortname = files_dic[filename]

        file_list[i] = ([sortidx, ext, sortname, file_list[i]])

    files_dic.clear()
    file_list.sort()
    return [i[3] for i in file_list]


def _file_id(file_handle, ext):
    if ext != '*noext*' and ext in file_id_dic:
        #print("used dic entry:", ext, file_handle, end='')
        return file_id_dic[ext]
    global file_id_fails
    if file_id_fails >= 10:
        return middleidx

    file_handle = file_handle.rstrip('\n')

    try:
        fileid_output = subprocess.check_output(['file', '-b', file_handle],
            stderr=subprocess.STDOUT)
    except:
        #print("error calling file tool", ext, file_handle)
        file_id_fails += 1
        return middleidx

    id_search = re.search('ASCII|text|ELF|executable', str(fileid_output))
    if id_search is None:
        #print("NOID", ext, file_handle, str(fileid_output))
        file_id_dic[ext] = middleidx
        return middleidx
    elif id_search.group() == 'ELF' or id_search.group() == 'executable':
        #print("BIN", ext, file_handle, str(fileid_output))
        file_id_dic[ext] = files_first.index('*bin*')
        return files_first.index('*bin*')
    else:
        #print("TEXT", ext, file_handle, str(fileid_output))
        file_id_dic[ext] = files_first.index('*text*')
        return files_first.index('*text*')


def main():
    file_list = []
    for line in fileinput.input():
        file_list.append(line)
    file_list = arcsort(file_list, id_unknown=True)
    for line in file_list:
        print(line, end='')
    return 0


if __name__ == '__main__':
    main()
