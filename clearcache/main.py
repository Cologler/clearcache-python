# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import os
import sys
import traceback
from datetime import timedelta, datetime

import click
from click_anno import click_app
from fsoopify import FileInfo, Path, DirectoryInfo, NodeType

def get_conf_file() -> FileInfo:
    path = Path.from_home() / '.config' / 'clearcache' / 'conf.json'
    return FileInfo(path)

def resolve_path(path: str):
    path = os.path.expandvars(path)
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    return path

def remove_expired_files(path: str, before: datetime):
    path = resolve_path(path)

    dir_info = DirectoryInfo(path)
    if dir_info.is_directory():
        for item in dir_info.iter_items(depth=99999):
            if item.node_type == NodeType.file:
                atime_int = os.path.getatime(item.path)
                access_time = datetime.fromtimestamp(atime_int)
                if before > access_time:
                    item.delete()
                    click.echo(click.style('Removed', fg='yellow') + ' ', nl=False)
                else:
                    click.echo(click.style('Skiped', fg='cyan') + '  ', nl=False)
                click.echo(f'{item.path!s}.')

@click_app
class Cache:
    def run(self, days=30):
        'begin clear cache.'

        before = datetime.now() - timedelta(days=days)
        conf_file = get_conf_file()
        if conf_file.is_file():
            conf = conf_file.load()
            for path in conf['paths']:
                remove_expired_files(path, before)

    class Path:
        'show or configure paths.'

        def ls(self):
            conf_file = get_conf_file()
            if conf_file.is_file():
                conf = conf_file.load()
                for path in conf['paths']:
                    rpath = resolve_path(path)
                    if rpath != path:
                        click.echo(f'{path} -> {rpath}', nl=False)
                    else:
                        click.echo(path, nl=False)
                    if os.path.isabs(rpath):
                        click.echo(' ({})'.format(click.style('Folder', fg='bright_green')))
                    elif os.path.isabs(rpath):
                        click.echo(' ({})'.format(click.style('File', fg='bright_green')))
                    else:
                        click.echo(' ({})'.format(click.style('Not exists', fg='red')))
            else:
                click.echo('path list is empty.')

        def add(self, path):
            conf_file = get_conf_file()
            conf_file.get_parent().ensure_created()
            with conf_file.load_context(lock=True) as ctx:
                ctx.save_on_exit = True
                if ctx.data is None:
                    ctx.data = {'paths': []}
                ctx.data['paths'].append(path)

        def rm(self, path):
            conf_file = get_conf_file()
            if conf_file.is_file():
                with conf_file.load_context(lock=True) as ctx:
                    ctx.save_on_exit = True
                    try:
                        ctx.data['paths'].remove(path)
                        return click.echo('Removed.')
                    except ValueError:
                        pass
            click.echo('No such path found.')


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        Cache(argv[1:])
    except Exception: # pylint: disable=W0703
        traceback.print_exc()

if __name__ == '__main__':
    main()
