<?php include "./inc/template.php"; 
head(
  $title = 'Learn CSS | Mozilla Developer Network',
  $pageid = 'learn-css', 
  $bodyclass = 'section-learning',
  $headerclass = 'compact'
); ?>

<header id="page-head">
  <div class="wrap">
    <nav class="crumb"><a href="learn-landing.php">Back to Home</a></nav>
    <h1 class="page-title">Learn CSS</h1>
    <p>CSS (<strong>Cascading Style Sheets</strong>) ​is a language for describing the appearance of web pages. 
    To create good-looking web pages, you need to learn CSS in order to define the appearance and location of 
    the HTML elements within the pages. The links on this page lead to a variety of CSS tutorials and CSS 
    training materials. ​Whether you are just starting out, learning the basics of CSS, or are an experienced web 
    developer wanting to learn <strong>CSS3</strong> (the newest version of the standard) and CSS best practices, 
    you can find helpful resources here.</p>
  </div>
</header>
  
<section id="content">
<div class="wrap">

  <section id="content-main" class="full" role="main">
    <div id="intro-level" class="learn-module boxed">
      <h2>Introductory Level</h2>
      <ul class="link-list">
        <li>
          <h3 class="title"><a href="https://developer.mozilla.org/en/CSS/Getting_Started">CSS Getting Started</a></h3>
          <h4 class="source">MDN</h4>
          <p>This tutorial introduces you to Cascading Style Sheets (CSS). It guides you through the basic features of CSS with practical examples that you can try for yourself on your own computer.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://dev.opera.com/articles/view/27-css-basics/" rel="external">CSS basics</a></h3> 
          <h4 class="source">Dev.Opera</h4>
          <p>What CSS is, how to apply it to HTML, and what basic CSS syntax looks like.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://en.wikiversity.org/wiki/Web_Design/CSS_Classes" rel="external">CSS Selector Classes</a></h3>
          <h4 class="source">Wikiversity</h4>
          <p>What are classes in CSS?</p>
        </li>
        <li>​
          <h3 class="title"><a href="http://en.wikiversity.org/wiki/Web_Design/External_CSS" rel="external">External CSS</a></h3>
          <h4 class="source">Wikiversity</h4>
          <p>Using CSS from an external style sheet.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://www.w3.org/MarkUp/Guide/Style" rel="external">Adding a touch of style</a></h3>
          <h4 class="source">W3C</h4>
          <p>A brief beginner’s guide to styling web pages with CSS.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://code.google.com/edu/submissions/html-css-javascript/#css" rel="external">CSS from the ground up</a></h3>
          <h4 class="source">Google Code University</h4>
          <p>Video tutorial on styling pages with CSS.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://en.wikiversity.org/wiki/Web_Design/CSS_challenges" rel="external">CSS challenges</a></h3>
          <h4 class="source">Wikiversity</h4>
          <p>Flex your CSS skills, and see where you need more practice.</p>
        </li>
        <li>
          <h3 class="title"><a href="https://developer.mozilla.org/en/Common_CSS_Questions">Common CSS questions</a></h3>
          <h4 class="source">MDN</h4>
          <p>Common questions and answers for beginners.</p>
        </li>
        <li>
          <h3 class="title"><a href="https://developer.mozilla.org/en/CSS_Reference">CSS Reference</a></h3>
          <h4 class="source">MDN</h4>
          <p>Complete reference to CSS, with details on support by Firefox and other browsers.</p>
        </li>
      </ul>
    </div>
    
    <div id="adv-level" class="learn-module boxed">
      <h2>Advanced Level</h2>
      <ul class="link-list">
        <li>
          <h3 class="title"><a href="http://www.html.net/tutorials/css/" rel="external">Intermediate CSS concepts</a></h3>
          <h4 class="source">HTML.net</h4>
          <p>Grouping, pseudo-classes, and more.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://www.alistapart.com/articles/css-positioning-101/" rel="external">CSS Positioning 101</a></h3>
          <h4 class="source">A List Apart</h4>
          <p>Using positioning for standards-compliant, table-free layout.</p>
        </li>
        <li>  
          <h3 class="title"><a href="http://www.alistapart.com/articles/progressiveenhancementwithcss/" rel="external">Progressive enhancement with CSS</a></h3>
          <h4 class="source">A List Apart</h4>
          <p>Integrate progressive enhancement into your web pages with CSS.</p>
        </li>
        <li>
          <h3 class="title"><a href="http://www.alistapart.com/articles/fluidgrids/" rel="external">Fluid grids</a></h3>
          <h4 class="source">A List Apart</h4>
          <p>Design layouts that fluidly resize with the browser window, while still using a typographic grid.</p>
        </li>
        <li>  
          <h3 class="title"><a href="http://addyosmani.com/blog/css3-screencast/" rel="external">CSS3 in under 5 minutes</a></h3>
          <h4 class="source">Addy Osmani</h4>
          <p>A quick introduction to some of the core features introduced in CSS3.</p>
        </li>
        <li>  
          <h3 class="title"><a href="https://developer.mozilla.org/En/CSS/Using_CSS_transforms">Using CSS Transforms</a></h3>
          <h4 class="source">MDN</h4>
          <p>Apply rotation, skewing, scaling, and translation using CSS.</p>
        </li>
        <li>  
          <h3 class="title"><a href="https://developer.mozilla.org/en/CSS/CSS_transitions">CSS Transitions</a></h3>
          <h4 class="source">MDN</h4>
          <p>CSS transitions, part of the draft CSS3 specification, provide a way to animate changes to CSS properties, instead of having the changes take effect instantly.</p>
        </li>
        <li>  
          <h3 class="title"><a href="http://www.alistapart.com/articles/understanding-css3-transitions/" rel="external">Understanding CSS3 Transitions</a></h3>
          <h4 class="source">A List Apart</h4>
          <p>Start using CSS3 transitions by carefully choosing the situations in which to use them.</p>
        </li>
        <li> 
          <h3 class="title"><a href="http://www.html5rocks.com/tutorials/webfonts/quick/" rel="external">Quick guide to implement web fonts with @font-face</a></h3>
          <h4 class="source">HTML5 Rocks</h4>
          <p>The @font-face feature from CSS3 allows you to use custom typefaces on the web in an accessible, manipulable, and scalable way.</p>
        </li>
      </ul>
    </div>

  </section><!-- /#content-main -->

  <section id="learn-p2pu">
    <h2>Are you tired of learning CSS on your own?<br> Do you want to join a community of people who are learning CSS and other open web technologies?</h2>
    <p>Consider signing up for free online peer-led classes through <a href="http://p2pu.org/">Peer-to-Peer University's<span title="Peer-to-Peer University"></span></a> <a href="http://p2pu.org/webcraft/course-listing">School of Webcraft</a>. Think of it as an online study group or book club, where you share your struggles and discoveries with others who are learning the same things.
	</section>

	<footer id="learn-fineprint">
		<p>These resources are created by forward-thinking companies and web developers who have embraced open standards and best practices for web development. If you think we've omitted a great resource, please tell us about it in the <a href="https://developer.mozilla.org/forums/viewforum.php?f=4">Open Web Forum</a>. We want to share these resources with our international community, so we prefer ones that provide or allow translations, through an open content license such as <a href="http://creativecommons.org" rel="external">Creative Commons</a>.</p>
	</footer>

</div>
</section>
<?php foot(); ?>
