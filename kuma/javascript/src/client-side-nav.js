const locale = window.location.pathname.split('/')[1];
const pattern = `/${locale}/docs/Web/`;

function init() {
    window.addEventListener('popstate', handlePopState);

    if (document.readyState === 'loading') {
        window.addEventListener('DOMContentLoaded', fixDocumentLinks);
    } else {
        fixDocumentLinks();
    }
}

function fixDocumentLinks() {
    fixLinks(document);
}

// XXX This doesn't work for dynamically created links like those in
// the React-based dropdown menus. Perhaps I should export a click
// handler that react elements can use on their links, or even export
// a Link component...
function fixLinks(root) {
    let links = root.querySelectorAll('a[href]');
    for (let link of links) {
        if (link.href.includes(pattern) && !link.href.includes('#')) {
            link.addEventListener('click', handleLinkClick);
        }
    }
}

function handleLinkClick(event) {
    let url = this.href;
    event.preventDefault();

    window.history.pushState({ url }, '', url.replace('/docs/', '/ducks/'));
    clientSideNavigate(url);
}

function handlePopState(event) {
    if (event.state) {
        clientSideNavigate(event.state.url);
    }
}

function clientSideNavigate(url) {
    // Erase the breadcrumb; we don't have an API for fetching those
    let breadcrumbs = document.querySelector('nav.crumbs');
    if (breadcrumbs) {
        breadcrumbs.textContent = '';
    }

    // These are sections that we need to update on navigation
    let h1Element = document.querySelector('h1');
    let articleElement = document.querySelector('article');
    let linksElement = document.querySelector('#quick-links');
    let TOC = document.querySelector('ol.toc-links');

    // If this document is missing any of those elements then
    // we can't do client-side navigation from here and should
    // force a hard reload
    if (!h1Element || !articleElement || !linksElement || !TOC) {
        window.location = url.replace('/docs/', '/ducks/');
        return;
    }

    // Hide the current content in those sections immediately
    h1Element.style.opacity = 0.25;
    articleElement.style.opacity = 0.25;
    linksElement.style.opacity = 0.25;
    TOC.style.opacity = 0.25;

    // Fetch the $json to get the document title
    fetch(url + '$json')
        .then(response => response.json())
        .then(json => {
            let title = json.title;
            h1Element.textContent = title;
            h1Element.style.opacity = 1;
            document.querySelector('head > title').textContent = title;
        });

    // Fetch the raw document content to get the article body, etc.
    fetch(url + '?raw&macros')
        .then(response => response.text())
        .then(html => {
            window.scrollTo(0, 0);

            let links = '';
            let article = html;
            let linksStart = html.indexOf('<section id="Quick_Links"');
            if (linksStart !== -1) {
                let prefix = html.substring(0, linksStart);
                html = html.substring(linksStart);
                let linksEnd = html.indexOf('</section>');
                links = html.substring(0, linksEnd + 10);
                article = prefix + html.substring(linksEnd + 10);
            }

            articleElement.innerHTML = article;
            articleElement.style.opacity = 1;
            fixLinks(articleElement);

            linksElement.innerHTML =
                '<div class="quick-links-head">Related Topics</div>' + links;
            linksElement.style.opacity = 1;
            fixLinks(linksElement);

            // Quick links in the "toc-links" section
            let sections = articleElement.querySelectorAll('h2');
            let tocitems = [...sections].map(
                s =>
                    `<li><a rel="internal" href="#${s.id}">${
                        s.textContent
                    }</a></li>`
            );
            TOC.innerHTML = tocitems.join('');
            TOC.style.opacity = 1;
        });
}

export default { init };
