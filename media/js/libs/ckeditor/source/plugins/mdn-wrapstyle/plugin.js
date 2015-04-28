'use strict';

(function() {
  // Definition of elements at which div operation should stopped.
  var divLimitDefinition = (function() {
    // Customzie from specialize blockLimit elements
    var definition = CKEDITOR.tools.extend({}, CKEDITOR.dtd.$blockLimit);

    // Exclude 'div' itself.
    delete definition.div;

    // Exclude 'td' and 'th'
    delete definition.td;
    delete definition.th;
    
    return definition;
  })();

  // DTD of 'div' element
  var dtd = CKEDITOR.dtd.div;

  CKEDITOR.plugins.add('mdn-wrapstyle', {
    onLoad: function() {
      CKEDITOR.style.addCustomHandler({
        type: 'wrap',
        assignedTo: CKEDITOR.STYLE_BLOCK,

        setup: function(definition) {
          this.element = definition.element;
        },

        apply: function(editor) {
          editor.execCommand('wrapstyle', this);
        },

        remove: function(editor) {
          editor.execCommand('wrapstyle', this);
        },

        checkElementRemovable: function(element, fullMatch) {
          element = element && element.getAscendant(this.element, true);
          if (element)
            return CKEDITOR.style.prototype.checkElementRemovable.call(this, element, fullMatch);
          else
            return false;
        }
      })
    },

    init: function(editor) {
      editor.addCommand('wrapstyle', {
        exec: function(editor, style) {
          var selection = editor.getSelection(),
            bookmarks = selection && selection.createBookmarks(),
            ranges = selection && selection.getRanges(),
            rangeIterator = ranges && ranges.createIterator(),
            range,
            iterator,
            div,
            removeDiv = true,
            toRemove = [];

          while((range = rangeIterator.getNextRange())) { // Only one =
            iterator = range.createIterator();
            iterator.enforceRealBlocks = true;

            var block;
            while((block = iterator.getNextParagraph())) { // Only one =
              div = block.getAscendant(style.element, true);

              if(div && style.checkElementRemovable(div)) {
                var prev = toRemove.pop(),
                  commonAncestor = prev && prev.getCommonAncestor(div);

                if(commonAncestor && style.checkElementRemovable(commonAncestor)) {
                  toRemove.push(commonAncestor);
                }
                else {
                  prev && toRemove.push(prev);
                  toRemove.push(div);
                }
              }
              else if(toRemove.length == 0) {
                removeDiv = false;
              }
            }
          }

          if(removeDiv) {
            for(var i = 0, count = toRemove.length; i < count; i++) {
              toRemove[i].remove(true);
            }
          }
          else {
            var divs = createDiv(editor);

            for(var i = 0, count = divs.length; i < count; i++) {
              div = divs[i];
              style.applyToObject(div);
            }
          }

          bookmarks && selection.selectBookmarks(bookmarks);
        }
      });
    }
  });

  /**
   * Add to collection with DUP examination.
   * @param {Object} collection
   * @param {Object} element
   * @param {Object} database
   */
  function addSafely(collection, element, database) {
    // 1. IE doesn't support customData on text nodes;
    // 2. Text nodes never get chance to appear twice;
    if(!element.is || !element.getCustomData('block_processed')) {
      element.is && CKEDITOR.dom.element.setMarker(database, element, 'block_processed', true);
      collection.push(element);
    }
  }

  /**
   * Get the first div limit element on the element's path.
   * @param {Object} element
   */
  function getDivLimitElement(element) {
    var pathElements = new CKEDITOR.dom.elementPath(element).elements,
      divLimit;
    for(var i = 0; i < pathElements.length; i++) {
      if(pathElements[i].getName() in divLimitDefinition) {
        divLimit = pathElements[i];
        break;
      }
    }
    return divLimit;
  }

  /**
   * Divide a set of nodes to different groups by their path's blocklimit element.
   * Note: the specified nodes should be in source order naturally, which mean they are supposed to produce a by following class:
   *  * CKEDITOR.dom.range.Iterator
   *  * CKEDITOR.dom.domWalker
   *  @return {Array []} the grouped nodes
   */
  function groupByDivLimit(nodes) {
    var groups = [],
      lastDivLimit = null,
      path, block;
    for(var i = 0; i < nodes.length; i++) {
      block = nodes[i];
      var limit = getDivLimitElement(block);
      if(!limit.equals(lastDivLimit)) {
        lastDivLimit = limit;
        groups.push([]);
      }
      groups[groups.length - 1].push(block);
    }
    return groups;
  }

  /**
   * Wrapping 'div' element around appropriate blocks among the selected ranges.
   * @param {Object} editor
   */
  function createDiv(editor) {
    // new adding containers OR detected pre-existed containers.
    var containers = [],
    // node markers store.
      database = {},
    // All block level elements which contained by the ranges.
      containedBlocks = [], block,
    // Get all ranges from the selection.
      selection = editor.document.getSelection(),
      ranges = selection.getRanges(),
      bookmarks = selection.createBookmarks(),
      i, iterator;

    // collect all included elements from dom-iterator
    for(i = 0; i < ranges.length; i++) {
      iterator = ranges[i].createIterator();
      while((block = iterator.getNextParagraph())) {
        // include contents of blockLimit elements.
        if(block.getName() in divLimitDefinition) {
          var j, childNodes = block.getChildren();
          for(j = 0; j < childNodes.count(); j++)
            addSafely(containedBlocks, childNodes.getItem(j) , database);
        }
        else {
          // Bypass dtd disallowed elements.
          while(!dtd[block.getName()] && block.getName() != 'body')
            block = block.getParent();
          addSafely(containedBlocks, block, database);
        }
      }
    }

    CKEDITOR.dom.element.clearAllMarkers(database);

    var blockGroups = groupByDivLimit(containedBlocks),
      ancestor, divElement;

    for(i = 0; i < blockGroups.length; i++) {
      var currentNode = blockGroups[i][0];

      // Calculate the common parent node of all contained elements.
      ancestor = currentNode.getParent();
      for(j = 1; j < blockGroups[i].length; j++)
        ancestor = ancestor.getCommonAncestor(blockGroups[i][j]);

      divElement = new CKEDITOR.dom.element('div', editor.document);

      // Normalize the blocks in each group to a common parent.
      for(j = 0; j < blockGroups[i].length; j++) {
        currentNode = blockGroups[i][j];

        while(!currentNode.getParent().equals(ancestor))
          currentNode = currentNode.getParent();

        // This could introduce some duplicated elements in array.
        blockGroups[i][j] = currentNode;
      }

      // Wrapped blocks counting
      for(j = 0; j < blockGroups[i].length; j++) {
        currentNode = blockGroups[i][j];

        // Avoid DUP elements introduced by grouping.
        if(!(currentNode.getCustomData && currentNode.getCustomData('block_processed')))
        {
          currentNode.is && CKEDITOR.dom.element.setMarker(database, currentNode, 'block_processed', true);

          // Establish new container, wrapping all elements in this group.
          if(!j)
            divElement.insertBefore(currentNode);

          divElement.append(currentNode);
        }
      }

      CKEDITOR.dom.element.clearAllMarkers(database);
      containers.push(divElement);
    }

    selection.selectBookmarks(bookmarks);
    return containers;
  }

})();