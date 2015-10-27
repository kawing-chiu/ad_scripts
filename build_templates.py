#!/usr/bin/env python2
# encoding: utf-8
"""Build html template for pages with resources inlined.

**EXPERIMENTAL**
"""
from __future__ import print_function, division, unicode_literals
from io import open
from subprocess import Popen, PIPE
import platform
import os
from time import sleep


# TODO: move all of these address things into a common config place
DEBUG = os.environ.get('FRONTEND_DEBUG') == 'on'
HOST = platform.node()
if DEBUG:
    PORT = 8100
else:
    PORT = 8000
TORNADO_SERVER = 'http://{}:{}/'.format(HOST, PORT)

BUILD_DIR = os.path.join(os.path.dirname(__file__), 'build')

PAGE_LIST = [
    ('/', 'index'),
]


TEMPLATE = """
{{% extends 'base.html' %}}
{{% block styles %}}<style>{style}</style>{{% end %}}
{{% block loadCSS %}}<script id="loadcss">{load_css_func}
loadCSS('/static/vendor.css');
loadCSS('/static/app.css');
</script>{{% end %}}
""".strip()

LOAD_CSS_FUNC = """
function loadCSS(href) {
  'use strict';
  var link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = href;
  link.media = 'only foo';

  var place = document.getElementById('loadcss');
  place.parentNode.insertBefore(link, place);

  var sheets = document.styleSheets;
  link.testReady = function(cb) {
    var ready = false;
    for (var i = 0; i < sheets.length; i++) {
      var sheet = sheets[i];
      var rules = sheet.cssRules || sheet.rules;
      if (sheet.href &&
          rules.length > 0 &&
          sheet.href.length >= href.length &&
          sheet.href.indexOf(href) == sheet.href.length - href.length) {
        ready = true;
        console.log(href + " ready.");
      }
    }
    if (ready) {
      cb();
    } else {
      setTimeout(function() {
        link.testReady(cb);
      }, 5);
    }
  };
  link.testReady(function() {
    link.media = 'all';
  });
  return link;
}
"""

def _process_js_func(func):
    lines = func.split('\n')
    lines = [l.strip() for l in lines]
    out_str = ' '.join(lines)
    return out_str

def _parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="")
    args = parser.parse_args()
    return args

def run():
    args = _parse_args()

    try:
        tornado = Popen(['python', '../static-server.py'])
        node = Popen(['node', 'build/server/server.js'])

        sleep(1)

        for url, page_name in PAGE_LIST:
            out_file = os.path.join(BUILD_DIR, page_name + '.html')
            # useless, since template is cached by tornado
            os.unlink(out_file)

            url = TORNADO_SERVER[:-1] + url
            phantom = Popen(['phantomjs', 'ph.js', url], stdout=PIPE)
            styles = phantom.stdout.readline().rstrip()
            load_css_func = _process_js_func(LOAD_CSS_FUNC)
            template = TEMPLATE.format(style=styles, load_css_func=load_css_func)

            with open(out_file, 'w') as f:
                f.write(template)
                print("out file:", out_file)
            phantom.communicate()
    finally:
        try:
            if tornado.poll() is None:
                tornado.terminate()
        except Exception:
            pass
        try:
            if node.poll() is None:
                node.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    run()


