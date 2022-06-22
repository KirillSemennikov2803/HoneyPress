#!/usr/bin/env python3
from flask import Flask, render_template, request

application = Flask(__name__)


def sanitize(inputstr):
    sanitized = inputstr
    badstrings = [
        ";",
        "$",
        "&&",
        "../",
        "<",
        ">",
        "%3C",
        "%3E",
        "'",
        "--",
        "1,2",
        "\x00",
        "`",
        "(",
        ")",
        "file://",
        "input://",
    ]
    for badstr in badstrings:
        if badstr in sanitized:
            sanitized = sanitized.replace(badstr, "")
    return sanitized


@application.route("/")
def index():
    return render_template("index.html"), 200


if __name__ == "__main__":
    application.run(host="0.0.0.0:1337", threaded=True)
