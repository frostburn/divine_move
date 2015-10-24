(function(){
    var move_num = 0;

    var undos = [];

    var coord_map = {
        "A": 0,
        "B": 1,
        "C": 2,
        "D": 3,
        "E": 4,
        "F": 5,
        "G": 6,
        "H": 7,
        "I": 8,
    };

    var game_info_structure = [
        ["black_player", "Black player"],
        ["black_rank", "Black rank"],
        ["white_player", "White player"],
        ["white_rank", "White rank"],
        ["result", "Result"],
        ["date", "Date"],
        ["handicap", "Handicap"],
        ["komi", "Komi"],
        ["event", "Event"],
        ["round", "Round"],
        ["place", "Place"],
        ["rules", "Rules"],
        ["time", "Game time"],
        ["overtime", "Overtime"],
        ["move_number", "Move number"],
        ["total_moves", "Number of Moves"]
    ];

    function heat_map(score){
        var rgb;
        if (score < -7){
            rgb = [0, 0, Math.pow((81 + score) / 74, 2)];
        }
        else if (score < 7){
            rgb = [(7 + score) / 14, 0, (7 - score) / 14];
        }
        else {
            var w = Math.pow((score - 7) / 74, 2);
            rgb = [1, w, w];
        }
        return "rgb(" + (255 * rgb[0]).toFixed(0) + ", " + (255 * rgb[1]).toFixed(0) + ", " + (255 * rgb[2]).toFixed(0) + ")";
    }

    var board_color = "#db7";

    var scale = 40;
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

    var board;

    function render_playing_area(draw)
    {
        var max_x = 8 * scale;
        var max_y = 8 * scale;
        board = draw.rect(max_x + 3 * scale, max_y + 3 * scale).move(-1.5 * scale, -1.5 * scale).fill(board_color);
        var x = 0;
        $(["A", "B", "C", "D", "E", "F", "G", "H", "J"]).each(function(_, letter){
            draw.text(letter).font({size: 0.5 * scale}).center(x, -scale);
            draw.text(letter).font({size: 0.5 * scale}).center(x, max_y + scale);
            x += scale;
        });
        var y = max_y;
        $(["1", "2", "3", "4", "5", "6", "7", "8", "9"]).each(function(_, number){
            draw.text(number).font({size: 0.5 * scale}).center(-scale, y);
            draw.text(number).font({size: 0.5 * scale}).center(max_x + scale, y);
            y -= scale;
        });
        for (var x = -0.5; x < 8 * scale; x += scale){
            draw.line(x, -0.5, x, 8 * scale - 0.5).stroke({
                width: 1,
                color: "#111"
            });
        }
        for (var y = -0.5; y < 8 * scale; y += scale){
            draw.line(-0.5, y, 8 * scale - 0.5, y).stroke({
                width: 1,
                color: "#111"
            });
        }
        for (var y = 2 * scale - 0.5; y < 7 * scale; y += 2 * scale){
            for (var x = 2 * scale - 0.5; x < 7 * scale; x += 2 * scale){
                draw.circle(0.15 * scale).center(x, y).fill("#111");
            }
        }
    }

    var hover_blacks = {};
    var hover_whites = {};
    var hover_triggers = {};
    function add_hovers(draw, hover_draw)
    {
        $(["A", "B", "C", "D", "E", "F", "G", "H", "I"]).each(function(_, x){
            $([0, 1, 2, 3, 4, 5, 6, 7, 8]).each(function(_, y){
                var coord = x + y;
                var c = draw_coords(coord);
                var stone = black_stone(draw, c[0], c[1]);
                stone.attr({"fill-opacity": 0.0});
                hover_blacks[coord] = stone;
                stone = white_stone(draw, c[0], c[1]);
                stone.attr({"fill-opacity": 0.0});
                hover_whites[coord] = stone;
                var trigger = hover_draw.rect(scale, scale).center(c[0], c[1]);
                trigger.attr({"fill-opacity": 0.0});
                hover_triggers[coord] = trigger;
            });
        });
    }

    var board_objects = {};
    var missing_objects = {};
    var ko = null;
    var hints = [];

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

    function set_score(data){
        var $score = $("#score");
        if ("low_score" in data && data.low_score !== null){
            if (data.low_score == data.high_score){
                var score = data.low_score
                if (!black_to_play()){
                    score = -score;
                }
                if (score >= 0){
                    $score.text("B+" + score);
                }
                else {
                    $score.text("W+" + (-score));
                }
            }
            else {
                var low = data.low_score;
                var high = data.high_score;
                if (!black_to_play()){
                    var temp = low;
                    low = -high;
                    high = -temp;
                }
                if (low >= 0){
                    low = "+" + low;
                }
                if (high >= 0){
                    high = "+" + high;
                }
                $score.text("From B" + low + " to B" + high + ", depending on super-ko rules.");
            }
        }
        else {
            $score.text("unknown");
        }
    }

    function render_stones(draw, hint_draw, data){
        var player, opponent, hover_players, hover_opponents;
        if (black_to_play()){
            player = black_stone;
            opponent = white_stone;
            hover_players = hover_blacks;
            hover_opponents = hover_whites;
        }
        else {
            player = white_stone;
            opponent = black_stone;
            hover_players = hover_whites;
            hover_opponents = hover_blacks;
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
        $(hints).each(function(_, object){
            object.remove();
        });
        hints = [];
        var $status = $("#status");
        var $statistics = $("#statistics");
        $statistics.empty();
        var $stats_row;
        $statistics_row = $("#statistics_row");
        $game_info_row = $("#game_info_row");
        $game_info = $("#game_info");
        $game_info.empty();
        if (data.info){
            $statistics_row.addClass("hidden");
            $game_info_row.removeClass("hidden");
            $(game_info_structure).each(function(_, kn){
                var key = kn[0];
                var name = kn[1];
                var value = data.info[key];
                if (String(value).length){
                    var $tr = $("<tr>");
                    var $td = $("<td>");
                    $td.html(name + ": " + value);
                    $tr.append($td);
                    $game_info.append($tr);
                }
            });
        }
        else {
            $statistics_row.removeClass("hidden");
            $game_info_row.addClass("hidden");
        }
        var $next = $("#next");
        var next_found = false;
        $next.off("click");
        $pass.off("click");
        $pass.prop("disabled", true);
        var label_index = 0;
        var moves = data.moves;

        $.each(hover_triggers, function(_, trigger){
            trigger.off();  // Doesn't seem to work.
            trigger.mouseover(function(){});
            trigger.mouseout(function(){});
            trigger.click(function(){});
        });

        $.each(hover_players, function(_, stone){
            stone.attr({"fill-opacity": 0.0});
        });
        $.each(hover_opponents, function(_, stone){
            stone.attr({"fill-opacity": 0.0});
        });


        $(moves).each(function(index, move_data){
            var make_move = function(event){
                event.preventDefault();
                undos.push(data.endgame);
                $status.empty();
                next_endgame(move_data);
                $("button.vote").prop("disabled", false);
            }
            if (!next_found && (move_data.color || move_data.label)){
                $next.click(make_move);
                next_found = true;
            }
            if (move_data.label){
                if (label_index % 2 == 0){
                    $stats_row = $('<tr>');
                }
                var $td = $('<td width="5%">');
                $td.html(move_data.label)
                $td.addClass("noselect");
                $td.css("cursor", "pointer");
                $td.hover(
                    function(){
                        $(this).addClass("active");
                    },
                    function(){
                        $(this).removeClass("active");
                    }
                );
                $td.click(make_move);
                $stats_row.append($td);
                $td = $('<td width="45%">');
                var score = move_data.low_score;
                if (score !== null && score !== undefined){
                    if (black_to_play()){
                        score = -score;
                    }
                    if (score >= 0){
                        score = " B+" + score;
                    }
                    else {
                        score = " W+" + (-score);
                    }
                }
                else {
                    score = "";
                }
                $td.html((100 * move_data.likelyhood).toFixed(1) + "% (" + move_data.times_played + ")" + score);
                $stats_row.append($td);
                if (label_index % 2 == 0){
                    $statistics.append($stats_row);
                }
                label_index += 1;
            }
            var coord = move_data.coord;
            if (coord == "pass"){
                $pass.prop("disabled", false);
                $pass.click(make_move);
                return;
            }
            var trigger = hover_triggers[coord];
            var stone = hover_players[coord];
            trigger.mouseover(function(){
                stone.attr({"fill-opacity": 0.5});
            });
            trigger.mouseout(function(){
                stone.attr({"fill-opacity": 0.0});
            });
            trigger.click(make_move);
            var c = draw_coords(coord);
            if (move_data.color){
                var hint = hint_draw.rect(0.9 * scale, 0.9 * scale).center(c[0], c[1]);
                hint.fill(move_data.color).attr({"fill-opacity": 0.5});
                hints.push(hint);
            }
            if (move_data.label){
                var label = draw.text(move_data.label).font({size: 0.7 * scale}).center(c[0], c[1]).fill("#eee");
                hints.push(label);
            }
            var val = move_data.heuristic_value;
            if (val !== null && val !== undefined){
                var hint = hint_draw.rect(1.0 * scale, 1.0 * scale).center(c[0], c[1]);
                hint.fill(heat_map(-move_data.heuristic_value));
                hint.attr({"fill-opacity": 0.75});
                hints.push(hint);
            }
        });
        if (!$statistics.html()){
            $statistics_row.addClass("hidden");
        }
    }

    var background_draw;
    var midground_draw;
    var foreground_draw;
    var hover_draw;

    function render_board(data){
        var svg = SVG("board");
        var draw = svg.group();
        background_draw = draw.nested();
        midground_draw = draw.nested();
        foreground_draw = draw.nested();
        hover_draw = draw.nested();
        render_playing_area(background_draw);
        add_hovers(foreground_draw, hover_draw);
        render_stones(foreground_draw, midground_draw, data);
        set_score(data);
        draw.move(-board.x(), -board.y());
        svg.size(board.width(), board.height());
        svg.addClass("center-block");
    }

    function next_endgame(move_data){
        move_num += 1;
        var parts = window.json_url.split("/");
        parts[parts.length - 2] = move_data.endgame;
        var url = parts.join("/");
        var $vote_buttons = $("button.vote")
        $vote_buttons.prop("disabled", true);
        var $resolve = $("#resolve");
        $resolve.addClass("hidden");
        //console.log(move_data);
        $.ajax({
            url: url,
            dataType: "json",
            success: function(data){
                console.log(data);
                if (data.status != "OK"){
                    return;
                }
                current_data = data;
                render_stones(foreground_draw, midground_draw, data);
                set_score(data);
                var $status = $("#status");
                if (data.passes == 1){
                    $status.text("The opponent passed.");
                }
                else if (data.passes == 2){
                    $status.text("The game has ended.");
                    $resolve.removeClass("hidden");
                }
                else {
                    $status.empty();
                }
                $vote_buttons.each(function(){
                    var $this = $(this);
                    var name = $this.attr("name");
                    var num = move_data[name];
                    $this.data("num", num);
                    if (num){
                        $this.text(name + " (" + num + ")");
                    }
                    else {
                        $this.text(name);
                    }
                });
            }
        });
    }

    var current_data;
    $(document).ready(function(){
        $("#undo").click(function(){
            if (undos.length){
                move_num -= 2;
                next_endgame({"endgame": undos.pop()});
            }
        });
        $("button.vote").click(function(){
            $("button.vote").prop("disabled", true);
            var $this = $(this);
            var name = $this.attr("name");
            var num = $this.data("num");
            $this.text(name + " (" + (num + 1) + ")");
            var data = {
                "type": name,
                "source": undos[undos.length - 1],
                "target": current_data.endgame
            };
            $.post(window.json_url, JSON.stringify(data));
        });
        $("#resolve").click(function(){
            if (!confirm("Are you sure you want to resolve this position?\nAll stones will be considered alive.")){
                return;
            }
            $("#resolve").addClass("hidden");
            var history = undos.slice();
            history.push(current_data.endgame);
            var data = {
                "resolve": history
            };
            $.post(
                window.json_url,
                JSON.stringify(data),
                function(data) {
                    set_score(data);
                },
                "json"
            );
        });
        $("#end").click(function(){
            var parts = window.end_json_url.split("/");
            parts[parts.length - 2] = current_data.endgame;
            var url = parts.join("/");
            $.ajax({
                url: url,
                dataType: "json",
                success: function(data){
                    if (data.length){
                        move_num += data.length - 1;
                        undos.push(current_data.endgame);
                        $.merge(undos, data.slice(0, data.length - 1));
                        // Clear the board. Color changing objects are a pain.
                        $.each(board_objects, function(coord, object){
                            delete board_objects[coord];
                            object.remove();
                        });
                        next_endgame({"endgame": data[data.length - 1]});
                    }
                }
            });
        });
        $.ajax({
            url: window.json_url,
            dataType: "json",
            success: function(data){
                console.log(data);
                if (data.status != "OK"){
                    return;
                }
                if (data.passes == 1){
                    $("#status").text("The opponent passed.");
                }
                render_board(data);
                current_data = data;
            }
        });
    });
})();
