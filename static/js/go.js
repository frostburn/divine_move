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
            if (mode == "edit"){
                move_num -= 2;
                $('#goal').empty();
            }
            else {
                move_num = Math.floor(0.5 * (move_num - 1)) * 2 - 1;
            }
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

    var board_color = "#db7";

    var scale = 50;
    function draw_coords(coord){
        return [scale * coord_map[coord[0]], scale * parseInt(coord.slice(1))];
    }

    function black_stone(draw, x, y){
        var stone = draw.circle(0.9 * scale).center(x, y).fill("#111");
        return stone;
    }

    function white_stone(draw, x, y){
        var stone = draw.circle(0.9 * scale).center(x, y).fill("#eee");
        return stone;
    }

    function ko_square(draw, x, y){
        var shape = draw.group();
        var bg = shape.rect(1.09 * scale, 1.09 * scale).center(x, y).fill(board_color);
        bg.attr({"fill-opacity": 0.7});
        var square = shape.rect(0.6 * scale, 0.6 * scale).center(x, y).fill("none");
        square.stroke({width: 2, color: "#333"});
        return shape;
    }

    function delete_cross(draw, x, y){
        var shape = draw.group();
        shape.rect(0.1 * scale, 0.8 * scale).center(x, y).fill("#c22");
        shape.rect(0.8 * scale, 0.1 * scale).center(x, y).fill("#c22");
        shape.rotate(45, x, y);
        return shape;
    }

    var board;

    function render_playing_area(draw, data)
    {
        var max_x = 0;
        var max_y = 0;
        var east = {};
        var south = {};
        $(data.playing_area).each(function(_, coord){
            var c = draw_coords(coord);
            var x = c[0];
            var y = c[1];
            if (x > max_x){
                max_x = x;
            }
            if (y > max_y){
                max_y = y;
            }
            east[[x + scale, y]] = true;
            south[[x, y + scale]] = true;
        });
        board = draw.rect(max_x + 3 * scale, max_y + 3 * scale).move(-1.5 * scale, -1.5 * scale).fill(board_color);
        var x = 0;
        $(["A", "B", "C", "D", "E", "F", "G", "H"]).each(function(_, letter){
            if (x > max_x){
                return;
            }
            draw.text(letter).font({size: 0.5 * scale}).center(x, -scale);
            draw.text(letter).font({size: 0.5 * scale}).center(x, max_y + scale);
            x += scale;
        });
        var y = max_y;
        $(["1", "2", "3", "4", "5", "6", "7", "8"]).each(function(_, number){
            if (y < 0){
                return;
            }
            draw.text(number).font({size: 0.5 * scale}).center(-scale, y);
            draw.text(number).font({size: 0.5 * scale}).center(max_x + scale, y);
            y -= scale;
        });
        $(data.playing_area).each(function(_, coord){
            var c = draw_coords(coord);
            var x = c[0] - 0.5;
            var y = c[1] - 0.5;
            if (east[c]){
                draw.line(x - scale, y, x, y).stroke({
                    width: 1,
                    color: "#111"
                });
            }
            if (south[c]){
                draw.line(x, y - scale, x, y).stroke({
                    width: 1,
                    color: "#111"
                });
            }
        });
    }

    var board_objects = {};
    var missing_objects = {};
    var ko = null;
    var hints = [];
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
        if (ko !== null){
            ko.remove();
            ko = null;
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
            var c = draw_coords(coord);
            ko = ko_square(draw, c[0], c[1]);
        });
        $.each(missing_objects, function(coord, object){
            delete board_objects[coord];
            object.remove();
        });
        var $pass = $("#pass");
        if (mode == "edit"){
            $(hints).each(function(_, object){
                object.remove();
            });
            $pass.removeClass("btn-success btn-primary btn-info");
            hints = [];
            var coincidents = {};
            $(data.strong_low_moves).each(function(_, coord){
                if (coord == "pass"){
                    $pass.addClass("btn-success");
                    coincidents[coord] = true;
                }
                else {
                    var c = draw_coords(coord);
                    var hint = draw.circle(0.2 * scale).center(c[0], c[1]).fill("#1d1");
                    coincidents[coord] = hint;
                    hints.push(hint);
                }
            });
            $(data.strong_high_moves).each(function(_, coord){
                if (coord == "pass"){
                    if (coord in coincidents){
                        $pass.removeClass("btn-success");
                        $pass.addClass("btn-info");
                    }
                    else{
                        $pass.addClass("btn-primary");
                    }
                }
                else {
                    if (coord in coincidents){
                        coincidents[coord].fill("#1dd");
                    }
                    else {
                        var c = draw_coords(coord);
                        var hint = draw.circle(0.2 * scale).center(c[0], c[1]);
                        hint.fill("#33d");
                        hints.push(hint);
                    }
                }
            });
        }
        $(hovers).each(function(_, object){
            object.remove();
        });
        hovers = [];
        var $status = $("#status");
        $pass.off("click");
        $pass.prop("disabled", true);
        var moves = data.moves;
        if (mode == "edit"){
            var edit_type = $("input[name=edit_type]:checked").val();
            if (black_to_play() ? edit_type == "white" : edit_type == "black"){
                player = opponent;
                moves = data.opponent_edits;
            }
            else if (black_to_play() ? edit_type == "black": edit_type == "white"){
                moves = data.player_edits;
            }
            else if (edit_type == "delete"){
                player = delete_cross;
                moves = data.deletes;
            }
        }
        $.each(moves, function(coord, endgame){
            if (coord == "pass"){
                $pass.prop("disabled", false);
                $pass.click(function(){
                    undos.push(data.endgame);
                    next_endgame(endgame);
                });
                return;
            }
            var c = draw_coords(coord);
            var stone = player(draw, c[0], c[1]);
            stone.attr({"fill-opacity": 0.0});
            var hover = draw.rect(scale, scale).center(c[0], c[1]);
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
        var svg = SVG("board");
        var draw = svg.group();
        background_draw = draw.nested();
        foreground_draw = draw.nested();
        render_playing_area(background_draw, data);
        render_stones(foreground_draw, data);
        draw.move(-board.x(), -board.y());
        svg.size(board.width(), board.height());
        svg.addClass('center-block');
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
            var $status = $("#status");
            if (coord == "pass"){
                if (ko !== null){
                    $status.text("The opponent cleared the ko.");
                }
                else {
                    $status.text("The opponent passed.");
                }
            }
            else {
                $status.empty();
            }
            var endgame = data.moves[coord];
            next_endgame(endgame);
            return false;
        }
        return true;
    }

    function next_endgame(endgame){
        if (mode == "edit"){
            var edit_type = $("input[name=edit_type]:checked").val();
            if (edit_type == "alternate"){
                move_num += 1;
            }
        }
        else {
            move_num += 1;
        }
        var parts = window.json_url.split("/");
        parts[parts.length - 2] = endgame;
        var url = parts.join("/");
        $.ajax({
            url: url,
            success: function(data){
                data = JSON.parse(data);
                //console.log(data);
                if (data.status != "OK"){
                    return;
                }
                current_data = data;
                render_stones(foreground_draw, data);
                if (play_book_move(data)){
                    set_goal(data);
                    var $status = $("#status");
                    if (mode == "edit"){
                        if (data.passes == 1){
                            $status.text("The opponent passed.");
                        }
                        else if (data.passes == 2){
                            $status.text("The game has ended.");
                        }
                        else {
                            $status.empty();
                        }
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
            if (mode == "edit"){
                $("#normal_link").text(player + " won by " + result + ".").attr("href", url + "mode=normal");
                $("#stalling_link").text(player + " won by " + result + ".").attr("href", url + "mode=stalling");
            }
            else {
                $goal.text(player + " won by " + result + ".");
                $("#edit_link").attr("href", url + "mode=edit");
            }
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
                $("#edit_link").attr("href", url + "mode=edit");
            }
        }
    }

    var current_data;
    $(document).ready(function(){
        $.ajax({
            url: window.json_url,
            success: function(data){
                data = JSON.parse(data);
                //console.log(data);
                if (data.status != "OK"){
                    return;
                }
                if (data.passes == 1){
                    $("#status").text("The opponent passed.");
                }
                render_board(data);
                set_goal(data);
                current_data = data;
                $("input[name=edit_type]").change(function(){render_stones(foreground_draw, current_data);});
            }
        });
    });
})();
