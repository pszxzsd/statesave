# -*- coding: utf-8 -*-

import os
import re
#import shutil
import tarfile
import time

from arcsort import arcsort
import cfg

class StateItem(object):
    def __init__(self, name, path, exclude, saves):
        self.name = name
        self.path = path
        self.exclude = exclude
        self.saves = sorted(saves)

        self._checked_files = False
        self.files_dirs = None

        self._checked_change_date = False
        self._epoch = 0
        self._date = None

        if self.saves:
            self.save_epoch = self._getSaveDate()
        else:
            self.save_epoch = 0


    def createArchive(self, show_progress=False):
        def blankLine():
            # TODO: use term width
            print('\r' + 75 * ' ', end='')

        arc_name = self.name + '_' + self.date() + cfg.arc_ext
        arc_path = os.path.join(cfg.saves_path, arc_name)
        if not os.path.isfile(arc_path):
            if self._checked_files is False:
                self.files_dirs = self._getFilesDirs()

            # sort file list
            if cfg.sort_files == 'age':
                self.files_dirs = self._sortByAge(self.files_dirs)
            elif cfg.sort_files == 'smart':
                self.files_dirs = arcsort(self.files_dirs, id_unknown=True)

            try:
                with tarfile.open(arc_path, 'w:xz') as tar:

                    if cfg.rel_path is True:
                        for i in range(len(self.files_dirs)):
                            self.files_dirs[i] = (self.files_dirs[i], re.sub('^' + os.environ['HOME'], '', self.files_dirs[i]))

                    total = len(self.files_dirs)
                    count = 0
                    width = len(str(total))

                    if show_progress:
                        blankLine()

                    for fname in self.files_dirs:
                        count += 1

                        if show_progress:
                            print("\r{} {:.<{col2}} {}{:{w}}/{}".format(
                                self.name, '', cfg.yellow('files: '), cfg.yellow(count), cfg.yellow(total), col2=cfg.col1-len(self.name), w=width), end='')

                        if cfg.rel_path is True:
                            tar.add(fname[0], arcname=fname[1])
                        else:
                            tar.add(fname)

                    if show_progress:
                        blankLine()
                        print("\r{} {:.<{col2}} {}".format(self.name, '', cfg.cyan('created'), col2=cfg.col1-len(self.name)))
                self.saves.append(arc_name)
            except KeyboardInterrupt as e:
                os.remove(arc_path)
                print("\nKeyboardInterrupt caught")
                exit(1)


    def date(self):
        if self._checked_change_date is False and os.path.isdir(self.path):
            self._epoch, self._date = self._getChangeDate()
            self._checked_change_date = True
        return self._date


    def deleteArchives(self):
        for f in self.saves:
            if not os.path.isfile(os.path.join(cfg.saves_path, f)):
                raise Exception('Saves list file mismatch')
        if len(self.saves) > cfg.arc_keep:
            for i in range(len(self.saves) - cfg.arc_keep):
                os.remove(os.path.join(cfg.saves_path, self.saves[i]))


    def epoch(self):
        if self._checked_change_date is False and os.path.exists(self.path):
            self._epoch, self._date = self._getChangeDate()
            self._checked_change_date = True
        return self._epoch


    def _getChangeDate(self):
        if self._checked_files is False:
            self.files_dirs = self._getFilesDirs()
        newest_file = max(self.files_dirs, key=lambda x: os.path.getmtime(x))
        date = time.strftime(cfg.date_string,
            time.localtime(os.path.getmtime(newest_file)))
        # use just generated date string for epoch calculation to remove
        # difference between date string on archive and real epoch float
        # of newest file
        epoch = time.mktime(time.strptime(date, cfg.date_string))
        return epoch, date


    def _getFilesDirs(self):
        # TODO: return only empty dirs
        if os.path.isdir(self.path):
            files_dirs = [os.path.join(dirpath, f) for dirpath, dirname, filename
                in os.walk(self.path) for f in filename]
            if self.exclude is not None:
                files_dirs = [f for f in files_dirs if re.search(self.exclude, f) is None]
        elif os.path.isfile(self.path):
            files_dirs = [self.path]
        else:
            files_dirs = None
        self._checked_files = True
        return files_dirs


    def _getSaveDate(self):
        date_regex = '(?<=[^_]_)[0-9_\-]{10,}(?=' \
            + str.replace(cfg.arc_ext, '.', '\.') + '$)'
        save_date_string = re.search(date_regex, self.saves[-1]).group()
        epoch = time.mktime(time.strptime(save_date_string, cfg.date_string))
        return epoch


    def _sortByAge(self, files):
        age_list = [(os.path.getmtime(x), x) for x in files]
        age_list.sort()
        return [i[1] for i in age_list]
