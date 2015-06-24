(function() {
    var board;
    var game = new Chess();
    var $status = $("#status");
    var $goal = $("#goal");
    var $solution_link = $("#solution_link");
    var $solution = $("#solution");
    var $undo = $("#undo");

    var mode = "normal";
    if (window.location.search.indexOf("mode=stalling") >= 0){
        mode = "stalling";
    }

    var undos = [];

    var onUndo = function(e) {
        e.preventDefault();
        if (undos.length){
            var fen = undos.pop();
            game.load(fen);
            board.position(fen);
            $goal.show();
            $solution_link.show();
            $solution.show();
            $solution.addClass("hidden");
            updateGoal();
        }
    }

    // do not pick up pieces if the game is over
    // only pick up pieces for the side to move
    var onDragStart = function(source, piece, position, orientation) {
        if (game.in_checkmate() || game.in_stalemate() ||
           (game.turn() === "w" && piece.search(/^b/) !== -1) ||
           (game.turn() === "b" && piece.search(/^w/) !== -1)) {
            return false;
        }
    };

    var onDrop = function(source, target) {
        var currentPosition = game.fen();
        
        var promotion = "q";
        var piece = game.get(source);
        var promotion_rank = game.turn() === "w" ? "7" : "2";
        if (piece.type === "p" && source[1] === promotion_rank){
            // test move legality before prompting
            var move = game.move({
                from: source,
                to: target,
                promotion: promotion,
            });
            if (move === null){
                return "snapback";
            }
            // undo test move and prompt for desired promotion
            game.load(currentPosition);
            promotion = prompt("Select promotion n/r/b/q", "q").toLowerCase();
            if (promotion == "knight"){
                promotion = "n";
            }
            else {
                promotion = promotion[0];
            }
            if ("nrbq".search(promotion) === -1){
                promotion = "q";
            }
        }


        // see if the move is legal
        var move = game.move({
            from: source,
            to: target,
            promotion: promotion,
        });

        // illegal move
        if (move === null){
            return "snapback";
        }

        undos.push(currentPosition);
        $solution.addClass("hidden");
    };

    // update the board position after the piece snap 
    // for castling, en passant, pawn promotion
    var onSnapEnd = function() {
        board.position(game.fen());
        playBookMove();
    };

    var updateStatus = function(data) {
        var game_over = false;
        var status = "";

        var moveColor = "White";
        if (game.turn() === "b") {
            moveColor = "Black";
        }

        // checkmate?
        if (game.in_checkmate()) {
            status = "Game over, " + moveColor + " is in checkmate.";
            game_over = true;
        }
        // stalemate?
        else if (game.in_stalemate()) {
            status = "Game over, " + moveColor + " is in stalemate.";
            game_over = true;
        }
        // draw according to backend?
        else if (!data.strong_low_children.length && !data.strong_high_children.length){
            status = "Game over, draw.";
            game_over = true;
        }
        if (game_over){
            $goal.hide();
            $solution_link.hide();
            $solution.hide();
        }
        // game still on
        else {
            status = moveColor + " to move";
            // check?
            if (game.in_check()) {
                status += ", " + moveColor + " is in check";
            }
        }

        $status.text(status);
    };

    var updateSolution = function(strong_moves, weak_moves) {
        var strong = {};
        var weak = {};
        $(strong_moves).each(function(_, fen){
            strong[fen.split(" ")[0]] = true;
        });
        $(weak_moves).each(function(_, fen){
            weak[fen.split(" ")[0]] = true;
        });
        var strongs = "";
        var weaks = "";
        var mistakes = "";
        var currentPosition = game.fen();
        $(game.moves()).each(function(_, move){
            game.load(currentPosition);
            game.move(move);
            var key = game.fen().split(" ")[0];
            if (key in strong) {
                strongs += move + " ";
            }
            else if (key in weak) {
                weaks += move + " ";
            }
            else {
                mistakes += move + " ";
            }
        });
        game.load(currentPosition);
        $("#strong_moves").text(strongs);
        $("#weak_moves").text(weaks);
        $("#mistakes").text(mistakes);
    }

    var positionQuery = function(callback) {
        var fen = game.fen().replace(/ /g, "_");
        var url = window.json_url.replace("_", fen);
        $.ajax({
            url: url,
            success: function(data){
                data = JSON.parse(data);
                //console.log(data);
                if (data.status !== "OK"){
                    return;
                }
                callback(data);
            }
        });
    }

    var updateGoal = function() {
        positionQuery(updateGoalCallback);
    }

    var updateGoalCallback = function(data) {
        var moveColor = "White";
        var otherColor = "Black";
        if (game.turn() === "b") {
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
                $goal.text(moveColor + " cannot force any result.");
                updateSolution(data.strong_high_children, data.weak_high_children);
                //$solution_link.hide();
                //$solution.hide();
            }
            else {
                $goal.text(moveColor + " to prevent any result.");
                updateSolution(data.strong_high_children, data.weak_high_children);
            }
            updateStatus(data);
            return;
        }
        var fullmoves = Math.floor((distance + 1) / 2);
        if (fullmoves == 0){
            $goal.empty();
        }
        else {
            var moves = fullmoves == 1 ? "move" : "moves";
            if (target.length){
                target = " " + target;
            }
            if (mode === "normal"){
                $goal.text(moveColor + " to " + action + target + " in " + fullmoves + " " + moves + ".");
            }
            else {
                $goal.text(moveColor + " to delay " + actioning + target + " for " + fullmoves + " " + moves + ".");
            }
        }

        updateStatus(data);
        if (mode === "normal"){
            updateSolution(data.strong_low_children, data.weak_low_children);
        }
        else {
            updateSolution(data.strong_high_children, data.weak_high_children);
        }
    }

    var playBookMove = function() {
        positionQuery(playBookMoveCallback);
    }

    var playBookMoveCallback = function(data) {
        var children;
        if (mode == "normal"){
            children = data.strong_high_children;
        }
        else {
            children = data.strong_low_children;
        }
        var move_count = children.length;
        if (!move_count){
            updateStatus(data);
            return;
        }
        var index = Math.floor(Math.random() * move_count);
        var fen = children[index];
        game.load(fen);
        board.position(game.fen());
        updateGoal();
    }

    $(document).ready(function() {
        $solution_link.click(function (e){
            e.preventDefault();
            $solution.removeClass("hidden");
        });
        $undo.click(onUndo);
        window.chess_cfg.onDragStart = onDragStart;
        window.chess_cfg.onDrop = onDrop;
        window.chess_cfg.onSnapEnd = onSnapEnd;
        board = new ChessBoard("board", window.chess_cfg);
        if (!game.load(window.chess_cfg.position)){
            alert("Invalid position");
            game.clear();
        }
        updateGoal();
    });
})();
