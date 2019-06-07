/*
retext.js: Node.js natural language processor
e.g: various grammar checks, profanities, language simplicity, ...

https://github.com/wooorm/retext

license: MIT https://github.com/wooorm/retext/blob/master/LICENSE
author: Titus Wormer http://wooorm.com

file walker: http://www.bymichaellancaster.com/blog/nodejs-recursively-access-folder/

install:
retext
to-vfile
vfile-reporter

+ plug-ins

*/

'use strict';

var fs = require('fs');
var path = require('path');

//use when no PATH variable set
var modulePath = ''; //nodejs/node_modules/';
var istr = '/index.js';

var unified = require(modulePath + 'unified' + istr);
var stringify = require(modulePath + 'retext-stringify' + istr);
var english = require(modulePath + 'retext-english' + istr);

var contractions = require(modulePath + 'retext-contractions' + istr);
var diacritics = require(modulePath + 'retext-diacritics' + istr);
var indefiniteArticle = require(modulePath + 'retext-indefinite-article' + istr);
var repeatedWords = require(modulePath + 'retext-repeated-words' + istr);
var redundantAcronyms = require(modulePath + 'retext-redundant-acronyms' + istr);
var sentenceSpacing = require(modulePath + 'retext-sentence-spacing' + istr);
var passive = require(modulePath + 'retext-passive' + istr);

var simplify = require(modulePath + 'retext-simplify' + istr);
var equality = require(modulePath + 'retext-equality' + istr);
var profanities = require(modulePath + 'retext-profanities' + istr);
//var cliches = require(modulePath + 'retext-cliches' + istr);
//var overuse = require(modulePath + 'retext-overuse' + istr);
//var usage = require(modulePath + 'retext-usage' + istr);


var vfile = require(modulePath + 'to-vfile' + istr);
var report = require(modulePath + 'vfile-reporter' + istr);

var rootdir = '../manual/';


// Windows?
var win32 = process.platform === 'win32';
// Normalize \\ paths to / paths.
function unixifyPath(filepath) {
  if (win32) {
	 return filepath.replace(/\\/g, '/');
  } else {
	 return filepath;
  }
};

function walk(rootdir, callback, subdir) {
  var abspath = subdir ? path.join(rootdir, subdir) : rootdir;
  fs.readdirSync(abspath).forEach(function(filename) {
	 var filepath = path.join(abspath, filename);
	 if (fs.statSync(filepath).isDirectory()) {
		walk(rootdir, callback, unixifyPath(path.join(subdir || '', filename || '')));
	 } else {
		if(path.extname(filename) === '.rst') {callback(unixifyPath(filepath), rootdir, subdir, filename);}
	 }
  });
};

walk(rootdir, function(filepath, rootdir, subdir, filename) {
	var processor = unified()
		.use(english)
		//add plug-ins here
		.use(equality)

		.use(stringify)
		.process(vfile.readSync(filepath), function (err, file) {
			if (err) throw err;
			console.error(report(err || file));
	});
});

//to activate move them to plug-ins
/*
		.use(equality, {ignore: ['disabled', 'actor', 'actors', 'mailman', 'groom']})
		.use(simplify, {ignore: [
			'very', 'similar', 'however', 'currently', 'previously', 'remain', 'determine', 'identical', 'overall', 'whereas', 'therefore', //block to avoid console overflow
			'all of', 'relative to', 'similar to', 'accordingly', 'benefit', 'perform', 'represents', 'adjustment', 'maintain', 'magnitude', 'ensure', //block
			'might', 'multiple', 'it is', 'there is', 'there are', 'previous',  'e.g.',  'i.e.', 'a number of',
			'maximum', 'minimum', 'equivalent', 'approximate', 'parameters', 'function', //math
			'request', 'interface', 'forward', 'type', 'initial', 'selection', 'monitor', 'implement', 'minimize', 'maximize', 'operate', 'option', 'submit', 'component', //CS
			'contains', 'delete', 'combined', 'requirement', 'require', 'additional', 'provide', 'identify', 'accurate',
			'render', 'effect', 'modify', 'reflect' //CG
		]})
		.use(profanities, {ignore: [
			'color', 'colors', 'colored', 'white', 'whites', 'black', 'blacks',
			'american', 'european', 'japanese', 'latin', 'uk', 'conservative', 'god', 'children\'s', 'girl\'s',
			'joint', 'joints', 'dope', 'pot',
			'hole', 'holes', 'strokes', 'hook', 'hooks', 'screw', 'screws', 'stroke', 'slope', 'slopes', 'kink', 'kinks', 'riggers',
			'harder', 'bigger', 'lie', 'lies', 'laid', 'fear', 'chin', 'ball', 'balls', 'desire', 'penetrations', 'period', 'dive', 'jade', 'bi',
			'death', 'dead', 'died', 'die', 'dies', 'kill', 'execution', 'executions', 'execute', 'executes', 'executed', 'remain', 'remains', 'reject',
			'doom', 'crash', 'crashes', 'failure', 'failures', 'failed', 'corruption', 'destroy', 'destroys',
			'attack', 'fight', 'shoots', 'shooting', 'failure', 'enemy', 'weapon', 'weapons', 'gun', 'knife',
			'slime', 'fire', 'fires', 'firing', 'burn', 'burns', 'cracks', 'split', 'splits','explosion', 'explosions'
		]})
*/
