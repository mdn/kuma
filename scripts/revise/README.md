## Introduction

`revise` is a command-line tool for revising the raw HTML of MDN documents.

## Installation

- Make sure you have Python 3 installed.
- Install `poetry` -- https://python-poetry.org/docs/#installation

- Assuming you're starting from the root directory of your local clone of the `kuma` repo, go to the `scripts/revise` sub-directory (`cd scripts/revise`).
- Create a virtual environment containing all of the dependencies required by `revise` (`poetry install`).
- Open a shell with that virtual environment activated (`poetry shell`).
- Make sure you can run `revise` (`revise --help`).

## Usage

### Configuration
- Create a project directory, for example `js-docs`.
- Create a `revise` configuration file within that `js-docs` project directory (`revise.config.yaml` is the filename that `revise` will find and use by default, but you can choose whatever name you'd like). The configuration file tells `revise` several things:
   - the site you're working on (e.g., `https://wiki.developer.mozilla.org` or `https://wiki.developer.allizom.org` or `http://wiki.localhost.org:8000`)
   - the documents you're revising within the project
   - the macros you'd like to render and/or remove
- Here's an example configuration file:
```yaml
site: http://wiki.developer.mozilla.org
documents:
    - /en-US/docs/Web/JavaScript/Reference/Operators/typeof
    - /en-US/docs/Web/JavaScript/Reference/Operators/this
    - /en-US/docs/Web/JavaScript/Reference/Operators/new
macros:
    render:
        - jsxref
        - domxref
        - bug
    remove:
        - Gecko
        - geckoRelease
        - Note
```
- Create and configure your **API token**. If you don't, your `revise commit` command will complain.
    - Create a new token for yourself via the Django admin
    - Copy the token and inform `revise` in one of two ways:
        - via the `MDN_REVISE_TOKEN` environment variable
        - save it in `$HOME/.revise/token`

### Render
- `cd js-docs`
- Let's render-out (`revise render`) the selected macros (the ones listed under the `render` section of your configuration file) for each of the documents as specified within the configuration file, with the results created within a `results` directory by default. Do a `revise render --help` to see how you could specify a different results directory and/or configuration file.
- When you run `revise render`, you'll see output like this:
```
   output directory: results
   log: results/render.log
   configuration: revise.config.yaml
   render macros:
   - jsxref
   - domxref
   - bug
   doc: /en-US/docs/Web/JavaScript/Reference/Operators/typeof
   - results/en-US.docs.Web.JavaScript.Reference.Operators.typeof/ref.html
   - results/en-US.docs.Web.JavaScript.Reference.Operators.typeof/rev.html
   - results/en-US.docs.Web.JavaScript.Reference.Operators.typeof/metadata.yaml
   doc: /en-US/docs/Web/JavaScript/Reference/Operators/this
   - results/en-US.docs.Web.JavaScript.Reference.Operators.this/ref.html
   - results/en-US.docs.Web.JavaScript.Reference.Operators.this/rev.html
   - results/en-US.docs.Web.JavaScript.Reference.Operators.this/metadata.yaml
   doc: /en-US/docs/Web/JavaScript/Reference/Operators/new
   - results/en-US.docs.Web.JavaScript.Reference.Operators.new/ref.html
   - results/en-US.docs.Web.JavaScript.Reference.Operators.new/rev.html
   - results/en-US.docs.Web.JavaScript.Reference.Operators.new/metadata.yaml
   ```
- Here's the meaning of each of those files:
   - `rev.html`: the modified content, i.e. the content with the macros either rendered-out or removed, depending on whether you did a `revise render` or a `revise remove` command. This content has **not** been committed. It only shows what the content would be if you committed the result.
   - `ref.html`: the baseline content, i.e. the content without any modifications (the raw HTML of the document's current revision), for comparison purposes, so you can do a `diff rev.html ref.html`
   - `metadata.yaml`: metadata later used by the `revise` tool when doing a `revise commit`

### Remove

- You can also remove your selected macros (the ones listed under the `remove` section of your configuration file) from your selected douments using the `revise remove` command.
- It will create the same kinds of files (`rev.html`, `ref.html`, and `metadata.yaml`) for each of your selected documents, but of course this time it will remove any trace of each of your selected macros from each of your selected documents (without committing the results, of course).

### Diff

- After running `revise remove` or `revise render` you'll probably want to visually check the differences between each of the `rev.html` and `ref.html` pairs in your results directory. You can do this using `revise diff <results-dir>` or in this case `revise commit results`.
- It uses `git diff`, so assumes you have `git` installed.
- By default it paginates the results (i.e., the results are piped into `less`) so you can view a page of differences at a time. Remember that each time you reach the end of the differences for a pair of files, you can use the `q` command to move to the differences for the next pair of files.
- If you'd prefer to see all the differences for all pairs of files at once, you can use `revise diff --no-pager <results-dir>`.

### Commit

- You can keep running `revise remove` or `revise render` until you're happy with the results. When you're happy with the results, you can commit them using `revise commit <results-dir>` or in this case `revise commit results`. Don't worry, if someone else changed one or more of the documents since the time you generated the results, the commit will fail for those documents (but succeed for the others). Simply re-run `revise render` (or `revise remove`), and try committing again. Here's what the output of `revise commit results` (the `results` directory generated by the `revise render` command) looks like in our case:
   ```
   commit: results
   log: results/commit.log
   results/en-US.docs.Web.JavaScript.Reference.Operators.new/rev.html
   - created http://wiki.localhost.org:8000/en-US/docs/Web/JavaScript/Reference/Operators/new$revision/1600884
   results/en-US.docs.Web.JavaScript.Reference.Operators.typeof/rev.html
   - created http://wiki.localhost.org:8000/en-US/docs/Web/JavaScript/Reference/Operators/typeof$revision/1600885
   results/en-US.docs.Web.JavaScript.Reference.Operators.this/rev.html
   - created http://wiki.localhost.org:8000/en-US/docs/Web/JavaScript/Reference/Operators/this$revision/1600886
   ```
