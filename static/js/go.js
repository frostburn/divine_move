(function(){
    var mode = "normal";
    if (window.location.search.indexOf("mode=stalling") >= 0){
        mode = "stalling";
    }
    else if (window.location.search.indexOf("mode=edit") >= 0){
        mode = "edit";
    }

    var move_num = 0;

    var undos = [];

    $("#undo").click(function(){
        if (undos.length){
            move_num = Math.floor(0.5 * (move_num - 1)) * 2 - 1;
            next_endgame(undos.pop());
        }
    });

    var coord_map = {
        "A": 0,
        "B": 1,
        "C": 2,
        "D": 3,
        "E": 4,
        "F": 5,
        "G": 6,
        "H": 7
    };

    var scale = 50;
    function draw_coords(coord){
        return [scale * coord_map[coord[0]], scale * parseInt(coord.slice(1))];
    }

    function black_stone(draw, x, y){
        var stone = draw.circle(0.9 * scale).center(x + 0.5 * scale, y + 0.5 * scale).fill("#111");
        return stone;
    }

    function white_stone(draw, x, y){
        var stone = draw.circle(0.9 * scale).center(x + 0.5 * scale, y + 0.5 * scale).fill("#eee");
        return stone;
    }

    function ko_square(draw, x, y){
        var square = draw.rect(0.7 * scale, 0.7 * scale).center(x + 0.5 * scale, y + 0.5 * scale).fill("none");
        square.stroke({width: 1, color: "#222"});
        return square;
    }

    function render_playing_area(draw, data)
    {
        var east = {};
        var south = {};
        $(data.playing_area).each(function(_, coord){
            var c = draw_coords(coord);
            var x = c[0];
            var y = c[1];
            draw.rect(scale, scale).move(x, y).fill("#db7");
            east[[x + scale, y]] = true;
            south[[x, y + scale]] = true;
        });
        $(data.playing_area).each(function(_, coord){
            var c = draw_coords(coord);
            var x = c[0];
            var y = c[1];
            if (east[c]){
                draw.line(x - 0.5 * scale, y + 0.5 * scale, x + 0.5 * scale, y + 0.5 * scale).stroke({
                    width: 1,
                    color: "#111"
                });
            }
            if (south[c]){
                draw.line(x + 0.5 * scale, y - 0.5 * scale, x + 0.5 * scale, y + 0.5 * scale).stroke({
                    width: 1,
                    color: "#111"
                });
            }
        });
    }

    var board_objects = {};
    var missing_objects = {};
    var hovers = [];

    function add_object(draw, coord, shape){
        if (coord in board_objects){
            delete missing_objects[coord];
        }
        else {
            var c = draw_coords(coord);
            var object = shape(draw, c[0], c[1]);
            board_objects[coord] = object;
        }
    }

    function black_to_play(){
        var result = move_num % 2 == 0;
        if (window.location.search.indexOf("player=white") >= 0){
            return !result;
        }
        return result;
    }

    function render_stones(draw, data){
        var player, opponent;
        if (black_to_play()){
            player = black_stone;
            opponent = white_stone;
        }
        else {
            player = white_stone;
            opponent = black_stone;
        }
        missing_objects = {};
        $.each(board_objects, function(coord, object){
            missing_objects[coord] = object;
        });
        $(data.player).each(function(_, coord){
            add_object(draw, coord, player);
        });
        $(data.opponent).each(function(_, coord){
            add_object(draw, coord, opponent);
        });
        $(data.ko).each(function(_, coord){
            add_object(draw, coord, ko_square);
        });
        $.each(missing_objects, function(coord, object){
            delete board_objects[coord];
            object.remove();
        });
        $(hovers).each(function(_, object){
            object.remove();
        });
        hovers = [];
        var $pass = $("#pass");
        var $status = $("#status");
        $pass.off();
        $.each(data.moves, function(coord, endgame){
            if (coord == "pass"){
                $pass.click(function(){
                    undos.push(data.endgame);
                    next_endgame(endgame);
                });
                return;
            }
            var c = draw_coords(coord);
            var stone = player(draw, c[0], c[1]);
            stone.attr({"fill-opacity": 0.0});
            var hover = draw.rect(scale, scale).move(c[0], c[1]);
            hover.attr({"fill-opacity": 0.0});
            hover.mouseover(function(){
                stone.attr({"fill-opacity": 0.5});
            });
            hover.mouseout(function(){
                stone.attr({"fill-opacity": 0.0});
            });
            hover.click(function(event){
                event.preventDefault();
                undos.push(data.endgame);
                $status.empty();
                next_endgame(endgame);
            });
            hovers.push(stone);
            hovers.push(hover);
        });
    }

    var background_draw;
    var foreground_draw;

    function render_board(data){
        var draw = SVG("board").size(300, 300);
        background_draw = draw.nested();
        foreground_draw = draw.nested();
        render_playing_area(background_draw, data);
        render_stones(foreground_draw, data);
    }

    function play_book_move(data){
        if (move_num % 2 == 0){
            return true;
        }
        if (mode == "normal" || mode == "stalling"){
            var moves;
            if (mode == "normal"){
                moves = data.strong_high_moves;
            }
            else {
                moves = data.strong_low_moves;
            }
            var move_count = moves.length;
            if (!move_count){
                return true;
            }
            var index = Math.floor(Math.random() * move_count);
            var coord = moves[index];
            var endgame = data.moves[coord];
            next_endgame(endgame);
            return false;
        }
        return true;
    }

    function next_endgame(endgame){
        move_num += 1;
        var parts = window.json_url.split("/");
        parts[parts.length - 2] = endgame;
        var url = parts.join("/");
        $.ajax({
            url: url,
            success: function(data){
                data = JSON.parse(data);
                if (data.status != "OK"){
                    return;
                }
                //console.log(data);
                render_stones(foreground_draw, data);
                if (play_book_move(data)){
                    set_goal(data);
                    var $status = $("#status");
                    if (data.passes == 1){
                        $status.text("The opponent passed.");
                    }
                    else {
                        $status.empty();
                    }
                }
            }
        });
    }

    function set_goal(data){
        var $goal = $("#goal");
        var player = black_to_play() ? "Black" : "White";
        var  parts = window.link_url.split("/");
        parts[parts.length - 2] = parseInt(data.endgame).toString(36);
        var url = parts.join("/");
        url += "?player=" + player.toLowerCase() + "&";
        if ($.isEmptyObject(data.moves)){
            var result = data.low;
            if (move_num % 2 == 1){
                player = black_to_play() ? "White" : "Black";
                result = -data.high;
            }
            $goal.text(player + " won by " + result + ".");
        }
        else {
            var normal_text = player + " to win by " + data.low + " in " + data.low_distance + " moves.";
            var stalling_text = player + " to delay winning by " + data.high + " for " + data.high_distance + " moves.";
            if (mode == "normal"){
                $goal.text(normal_text);
            }
            else if (mode == "stalling"){
                $goal.text(stalling_text);
            }
            if (mode == "edit"){
                $("#normal_link").text(normal_text).attr("href", url + "mode=normal");
                $("#stalling_link").text(stalling_text).attr("href", url + "mode=stalling");
            }
            else {
                $("#edit_link").text("edit").attr("href", url + "mode=edit");
            }
        }
    }

    $(document).ready(function(){
        $.ajax({
            url: window.json_url,
            success: function(data){
                data = JSON.parse(data);
                if (data.status != "OK"){
                    return;
                }
                //console.log(data);
                render_board(data);
                set_goal(data);
            }
        });
    });
})();
