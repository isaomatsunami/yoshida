$(document).ready(function() {
	// DjangoのCSRF対策に通過するため、Backbone.syncに前処理を加える
	function getCookie(name) {
		var cookieValue = null;
		if (document.cookie && document.cookie != '') {
			var cookies = document.cookie.split(';');
			for (var i = 0; i < cookies.length; i++) {
				var cookie = jQuery.trim(cookies[i]);
				if (cookie.substring(0, name.length + 1) == (name + '=')) {
					// Does this cookie string begin with the name we want?
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
					break;
				}
			}
		}
		return cookieValue;
	};
	var baseSync = Backbone.sync;
	Backbone.sync = function(method, model, options){
		options.beforeSend = function(xhr){
			var csrf = getCookie('csrftoken');
			xhr.setRequestHeader("X-CSRFToken", csrf);
		};
		return baseSync(method, model, options);
	};

  var Line = Backbone.Model.extend({
    idAttribute: "id",
    defaults: function() {  // もしこの属性がないなら追加する
      return { text: "", top: 0, left:0, width:0, height:0, fontsize: 10, letterspace:0, textalign:"center" };
    }
  });

  var Lines = Backbone.Collection.extend({
    model: Line,
    // localStorage: new Backbone.LocalStorage("ocr-backbone"),
    url: function() {
      return '../api/lineinfos';
    },
    comparator: function(a,b){if(a.top == b.top) return a.left > b.left;return a.top > b.top;}
  });

  // The DOM element for Line
  var lineView = Backbone.View.extend({
    tagName:  "div",
    events: {
      "dblclick .linetext"  : "edit", // ダブルクリックで編集開始
      "keypress"  : "updateOnEnter",
      "mouseover" : "mouseover",
      "mouseout"  : "mouseout"
    },
  // font-sizeは10未満にはならないのでchoromeでは詳細設定で最小フォントを変更すること！
    initialize: function() {
      this.listenTo(this.model, 'change', this.render); // 書き換え
      this.listenTo(this.model, 'destroy',this.remove); // 通常のremove
      var self = this;
      this.$el.draggable({
        stop: function( event, ui ) {
          self.model.set({"top":ui.position.top, "left":ui.position.left});
          self.model.save();
        }
      });
      this.$el.html( $('#line-template').html() ).addClass("editableline");

      this.text = this.$(".linetext").css("display","inherit");
      this.input = this.$(".lineedit").css("display","none");
    },
    render: function() {
      this.$el
        .css("position","absolute")
        .css("width", this.model.get("width") +"px")
        .css("height", this.model.get("height") + "px")
        .css("left", this.model.get("left") +"px")
        .css("top", this.model.get("top") + "px")
        .css("font-size", this.model.get("fontsize") +"px");
      this.text
        .css("letter-spacing", this.model.get("letterspace") +"px")
        .css("text-align", this.model.get("textalign"))
        .text(this.model.get("content"));
      return this;
    },
    mouseover : function(){
      this.$el.css("background-color", "#ff0");
      App.highLighted = this;
    },
    mouseout : function(){
      this.$el.css("background-color", "transparent");
      App.highLighted = null;
    },
    resizeHeight: function(){
      console.log("height", this.el.scrollHeight + 5);
      this.model.set("height", this.el.scrollHeight + 5);
      this.render();
    },
    resizeWidth: function(){
      console.log("width", this.el.scrollWidth + 5);
      this.model.set("width", this.el.scrollWidth + 5);
      this.render();
    },
    // 編集開始
    edit: function() {
      if ( App.selectedLineView ) App.selectedLineView.close();
      var width = parseInt( this.$el.css("width") ) * 1.2;
      this.text.css("display", "none");
      this.input.attr("value", this.model.get("content"));
      this.input.css("display","inherit").css("width", width + "px").focus();
      App.lines.trigger("beginEdit", this);
    },
    // 編集終了
    close: function() {
      var value = this.input.val();
      if (value.length == 0) { // 中身がない場合は削除される
        this.clear();
      } else {
        this.model.set({"content": value});
        this.model.save();
        this.text.css("display","inherit"); // textはchangeで変更される
        this.input.css("display","none");
      }
      App.lines.trigger("endEdit",this);
    },
    // 編集中の改行で編集終了
    updateOnEnter: function(e) {
      if (e.keyCode == 13) this.close();
    },
    clear : function(){ // 削除
      console.log("lineView:clear");
      var res = this.model.destroy({
        success: function(model, response){console.log("model destroy success")},
        error:   function(model, response){console.log("model destroy error")}
      });
      if(!res) console.log("model is new, no need to delete");
    }
  });

// 全体のロジック
  var AppView = Backbone.View.extend({
    el: $("#app"),
    events: {},
    initialize: function() {
      // 初期化部分でデータ読み込み
      var id = $("#app").attr("data-document");
      if( id !== undefined){
        Backbone.$.when(
          Backbone.$.ajax({url: encodeURI("../api/pageinfos/?document=" + id)}),
          Backbone.$.ajax({url: encodeURI("../api/lineinfos/?document=" + id)})
        ).then(this.init.bind(this));
      }else{
        id = $("#app").attr("data-page");
        if( id !== undefined ){
          Backbone.$.when(
            Backbone.$.ajax({url: encodeURI("../api/pageinfos/?page=" + id)}),
            Backbone.$.ajax({url: encodeURI("../api/lineinfos/?page=" + id)})
          ).then(this.init.bind(this));
        }
      }
    },
    init: function(res1,res2){
      var _pageInfos = res1[0], _lineInfos = res2[0];
      // console.log(_pageInfos,_lineInfos);
      var that = this;
      // データの再構成
      this.nPage = _pageInfos.length;

      this.lines = new Lines();
      this.listenTo(this.lines, 'add', this.addOne);	// Lineが追加された場合
      this.listenTo(this.lines, 'reset', this.addAll);	// すべての要素がresetされた場合
      this.listenTo(this.lines, 'beginEdit', this.beginEdit);	// ある要素を編集開始した時
      this.listenTo(this.lines, 'endEdit',   this.endEdit);		// ある要素を編集終了した時
      this.sync = $("#sync").hide();
      // requestを開始した時
      this.listenTo(this.lines, 'request', function(_model_or_collection, _xhr, _options){that.sync.attr("src","/static/yoshida/images/sync.gif").show();} );
      // requestが失敗した時
      this.listenTo(this.lines, 'error',   function(_model_or_collection, _response, _options){that.sync.attr("src","/static/yoshida/images/error.png").show();} );
      // 同期が完了した時
      this.listenTo(this.lines, 'sync',    function(_model_or_collection, _response, _options){that.sync.attr("src","/static/yoshida/images/sync.png").show();} );

      var pagelinks = $('#pagelink ul');
      this.$pages = {};

      // ページのリンクを作る
      var compPage = function(a,b){return a.page > b.page ? 1 : -1;};
      _pageInfos.sort(compPage).forEach(function(page){
        var thisPage = page.page, width = page.width, height = page.height, url = page.url;
        var lines = _lineInfos.filter(function(line){return line.pageinfo == page.id;});

        // DOMを組み立てる
        var pageContainer = $(document.createElement("div"))
          .addClass("ocr_pagecontainer")
          .attr("id", "page" + thisPage)
          .css("height", (height + 140) + "px");
        var leftDiv  = $(document.createElement("div")).addClass("ocr_left");
        var rightDiv = $(document.createElement("div")).addClass("ocr_right");
        var pageDiv  = $(document.createElement("div")).addClass("ocr_page")
          .css("width", width +"px")
          .css("height", height + "px");
        that.$pages[page.id] = pageDiv;
        leftDiv.append(pageDiv);
        var pageImg  = $(document.createElement("img")).addClass("ocr_image")
          .attr("src", "../" + url)
          .attr("width", width +"px")
          .attr("height", height + "px");
        that.$el.append(pageContainer);
        rightDiv.append(pageImg);
        // page number
        var pagenumber = $(document.createElement("h4")).addClass("ocr_pagenumber")
          .attr("name", "page" + thisPage)
          .text("Page:" + String(thisPage));
        pageContainer.append(pagenumber);
        var pagelink_li = $(document.createElement("li")).addClass("pageindex");
        var pagelink = $(document.createElement("a"))
          .attr("href", "#page" + thisPage)
          .text("Page:" + String(thisPage));
        pagelink_li.append(pagelink);
        pagelinks.append(pagelink_li);

        pageContainer.append(leftDiv);
        pageContainer.append(rightDiv);
        that.lines.add(lines);
      });

      // UI要素
      // フォーカス行に対する操作
      this.removeLine = $("#removeLine").on("click", this.onRemoveLine.bind(this));
      this.separateLine = $("#separateLine").on("click", this.onSeparateLine.bind(this));
      this.cloneLine = $("#cloneLine").on("click", this.onCloneLine.bind(this));
      this.changeFontSize = $("#changeFontSize");
      this.cleanLine = $("#cleanLine").on("click", this.onCleanLine.bind(this));
      this.changeLetterSpacing = $("#changeLetterSpacing");
      this.changeTextAlign = $("#changeTextAlign");

      $("#inputTextAlign").on("change", this.onChangeTextAlign.bind(this));
      $("#inputFontSize").on("change", this.onChangeFontSize.bind(this));
      $("#inputLetterSpacing").on("change", this.onChangeLetterSpacing.bind(this));
      $("#linecolor").on("change", this.onChangeLineColor.bind(this));

      // 全体に関する操作
      this.replaceWords = $("#replaceWords").on("click", this.onReplaceWords.bind(this));
      this.replaceWordsAll = $("#replaceWordsAll").on("click", this.onReplaceWordsAll.bind(this));
      this.replaceFrom = $("#replaceFrom");
      this.replaceTo = $("#replaceTo");
      this.removeSpace = $("#cleanAllLines").on("click", this.onCleanAllLines.bind(this));
      this.footer = $("#webapp_bottom_fixed").animate({"bottom":"-35px"}, 0);
    },
    render: function() {
      // todo no need?
    },
    addOne: function(line, _collection, _options) {
      var view = new lineView({model:line});
      line.el = view.el; // モデルからDOMを探せるようにする
      if(this.$pages.hasOwnProperty( line.get("pageinfo")) ){
        this.$pages[line.get("pageinfo")].append( view.render().el );
      }else{
        console.log( "this.$pages:", this.$pages.length, "  wrong number of page:", line.get("page") , line);        
      }
    },
    addAll: function(_collection, _options) {
      this.lines.each(this.addOne, this);
    },
    beginEdit: function (lineView) {
      this.selectedLineView = lineView;
      this._editing(true);
    },
    endEdit: function (lineView) {
      this.selectedLineView = null;
      this._editing(false);
    },
    onKey: function(e) {
      if(this.highLighted){
        if (e.keyCode == 72) this.highLighted.resizeHeight(); // Hの時は高くする
        if (e.keyCode == 87) this.highLighted.resizeWidth();  // Wの時は高くする
      }
    },
    _editing: function(b){
      if(b){
        // 行にフォーカスがある場合
        this.replaceWordsAll.hide();
        this.replaceWords.show();
        $("#inputFontSize").val( this.selectedLineView.model.get("fontsize") );
        $("#inputLetterSpacing").val( this.selectedLineView.model.get("letterspace") );
        $("#inputTextAlign").val( this.selectedLineView.model.get("textalign") );
        this.footer.animate({ "bottom":"0px"}, 1000);
      }else{
        this.replaceWordsAll.show();
        this.replaceWords.hide();
        this.footer.animate({ "bottom":"-35px"}, 1000);
      }
    },
    onSeparateLine: function () {
      if(this.selectedLineView){
        // カーソルの前後で分割する
        var txt = this.selectedLineView.input.val();
        var posCaret = this.selectedLineView.input[0].selectionStart;
        var second = this.selectedLineView.model.clone();
        this.selectedLineView.input.val( txt.substring(0, posCaret) );
        this.selectedLineView.model.set("height", second.attributes["fontsize"] + 3);
        second.attributes["text"] = txt.substring(posCaret);
        second.attributes["top"] = second.attributes["top"] + second.attributes["fontsize"] * 2;
        second.attributes["height"] = second.attributes["fontsize"] + 3;
        delete second.attributes[second.idAttribute];
        second = this.lines.add(second.attributes);
        second.save();
      }
      this.selectedLineView.input.focus();
    },
    onCloneLine: function () {
      if(this.selectedLineView){
        var cloned = this.selectedLineView.model.clone();
        cloned.attributes["top"] = cloned.attributes["top"] + cloned.attributes["fontsize"] * 2;
        cloned.attributes["height"] = cloned.attributes["fontsize"] + 3;
        delete cloned.attributes[cloned.idAttribute];
        cloned = this.lines.add(cloned.attributes);
        cloned.save();
      }
      this.selectedLineView.input.focus();
    },
    onCleanLine: function () {
      if(this.selectedLineView){
        var txt = this.selectedLineView.input.val();
        this.selectedLineView.input.val( txt.replace( /[ 　]*/g, "") ); // 半角全角スペース
      }
      this.selectedLineView.input.focus();
    },
    onRemoveLine: function () {
      if(this.selectedLineView){
        this.selectedLineView.clear();
        this.selectedLineView = null;
      }
    },
    onChangeFontSize: function () {
      if(this.selectedLineView){
        this.selectedLineView.model.set("fontsize", $("#inputFontSize").val() );
      }
      this.selectedLineView.input.focus();
    },
    onChangeLetterSpacing: function () {
      if(this.selectedLineView){
        console.log("onChangeLetterSpacing", this.selectedLineView.model.get("letterspace"), $("#inputLetterSpacing").val() );
        this.selectedLineView.model.set("letterspace", $("#inputLetterSpacing").val() );
      }
      this.selectedLineView.input.focus();
    },
    onChangeTextAlign: function () {
      if(this.selectedLineView){
        console.log("onChangeTextAlign", this.selectedLineView.model.get("textalign"), $("#inputTextAlign").val() );
        this.selectedLineView.model.set("textalign", $("#inputTextAlign").val() );
      }
      this.selectedLineView.input.focus();
    },
    onReplaceWords: function () {
      var fromWord = $("#inputReplaceFrom").val(), toWord = $("#inputReplaceTo").val();
      if(this.selectedLineView){
        var txt = this.selectedLineView.input.val();
        this.selectedLineView.input.val( txt.replace(fromWord, toWord) );
      }
      this.selectedLineView.input.focus();
    },
    onReplaceWordsAll: function () {
      var fromWord = $("#inputReplaceFrom").val(), toWord = $("#inputReplaceTo").val();
      this.lines.forEach(function(line){
        var txt = line.get("content").replace(fromWord, toWord);
        line.set("content", txt);
        // line.save();
      });
    },
    onCleanAllLines: function () {
      console.log("onCleanAllLines");
      this.lines.forEach(function(line){
        var txt = line.get("content").replace( /[ 　]*/g, ""); // 半角全角スペース
        line.set("content", txt)
        // line.save();
      });
    },
    onChangeLineColor: function (e) {
      function getCSSRule(_sheetName,_ruleName){
        for(var i = 0, n = document.styleSheets.length;i < n;++i){
          var paths = document.styleSheets[i].href.split("/"), name = paths[paths.length - 1];
          if (name == _sheetName){
            for(var j = 0, m = document.styleSheets[i].cssRules.length;j < m;++j){
              if (document.styleSheets[i].cssRules[j].selectorText == _ruleName) return document.styleSheets[i].cssRules[j];
            }
          }
        }
        return null;
      }
      var _css = getCSSRule("ocr.base.css", ".linetext");
      _css.style.backgroundColor = "#" + e.currentTarget.value;
    }
  });
  // メニューの初期化
  imat.webapp.initMenu();
  // 本体
  var App = new AppView;
});
