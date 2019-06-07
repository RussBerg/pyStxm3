(function() {//switch: v.b0i
"use strict"; 

var debug_versions = { //@
	"latest": "Latest",
	"dev": "Developmental"
};

var all_versions = "";

var all_langs = {
	"en": "English",
	"de": "Deutsch",
	"es": "Espa&ntilde;ol",
	"fr": "Fran&ccedil;ais",
	"it": "Italiano",
	"ja": "&#x65E5;&#x672C;&#x8A9E;",
	"nb": "Norsk Bokm&#x00E5;l",
	"pt": "Portugu&ecirc;s",
	"ru": "&#x3A1;&#x443;&#x441;&#x441;&#x43A;&#x438;&#x439;",
	"fi": "Suomeksi",
	"uk": "Ukra&#1111;na",
	"zh-hans": "&#x4E2D;&#x6587;(&#x7B80;&#x4F53;)",
	"zh-hant": "&#x4E2D;&#x6587;(&#x7E41;&#x9AD4;)"
};

var Drop=function(){
function Drop(id){
	this.isOpen=false;
	this.label = "";
	if(id === "version-dropdown") {this.type = true;}else{this.type = false;}
	if(id === "version-dropdown") {this.listlabel = "Versions";} else {this.listlabel = "Language";}
	this.$btn = $('#' + id);
	this.$list = this.$btn.next();
	this.sel = null;
	this.beforeInit();
}

Drop.prototype={
beforeInit: function() {
	var that=this;
	this.$btn.on("click", function(e){that.init();e.preventDefault();e.stopPropagation();});
	this.$btn.on("keypress", function(e) { if(that.keybtnfilter(e)){that.init();e.preventDefault();e.stopPropagation();} });
},
init: function() {
	this.$btn.off("click");
	this.$btn.off("keypress");

	if(all_versions === "") {
		this.$btn.addClass("wait");
		this.loadVL(this);
	} else {
		this.afterload();
	}
},
loadVL: function(that) {
	$.getJSON("https://docs.blender.org/manual/en/dev/versions.json", function(data) {
		all_versions = data;
		that.afterload();
		return true;
	})
	.fail( function() {
		console.log("Version Switch Error: versions.json could not be loaded.");
		all_versions = debug_versions; //@
		that.afterload(); //@
		that.$btn.addClass("disabled");
		return false;
	});
},
afterload: function() {
	var release = DOCUMENTATION_OPTIONS.VERSION;
	//release = 2.79; //@
	var lang = DOCUMENTATION_OPTIONS.LANGUAGE;
	if(lang === "None" || lang === undefined) {lang = "en";}

	var version = this.get_named(release);
	if(this.type) {this.label = all_versions[version];}else{this.label = all_langs[lang];}
	var list = this.build_list(version, lang);

	this.$list.children(":first-child").remove();
	this.$list.append(list);
	var that = this;
	this.$list.on("keypress", function(e) {that.keymove(e);});

	this.$btn.removeClass("wait");
	this.btnhandler();
	this.$btn.on("mousedown", function(e){that.btnhandler(); e.preventDefault()});
	this.$btn.on("keypress", function(e){ if(that.keybtnfilter(e)){that.btnhandler();} });
},
build_list: function(v, l) {
	var neutral_url = this.get_neutral();
	if(this.type) {
		var dyn = all_versions;
		var cur = v;
	} else {
		var dyn = all_langs;
		var cur = l;
	}
	var buf = [];
	var that=this;
	$.each(dyn, function(ix, title) {
		buf.push("<li");
		if (ix === cur) {
			buf.push(' class="selected" tabindex="-1" role="presentation"><span tabindex="-1" role="menuitem" aria-current="page">' + title + '</spanp></li>');
		} else {
			if(that.type) {
				v = ix;
			} else {
				l = ix;
			}
			var new_url = neutral_url.replace(/\/manual\//, '/manual/' + l + '/' + v + '/');
			buf.push(' tabindex="-1" role="presentation"><a href ="' + new_url + '" tabindex="-1">' + title + '</a></li>');
		}
	});
	return buf.join('');
},
get_neutral: function() {
	var url = window.location.href;
	var url_re = /\/manual\/([\w|\-|\.]*\/(?:dev|latest|\d\.\d[\w\d\.]*))\//;
	return url.replace(url_re, "/manual/");
},
get_named: function(v) {
	$.each(all_versions, function(ix, title) {
		if (ix === "dev" || ix === "latest") {
			var m = title.match(/\d\.\d[\w\d\.]*/)[0];
			if (parseFloat(m) == v) {
				v = ix;
				return false;
			}
		}
	});
	return v;
},
listtoggle: function(speed) {
	var d = !this.isOpen;
	var that=this;
	if(!this.isOpen) {
		this.$btn.addClass("version-btn-open");
		this.$btn.removeClass("version-btn");
		this.$btn.attr("aria-pressed", true);
		this.$list.attr("aria-hidden", false);
		this.$btn.html(this.listlabel);
		this.$list.slideDown(speed, function() {
			that.$list.on("focusout", function(e) {that.lvefohandler(e); e.stopImmediatePropagation();})
			that.$btn.on("mouseleave", function(e){that.lvefohandler(e); e.stopImmediatePropagation();});
			that.$list.on("mouseleave", function(e){that.lvehandler(e); e.stopImmediatePropagation();});
		});
		this.isOpen = true;
	} else {
		this.$btn.addClass("version-btn");
		this.$btn.removeClass("version-btn-open");
		this.$btn.attr("aria-pressed", false);
		this.$list.attr("aria-hidden", true);
		this.$btn.html(this.label);
		this.$btn.off("mouseleave");
		this.$list.off("mouseleave");
		this.$list.off("focusout");
		this.$list.slideUp(speed, function() {
			if(document.activeElement !== null && document.activeElement !== document && document.activeElement !== document.body) {
				if(that.$sel) {that.$sel.attr("tabindex", -1);}
				that.$btn.focus();
			}
		});
		this.isOpen = false;
	}

	if(d) {
		if(document.activeElement !== null && document.activeElement !== document && document.activeElement !== document.body) {
			var $nw = this.listEnter(this.$btn);
			$nw.attr("tabindex", 0);
			$nw.focus();
			this.$sel = $nw;
		}
	}
},
btnhandler: function() {
	this.listtoggle(300);
},
lvefohandler: function(e) {
	var element = e.toElement || e.relatedTarget;
	var i = 0;
	while(i < 4 && element !== null && element.tagName !== "DIV" && element.tagName !== "UL")  {
		element =  element.parentNode;
		i++;
	}
	if(!this.$list.is(element)) {
		this.listtoggle(200);
	}
	$(e.target).attr("tabindex", -1);
	if($(e.target).attr("id") === "version-dropdown" || $(e.target).attr("id") === "lang-dropdown") {$(e.target).attr("tabindex", 0);}
},
lvehandler: function(e) {
	var element = e.toElement || e.relatedTarget;
	if(element !== null && element.tagName !== "SPAN") {
		if(!this.$btn.is(element)) {
			this.listtoggle(300);
		}
	}
},
keybtnfilter: function(e) {
	if (e.ctrlKey || e.shiftKey) {return false;}
	var k = e.which || e.keyCode;
	if(e.key === " " || e.key === "Enter" || (e.key === "ArrowDown" && e.altKey) || e.key === "ArrowDown" || e.key === "ArrowUp" ||
			k === 32 || k === 13 || (k === 40 && e.altKey) || k === 40 || k === 38) {
		return true;
	}
	return false;
},
keymove: function(e) {
	if (e.ctrlKey || e.shiftKey) {return true;}
	var p = false;
	var k = e.which || e.keyCode;
	var $nw = $(e.target);
	if(e.key === "ArrowUp" || k === 38) {
		p = true;
		$nw = this.listPrev($nw);
	} else if (e.key === "ArrowDown" || k === 40) {
		p = true;
		$nw = this.listNext($nw);
	} else if (e.key === "Home" || k === 36) {
		p = true;
		$nw = this.listFirst($nw);
	} else if (e.key === "End" || k === 35) {
		p = true;
		$nw = this.listLast($nw);
	} else if (e.key === "Escape" || k === 27) {
		p = true;
		$nw = this.listExit($nw);
	} else if (e.key === "ArrowLeft" || k === 37 || e.key === "ArrowRight" || k === 39) {
		p = true;
		$nw = this.listExit($nw);
	}
	if(p) {
		$nw.attr("tabindex", 0);
		$nw.focus();
		this.$sel = $nw;
		e.preventDefault();
		e.stopPropagation();
	}
},
listPrev: function($nw) {
	if ($nw.parent().prev().length !== 0) {
		return $nw.parent().prev().children(":first-child");
	} else {
		return this.listLast($nw);
	}
},
listNext: function($nw) {
	if ($nw.parent().next().length !== 0) {
		return $nw.parent().next().children(":first-child");
	} else {
		return this.listFirst($nw);
	}
},
listFirst: function($nw) {
	return $nw.parent().parent().children(":first-child").children(":first-child");
},
listLast: function($nw) {
	return $nw.parent().parent().children(":last-child").children(":first-child");
},
listExit: function($nw) {
	return $nw.parent().parent().prev();
},
listEnter: function($nw) {
	return $nw.next().children(":first-child").children(":first-child");
}
};
return Drop}();

$(document).ready(function() {
	var lang = DOCUMENTATION_OPTIONS.LANGUAGE;
	if(lang === "None") {lang = "en";}
	if(lang === undefined) {lang = $("#lang-dropdown").html().trim(); DOCUMENTATION_OPTIONS.LANGUAGE = lang;} //@
	var n =  all_langs[lang];
	if(n) {$("#lang-dropdown").html(n);}
	var lng_drop=new Drop("version-dropdown");
	var vsn_drop=new Drop("lang-dropdown");
});
})();
