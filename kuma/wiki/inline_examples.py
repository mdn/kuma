INLINE_EXAMPLES = {
    "FOR_EACH": """
<div class="interactive interactive-js">
<link href="/static/styles/libs/interactive-examples/codemirror-5-31-0.css" rel="stylesheet" />
<link href="/static/styles/libs/interactive-examples/editor-js.css" rel="stylesheet" />

<script>"use strict";function postToKuma(e){postMessage(e,"https://developer.mozilla.org")}postToKuma({markName:"interactive-editor-loading"}),document.addEventListener("readystatechange",function(e){switch(e.target.readyState){case"interactive":postToKuma({markName:"interactive-editor-interactive",measureName:"ie-time-to-interactive",startMark:"interactive-editor-loading",endMark:"interactive-editor-interactive"});break;case"complete":postToKuma({markName:"interactive-editor-complete",measureName:"ie-time-to-complete",startMark:"interactive-editor-loading",endMark:"interactive-editor-complete"})}});</script>
<section id="static">
  <pre>
<code id="static-js">var array1 = ['a', 'b', 'c'];

array1.forEach(function(element) {
  console.log(element);
});

// expected output: "a"
// expected output: "b"
// expected output: "c"
</code>
</pre>

</section>

<section id="live" class="live hidden">
  <header><h4>JavaScript Demo: Array.forEach()</h4></header>
  <div id="editor" class="editor"></div>

  <div class="output-container">
      <div class="buttons-container">
          <button id="execute" class="button run" type="button">Run &rsaquo;</button>
          <button id="reset" type="button" class="button">Reset</button>
      </div>
      <div id="output" class="output"><code></code></div>
  </div>
</section>

<script src="/static/js/libs/interactive-examples/codemirror-5-31-0.js"></script>
<script src="/static/js/libs/interactive-examples/editor-js.js"></script>
</div>
""",
    "MAP": """
<div class="interactive interactive-js">
<link href="/static/styles/libs/interactive-examples/codemirror-5-31-0.css" rel="stylesheet" />
<link href="/static/styles/libs/interactive-examples/editor-js.css" rel="stylesheet" />

<script>"use strict";function postToKuma(e){postMessage(e,"https://developer.mozilla.org")}postToKuma({markName:"interactive-editor-loading"}),document.addEventListener("readystatechange",function(e){switch(e.target.readyState){case"interactive":postToKuma({markName:"interactive-editor-interactive",measureName:"ie-time-to-interactive",startMark:"interactive-editor-loading",endMark:"interactive-editor-interactive"});break;case"complete":postToKuma({markName:"interactive-editor-complete",measureName:"ie-time-to-complete",startMark:"interactive-editor-loading",endMark:"interactive-editor-complete"})}});</script>

<section id="static">
  <pre>
<code id="static-js">var array1 = [1, 4, 9, 16];

// pass a function to map
const map1 = array1.map(x => x * 2);

console.log(map1);
// expected output: Array [2, 8, 18, 32]
</code>
</pre>

</section>

<section id="live" class="live hidden">
  <header><h4>JavaScript Demo: Array.map()</h4></header>
  <div id="editor" class="editor"></div>

  <div class="output-container">
      <div class="buttons-container">
          <button id="execute" class="button run" type="button">Run &rsaquo;</button>
          <button id="reset" type="button" class="button">Reset</button>
      </div>
      <div id="output" class="output"><code></code></div>
  </div>
</section>

<script src="/static/js/libs/interactive-examples/codemirror-5-31-0.js"></script>
<script src="/static/js/libs/interactive-examples/editor-js.js"></script>
</div>
""",
    "FILTER": """
<div class="interactive interactive-js">
<link href="/static/styles/libs/interactive-examples/codemirror-5-31-0.css" rel="stylesheet" />
<link href="/static/styles/libs/interactive-examples/editor-js.css" rel="stylesheet" />

<script>"use strict";function postToKuma(e){postMessage(e,"https://developer.mozilla.org")}postToKuma({markName:"interactive-editor-loading"}),document.addEventListener("readystatechange",function(e){switch(e.target.readyState){case"interactive":postToKuma({markName:"interactive-editor-interactive",measureName:"ie-time-to-interactive",startMark:"interactive-editor-loading",endMark:"interactive-editor-interactive"});break;case"complete":postToKuma({markName:"interactive-editor-complete",measureName:"ie-time-to-complete",startMark:"interactive-editor-loading",endMark:"interactive-editor-complete"})}});</script>

<section id="static">
  <pre>
<code id="static-js">var words = ['spray', 'limit', 'elite', 'exuberant', 'destruction', 'present'];

const result = words.filter(word => word.length > 6);

console.log(result);
// expected output: Array ["exuberant", "destruction", "present"]
</code>
</pre>

</section>

<section id="live" class="live hidden">
  <header><h4>JavaScript Demo: Array.filter()</h4></header>
  <div id="editor" class="editor"></div>

  <div class="output-container">
      <div class="buttons-container">
          <button id="execute" class="button run" type="button">Run &rsaquo;</button>
          <button id="reset" type="button" class="button">Reset</button>
      </div>
      <div id="output" class="output"><code></code></div>
  </div>
</section>

<script src="/static/js/libs/interactive-examples/codemirror-5-31-0.js"></script>
<script src="/static/js/libs/interactive-examples/editor-js.js"></script>
</div>
""",
    "FIND": """
<div class="interactive interactive-js">
<link href="/static/styles/libs/interactive-examples/codemirror-5-31-0.css" rel="stylesheet" />
<link href="/static/styles/libs/interactive-examples/editor-js.css" rel="stylesheet" />

<script>"use strict";function postToKuma(e){postMessage(e,"https://developer.mozilla.org")}postToKuma({markName:"interactive-editor-loading"}),document.addEventListener("readystatechange",function(e){switch(e.target.readyState){case"interactive":postToKuma({markName:"interactive-editor-interactive",measureName:"ie-time-to-interactive",startMark:"interactive-editor-loading",endMark:"interactive-editor-interactive"});break;case"complete":postToKuma({markName:"interactive-editor-complete",measureName:"ie-time-to-complete",startMark:"interactive-editor-loading",endMark:"interactive-editor-complete"})}});</script>

<section id="static">
  <pre>
<code id="static-js">var array1 = [5, 12, 8, 130, 44];

var found = array1.find(function(element) {
  return element > 10;
});

console.log(found);
// expected output: 12
</code>
</pre>

</section>

<section id="live" class="live hidden">
  <header><h4>JavaScript Demo: Array.find()</h4></header>
  <div id="editor" class="editor"></div>

  <div class="output-container">
      <div class="buttons-container">
          <button id="execute" class="button run" type="button">Run &rsaquo;</button>
          <button id="reset" type="button" class="button">Reset</button>
      </div>
      <div id="output" class="output"><code></code></div>
  </div>
</section>

<script src="/static/js/libs/interactive-examples/codemirror-5-31-0.js"></script>
<script src="/static/js/libs/interactive-examples/editor-js.js"></script>
</div>
""",
    "REDUCE": """
<div class="interactive interactive-js">
<link href="/static/styles/libs/interactive-examples/codemirror-5-31-0.css" rel="stylesheet" />
<link href="/static/styles/libs/interactive-examples/editor-js.css" rel="stylesheet" />

<script>"use strict";function postToKuma(e){postMessage(e,"https://developer.mozilla.org")}postToKuma({markName:"interactive-editor-loading"}),document.addEventListener("readystatechange",function(e){switch(e.target.readyState){case"interactive":postToKuma({markName:"interactive-editor-interactive",measureName:"ie-time-to-interactive",startMark:"interactive-editor-loading",endMark:"interactive-editor-interactive"});break;case"complete":postToKuma({markName:"interactive-editor-complete",measureName:"ie-time-to-complete",startMark:"interactive-editor-loading",endMark:"interactive-editor-complete"})}});</script>

<section id="static">
  <pre>
<code id="static-js">const array1 = [1, 2, 3, 4];
const reducer = (accumulator, currentValue) => accumulator + currentValue;

// 1 + 2 + 3 + 4
console.log(array1.reduce(reducer));
// expected output: 10

// 5 + 1 + 2 + 3 + 4
console.log(array1.reduce(reducer, 5));
// expected output: 15
</code>
</pre>

</section>

<section id="live" class="live hidden">
  <header><h4>JavaScript Demo: Array.reduce()</h4></header>
  <div id="editor" class="editor"></div>

  <div class="output-container">
      <div class="buttons-container">
          <button id="execute" class="button run" type="button">Run &rsaquo;</button>
          <button id="reset" type="button" class="button">Reset</button>
      </div>
      <div id="output" class="output"><code></code></div>
  </div>
</section>

<script src="/static/js/libs/interactive-examples/codemirror-5-31-0.js"></script>
<script src="/static/js/libs/interactive-examples/editor-js.js"></script>
</div>
""",
    "SPLICE": """
<div class="interactive interactive-js">
<link href="/static/styles/libs/interactive-examples/codemirror-5-31-0.css" rel="stylesheet" />
<link href="/static/styles/libs/interactive-examples/editor-js.css" rel="stylesheet" />

<script>"use strict";function postToKuma(e){postMessage(e,"https://developer.mozilla.org")}postToKuma({markName:"interactive-editor-loading"}),document.addEventListener("readystatechange",function(e){switch(e.target.readyState){case"interactive":postToKuma({markName:"interactive-editor-interactive",measureName:"ie-time-to-interactive",startMark:"interactive-editor-loading",endMark:"interactive-editor-interactive"});break;case"complete":postToKuma({markName:"interactive-editor-complete",measureName:"ie-time-to-complete",startMark:"interactive-editor-loading",endMark:"interactive-editor-complete"})}});</script>

<section id="static">
  <pre>
<code id="static-js">var months = ['Jan', 'March', 'April', 'June'];
months.splice(1, 0, 'Feb');
// inserts at 1st index position
console.log(months);
// expected output: Array ['Jan', 'Feb', 'March', 'April', 'June']

months.splice(4, 1, 'May');
// replaces 1 element at 4th index
console.log(months);
// expected output: Array ['Jan', 'Feb', 'March', 'April', 'May']
</code>
</pre>

</section>

<section id="live" class="live hidden">
  <header><h4>JavaScript Demo: Array.splice()</h4></header>
  <div id="editor" class="editor"></div>

  <div class="output-container">
      <div class="buttons-container">
          <button id="execute" class="button run" type="button">Run &rsaquo;</button>
          <button id="reset" type="button" class="button">Reset</button>
      </div>
      <div id="output" class="output"><code></code></div>
  </div>
</section>

<script src="/static/js/libs/interactive-examples/codemirror-5-31-0.js"></script>
<script src="/static/js/libs/interactive-examples/editor-js.js"></script>
</div>
""",
}
