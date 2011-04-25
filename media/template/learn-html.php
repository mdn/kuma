<?php include "./inc/template.php"; 
head(
  $title = 'Learn HTML | Mozilla Developer Network',
  $pageid = 'learn-html', 
  $bodyclass = 'section-learning',
  $headerclass = 'compact'
); ?>

  <header id="page-head">
    <div class="wrap">
      <nav class="crumb"><a href="learn-landing.php">Back to Home</a></nav>
      <h1 class="page-title">Learn HTML</h1>
      <p>HTML (<strong>HyperText Markup Language</strong>) is the core syntax for putting information on the worldwide web. 
      If you want to create or modify web pages, it’s best if you learn HTML. The links on this page lead 
      to a variety of HTML tutorials and HTML training materials. Whether you are just starting out, learning 
      the basics of HTML, or are an old hand at web development wanting to learn <strong>HTML5</strong> (the newest version 
      of the standard), you can find helpful resources here for HTML best practices.</p>
    </div> 
  </header>

<section id="content">
<div class="wrap">

  <section id="content-main" class="full" role="main">
  
    <div id="intro-level" class="learn-module boxed">
      <h2>Introductory Level</h2>
      <ul class="link-list">
        <li>
          <h3 class="title"><a href="http://dev.opera.com/articles/view/12-the-basics-of-html/" rel="external">The basics of HTML</a></h3>
          <h4 class="source">Dev.Opera</h4>
          <p>What HTML is, what it does, its history in brief, and what the structure of an HTML document looks like. The articles that follow this one look at each individual part of HTML in much greater depth.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://reference.sitepoint.com/html/page-structure" rel="external">Basic structure of a web page</a></h3>
          <h4 class="source">SitePoint</h4>
          <p>Learn how HTML elements fit together into the bigger picture.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://reference.sitepoint.com/html/elements" rel="external">Fundamental HTML elements</a></h3>
          <h4 class="source">SitePoint</h4>
          <p>Describes the different types of elements you can use to write an HTML document.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://htmldog.com/guides/htmlbeginner/" rel="external">HTML beginner tutorial</a></h3>
          <h4 class="source">HTML Dog</h4>
          <p>A tutorial and exercises that take you through the basics.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://code.google.com/edu/submissions/html-css-javascript/#html" rel="external">HTML from the ground up</a></h3>
          <h4 class="source">Google Code University</h4>
          <p>Video tutorial on best practices and approaches for how to write good HTML code.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://en.wikiversity.org/wiki/Web_Design/HTML_Challenges" rel="external">HTML challenges</a></h3>
          <h4 class="source">Wikiversity</h4>
          <p>Use these challenges to hone your HTML skills (for example, “Should I use an &lt;h2&gt; element or a &lt;strong&gt; element?”), focusing on meaningful mark-up.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://diveintohtml5.org/" rel="external">Dive into HTML5</a> <span class="tag html5">(HTML5)</span></h3>
          <h4 class="source">From Mark Pilgrim</h4>
          <p>Learn about a selection of features of HTML5, the newest version of the HTML specification.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://www.alistapart.com/articles/get-ready-for-html-5/" rel="external">Get Ready for HTML5</a> <span class="tag html5">(HTML5)</span></h3>
          <h4 class="source">A List Apart</h4>
          <p>Some suggestions to help you get on board with HTML5.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://www.html5rocks.com/tutorials/%E2%80%8B" rel="external">HTML5 tutorials</a> <span class="tag html5">(HTML5)</span></h3>
          <h4 class="source">HTML5 Rocks</h4>
          <p>Take a guided tour through code that uses HTML5 features.</p>
        </li>
        <li>
          <h3 class="title"><a href="https://developer.mozilla.org/HTML/Element">MDN HTML Element Reference</a></h3>
          <h4 class="source">MDN</h4>
          <p>A comprehensive reference for HTML elements, and how Firefox and other browsers support them.</p>
        </li>
      </ul>
    </div>
    
    <div id="adv-level" class="learn-module boxed">
      <h2>Advanced Level</h2>
      <ul class="link-list">
        <li>
          <h3 class="title"><a href="https://developer.mozilla.org/en/Tips_for_Authoring_Fast-loading_HTML_Pages">Tips for authoring fast-loading HTML pages</a></h3>
          <h4 class="source">MDN</h4>
          <p>Optimize web pages to provide a more responsive site for visitors and reduce the load on your web server and Internet connection.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://www.alistapart.com/articles/semanticsinhtml5/" rel="external">Semantics in HTML5</a> <span class="tag html5">(HTML5)</span></h3>
          <h4 class="source">A List Apart</h4>
          <p>Learn meaningful mark-up that is extensible and backwards- and forwards-compatible.</p>
        </li>
        <li>
          <h3 class="title"><a href="https://developer.mozilla.org/en/Canvas_tutorial">Canvas tutorial</a> <span class="tag html5">(HTML5)</span></h3>
          <h4 class="source">MDN</h4>
          <p>Learn how to draw graphics using scripting using the &lt;canvas&gt; element.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://html5doctor.com/" rel="external">&lt;html&gt;5 Doctor</a> <span class="tag html5">(HTML5)</span></h3>
          <p>Articles about using HTML5 right now.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://www.elated.com/articles/html5-audio/" rel="external">The Joy of HTML5 Audio</a> <span class="tag html5">(HTML5)</span></h3>
          <h4 class="source">Elated</h4>
          <p>Learn how to use the HTML audio element to embed sounds in your web pages easily. Lots of code examples are included in the tutorial.</p>
        </li>
      </ul>
    </div>
  
    <div id="examples" class="learn-module boxed">
      <h2>HTML5 Examples</h2>
      <ul class="link-list col1">
        <li>
          <h3 class="title"><a href="https://demos.mozilla.org/" rel="external">Web o’ Wonder</a></h3>
          <h4 class="source">Mozilla</h4>
          <p>Demos from Mozilla developers and evangelists.</p>
        </li>
        <li>
          <h3 class="title"><a href="https://developer.mozilla.org/en-US/demos/">MDN Demo Studio</a></h3>
          <p>Run, inspect, and submit demos that show what HTML, CSS, and JavaScript can do.</p>
        </li>
      </ul>
      <ul class="link-list col2">
        <li>
          <h3 class="title"><a href="http://html5demos.com/" rel="external">HTML5 Demos and Examples</a> <span class="tag html5">(HTML5)</span></h3>
          <p>Demos that you can filter by technology or browser support.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://html5gallery.com/" rel="external">&lt;html&gt;5 Gallery</a> <span class="tag html5">(HTML5)</span></h3>
          <p>Showcase of sites that use HTML5 to help you learn about how it should be used.</p>
        </li>
      </ul>
    </div>
  </section><!-- /#content-main -->

  <section id="learn-p2pu">
		<h2>Tired of learning on your own?<br>Want to join a community of people learning HTML and other open web technologies?</h2>
		<p>Sign up now for free online peer-led classes through <a href="http://p2pu.org/">Peer-to-Peer University's<span title="Peer-to-Peer University"></span></a> <a href="http://p2pu.org/webcraft/course-listing">School of Webcraft</a>. Think of it as an online study group or book club, where you share your struggles and discoveries with others who are learning the same things.</p>
	</section>

	<footer id="learn-fineprint">
    <p>These resources are created by forward-thinking companies and web developers who have embraced open standards and best practices for web development. If you think we’ve omitted a great resource, please tell us about it in the <a href="https://developer.mozilla.org/forums/viewforum.php?f=4&start=0">Open Web Forum</a>. We want to share these resources with our international community, so we prefer ones that provide or allow translations, through an open content license such as a <a href="http://creativecommons.org/licenses/">Creative Commons license</a>.</p>
	</footer>

