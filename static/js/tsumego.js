(function(){
    $(document).ready(function(){
        $(".collection-header").click(function() {
            var $this = $(this);
            if ($this.hasClass("loaded")) {
                return;
            }
            $this.addClass("loaded");
            $(this).siblings("ul").children("li").children("a").children("img").each(function () {
                var $this = $(this);
                $this.attr("src", $this.data("src"));
            });
        });
    });
})();
