#!/usr/bin/env python
"""
This script provides a command-line interface for revising the current revision
of one or more documents. It currently supports three kinds of operations:
   - removes one or more select macros from the current revision of each of
     one or more documents, saving each result in a separate revision file
   - renders-out one or more select macros from the current revision of each
     of one or more documents, saving each result in a separate revision file
   - takes one or more revision files and uses each to create a new revision
     for its associated document
"""
import os
import time
from functools import partial, wraps
from http import HTTPStatus
from pathlib import Path
from subprocess import run
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit

import click
import requests
import yaml


HTTP_STATUS_DESCRIPTIONS = dict((s, s.description) for s in HTTPStatus)


class ReviseException(click.ClickException):
    def show(self, file=None):
        click.secho(f"Error: {self.format_message()}", file=file, fg="red")


def retry(
    func=None, delays=(1, 2, 4), errors=(requests.ConnectionError, requests.Timeout)
):
    """
    The default errors are only safe for the safe HTTP methods, i.e. GET, HEAD,
    and OPTIONS. Use "errors=requests.ConnectTimeout" for non-safe HTTP methods.
    """
    if func is None:
        return partial(retry, delays=delays, errors=errors)

    @wraps(func)
    def wrapper(*args, **kwargs):
        delays_stack = list(reversed(delays))
        while True:
            try:
                return func(*args, **kwargs)
            except errors:
                if not delays_stack:
                    raise
                time.sleep(delays_stack.pop())

    return wrapper


def with_logger(func=None, log_path=None):
    if func is None:
        return partial(with_logger, log_path=log_path)

    @wraps(func)
    def wrapper(*args, **kwargs):
        with log_path.open("w") as log_file:

            def log(text, **kwargs):
                if "fg" not in kwargs:
                    kwargs["fg"] = "green"
                click.secho(text, **kwargs)
                click.secho(text, file=log_file, **kwargs)

            return func(*args, **kwargs, log=log)

    return wrapper


# Let's define more robust HTTP functions, ones that retry up to 3 times.
get = retry(requests.get)
post = retry(requests.post, errors=requests.ConnectTimeout)


@click.group()
def revise():
    pass


@revise.command()
@click.option("-c", "--config", "config_path", default="./revise.config.yaml")
@click.option("-o", "--output-dir", default="results")
def render(config_path, output_dir):
    handle_edit("render", config_path, output_dir)


@revise.command()
@click.option("-c", "--config", "config_path", default="./revise.config.yaml")
@click.option("-o", "--output-dir", default="results")
def remove(config_path, output_dir):
    handle_edit("remove", config_path, output_dir)


@revise.command()
@click.argument("dir", required=True)
def commit(dir):
    handle_commit(dir)


@revise.command()
@click.argument("dir", required=True)
@click.option("--no-pager", is_flag=True)
def diff(dir, no_pager):
    dir = Path(dir)
    if not dir.exists():
        raise ReviseException(f"{dir} does not exist")
    pager = "--no-pager" if no_pager else "--paginate"
    cmd = f"git {pager} diff --no-index {{ref}} {{rev}}"
    for rev in dir.rglob(f"rev.html"):
        ref = rev.with_name("ref.html")
        run(cmd.format(rev=rev, ref=ref).split())


def handle_commit(dir):
    token = get_token()
    dir = Path(dir)
    click.secho(f"commit: {dir}", fg="green")
    if not dir.exists():
        raise ReviseException(f"{dir} does not exist")
    log_path = dir / "commit.log"
    click.secho(f"log: {log_path}")
    with_logger(do_commit, log_path=log_path)(dir, token)


def do_commit(dir, token, log):
    for rev in dir.rglob(f"rev.html"):
        log(f"{rev}")
        metadata = get_metadata(rev.with_name("metadata.yaml"), log)
        if not metadata:
            continue
        last_modified = metadata["last_modified"]
        parts = urlsplit(metadata["url"])
        doc = parts.path
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        headers = {
            "Authorization": f"Token {token}",
            "If-Unmodified-Since": last_modified,
        }
        try:
            with rev.open() as f:
                rev_text = f.read().strip()
        except OSError as e:
            log(f"error: {str(e)}")
            continue
        resp = post(url, data=dict(content=rev_text), headers=headers)
        if resp.status_code != HTTPStatus.CREATED:
            message = resp.text or HTTP_STATUS_DESCRIPTIONS.get(resp.status_code, "")
            log(
                f"error: while trying to create revision for {doc} "
                f"({resp.status_code} - {message})",
                fg="red",
            )
            continue
        log(f'- created {resp.headers.get("Location")}')


