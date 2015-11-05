#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cfg

def main():
    cfg.init()

    print("Config file:", cfg.ini_file)
    print("Saves path:", cfg.saves_path)

    for i in cfg.states:
        print("{} {:.<{col2}} ".format(i.name, '', col2=cfg.col1-len(i.name)), end='')
        if i.epoch() == 0:
            print(cfg.red("no dir '{}'".format(i.path)))
        elif i.epoch() > i.save_epoch:
            print(cfg.cyan("creating new archive"), end='')
            i.createArchive(show_progress=True)
        else:
            print(cfg.green("current"))
        if len(i.saves) > cfg.arc_keep:
            i.deleteArchives()

    return 0

if __name__ == '__main__':
    main()

