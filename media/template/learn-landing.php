<?php include "./inc/template.php"; 
head(
  $title = 'Learn How to Make Websites | Mozilla Developer Network',
  $pageid = '', 
  $bodyclass = 'section-learning landing',
  $headerclass = 'compact'
); ?>

<header id="page-head" class="landing">
  <div class="wrap">
    <h1 class="page-title">Learn How to Make Websites</h1>
    <p>Want to learn to use the technologies that power the Web?
    <br>We've put together a great collection of resources to get your started.</p>
  </div>   
</header>


<section id="content">
<div class="wrap">

  <section id="content-main" class="full" role="main">
    <div id="blackboard">
      <ul>
        <li id="sub-html">
          <a href="learn-html.php">
            <h2>HTML</h2>
				    <p><strong>HyperText Markup Language</strong> is the basic building block of the Web. It describes the words, images, and links that make up web pages. If you want to create content for the Web, HTML is the first thing you should learn.</p>
				  </a>
				</li>
        <li id="sub-css">
          <a href="learn-css.php">
            <h2>CSS</h2>
				    <p><strong>Cascading Style Sheets</strong> let you add style to the web pages you make. The fonts, colors, backgrounds and layout of a web page are all added using CSS.</p>
				  </a>
        </li>
        <li id="sub-js">
          <a href="learn-js.php">
            <h2>JavaScript</h2>
				    <p><strong>JavaScript</strong> is used to add behavior to a web page. It can be used to respond to user input, add dynamic content or animate your web pages.</p>
				  </a>
        </li>
      </ul>
    </div>
  </section><!-- /#content-main -->

  <section id="learn-p2pu">
		<h2>Are you tired of learning on your own?<br>Do you want to join a community of people learning about open web technologies?</h2>
		<p>Consider signing up for free online peer-led classes through <a href="http://p2pu.org/">Peer-to-Peer University's<span title="Peer-to-Peer University"></span></a> <a href="http://p2pu.org/webcraft/course-listing">School of Webcraft</a>. Think of it as an online study group or book club, where you share your struggles and discoveries with others who are learning the same things.</p>
	</section>

	<footer id="learn-fineprint">
		<p>These resources are created by forward-thinking companies and web developers who have embraced open standards and best practices for web development. If you think we've omitted a great resource, please tell us about it in the <a href="https://developer.mozilla.org/forums/viewforum.php?f=4">Open Web Forum</a>. We want to share these resources with our international community, so we prefer ones that provide or allow translations, through an open content license such as <a href="http://creativecommons.org" rel="external">Creative Commons</a>.</p>
	</footer>

</div>
</section>
<?php foot(); ?>
