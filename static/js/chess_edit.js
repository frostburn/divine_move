(function() {
    var board;
    var $player_cb = $("#player_cb");
    var $white_kingside = $("#white_kingside");
    var $white_queenside = $("#white_queenside");
    var $black_kingside = $("#black_kingside");
    var $black_queenside = $("#black_queenside");
    var $double_pawn_push = $("#double_pawn_push");
    var $fen = $("#fen");
    var $normal_link = $("#normal_link");
    var $stalling_link = $("#stalling_link");

    var onChange = function(old_position, new_position) {
        positionQuery(ChessBoard.objToFen(new_position));
    };

    var positionQuery = function(fen) {
        // Abuses backend fen parsing.
        if (typeof(fen) !== "string"){
            fen = board.fen();
        }
        var color = $player_cb.prop("checked") ? "w" : "b";
        fen += "_" + color;
        var castling = "";
        castling += $white_kingside.prop("checked") ? "K" : "-";
        castling += $white_queenside.prop("checked") ? "Q" : "-";
        castling += $black_kingside.prop("checked") ? "k" : "-";
        castling += $black_queenside.prop("checked") ? "q" : "-";
        fen += "_" + castling;
        fen += "_" + $double_pawn_push.val();
        var url = window.json_url.replace("_", fen);
        $.ajax({
            url: url,
            success: function(data){
                data = JSON.parse(data);
                //console.log(data);
                if (data.status !== "OK"){
                    $fen.val(data.error_message);
                    $normal_link.empty();
                    $stalling_link.empty();
                    return;
                }
                else {
                    $fen.val(data.fen);
                    activateLinks(data, color);
                }
            }
        });
    }

    var activateLinks = function(data, color) {
        var fen = data.fen.replace(/ /g, "_");
        var normal_url = window.chess_url.replace("_", fen);
        $normal_link.attr("href", normal_url);
        $stalling_link.attr("href", normal_url + "?mode=stalling");
        $normal_link.text(getGoal(data, color, "normal"));
        $stalling_link.text(getGoal(data, color, "stalling"));
    }

    var getGoal = function(data, color, mode) {
        var moveColor = "White";
        var otherColor = "Black";
        if (color === "b"){
            moveColor = "Black";
            otherColor = "White";
        }
        var goal;
        var distance;
        if (mode === "normal"){
            goal = data.low;
            distance = data.low_distance;
        }
        else {
            goal = data.high;
            distance = data.high_distance;
        }
        var action;
        var actioning;
        var target = "";
        if (goal === 2){
            action = "mate";
            actioning = "mating";
            target = otherColor;
        }
        else if (goal === 1){
            action = "stalemate";
            actioning = "stalemating";
            target = otherColor;
        }
        else if (goal === 0){
            action = "draw";
            actioning = "drawing";
        }
        else if (goal === -1){
            action = "get stalemated";
            actioning = "getting stalemated";
        }
        else if (goal === -2){
            action = "get mated";
            actioning = "getting mated";
        }
        if (goal === null){
            if (mode === "normal"){
                return moveColor + " cannot force any result";
            }
            else {
                return moveColor + " to prevent any result";
            }
        }
        var fullmoves = Math.floor((distance + 1) / 2);
        if (fullmoves == 0){
            return "Game over";
        }
        else {
            var moves = fullmoves == 1 ? "move" : "moves";
            if (target.length){
                target = " " + target;
            }
            if (mode === "normal"){
                return moveColor + " to " + action + target + " in " + fullmoves + " " + moves;
            }
            else {
                return moveColor + " to delay " + actioning + target + " for " + fullmoves + " " + moves;
            }
        }
    }

    $(document).ready(function() {
        window.chess_cfg.onChange = onChange;
        board = new ChessBoard("board", window.chess_cfg);
        $player_cb.change(positionQuery);
        $white_kingside.change(positionQuery);
        $white_queenside.change(positionQuery);
        $black_kingside.change(positionQuery);
        $black_queenside.change(positionQuery);
        $double_pawn_push.change(positionQuery);
    });
})();