<div id="html5-popup">
	<div class="bubble">
		<p>This site features <strong>HTML5</strong>, the next generation of open web technology. Please consult your doctor before starting HTML5.</p>
		<span></span>
	</div>
</div>

<script type="text/javascript">
// <![CDATA[
(function($) {
	$.fn.showLightbox = function() {
		var self = this;
		self.addClass('entering');
		setTimeout(function() {
			self.addClass('on').removeClass('entering');
		}, 100);
		return this;
	};
	$.fn.hideLightbox = function() {
		var self = this;
		self.addClass('leaving').removeClass('on');
		setTimeout(function() {
			self.removeClass('leaving');
		}, 400);
		return this;
	};
	
	$.fn.popup = function(popupElem) {
		this.removeAttr('title');
		
		return this.hover(
			function onIn() {
				var self = $(this),
				    offs = self.offset(),
				    w = self.outerWidth(),
				    h = self.outerHeight();
				$(popupElem)
					.offset( { left: (offs.left + w/2), top: (offs.top + h/2) })
					.addClass('visible');
			},
			function onOut() {
				$(popupElem).removeClass('visible');
			}
		);
	};
	
	$(function() {
		$('.tag.html5').popup('#html5-popup');
	});
})(jQuery);
	
// ]]>
</script>


</div>
</section>
<?php foot(); ?>