def handle_edit(cmd, config_path, output_dir):
    output_dir = Path(output_dir)
    config_path = Path(config_path)
    # Create a fresh directory for the results.
    output_dir = get_fresh_output_dir(output_dir)
    click.secho(f"output directory: {output_dir}")
    output_dir.mkdir(parents=True)

    log_path = output_dir / f"{cmd}.log"
    click.secho(f"log: {log_path}")
    with_logger(do_edit, log_path=log_path)(cmd, config_path, output_dir)


def do_edit(cmd, config_path, output_dir, log):
    # Get the configured documents and macros.
    log(f"configuration: {config_path}")
    config = get_config(config_path)
    site = config["site"]
    macros = config["macros"][cmd]
    if not macros:
        # If no macros have been defined for this command, we can't do anything.
        raise ReviseException(f'no macros have been configured for "{cmd}"')
    log(f"{cmd} macros:")
    for macro in macros:
        log(f"- {macro}")
    documents = config["documents"]

    qs = urlencode(dict(mode=cmd, macros=",".join(macros)))

    for doc in documents:
        ref_url = f"{urljoin(site, doc)}$revision"
        rev_url = f"{ref_url}?{qs}"

        try:
            ref_text, rev_text, last_modified = get_ref_and_rev(ref_url, rev_url)
        except requests.HTTPError as e:
            log(f"error: while getting data for {doc} ({str(e)})", fg="red")
            continue

        if rev_text == ref_text:
            # The render or removal of these macros yielded a result that
            # was no different from the current content, so let's note that
            # and skip saving the results.
            log(f"doc: {doc} (no change)", fg="white")
            continue

        log(f"doc: {doc}")

        doc_dir = output_dir / doc.strip("/").replace("/", ".")
        ref_path = doc_dir / "ref.html"
        rev_path = doc_dir / "rev.html"
        metadata_path = doc_dir / "metadata.yaml"

        doc_dir.mkdir()

        for path, text in ((ref_path, ref_text), (rev_path, rev_text)):
            log(f"- {path}")
            with path.open("w") as f:
                f.write(text)

        log(f"- {metadata_path}")
        with metadata_path.open("w") as f:
            yaml.dump(dict(url=rev_url, last_modified=last_modified), f)


def get_ref_and_rev(ref_url, rev_url):
    done = False
    while not done:
        ref_resp = get(ref_url)
        ref_resp.raise_for_status()
        ref_last_modified = ref_resp.headers.get("last-modified")
        rev_resp = get(rev_url)
        rev_resp.raise_for_status()
        rev_last_modified = rev_resp.headers.get("last-modified")
        done = ref_last_modified == rev_last_modified
    return (ref_resp.text, rev_resp.text, rev_last_modified)


def get_fresh_output_dir(output_dir):
    while output_dir.exists():
        try:
            new_suffix = f'.{int(output_dir.suffix.lstrip(".")) + 1}'
        except ValueError:
            new_suffix = ".1"
        output_dir = output_dir.with_suffix(new_suffix)
    return output_dir


def get_config(path):
    try:
        with path.open() as f:
            config = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        raise ReviseException(str(e))
    for s in ("site", "documents", "macros"):
        if not config.get(s):
            raise ReviseException(f'{path} has no "{s}" key or its value is empty')
    macros = config["macros"]
    if all(s not in macros for s in ("render", "remove")):
        raise ReviseException(
            f'the "macros" block within {path} must '
            'contain a "render" and/or "remove" block'
        )
    for s in ("render", "remove"):
        if (s in macros) and not macros[s]:
            raise ReviseException(f'the "{s}" block within {path} is empty')
    # Let's ensure we use the wiki site (mainly so POST's don't redirect).
    site = config["site"]
    status_url = urljoin(site, "_kuma_status.json")
    resp = get(status_url)
    if resp.status_code != requests.codes.ok:
        raise ReviseException(f"{site} doesn't seem to be an MDN site")
    config["site"] = resp.json()["settings"]["WIKI_SITE_URL"]
    return config


def get_metadata(path, log):
    try:
        with path.open() as f:
            metadata = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        log(f"error: {str(e)}", fg="red")
        return None
    for k in ("last_modified", "url"):
        if not metadata.get(k):
            log(f'error: {path} has no "{k}" key or its value is empty', fg="red")
            return None
    return metadata


def get_token():
    revise_token = Path.home() / ".revise" / "token"
    if revise_token.exists():
        token = revise_token.read_text().strip()
    else:
        token = os.getenv("MDN_REVISE_TOKEN")
    if not token:
        raise ReviseException(
            f"You must provide your personal authorization token via a "
            f'"{revise_token}" file or the "MDN_REVISE_TOKEN" environment '
            "variable."
        )
    return token
