# -*- coding: utf-8 -*-

from .controllers import app
import re

def render_post_content(content):
    pattern = re.compile(r"(@[^() ]+?)\(([^ )]+?)\)")
    for nickname, user_id in pattern.findall(content):
        origin = nickname + '(' + user_id + ')'
        transformed = '<a href="/user/' + user_id + '">' + nickname + '</a>'
        content = content.replace(origin, transformed)
    return content


app.jinja_env.globals.update(render_post_content=render_post_content)
app.jinja_env.globals.update(len=len)