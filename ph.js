var fs = require('fs');
var system = require('system');
var page = require('webpage').create();


console.warn = console.error = function() {
  system.stderr.writeLine(Array.prototype.join.call(arguments, ' '));
}

var build_dir = fs.workingDirectory + '/build/'

if (system.args[1]) {
  var url = system.args[1];
} else {
  var url = 'some_url'
}

page.viewportSize = {
  width: 1600,
  height: 1200,
}

page.onResourceRequested = function(requestData, networkRequest) {
  console.warn("Requested:", requestData.url);
}

page.onConsoleMessage = function(msg) {
  console.warn(msg)
}

page.onInitialized = function() {
  if (page.injectJs('node_modules/es6-promise/dist/es6-promise.js')) {
    page.evaluate(function() {
      ES6Promise.polyfill();
    });
  } else {
    console.error("Error: cannot inject es6-promise.")
  }
}

page.open(url, function(status) {
  console.warn("Status:", status);
  if (status === 'success') {
    if (
      page.injectJs('node_modules/jquery/dist/jquery.js')
      && page.injectJs('node_modules/lodash/index.js')
    ) {

      var res = page.evaluate(function() {
        console.warn('Begin to execute in page environment.')

        var results = [];

        var sheets = document.styleSheets;
        var elems = document.getElementsByTagName('*');
        for (var i = 0; i < sheets.length; i++) {
          var rules = sheets[i].cssRules;
          var usedRules = [];

          for (var j = 0; j < elems.length; j++) {
            var elem = $(elems[j]);

            for (var k = 0; k < rules.length; k++) {
              var cssTarget = rules[k].selectorText;
              var cssText = rules[k].cssText;
              if (cssText.indexOf('@media') > -1) {
                usedRules.push(k);
              }
              try {
                if (elem.is(cssTarget)) {
                  usedRules.push(k);
                }
              } catch (e) {
                usedRules.push(k);
              }
            }

          }

          usedRules = _.uniq(usedRules.sort());
          usedCSS = usedRules.map(function(i) {
            var cssText = (rules[i].cssText
                           .replace(/\n/g, '')
                           .replace(/ +/g, ' '));
            return cssText;
          }).join('');
          if (usedCSS) {
            results.push(usedCSS);
          }
        }

        return results.join(' ');
      });

      console.log(res)

    } else {
      console.error("Error: cannot inject js files.")
    }

    //window.setTimeout(function() {
    //  console.warn("Generating screen shot...");
    //  page.render(build_dir + 'comments.png');
    //  phantom.exit();
    //}, 500);
    phantom.exit();
  } else {
    console.error("Cannot open url: " + url + ", check your webserver.")
    phantom.exit(1);
  }
});
